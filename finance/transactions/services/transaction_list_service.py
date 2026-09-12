import copy
import logging
from collections import defaultdict
from decimal import Decimal

import pandas as pd
from django.db import IntegrityError, transaction
from rest_framework.exceptions import ValidationError

from changelog.models import ActionEnum, SectionEnum
from changelog.signals import log_change_signal
from finance.payees.models import DestinationMap
from finance.transactions.models import Transaction
from finance.transactions.serializers import ResponseTransactionSerializer, TransactionSerializer
from finance.transactions.validators.transaction_validator import TransactionListValidator
from oauth.middleware import get_current_user


class TransactionListService:

    def get_queryset(self):
        return Transaction.objects.select_related('category', 'subcategory', 'account', 'user')

    def _group_by(self, data):
        if hasattr(data, 'empty') and data.empty:
            return []
        if isinstance(data, pd.DataFrame):
            records = data.to_dict('records')
        elif isinstance(data, list):
            records = data
        else:
            return []

        if not records:
            return []

        groups = defaultdict(lambda: {'month_text': '', 'total': 0.0, 'transactions': []})
        for item in records:
            item_dict = dict(item)
            try:
                amt = float(item_dict.get('amount') or 0.0)
            except (ValueError, TypeError):
                amt = 0.0
            item_dict['amount'] = float('{:.2f}'.format(amt))
            key = (item_dict.get('year'), item_dict.get('month'))
            group = groups[key]
            group['month_text'] = item_dict.get('month_text', '')
            group['total'] += amt
            group['transactions'].append(item_dict)

        group_data = []
        for (year, month), val in groups.items():
            group_data.append({
                'year': year,
                'month': month,
                'month_text': val['month_text'],
                'total': float('{:.2f}'.format(val['total'])),
                'transactions': val['transactions']
            })
        return list(reversed(group_data))

    def get_transaction_by_id(self, transaction_id):
        try:
            transaction = self.get_queryset().get(pk=transaction_id)
            serializer = ResponseTransactionSerializer(transaction)
            return serializer.data
        except Transaction.DoesNotExist:
            logging.error(f"Transaction with id {transaction_id} does not exist.")
            return None
        except Exception as e:
            logging.exception("An unexpected error occurred while fetching transaction: %s", e)
            return None

    def get_transactions(self, query_params):

        TransactionListValidator().validate(query_params)
        year = query_params.get('year', None)
        target = query_params.get('target', None)
        category_ids = query_params.get('cat', None)
        subcategory_ids = query_params.get('subcat', None)
        filter_params = {'is_deleted': False, 'date__year': year}

        if target == 'payment':
            filter_params['is_payment'] = True
        elif target == 'saving':
            filter_params['is_saving'] = True
        elif target == 'expense':
            filter_params['is_expense'] = True
        elif target == 'income':
            filter_params['is_income'] = True

        queryset = self.get_queryset().filter(**filter_params).order_by('date')
        if category_ids:
            category_ids = category_ids.split(',')
            queryset = queryset.filter(category_id__in=category_ids)
        if subcategory_ids:
            subcategory_ids = subcategory_ids.split(',')
            queryset = queryset.filter(subcategory_id__in=subcategory_ids)

        serializer = ResponseTransactionSerializer(queryset, many=True)
        return self._group_by(serializer.data)

    def create_transaction(self, data):
        if 'user' not in data:
            user = get_current_user()
            data['user'] = getattr(user, 'id', None)
        serializer = TransactionSerializer(data=data)
        is_created, data, created_instance = self.handle_serializer(serializer)
        if is_created:
            log_change_signal.send_robust(sender=self.__class__, instance=created_instance, section=SectionEnum.TRANSACTION,
                                   action=ActionEnum.CREATE)
            return True, data
        return False, data

    def update_transaction(self, data):
        pk = data.get('id')
        instance = self.get_queryset().get(pk=pk)
        old_instance = copy.copy(instance)
        serializer = TransactionSerializer(instance, data=data)
        is_updated, data, saved_instance = self.handle_serializer(serializer)
        if is_updated:
            log_change_signal.send_robust(sender=self.__class__, instance=saved_instance, section=SectionEnum.TRANSACTION,
                                   old_instance=old_instance, action=ActionEnum.UPDATE)
            return True, data
        return False, data

    def handle_serializer(self, serializer):
        if serializer.is_valid(raise_exception=True):
            item = serializer.save()
            response = Transaction.objects.get(pk=item.pk)
            response_serializer = ResponseTransactionSerializer(response)
            return True, response_serializer.data, item
        return False, serializer.errors, None

    def update_similar_transactions(self, request_data):
        destination = request_data.get('destination')
        category = request_data.get('category')
        subcategory = request_data.get('subcategory')
        is_saving = request_data.get('is_saving')
        is_payment = request_data.get('is_payment')
        is_expense = request_data.get('is_expense')
        alias = request_data.get('alias')
        try:
            Transaction.objects.filter(destination=destination).update(
                category_id=category, alias=alias,
                subcategory_id=subcategory, is_saving=is_saving,
                is_payment=is_payment, is_expense=is_expense)
        except ValidationError as e:
            logging.exception("Validation error: %s", e)
        except IntegrityError as e:
            logging.exception("Integrity error: %s", e)
        except Exception as e:
            logging.exception("An unexpected error occurred: %s", e)

    def merge_transactions(self, request_data):
        merge_ids = request_data.get('merge_ids')
        pk = request_data.get('pk')
        if merge_ids and pk:
            with transaction.atomic():
                queryset = Transaction.objects.filter(id__in=merge_ids)
                merged = queryset.update(is_deleted=True, merge_id=pk)
                if merged:
                    log_change_signal.send_robust(sender=self.__class__, instances=list(queryset), section=SectionEnum.TRANSACTION,
                                           action=ActionEnum.MERGE)
                    return True
            return None
        else:
            logging.warning("No merge ids provided")


