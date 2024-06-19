import time

from django.db import IntegrityError
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from transactions.models import Income, Transaction, DestinationMap
from transactions.serializers.response_serializers import ResponseIncomeSerializer, ResponseTransactionSerializer, \
    ResponseDestinationMapSerializer
import calendar
import datetime
import pandas as pd
import logging

from transactions.serializers.serializers import IncomeSerializer, TransactionSerializer, DestinationMapSerializer


class FinanceView(APIView):
    def get(self, request):
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        current_date = datetime.date.today()
        if not start_date:
            last_day_of_month = calendar.monthrange(current_date.year, current_date.month)[1]
            start_date = current_date.replace(day=last_day_of_month)
            start_date = start_date.strftime('%Y-%m-%d')
        if not end_date:
            five_years_ago = current_date - datetime.timedelta(days=365 * 5)
            end_date = five_years_ago.replace(day=1)
            end_date = end_date.strftime("%Y-%m-%d")
        incomes = Income.objects.select_related('category').filter(date__range=[end_date, start_date]).order_by('date')
        destinations = (DestinationMap.objects.values_list('destination_eng', flat=True)
                        .exclude(destination_eng=None).distinct().order_by('destination_eng'))
        transactions = Transaction.objects.select_related('category', 'subcategory', 'payment_method').filter(
            date__range=[end_date, start_date], is_deleted=False).order_by('date')
        transactions_serializer = ResponseTransactionSerializer(transactions, many=True)
        expenses, payments, savings = self.split_transactions(transactions_serializer.data)

        income_serializer = ResponseIncomeSerializer(incomes, many=True)
        incomes = self._group_by(pd.DataFrame(income_serializer.data))
        return Response({"income": incomes, "expense": expenses, "saving": savings, "payment": payments,
                         "destinations": destinations}, status=status.HTTP_200_OK)

    def split_transactions(self, transactions):
        if not len(transactions):
            return [], [], []
        df = pd.DataFrame(transactions)
        expenses = df[df['is_expense'] == 1]
        payments = df[df['is_payment'] == 1]
        savings = df[df['is_saving'] == 1]
        expense_group = self._group_by(expenses)
        payment_group = self._group_by(payments)
        saving_group = self._group_by(savings)
        return expense_group, payment_group, saving_group

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


class IncomeViewSet(ModelViewSet):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer


class TransactionViewSet(ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

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

        is_regular_destination = data.get('is_regular_destination')
        update_similar = data.get('update_similar')
        is_deleted = data.get('is_deleted')

        if is_deleted:
            print('delete')

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

