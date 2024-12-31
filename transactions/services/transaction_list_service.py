import logging
from decimal import Decimal

import numpy as np
import pandas as pd
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError

from oauth.middleware import get_current_user
from transactions.models import Transaction, DestinationMap
from transactions.serializers.response_serializers import ResponseTransactionSerializer
from transactions.serializers.serializers import TransactionSerializer
from transactions.validators.transaction_validator import TransactionListValidator


class TransactionListService:

    def get_queryset(self):
        return Transaction.objects.select_related('category', 'subcategory', 'account', 'user')

    def _group_by(self, data: pd.DataFrame):
        if data.empty:
            return []

        group_data = []
        for group_k, vals in data.groupby(['year', 'month']):
            vals['amount'] = vals['amount'].apply(lambda x: '{:.2f}'.format(float(x)))
            vals['amount'] = vals['amount'].astype(float)
            transactions = vals.to_dict('records')
            group_data.append({'year': group_k[0], 'month': group_k[1], 'month_text': vals['month_text'].iloc[0],
                               'total': float(vals.amount.sum()), 'transactions': transactions})
        return list(reversed(group_data))

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
        df = pd.DataFrame(serializer.data)
        df = df.replace({np.nan: None})
        return self._group_by(df)

    def create_transaction(self, data):
        if 'user' not in data:
            user = get_current_user()
            data['user'] = user.id
        serializer = TransactionSerializer(data=data)
        return self.handle_serializer(serializer)

    def update_transaction(self, data):
        pk = data.get('id')
        instance = self.get_queryset().get(pk=pk)
        serializer = TransactionSerializer(instance, data=data)
        return self.handle_serializer(serializer)

    def handle_serializer(self, serializer):
        if serializer.is_valid(raise_exception=True):
            item = serializer.save()
            response = Transaction.objects.get(pk=item.pk)
            response_serializer = ResponseTransactionSerializer(response)
            return True, response_serializer.data
        return False, serializer.errors

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
            logging.exception("Validation error:", e)
        except IntegrityError as e:
            logging.exception("Integrity error:", e)
        except Exception as e:
            logging.exception("An unexpected error occurred:", e)

    def merge_transactions(self, request_data):
        merge_ids = request_data.get('merge_ids')
        pk = request_data.get('pk')
        if merge_ids and pk:
            Transaction.objects.filter(id__in=merge_ids).update(is_deleted=True, merge_id=pk)
        else:
            logging.warning("No merge ids provided")


class TransactionBulkService:

    def bulk_delete(self, request_data):
        delete_ids = request_data.get('delete_ids')
        if delete_ids:
            try:
                Transaction.objects.filter(id__in=delete_ids).update(is_deleted=True)
                return True
            except ValidationError as e:
                logging.exception("Validation error:", e)
                return False

    def split_transactions(self, request_data):
        transaction_data = request_data.get('main')
        splits = request_data.get('splits', [])
        user = get_current_user()
        total_split_amount = 0
        response_instances = []
        try:
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
                    transaction_split['user_id'] = user.id
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
            logging.exception("An unexpected error occurred:", e)
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
