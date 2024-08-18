import calendar

from rest_framework import serializers

from transactions.models import Income, Transaction, DestinationMap


class DateSerializeHelper(object):

    def get_year(self, data):
        return data.date.year

    def get_month(self, data):
        return data.date.month

    def get_month_text(self, data):
        return calendar.month_name[data.date.month]


class ResponseIncomeSerializer(serializers.ModelSerializer, DateSerializeHelper):
    class Meta:
        model = Income
        fields = ['id', 'category', 'category_text', 'amount', 'date', 'destination', 'year', 'month', 'month_text',
                  'notes']

    year = serializers.SerializerMethodField(method_name='get_year')
    month = serializers.SerializerMethodField(method_name='get_month')
    month_text = serializers.SerializerMethodField(method_name='get_month_text')
    category_text = serializers.ReadOnlyField(source='category.category')


class ResponseTransactionSerializer(serializers.ModelSerializer, DateSerializeHelper):
    class Meta:
        model = Transaction
        fields = ['id', 'category', 'category_text', 'subcategory', 'subcategory_text', 'is_payment', 'is_deleted',
                  'is_merge', 'is_saving', 'is_expense', 'merge_id', 'account', 'account_name', 'account_type', 'amount',
                  'date', 'destination_original', 'destination', 'alias', 'year', 'month', 'month_text', 'notes', 'delete_reason']

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
        fields = ['id', 'destination_original', 'destination', 'destination_eng', 'keywords', 'category', 'category_text', 'subcategory',
                  'subcategory_text']

    category_text = serializers.ReadOnlyField(source='category.category')
    subcategory_text = serializers.ReadOnlyField(source='subcategory.name')
