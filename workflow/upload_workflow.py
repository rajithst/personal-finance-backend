import logging
import time
from typing import Any, Dict, List, Union

from django.conf import settings

from common.constants import TRANSACTION_DATA_FOLDER, LOCAL_STORAGE, GOOGLE_CLOUD_STORAGE
from common.enums import WorkflowContextType
from oauth.middleware import get_current_user
from workflow.contracts.storage_backend_contract import StorageBackendContract
from workflow.providers.storage_backend_provider import StorageBackendProvider

logger = logging.getLogger(__name__)


class UploadWorkflow:
    def __init__(self, account, storage_provider: StorageBackendContract = None,
                 is_development: bool = False):
        self.account = account
        self.storage_provider = storage_provider or StorageBackendProvider
        self.is_dev_env = is_development or settings.ENV == 'dev'

    def _upload_files(self, files, target: str) -> List[str]:
        file_map = self._get_target_file_mapping(files, target)
        storage_provider = self._get_storage_provider()
        uploaded_files = []
        for file_name, file in file_map.items():
            try:
                uploaded = storage_provider.upload_file(file, file_name)
                if uploaded:
                    uploaded_files.append(file_name)
                else:
                    logger.warning("Failed to upload file to storage: %s", file_name)
            except Exception as e:
                logger.exception("Error uploading file %s: %s", file_name, e)
                raise
        return uploaded_files

    def _get_target_file_mapping(self, files, target: str) -> Dict[str, Any]:
        user = get_current_user()
        account_id = getattr(self.account, 'id', 'default')
        user_id = getattr(user, 'id', 'anonymous') if user else 'anonymous'
        file_map = {}
        for upload_file in files:
            file_basename = getattr(upload_file, 'name', 'unnamed_file')
            upload_file_name = f"{int(time.time())}_{file_basename}"
            file_name = f"user_{user_id}/{target}/acc_{account_id}/{upload_file_name}"
            file_map[file_name] = upload_file
        return file_map

    def upload_files(self, workflow_type: Union[WorkflowContextType, str], files) -> List[str]:
        if isinstance(workflow_type, WorkflowContextType):
            match workflow_type:
                case WorkflowContextType.TRANSACTION_FILES:
                    target = TRANSACTION_DATA_FOLDER
                case _:
                    raise ValueError(f"Invalid workflow type: {workflow_type}")
        elif isinstance(workflow_type, str):
            target = workflow_type
        else:
            raise ValueError(f"Invalid workflow type: {workflow_type}")
        return self._upload_files(files, target)

    def _get_storage_provider(self) -> StorageBackendContract:
        return self.storage_provider.get_provider(LOCAL_STORAGE if self.is_dev_env else GOOGLE_CLOUD_STORAGE)

