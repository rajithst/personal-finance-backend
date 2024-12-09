import pandas as pd

from common.constants import TRANSACTION_DATA_FOLDER, INVESTMENT_DATA_FOLDER, LOCAL_STORAGE, GOOGLE_CLOUD_STORAGE
from common.enums import WorkflowContextType
from workflow.providers.storage_backend_provider import StorageBackendProvider
from workflow.contracts.storage_backend_contract import StorageBackendContract
from django.conf import settings

from workflow.contracts.import_workflow_contract import ImportWorkflowContract


class ImportWorkflow:
    def __init__(self, account, account_processor: ImportWorkflowContract, storage_provider: StorageBackendContract = None,
                 is_development=False):
        super().__init__()
        self.account = account
        self.account_processor = account_processor
        self.storage_provider = storage_provider or StorageBackendProvider
        self.is_dev_env = is_development or settings.ENV == 'dev'

    def _load_data(self, file_names, target_path):
        try:
            if file_names:
                formatted_dfs = [
                    self._process_single_file(file_name)
                    for file_name in file_names
                ]
            else:
                formatted_dfs = self._process_all_files(target_path)
            return pd.concat(formatted_dfs, ignore_index=True)
        except Exception as e:
            raise ValueError(f"Error processing files: {str(e)}") from e

    def _process_single_file(self, file_name: str) -> pd.DataFrame:
        try:
            storage = self._get_storage_provider()
            df = storage.read_file(file_name, read_config=self.account_processor.get_read_config())
            df = self.account_processor.process_data(df, self.account)
            return self.account_processor.validate_dataframe(df)
        except Exception as e:
            raise ValueError(f"Error processing file {file_name}: {str(e)}") from e

    def _process_all_files(self, target_path):
        storage = self._get_storage_provider()
        formatted_dfs = storage.read_all_files(target_path)
        return formatted_dfs

    def import_data_from_files(self, workflow_type: WorkflowContextType, file_names=None):
        match workflow_type:
            case WorkflowContextType.TRANSACTION_FILES:
                return self._load_data(file_names, TRANSACTION_DATA_FOLDER)
            case WorkflowContextType.INVESTMENT_FILES:
                return self._load_data(file_names, INVESTMENT_DATA_FOLDER)
            case _:
                raise ValueError(f"Invalid workflow type: {workflow_type}")

    def _get_storage_provider(self):
        return self.storage_provider.get_provider(LOCAL_STORAGE if self.is_dev_env else GOOGLE_CLOUD_STORAGE)
