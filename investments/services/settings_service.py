from common.constants import ACCOUNT_TYPE_INVESTMENT_ACCOUNT
from investments.models import Portfolio
from investments.serializers.response_serializers import ResponsePortfolioSerializer
from transactions.models import Account
from transactions.serializers.response_serializers import ResponseAccountSerializer


class SettingsService:

    def get_portfolios(self):
        portfolios = Portfolio.objects.all()
        serializer = ResponsePortfolioSerializer(portfolios, many=True)
        return serializer.data

    def get_broker_accounts(self):
        accounts = Account.objects.filter(account_type=ACCOUNT_TYPE_INVESTMENT_ACCOUNT).all()
        serializer = ResponseAccountSerializer(accounts, many=True)
        return serializer.data