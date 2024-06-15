import calendar

from rest_framework import serializers
from transactions.models import IncomeCategory, TransactionCategory, PaymentMethod, Income, TransactionSubCategory, \
    Transaction, DestinationMap


class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class DestinationMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationMap
        fields = '__all__'
