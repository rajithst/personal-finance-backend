import calendar

from rest_framework import serializers

from finance.transactions.models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


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
                  'is_merge', 'is_saving', 'is_expense', 'is_income', 'is_third_party', 'on_behalf_of', 'merge_id', 'account', 'account_name',
                  'account_type', 'counterparty_account', 'counterparty_account_name', 'counterparty_account_type', 'amount', 'source',
                  'date', 'destination_original', 'destination', 'alias', 'year', 'month', 'month_text', 'notes',
                  'delete_reason']

    year = serializers.SerializerMethodField(method_name='get_year')
    month = serializers.SerializerMethodField(method_name='get_month')
    month_text = serializers.SerializerMethodField(method_name='get_month_text')
    category_text = serializers.SerializerMethodField()
    subcategory_text = serializers.SerializerMethodField()
    account_name = serializers.ReadOnlyField(source='account.account_name')
    account_type = serializers.ReadOnlyField(source='account.account_type')
    counterparty_account_name = serializers.ReadOnlyField(source='counterparty_account.account_name')
    counterparty_account_type = serializers.ReadOnlyField(source='counterparty_account.account_type')

    def get_category_text(self, obj):
        return obj.category.category if obj.category else None

    def get_subcategory_text(self, obj):
        return obj.subcategory.name if obj.subcategory else None
