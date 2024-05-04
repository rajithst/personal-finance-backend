import calendar

from rest_framework import serializers
from .models import IncomeCategory, TransactionCategory, PaymentMethod, Income, TransactionSubCategory, Transaction


class DateSerializeHelper(object):

    def get_year(self, data):
        return data.date.year

    def get_month(self, data):
        return data.date.month

    def get_month_text(self, data):
        return calendar.month_name[data.date.month]


class IncomeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = IncomeCategory
        fields = ['id', 'category']


class TransactionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionCategory
        fields = ['id', 'category']


class TransactionSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionSubCategory
        fields = ['id', 'category', 'name']


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name']


class IncomeSerializer(serializers.ModelSerializer, DateSerializeHelper):
    class Meta:
        model = Income
        fields = ['id', 'category', 'category_text', 'amount', 'date', 'destination', 'year', 'month', 'month_text',
                  'notes']

    year = serializers.SerializerMethodField(method_name='get_year')
    month = serializers.SerializerMethodField(method_name='get_month')
    month_text = serializers.SerializerMethodField(method_name='get_month_text')
    category_text = serializers.ReadOnlyField(source='category.category')


class TransactionSerializer(serializers.ModelSerializer, DateSerializeHelper):
    class Meta:
        model = Transaction
        fields = ['id', 'category', 'category_text', 'subcategory', 'subcategory_text', 'is_payment', 'is_deleted',
                  'is_merge', 'is_saving', 'is_expense', 'merge_id', 'payment_method', 'payment_method_text', 'amount',
                  'date', 'destination', 'alias', 'year', 'month', 'month_text', 'notes', 'delete_reason']

    year = serializers.SerializerMethodField(method_name='get_year')
    month = serializers.SerializerMethodField(method_name='get_month')
    month_text = serializers.SerializerMethodField(method_name='get_month_text')
    category_text = serializers.ReadOnlyField(source='category.category')
    subcategory_text = serializers.ReadOnlyField(source='subcategory.name')
    payment_method_text = serializers.ReadOnlyField(source='payment_method.name')
