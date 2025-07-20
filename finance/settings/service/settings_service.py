from accounts.models import Account
from accounts.serializers import ResponseAccountSerializer
from finance.categories.models import TransactionCategory, TransactionSubCategory
from finance.categories.serializers import ResponseTransactionCategorySerializer, ResponseTransactionSubCategorySerializer
from common.constants import ACCOUNT_TYPE_CREDIT_CARD, ACCOUNT_TYPE_BANK_ACCOUNT, ACCOUNT_TYPE_INVESTMENT_ACCOUNT, \
    CREDIT_CARD_PROVIDER_RAKUTEN, CREDIT_CARD_PROVIDER_EPOS, CREDIT_CARD_PROVIDER_DOCOMO, BANK_ACCOUNT_PROVIDER_MIZUHO, \
    BANK_ACCOUNT_PROVIDER_JP_POST, INVESTMENT_ACCOUNT_PROVIDER_RAKUTEN


class SettingsService:

    def get_credit_accounts(self):
        accounts = Account.objects.all()
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

    def get_account_types(self):
        return [ACCOUNT_TYPE_BANK_ACCOUNT, ACCOUNT_TYPE_CREDIT_CARD, ACCOUNT_TYPE_INVESTMENT_ACCOUNT]

    def get_account_providers(self):
        return [
            {
                'provider_type': ACCOUNT_TYPE_CREDIT_CARD,
                'value': CREDIT_CARD_PROVIDER_RAKUTEN,
            },
            {
                'provider_type': ACCOUNT_TYPE_CREDIT_CARD,
                'value': CREDIT_CARD_PROVIDER_EPOS,
            },
            {
                'provider_type': ACCOUNT_TYPE_CREDIT_CARD,
                'value': CREDIT_CARD_PROVIDER_DOCOMO,
            },
            {
                'provider_type': ACCOUNT_TYPE_BANK_ACCOUNT,
                'value': BANK_ACCOUNT_PROVIDER_MIZUHO,
            },
            {
                'provider_type': ACCOUNT_TYPE_BANK_ACCOUNT,
                'value': BANK_ACCOUNT_PROVIDER_JP_POST,
            },
            {
                'provider_type': ACCOUNT_TYPE_INVESTMENT_ACCOUNT,
                'value': INVESTMENT_ACCOUNT_PROVIDER_RAKUTEN,
            }
        ]