class TransactionBulkService:

    def bulk_delete(self, request_data):
        delete_ids = request_data.get('delete_ids')
        if delete_ids:
            try:
                with transaction.atomic():
                    queryset = Transaction.objects.filter(id__in=delete_ids)
                    deleted = queryset.update(is_deleted=True, delete_reason=request_data.get('delete_reason', ''))
                    if deleted:
                        log_change_signal.send_robust(sender=self.__class__, instances=list(queryset), section=SectionEnum.TRANSACTION,
                                               action=ActionEnum.BULK_DELETE)
                    return True
            except ValidationError as e:
                logging.exception("Validation error: %s", e)
                return False

    def split_transactions(self, request_data):
        transaction_data = request_data.get('main')
        splits = request_data.get('splits', [])
        user = get_current_user()
        user_id = getattr(user, 'id', None)
        total_split_amount = 0
        response_instances = []
        try:
            with transaction.atomic():
                if splits:
                    for split in splits:
                        payee = DestinationMap.objects.get(destination=split.get('destination'))
                        transaction_split = self.extract_valid_fields(transaction_data)
                        transaction_split['id'] = None
                        transaction_split['amount'] = Decimal(split.get('amount'))
                        transaction_split['category_id'] = payee.category_id
                        transaction_split['subcategory_id'] = None
                        transaction_split['account_id'] = transaction_data.get('account')
                        transaction_split['destination'] = payee.destination
                        transaction_split['destination_original'] = payee.destination_original
                        transaction_split['alias'] = None
                        transaction_split['user_id'] = user_id
                        total_split_amount += Decimal(split.get('amount'))
                        instance = Transaction(**transaction_split)
                        instance.save()
                        if instance.id:
                            response_instances.append(instance.id)
                    if response_instances:
                        response_instances.append(transaction_data['id'])
                        remaining = Decimal(transaction_data['amount']) - total_split_amount
                        Transaction.objects.filter(id=transaction_data['id']).update(amount=remaining)
                if response_instances:
                    queryset = Transaction.objects.filter(id__in=response_instances)
                    response_serializer = ResponseTransactionSerializer(queryset, many=True)
                    return True, response_serializer.data
            return False, None
        except Exception as e:
            logging.exception("An unexpected error occurred: %s", e)
            return False, None


    def extract_valid_fields(self, transaction_data):
        valid_fields = [field.name for field in Transaction._meta.get_fields()]
        override_fields = {'category': 'category_id', 'subcategory': 'subcategory_id', 'account': 'account_id'}
        for override_field in override_fields.keys():
            if override_field in valid_fields:
                valid_fields.remove(override_field)
                valid_fields.append(override_fields[override_field])
        transaction_data_copy = {}
        for field in valid_fields:
            if field in transaction_data:
                transaction_data_copy[field] = transaction_data[field]
            else:
                transaction_data_copy[field] = None
        return transaction_data_copy
