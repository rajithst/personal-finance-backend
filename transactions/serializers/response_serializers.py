import calendar

from rest_framework import serializers

from transactions.common.transaction_const import EXPENSE_CATEGORY_TYPE, \
    TRANSACTION_CATEGORY_TEXT, INCOME_CATEGORY_TYPE, INCOME_CATEGORY_TEXT, SAVINGS_CATEGORY_TYPE, SAVINGS_CATEGORY_TEXT, \
    PAYMENT_CATEGORY_TYPE, PAYMENT_CATEGORY_TEXT
from transactions.models import Transaction, DestinationMap, TransactionCategory, TransactionSubCategory


class DateSerializeHelper(object):

    def get_year(self, data):
        return data.date.year

    def get_month(self, data):
        return data.date.month

    def get_month_text(self, data):
        return calendar.month_name[data.date.month]


class ResponseTransactionSerializer(serializers.ModelSerializer, DateSerializeHelper):
    class Meta:
        model = Transaction
        fields = ['id', 'category', 'category_text', 'subcategory', 'subcategory_text', 'is_payment', 'is_deleted',
                  'is_merge', 'is_saving', 'is_expense', 'is_income', 'merge_id', 'account', 'account_name',
                  'account_type', 'amount',
                  'date', 'destination_original', 'destination', 'alias', 'year', 'month', 'month_text', 'notes',
                  'delete_reason']

    year = serializers.SerializerMethodField(method_name='get_year')
    month = serializers.SerializerMethodField(method_name='get_month')
    month_text = serializers.SerializerMethodField(method_name='get_month_text')
    category_text = serializers.ReadOnlyField(source='category.category')
    subcategory_text = serializers.ReadOnlyField(source='subcategory.name')
    account_name = serializers.ReadOnlyField(source='account.account_name')
    account_type = serializers.ReadOnlyField(source='account.account_type')


class ResponseDestinationMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationMap
        fields = ['id', 'destination_original', 'destination', 'destination_eng', 'keywords', 'category',
                  'category_text', 'subcategory', 'subcategory_text', 'category_type']

    category_text = serializers.ReadOnlyField(source='category.category')
    subcategory_text = serializers.ReadOnlyField(source='subcategory.name')


class ResponseTransactionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionCategory
        fields = ['id', 'category', 'category_type', 'category_type_text', 'description']

    category_type_text = serializers.SerializerMethodField(method_name='get_category_type_text')

    def get_category_type_text(self, obj):
        if obj.category_type == EXPENSE_CATEGORY_TYPE:
            return TRANSACTION_CATEGORY_TEXT
        elif obj.category_type == INCOME_CATEGORY_TYPE:
            return INCOME_CATEGORY_TEXT
        elif obj.category_type == SAVINGS_CATEGORY_TYPE:
            return SAVINGS_CATEGORY_TEXT
        elif obj.category_type == PAYMENT_CATEGORY_TYPE:
            return PAYMENT_CATEGORY_TEXT


class ResponseTransactionSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionSubCategory
        fields = ['id', 'name', 'category', 'category_text', 'description']

    category_text = serializers.ReadOnlyField(source='category.category')

