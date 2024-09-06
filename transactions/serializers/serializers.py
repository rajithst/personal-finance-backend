from rest_framework import serializers
from transactions.models import Transaction, DestinationMap, Account, TransactionCategory, \
    TransactionSubCategory



class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class TransactionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionCategory
        fields = '__all__'


class TransactionSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionSubCategory
        fields = '__all__'


class DestinationMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationMap
        fields = '__all__'


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
