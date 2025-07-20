from rest_framework import serializers

from finance.categories.models import TransactionSubCategory, TransactionCategory
from common.transaction_const import EXPENSE_CATEGORY_TYPE, TRANSACTION_CATEGORY_TEXT, INCOME_CATEGORY_TYPE, \
    INCOME_CATEGORY_TEXT, SAVINGS_CATEGORY_TYPE, SAVINGS_CATEGORY_TEXT, PAYMENT_CATEGORY_TYPE, PAYMENT_CATEGORY_TEXT


class TransactionCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionCategory
        fields = '__all__'


class TransactionSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionSubCategory
        fields = '__all__'


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
        return None


class ResponseTransactionSubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionSubCategory
        fields = ['id', 'name', 'category', 'category_text', 'description']

    category_text = serializers.ReadOnlyField(source='category.category')
