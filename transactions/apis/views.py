import numpy as np
from django.db import IntegrityError
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from decimal import Decimal

from transactions.common.transaction_const import INCOME_CATEGORY_TYPE, SAVINGS_CATEGORY_TYPE, EXPENSE_CATEGORY_TYPE, \
    PAYMENT_CATEGORY_TYPE
from transactions.models import Transaction, DestinationMap, Account, TransactionCategory, \
    TransactionSubCategory
from transactions.serializers.response_serializers import ResponseTransactionSerializer, \
    ResponseDestinationMapSerializer, ResponseTransactionCategorySerializer, ResponseTransactionSubCategorySerializer, \
    ResponseAccountSerializer
import pandas as pd
import logging

from transactions.serializers.serializers import AccountSerializer, TransactionSerializer, \
    TransactionSubCategorySerializer, TransactionCategorySerializer


class DashboardView(APIView):

    def get_queryset(self):
        return Transaction.objects.select_related('category', 'subcategory', 'account').filter(
            user__id=self.request.user.id, is_deleted=False)

    def get_monthly_payment_destination_wise_sum(self, transaction_type, year):
        queryset = (self.get_queryset().filter(
            **{transaction_type: True, 'date__year': year})
                    .annotate(month=TruncMonth('date'))
                    .values('month', 'destination_original', 'destination')
                    .annotate(total_amount=Sum('amount'))
                    .order_by('month')
                    )
        results = {}
        for item in queryset:
            date_str = item['month'].strftime('%Y-%m-%d')
            if date_str not in results:
                results[date_str] = []
            results[date_str].append(
                {'destination_original': item['destination_original'], 'destination': item['destination'],
                 'amount': item['total_amount']})
        return results

    def get_monthly_transaction_summary(self, transaction_type, year):
        queryset = (self.get_queryset().filter(
            **{transaction_type: True, 'date__year': year})
                    .annotate(month=TruncMonth('date'))
                    .values('month')
                    .annotate(total_amount=Sum('amount'))
                    .order_by('month')
                    )
        results = []
        for item in queryset:
            date = item['month']
            results.append({'year': date.year, 'month': date.month, 'amount': item['total_amount']})
        return results

    def get_monthly_transaction_category_summary(self, transaction_type, year):
        queryset = (self.get_queryset().filter(
            **{transaction_type: True, 'date__year': year})
                    .annotate(month=TruncMonth('date'))
                    .values('month', 'category_id')
                    .annotate(total_amount=Sum('amount'))
                    .order_by('month', 'category_id')
                    )
        results = {}
        for item in queryset:
            date_str = item['month'].strftime('%Y-%m-%d')
            if date_str not in results:
                results[date_str] = []
            results[date_str].append({'category_id': item['category_id'], 'amount': item['total_amount']})
        return results

    def get_account_wise_sum(self, transaction_type, year):
        queryset = self.get_queryset()
        queryset = (queryset.filter(
            **{transaction_type: True, 'is_deleted': False, 'date__year': year})
                    .annotate(month=TruncMonth('date'))
                    .values('month', 'account_id')
                    .annotate(total_amount=Sum('amount'))
                    .order_by('month')
                    )
        results = {}
        for item in queryset:
            date_str = item['month'].strftime('%Y-%m-%d')
            if date_str not in results:
                results[date_str] = []
            results[date_str].append({'category_id': item['account_id'], 'amount': item['total_amount']})
        return results

    def get(self, request):
        year = request.query_params.get('year', 2024)
        incomes = self.get_monthly_transaction_summary('is_income', year)
        expenses = self.get_monthly_transaction_summary('is_expense', year)
        payments = self.get_monthly_transaction_summary('is_payment', year)
        savings = self.get_monthly_transaction_summary('is_saving', year)
        category_wise_expenses = self.get_monthly_transaction_category_summary('is_expense', year)
        account_wise_expenses = self.get_account_wise_sum('is_expense', year)
        payment_by_destination = self.get_monthly_payment_destination_wise_sum('is_payment', year)
        return Response({"income": incomes, "payment_by_destination": payment_by_destination,
                         "account_wise_expenses": account_wise_expenses,
                         "category_wise_expenses": category_wise_expenses, "expense": expenses,
                         "payment": payments, "saving": savings})


