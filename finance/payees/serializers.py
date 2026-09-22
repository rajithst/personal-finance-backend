from rest_framework import serializers

from common.transaction_const import EXPENSE_CATEGORY_TYPE, TRANSACTION_CATEGORY_TEXT, INCOME_CATEGORY_TYPE, \
    INCOME_CATEGORY_TEXT, SAVINGS_CATEGORY_TYPE, SAVINGS_CATEGORY_TEXT, PAYMENT_CATEGORY_TYPE, PAYMENT_CATEGORY_TEXT
from finance.payees.models import DestinationMap


class ResponseDestinationMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationMap
        fields = [
            'id', 'destination_original', 'destination', 'destination_eng', 'keywords', 'category',
            'category_text', 'subcategory', 'subcategory_text', 'category_type', 'category_type_text',
            'is_expense', 'is_income', 'is_saving', 'is_payment'
        ]

    category_text = serializers.ReadOnlyField(source='category.category')
    subcategory_text = serializers.ReadOnlyField(source='subcategory.name')
    category_type_text = serializers.SerializerMethodField(method_name='get_category_type_text')
    is_expense = serializers.SerializerMethodField()
    is_income = serializers.SerializerMethodField()
    is_saving = serializers.SerializerMethodField()
    is_payment = serializers.SerializerMethodField()

    def _resolve_type(self, obj):
        if obj.category_type is not None:
            return obj.category_type
        if obj.category and obj.category.category_type is not None:
            return obj.category.category_type
        return None

    def get_category_type_text(self, obj):
        cat_type = self._resolve_type(obj)
        if cat_type == EXPENSE_CATEGORY_TYPE:
            return TRANSACTION_CATEGORY_TEXT
        elif cat_type == INCOME_CATEGORY_TYPE:
            return INCOME_CATEGORY_TEXT
        elif cat_type == SAVINGS_CATEGORY_TYPE:
            return SAVINGS_CATEGORY_TEXT
        elif cat_type == PAYMENT_CATEGORY_TYPE:
            return PAYMENT_CATEGORY_TEXT
        return None

    def get_is_expense(self, obj):
        return self._resolve_type(obj) == EXPENSE_CATEGORY_TYPE

    def get_is_income(self, obj):
        return self._resolve_type(obj) == INCOME_CATEGORY_TYPE

    def get_is_saving(self, obj):
        return self._resolve_type(obj) == SAVINGS_CATEGORY_TYPE

    def get_is_payment(self, obj):
        return self._resolve_type(obj) == PAYMENT_CATEGORY_TYPE


class DestinationMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationMap
        fields = [
            'id',
            'destination_original',
            'destination',
            'destination_eng',
            'keywords',
            'category',
            'subcategory',
            'category_type',
        ]
