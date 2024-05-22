from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.connector.card_loader import CardLoader
from transactions.serializers.serializers import TransactionSerializer, IncomeSerializer


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