class TransactionView(APIView):

    def get_queryset(self):
        queryset = Transaction.objects.select_related('category', 'subcategory', 'account', 'user').filter(
            user_id=self.request.user.id)
        return queryset

    def _group_by(self, data: pd.DataFrame):
        if data.empty:
            return []
        # df = pd.DataFrame(data)
        group_data = []
        for group_k, vals in data.groupby(['year', 'month']):
            vals['amount'] = vals['amount'].apply(lambda x: '{:.2f}'.format(float(x)))
            vals['amount'] = vals['amount'].astype(float)
            transactions = vals.to_dict('records')
            group_data.append({'year': group_k[0], 'month': group_k[1], 'month_text': vals['month_text'].iloc[0],
                               'total': float(vals.amount.sum()), 'transactions': transactions})
        return list(reversed(group_data))

    def get(self, request, *args, **kwargs):
        query_params = request.query_params
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
        return Response({'payload': self._group_by(df)}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        update_similar = data.get('update_similar')
        if update_similar:
            self.update_similar_transactions(data)
        data['user'] = self.request.user.id
        serializer = TransactionSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            item = serializer.save()
            response = Transaction.objects.get(pk=item.pk)
            response_serializer = ResponseTransactionSerializer(response)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        data = request.data
        pk = self.kwargs['id']
        update_similar = data.get('update_similar')
        merge_ids = data.get('merge_ids')

        if merge_ids:
            Transaction.objects.filter(id__in=merge_ids).update(is_deleted=True, merge_id=pk)

        if update_similar:
            self.update_similar_transactions(data)

        instance = self.get_queryset().get(pk=pk)
        serializer = ResponseTransactionSerializer(instance, data=data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update_similar_transactions(self, request_data):
        destination = request_data.get('destination')
        category = request_data.get('category')
        subcategory = request_data.get('subcategory')
        is_saving = request_data.get('is_saving')
        is_payment = request_data.get('is_payment')
        is_expense = request_data.get('is_expense')
        alias = request_data.get('alias')
        try:
            Transaction.objects.filter(destination=destination, user_id=self.request.user.id).update(
                category_id=category, alias=alias,
                subcategory_id=subcategory, is_saving=is_saving,
                is_payment=is_payment, is_expense=is_expense)
        except ValidationError as e:
            logging.exception("Validation error:", e)
        except IntegrityError as e:
            logging.exception("Integrity error:", e)
        except Exception as e:
            logging.exception("An unexpected error occurred:", e)


class BasePayeeView:
    def get_queryset(self):
        queryset = DestinationMap.objects.select_related('category', 'subcategory').all().order_by(
            'category_id',
            'subcategory_id')
        return queryset

    def get_by_id(self, pk):
        instance = self.get_queryset().get(pk=pk)
        return instance

    def get_by_name(self, name):
        instance = self.get_queryset().get(destination=name)
        return instance


class PayeeDetailView(APIView, BasePayeeView):
    def get(self, request, *args, **kwargs):
        id = kwargs.get('id', None)
        name = kwargs.get('name', None)
        if id:
            instance = self.get_by_id(id)
        elif name:
            instance = self.get_by_name(name)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
        transactions = Transaction.objects.select_related('category', 'subcategory', 'account').filter(
            destination=instance.destination, user_id=request.user.id)
        payee_serializer = ResponseDestinationMapSerializer(instance)
        transaction_serializer = ResponseTransactionSerializer(transactions, many=True)
        return Response({'payee': payee_serializer.data, 'transactions': transaction_serializer.data})


class PayeeView(APIView, BasePayeeView):
    def get(self, request, *args, **kwargs):
        id = kwargs.get('id', None)
        if id:
            instance = self.get_by_id(id)
            payee_serializer = ResponseDestinationMapSerializer(instance)
            return Response({'payee': payee_serializer.data})
        else:
            queryset = self.get_queryset()
            serializer = ResponseDestinationMapSerializer(queryset, many=True)
            return Response({'payees': serializer.data})

    def put(self, request, *args, **kwargs):
        data = request.data
        pk = data.get('id')
        keywords = data.get('keywords')
        category = data.get('category')
        subcategory = data.get('subcategory')
        new_destination = data.get('destination')
        new_alias = data.get('destination_eng')
        merge_ids = data.get('merge_ids')
        exist_settings = DestinationMap.objects.get(pk=pk)
        is_payee_renamed = data.get('destination') != exist_settings.destination
        destination = new_destination if is_payee_renamed else exist_settings.destination
        category_type = data.get('category_type')
        target_destinations = [exist_settings.destination]

        serializer = ResponseDestinationMapSerializer(exist_settings, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            if merge_ids:
                merge_records = DestinationMap.objects.filter(id__in=merge_ids, user_id=self.request.user.id)
                target_destinations.extend(list(merge_records.values_list('destination_original', flat=True)))

            try:
                update_params = {
                    'destination': destination,
                    'alias': new_alias,
                    'category_id': category,
                    'subcategory_id': subcategory,
                }
                if category_type == INCOME_CATEGORY_TYPE:
                    update_params['is_income'] = 1
                    update_params['is_expense'] = 0
                    update_params['is_saving'] = 0
                    update_params['is_payment'] = 0
                elif category_type == SAVINGS_CATEGORY_TYPE:
                    update_params['is_income'] = 0
                    update_params['is_expense'] = 1
                    update_params['is_saving'] = 1
                    update_params['is_payment'] = 0
                elif category_type == EXPENSE_CATEGORY_TYPE:
                    update_params['is_income'] = 0
                    update_params['is_expense'] = 1
                    update_params['is_saving'] = 0
                    update_params['is_payment'] = 0
                elif category_type == PAYMENT_CATEGORY_TYPE:
                    update_params['is_income'] = 0
                    update_params['is_expense'] = 1
                    update_params['is_saving'] = 0
                    update_params['is_payment'] = 1

                Transaction.objects.filter(destination__in=target_destinations, user_id=request.user.id).update(
                    **update_params)
                DestinationMap.objects.filter(id__in=merge_ids).delete()
            except Exception as e:
                logging.exception("An unexpected error occurred:", e)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionBulkView(APIView):
    def put(self, request):
        data = request.data
        task = data.get('task')
        user_id = request.user.id
        if task == 'delete':
            delete_ids = data.get('delete_ids')
            if delete_ids:
                try:
                    Transaction.objects.filter(id__in=delete_ids).update(is_deleted=True)
                    queryset = Transaction.objects.filter(id__in=delete_ids)
                    response_serializer = ResponseTransactionSerializer(queryset, many=True)
                    return Response({'status': status.HTTP_200_OK, 'data': response_serializer.data})
                except ValidationError as e:
                    logging.exception("Validation error:", e)
                    return Response({'status': status.HTTP_400_BAD_REQUEST, 'data': None})
        elif task == 'split':
            transaction_data = data.get('main')
            splits = data.get('splits', [])
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
                        # TODO get N/A subcategory id for user
                        transaction_split['subcategory_id'] = 1000
                        transaction_split['account_id'] = transaction_data.get('account')
                        transaction_split['destination'] = payee.destination
                        transaction_split['destination_original'] = payee.destination_original
                        transaction_split['alias'] = None
                        transaction_split['user_id'] = user_id
                        total_split_amount += Decimal(split.get('amount'))
                        instance = Transaction(**transaction_split)
                        instance.save()
                        response_instances.append(instance.id)
                    response_instances.append(transaction_data['id'])
                    remaining = Decimal(transaction_data['amount']) - total_split_amount
                    Transaction.objects.filter(id=transaction_data['id']).update(amount=remaining)
                queryset = Transaction.objects.filter(id__in=response_instances)
                response_serializer = ResponseTransactionSerializer(queryset, many=True)
                return Response({'status': status.HTTP_200_OK, 'data': response_serializer.data})
            except Exception as e:
                logging.exception("An unexpected error occurred:", e)
                return Response({'status': status.HTTP_400_BAD_REQUEST, 'data': None})

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


class ClientSettingsView(APIView):

    def get(self, request):
        user_id = request.user.id
        accounts = Account.objects.filter(user_id=user_id).all()
        transaction_categories = TransactionCategory.objects.filter(user_id=user_id).all()
        transaction_subcategories = TransactionSubCategory.objects.filter(user_id=user_id).select_related(
            'category').all()
        transaction_category_serializer = ResponseTransactionCategorySerializer(transaction_categories, many=True)
        transaction_subcategories_serializer = ResponseTransactionSubCategorySerializer(transaction_subcategories,
                                                                                        many=True)
        accounts_serializer = ResponseAccountSerializer(accounts, many=True)
        return Response({'accounts': accounts_serializer.data,
                         'transaction_categories': transaction_category_serializer.data,
                         'transaction_sub_categories': transaction_subcategories_serializer.data})


class CategorySettingsView(APIView):

    def get_category_queryset(self, params):
        return TransactionCategory.objects.filter(user_id=self.request.user.id, **params)

    def get_subcategory_queryset(self, params):
        return TransactionSubCategory.objects.select_related('category').filter(user_id=self.request.user.id, **params)

    def get_transaction_queryset(self, params):
        return Transaction.objects.select_related('category', 'subcategory', 'account').filter(
            user_id=self.request.user.id, **params).only('id', 'category_id', 'subcategory_id')

    def get_payee_queryset(self, params):
        return DestinationMap.objects.select_related('category', 'subcategory').filter(user_id=self.request.user.id,
                                                                                       **params)

    def put(self, request):
        data = request.data.copy()
        category = data.get('category')
        subcategories = data.get('subcategories')
        deleted_subcategories = data.get('deleted_sub_categories')
        delete_category = data.get('delete_category')
        user_id = self.request.user.id
        processed_subcategories = []

        category['user_id'] = user_id
        category_id = category.get('id')

        try:
            if delete_category:
                self.get_subcategory_queryset({'category_id': category_id}).delete()
                self.get_category_queryset({'id': category_id}).delete()
                return Response({'category': None, 'subcategories': []})

            existing_category = self.get_category_queryset({'id': category_id}).first()
            category_serializer = TransactionCategorySerializer(existing_category, data=category, partial=True)
            if category_serializer.is_valid(raise_exception=True):
                saved_category = category_serializer.save()
            else:
                return Response(category_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            if deleted_subcategories:
                deleted_sub_category_ids = [obj.get('id') for obj in deleted_subcategories]
                self.get_subcategory_queryset({'id__in': deleted_sub_category_ids}).delete()

            subcategory_ids = [obj.get('id') for obj in subcategories]
            queryset = self.get_subcategory_queryset({'id__in': subcategory_ids})
            new_subcategories = []
            for item in subcategories:
                subcategory_id = item.get('id')
                if subcategory_id:
                    instance = queryset.get(id=subcategory_id)
                    instance.name = item.get('name')
                    instance.description = item.get('description')
                    instance.save()
                    processed_subcategories.append(instance)
                else:
                    item['user'] = user_id
                    new_subcategories.append(item)

            if new_subcategories:
                self.collect_new_subcategories(new_subcategories, processed_subcategories)

            return self.handle_success_response(saved_category, None)
        except ValidationError as e:
            logging.exception("Validation error:", e)
            return Response({'status': status.HTTP_400_BAD_REQUEST, })

    def post(self, request):
        data = request.data.copy()
        category = data.get('category')
        subcategories = data.get('subcategories')
        processed_subcategories = []
        category['user'] = self.request.user.id
        new_subcategories = []
        try:
            serializer = TransactionCategorySerializer(data=category)
            if serializer.is_valid(raise_exception=True):
                item = serializer.save()
                saved_category = TransactionCategory.objects.get(pk=item.pk)
                for item in subcategories:
                    item['user'] = self.request.user.id
                    item['category'] = saved_category.id
                    new_subcategories.append(item)
                self.collect_new_subcategories(new_subcategories, processed_subcategories)

                return self.handle_success_response(saved_category, processed_subcategories)
        except ValidationError as e:
            logging.exception("Validation error:", e)
            return Response({'status': status.HTTP_400_BAD_REQUEST, })

    def collect_new_subcategories(self, new_subcategories, processed_subcategories):
        subcategory_serializer = TransactionSubCategorySerializer(data=new_subcategories, many=True)
        if subcategory_serializer.is_valid(raise_exception=True):
            saved_items = subcategory_serializer.save()
            for item in saved_items:
                processed_subcategories.append(item)

    def handle_success_response(self, saved_category, processed_subcategories):
        response_category_serializer = ResponseTransactionCategorySerializer(saved_category)
        if not processed_subcategories:
            processed_subcategories = self.get_subcategory_queryset({'category_id': saved_category.id}).all()
        response_subcategory_serializer = ResponseTransactionSubCategorySerializer(processed_subcategories,
                                                                                   many=True)
        return Response({'category': response_category_serializer.data,
                         'subcategories': response_subcategory_serializer.data})


class CreditAccountView(APIView):

    def post(self, request):
        data = request.data.copy()
        data['user'] = self.request.user.id
        serializer = AccountSerializer(data=data)
        return self.handle_serializer(serializer)

    def put(self, request):
        data = request.data.copy()
        data['user'] = self.request.user.id
        account = Account.objects.get(pk=data.get('id'))
        serializer = AccountSerializer(account, data=data, partial=True)
        return self.handle_serializer(serializer)

    def handle_serializer(self, serializer):
        if serializer.is_valid(raise_exception=True):
            saved_item = serializer.save()
            response_serializer = ResponseAccountSerializer(saved_item)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
