from itertools import chain

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .loader.card_loader import CardLoader
from .models import Income, Transaction, DestinationMap
from .serializers import IncomeSerializer, TransactionSerializer
import calendar
import datetime
import pandas as pd


class TransactionsView(APIView):
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
        destinations = DestinationMap.objects.values_list('destination_eng', flat=True).exclude(destination_eng=None)
        transactions = Transaction.objects.select_related('category', 'subcategory', 'payment_method').filter(
            date__range=[end_date, start_date]).order_by('date')
        expenses = transactions.filter(is_expense=True, is_deleted=False)
        savings = transactions.filter(is_saving=True, is_deleted=False)
        payments = transactions.filter(is_payment=True, is_deleted=False)
        income_serializer = IncomeSerializer(incomes, many=True)
        expense_serializer = TransactionSerializer(expenses, many=True)
        saving_serializer = TransactionSerializer(savings, many=True)
        payment_serializer = TransactionSerializer(payments, many=True)
        return Response({"income": self._group_by(income_serializer.data), "expense": self._group_by(expense_serializer.data), "saving": self._group_by(saving_serializer.data), "payment": self._group_by(payment_serializer.data), "destinations": destinations}, status=status.HTTP_200_OK)

    def _group_by(self, data):
        if not len(data):
            return []
        df = pd.DataFrame(data)
        group_data = []
        for group_k, vals in df.groupby(['year', 'month']):
            group_data.append({'year': group_k[0], 'month': group_k[1], 'month_text': vals['month_text'].iloc[0],
                               'total': vals.amount.sum(), 'transactions': vals.to_dict('records')})
        return reversed(group_data)

    def post(self, request):
        data = request.data
        pk = data.get('id')
        destination = data.get('destination')
        category = data.get('category')
        subcategory = data.get('subcategory')
        is_saving = data.get('is_saving')
        is_payment = data.get('is_payment')
        is_expense = data.get('is_expense')
        alias = data.get('alias')
        is_regular_destination = data.get('is_regular_destination')

        if pk:
            instance = get_object_or_404(Transaction, pk=pk)
            serializer = TransactionSerializer(instance, data=data)
        else:
            serializer = TransactionSerializer(data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        update_similar = data.get('update_similar')
        if update_similar:
            Transaction.objects.filter(destination=destination).update(category=category, alias=alias, subcategory=subcategory, is_saving=is_saving, is_payment=is_payment, is_expense=is_expense)

        if is_regular_destination:
            existing_payee = DestinationMap.objects.filter(destination=destination)
            if existing_payee.exists():
                existing_payee.update(category_id=category, destination_eng=alias, subcategory_id=subcategory)
            else:
                DestinationMap.objects.create(destination=destination, destination_eng=alias, category_id=category,
                                              subcategory_id=subcategory)
        return Response(serializer.data, status=status.HTTP_200_OK)

class IncomeViewSet(ModelViewSet):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer


class TransactionImportView(APIView):
    def get(self, request):
        loader = CardLoader()
        expenses, incomes = loader.process()
        transactions_serializer = TransactionSerializer(data=expenses.to_dict('records'), many=True)
        income_serializer = IncomeSerializer(data=incomes.to_dict('records'), many=True)
        v1 = transactions_serializer.is_valid()
        v2 = income_serializer.is_valid()
        if v1 and v2:
            transactions_serializer.save()
            income_serializer.save()
            return Response("Successfully saved", status=status.HTTP_201_CREATED)
        else:
            return Response({
                'transactions': transactions_serializer.errors,
                'income': income_serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)