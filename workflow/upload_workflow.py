import time

from django.conf import settings

from common.constants import TRANSACTION_DATA_FOLDER, INVESTMENT_DATA_FOLDER, LOCAL_STORAGE, GOOGLE_CLOUD_STORAGE
from common.enums import WorkflowContextType
from oauth.middleware import get_current_user
from workflow.contracts.storage_backend_contract import StorageBackendContract
from workflow.providers.storage_backend_provider import StorageBackendProvider


class UploadWorkflow:
    def __init__(self, account, storage_provider: StorageBackendContract = None,
                 is_development=False):
        super().__init__()
        self.account = account
        self.storage_provider = storage_provider or StorageBackendProvider
        self.is_dev_env = is_development or settings.ENV == 'dev'

    def _upload_files(self, files, target):
        file_map = self._get_target_file_mapping(files, target)
        storage_provider = self._get_storage_provider()
        uploaded_files = []
        for file_name, file in file_map.items():
            uploaded = storage_provider.upload_file(file, file_name)
            if uploaded:
                uploaded_files.append(file_name)
        return uploaded_files

    def _get_target_file_mapping(self, files, target):
        user = get_current_user()
        account_id = self.account.id
        file_map = {}
        for upload_file in files:
            upload_file_name = f"{int(time.time())}_{upload_file.name}"
            file_name = f"user_{user.id}/{target}/acc_{account_id}/{upload_file_name}"
            file_map[file_name] = upload_file
        return file_map

    def upload_files(self, workflow_type: WorkflowContextType, file_names):
        match workflow_type:
            case WorkflowContextType.TRANSACTION_FILES:
                return self._upload_files(file_names, TRANSACTION_DATA_FOLDER)
            case WorkflowContextType.INVESTMENT_FILES:
                return self._upload_files(file_names, INVESTMENT_DATA_FOLDER)
            case _:
                raise ValueError(f"Invalid workflow type: {workflow_type}")

    def _get_storage_provider(self):
        return self.storage_provider.get_provider(LOCAL_STORAGE if self.is_dev_env else GOOGLE_CLOUD_STORAGE)
