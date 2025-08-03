from accounts.models import Account
from accounts.serializers import ResponseAccountSerializer
from common.constants import ACCOUNT_TYPE_INVESTMENT_ACCOUNT
from investments.portfolio.models import Portfolio
from investments.portfolio.serializers import ResponsePortfolioSerializer


class SettingsService:

    def get_portfolios(self):
        portfolios = Portfolio.objects.all()
        serializer = ResponsePortfolioSerializer(portfolios, many=True)
        return serializer.data

    def get_broker_accounts(self):
        accounts = Account.objects.filter(account_type=ACCOUNT_TYPE_INVESTMENT_ACCOUNT).all()
        serializer = ResponseAccountSerializer(accounts, many=True)
        return serializer.data
