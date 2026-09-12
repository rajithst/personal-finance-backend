from rest_framework import serializers

from common.transaction_const import EXPENSE_CATEGORY_TYPE, TRANSACTION_CATEGORY_TEXT, INCOME_CATEGORY_TYPE, \
    INCOME_CATEGORY_TEXT, SAVINGS_CATEGORY_TYPE, SAVINGS_CATEGORY_TEXT, PAYMENT_CATEGORY_TYPE, PAYMENT_CATEGORY_TEXT
from finance.payees.models import DestinationMap


class ResponseDestinationMapSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationMap
        fields = ['id', 'destination_original', 'destination', 'destination_eng', 'keywords', 'category',
                  'category_text', 'subcategory', 'subcategory_text', 'category_type', 'category_type_text']

    category_text = serializers.ReadOnlyField(source='category.category')
    subcategory_text = serializers.ReadOnlyField(source='subcategory.name')
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
        return None


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
