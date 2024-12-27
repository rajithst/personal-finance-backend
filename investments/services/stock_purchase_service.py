import logging

from django.db import transaction
from rest_framework.exceptions import ValidationError

from common.enums import BrokerProviders, WorkflowContextType
from investments.models import StockPurchaseHistory, Portfolio, Company
from investments.serializers.response_serializers import ResponseStockPurchaseHistorySerializer
from investments.serializers.serializers import StockPurchaseHistorySerializer
from investments.services.broker_loaders import RakutenBrokerForeignStockLoader, \
    RakutenBrokerDomesticStockLoader
from investments.services.company_service import CompanyService
from investments.validators.import_validator import ImportParamsValidator
from investments.validators.stock_validator import PurchaseHistoryValidator
from investments.validators.upload_validator import UploadParamsValidator
from transactions.models import Account
from workflow.import_workflow import ImportWorkflow, ImportWorkflowContract
from workflow.providers.storage_backend_provider import StorageBackendProvider
from workflow.upload_workflow import UploadWorkflow

logger = logging.getLogger(__name__)


class StockPurchaseService:
    def __init__(self, broker_factory=None, storage_factory=None, import_workflow=None,
                 upload_workflow=None):
        self.broker_factory = broker_factory or BrokerProcessFactory
        self.storage_factory = storage_factory or StorageBackendProvider
        self.import_workflow = import_workflow or ImportWorkflow
        self.upload_workflow = upload_workflow or UploadWorkflow

    def import_purchases(self, import_params):
        try:
            ImportParamsValidator.validate(import_params)
            account = self.get_account_from_id(import_params['account'])
            portfolio = self.get_portfolio_from_id(import_params['portfolio'])
            if not account:
                raise ValidationError({"account_id": "Invalid account ID."})
            if not portfolio:
                raise ValidationError({"portfolio_id": "Invalid account ID."})
            account_processor = self.broker_factory.get_processor(account.provider, import_params.get('target', None))
            service = self.import_workflow(account, account_processor)
            trades = service.import_data_from_files(WorkflowContextType.INVESTMENT_FILES,
                                                    import_params.get('files', None))
            if trades.empty:
                return True
            trades = trades.assign(**{'account': account.id, 'portfolio': portfolio.id})
            return trades.to_dict(orient='records')
        except Exception as e:
            logger.error(f"Error importing purchases: {e}")
            raise e

    def get_account_from_id(self, account_id):
        account = Account.objects.filter(id=account_id).first()
        return account

    def get_portfolio_from_id(self, account_id):
        account = Portfolio.objects.filter(id=account_id).first()
        return account

    def upload_purchase_files(self, upload_params):
        try:
            UploadParamsValidator.validate(upload_params)
            account = self.get_account_from_id(upload_params['account_id'])
            service = self.upload_workflow(account)
            uploaded_files = service.upload_files(WorkflowContextType.INVESTMENT_FILES, upload_params['upload_files'])
            return uploaded_files
        except Exception as e:
            logger.error(f"Error uploading purchase files: {e}")
            raise e

    def create_bulk_purchase(self, trade_data):
        companies = [item.get('company') for item in trade_data]
        existing_companies = list(Company.objects.values_list('symbol', flat=True))
        new_companies = [c for c in companies if c not in existing_companies]
        if new_companies:
            company_service = CompanyService()
            company_service.fetch_company_info({'companies': ','.join(new_companies)})
        with transaction.atomic():
            purchase_history_serializer = StockPurchaseHistorySerializer(data=trade_data, many=True)
            if purchase_history_serializer.is_valid(raise_exception=True):
                purchase_history_serializer.save()
                return True, purchase_history_serializer.data
            return False, purchase_history_serializer.errors

    def create_purchase(self, request_data):
        serializer = StockPurchaseHistorySerializer(data=request_data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return True, serializer.data
        return False, serializer.errors

    def get_purchase_history(self, purchase_params):
        PurchaseHistoryValidator.validate(purchase_params)
        filter_params = {'portfolio_id': purchase_params.get('portfolio')}
        if purchase_params.get('company'):
            filter_params['company_id'] = purchase_params.get('company')
        queryset = StockPurchaseHistory.objects.select_related('company').filter(**filter_params)
        serializer = ResponseStockPurchaseHistorySerializer(queryset, many=True)
        return serializer.data


class BrokerProcessFactory:
    """
    Factory class for retrieving broker-specific data processing loaders.
    """

    @staticmethod
    def get_processor(provider, target=None) -> ImportWorkflowContract:
        """
        Retrieves the appropriate loader for a given provider and target.

        Args:
            provider (str): Broker provider name.
            target (str, optional): Target type ('FOREIGN' or 'DOMESTIC').

        Returns:
            ImportWorkflowContract: An instance of the appropriate loader class.

        Raises:
            ValueError: If the target is missing or no loader is found for the provider and target combination.
        """
        BROKER_LOADERS = {
            (BrokerProviders.RAKUTEN.value, 'FOREIGN'): RakutenBrokerForeignStockLoader,
            (BrokerProviders.RAKUTEN.value, 'DOMESTIC'): RakutenBrokerDomesticStockLoader,
        }
        if not target:
            raise ValueError("Target is required for RakutenBroker.")
        loader_class = BROKER_LOADERS.get((provider, target))
        if not loader_class:
            raise ValueError(f"No loader found for provider {provider} and target {target}.")
        return loader_class()
