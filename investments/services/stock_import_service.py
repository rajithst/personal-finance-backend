import pandas as pd

from common.enums import BrokerProviders
from investments.serializers.serializers import StockPurchaseHistorySerializer
from investments.services.broker_loaders import RakutenBrokerForeignStockLoader, \
    RakutenBrokerDomesticStockLoader
from oauth.middleware import get_current_user
from transactions.models import Account
from utils.import_service_worker import ImportServiceWorker, ServiceLoader


class StockImportService:
    def import_trades(self, import_params):
        user = get_current_user()
        account_id = import_params['account_id']
        account = Account.objects.filter(id=account_id).first()
        file_names = import_params.get('files', None)
        target = import_params.get('target', None)
        account_processor = BrokerProcessFactory.get_processor(account.provider, target)
        service = ImportServiceWorker(account, account_processor)
        trades = service.load_stock_trades(file_names)
        return trades

class BrokerProcessFactory:
    @staticmethod
    def get_processor(provider, target=None) -> ServiceLoader:
        if provider == BrokerProviders.RAKUTEN.value:
            if target is None:
                raise ValueError('target is required for RakutenBroker')
            if target == 'FOREIGN':
                return RakutenBrokerForeignStockLoader()
            elif target == 'DOMESTIC':
                return RakutenBrokerDomesticStockLoader()
        else:
            raise ValueError('Unknown source')
