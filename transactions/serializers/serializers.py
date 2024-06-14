import calendar

from rest_framework import serializers
from transactions.models import IncomeCategory, TransactionCategory, PaymentMethod, Income, TransactionSubCategory, \
    Transaction, DestinationMap, RewriteRules


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

class RewriteRulesSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewriteRules
        fields = '__all__'