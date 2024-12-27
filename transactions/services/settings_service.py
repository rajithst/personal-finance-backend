from transactions.models import Account, TransactionCategory, TransactionSubCategory
from transactions.serializers.response_serializers import ResponseAccountSerializer, \
    ResponseTransactionCategorySerializer, ResponseTransactionSubCategorySerializer


class SettingsService:

    def get_credit_accounts(self):
        accounts = Account.objects.filter(account_type='CREDIT_ACCOUNT').all()
        serializer = ResponseAccountSerializer(accounts, many=True)
        return serializer.data

    def get_transaction_categories(self):
        transaction_categories = TransactionCategory.objects.all()
        serializer = ResponseTransactionCategorySerializer(transaction_categories, many=True)
        return serializer.data

    def get_transaction_subcategories(self):
        transaction_subcategories = TransactionSubCategory.objects.select_related('category').all()
        serializer = ResponseTransactionSubCategorySerializer(transaction_subcategories, many=True)
        return serializer.data
