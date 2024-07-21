from django.db import IntegrityError
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from transactions.models import Income, Transaction, DestinationMap
from transactions.serializers.response_serializers import ResponseTransactionSerializer, \
    ResponseDestinationMapSerializer
import pandas as pd
import logging

from transactions.serializers.serializers import IncomeSerializer


class DashboardViewSet(APIView):

    def get_monthly_payment_destination_wise_sum(self, transaction_type, year):
        queryset = (
            Transaction.objects
            .filter(**{transaction_type: True, 'is_deleted': False, 'date__year': year})
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
        queryset = (
            Transaction.objects
            .filter(**{transaction_type: True, 'is_deleted': False, 'date__year': year})
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
        queryset = (
            Transaction.objects
            .filter(**{transaction_type: True, 'is_deleted': False, 'date__year': year})
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

    def get_monthly_income_summary(self, year):
        queryset = (
            Income.objects
            .filter(**{'date__year': year}).annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total_amount=Sum('amount'))
            .order_by('month')
        )
        results = []
        for item in queryset:
            date = item['month']
            results.append({'year': date.year, 'month': date.month, 'amount': item['total_amount']})
        return results

    def get_payment_method_wise_sum(self, transaction_type, year):
        queryset = (
            Transaction.objects
            .filter(**{transaction_type: True, 'is_deleted': False, 'date__year': year})
            .annotate(month=TruncMonth('date'))
            .values('month', 'payment_method_id')
            .annotate(total_amount=Sum('amount'))
            .order_by('month')
        )
        results = {}
        for item in queryset:
            date_str = item['month'].strftime('%Y-%m-%d')
            if date_str not in results:
                results[date_str] = []
            results[date_str].append({'category_id': item['payment_method_id'], 'amount': item['total_amount']})
        return results

    def get(self, request):
        year = request.query_params.get('year', 2024)
        incomes = self.get_monthly_income_summary(year)
        expenses = self.get_monthly_transaction_summary('is_expense', year)
        payments = self.get_monthly_transaction_summary('is_payment', year)
        savings = self.get_monthly_transaction_summary('is_saving', year)
        category_wise_expenses = self.get_monthly_transaction_category_summary('is_expense', year)
        payment_method_wise_expenses = self.get_payment_method_wise_sum('is_expense', year)
        payment_by_destination = self.get_monthly_payment_destination_wise_sum('is_payment', year)
        return Response({"income": incomes, "payment_by_destination": payment_by_destination,
                         "payment_method_wise_expenses": payment_method_wise_expenses,
                         "category_wise_expenses": category_wise_expenses, "expense": expenses,
                         "payment": payments, "saving": savings})


class IncomeViewSet(ModelViewSet):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer


class TransactionViewSet(ModelViewSet):
    queryset = Transaction.objects.select_related('category', 'subcategory', 'payment_method').all()
    serializer_class = ResponseTransactionSerializer

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
        return reversed(group_data)

    def list(self, request, *args, **kwargs):
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
        queryset = self.get_queryset().filter(**filter_params).order_by('date')
        if category_ids:
            category_ids = category_ids.split(',')
            queryset = queryset.filter(category_id__in=category_ids)
        if subcategory_ids:
            subcategory_ids = subcategory_ids.split(',')
            queryset = queryset.filter(subcategory_id__in=subcategory_ids)

        serializer = self.get_serializer(queryset, many=True)
        df = pd.DataFrame(serializer.data)
        return Response({'payload': self._group_by(df)}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        data = request.data
        update_similar = data.get('update_similar')
        if update_similar:
            self.update_similar_transactions(data)

        serializer = ResponseTransactionSerializer(data=data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        data = request.data

        pk = self.kwargs['pk']
        update_similar = data.get('update_similar')
        merge_ids = data.get('merge_ids')

        if merge_ids:
            Transaction.objects.filter(id__in=merge_ids).update(is_deleted=True, merge_id=pk)

        if update_similar:
            self.update_similar_transactions(data)

        instance = self.get_object()
        serializer = ResponseTransactionSerializer(instance, data=data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def update_similar_transactions(request_data):
        destination = request_data.get('destination')
        category = request_data.get('category')
        subcategory = request_data.get('subcategory')
        is_saving = request_data.get('is_saving')
        is_payment = request_data.get('is_payment')
        is_expense = request_data.get('is_expense')
        alias = request_data.get('alias')
        try:
            Transaction.objects.filter(destination=destination).update(category_id=category, alias=alias,
                                                                       subcategory_id=subcategory, is_saving=is_saving,
                                                                       is_payment=is_payment, is_expense=is_expense)
        except ValidationError as e:
            logging.exception("Validation error:", e)
        except IntegrityError as e:
            logging.exception("Integrity error:", e)
        except Exception as e:
            logging.exception("An unexpected error occurred:", e)


class PayeeViewSet(ModelViewSet):
    queryset = DestinationMap.objects.select_related('category', 'subcategory').all()
    serializer_class = ResponseDestinationMapSerializer

    def update(self, request, *args, **kwargs):
        data = request.data
        pk = data.get('id')
        keywords = data.get('keywords')
        category = data.get('category')
        subcategory = data.get('subcategory')
        new_destination = data.get('destination')
        new_alias = data.get('destination_eng')
        update_ids = data.get('merge_ids')
        exist_settings = DestinationMap.objects.get(pk=pk)
        is_payee_renamed = data.get('destination') != exist_settings.destination
        destination = new_destination if is_payee_renamed else exist_settings.destination

        target_destinations = [exist_settings.destination]

        serializer = self.serializer_class(exist_settings, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            if update_ids:
                merge_records = DestinationMap.objects.filter(id__in=update_ids)
                target_destinations.extend(list(merge_records.values_list('destination_original', flat=True)))

            try:
                Transaction.objects.filter(destination__in=target_destinations).update(category_id=category,
                                                                                       subcategory_id=subcategory,
                                                                                       destination=destination,
                                                                                       alias=new_alias)
                DestinationMap.objects.filter(id__in=update_ids).delete()
            except Exception as e:
                logging.exception("An unexpected error occurred:", e)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
