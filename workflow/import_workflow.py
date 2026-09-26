import logging
from typing import List, Optional, Union

import pandas as pd
from django.conf import settings

from common.constants import TRANSACTION_DATA_FOLDER, LOCAL_STORAGE, GOOGLE_CLOUD_STORAGE
from common.enums import WorkflowContextType
from workflow.contracts.import_workflow_contract import ImportWorkflowContract
from workflow.contracts.storage_backend_contract import StorageBackendContract
from workflow.providers.storage_backend_provider import StorageBackendProvider

logger = logging.getLogger(__name__)

__all__ = ["ImportCsvWorkflow", "ImportWorkflowContract"]


class ImportCsvWorkflow:
    def __init__(self, account, account_processor: ImportWorkflowContract,
                 storage_provider: StorageBackendContract = None,
                 is_development: bool = False):
        self.account = account
        self.account_processor = account_processor
        self.storage_provider = storage_provider or StorageBackendProvider
        self.is_dev_env = is_development or settings.ENV == 'dev'

    def _load_data(self, file_names: Optional[List[str]], target_path: str) -> pd.DataFrame:
        try:
            if file_names:
                formatted_dfs = [
                    self._process_single_file(file_name)
                    for file_name in file_names
                ]
            else:
                formatted_dfs = self._process_all_files(target_path)
            if not formatted_dfs:
                return pd.DataFrame()
            return pd.concat(formatted_dfs, ignore_index=True)
        except Exception as e:
            logger.exception("Error processing files from target path %s: %s", target_path, e)
            raise ValueError(f"Error processing files: {str(e)}") from e

    def _skip_rows(self, file_object, keywords: List[str]) -> int:
        skip_count = 0
        for line in file_object:
            row = [item.strip('\'"').lstrip('\ufeff') for item in line.strip().split(",")]
            row = [item.strip('\'"') for item in row]
            if set(keywords).issubset(row):
                break
            skip_count += 1
        return skip_count

    def _read_with_encoding_fallback(self, storage, file_name: str, base_read_config: dict) -> pd.DataFrame:
        candidate_encodings = []
        preferred = base_read_config.get('encoding')
        if preferred:
            candidate_encodings.append(preferred)
        for enc in ['cp932', 'shift_jis', 'utf-8-sig', 'utf-8']:
            if enc not in candidate_encodings:
                candidate_encodings.append(enc)

        last_error = None
        for enc in candidate_encodings:
            cfg = base_read_config.copy()
            cfg['encoding'] = enc
            try:
                if not cfg.get('skiprows'):
                    expected_columns = self.account_processor.get_expected_columns()
                    if not expected_columns:
                        raise ValueError('Expected columns should be defined or skiprows should be set in read_config')
                    file_object = storage.read_file(file_name, read_config=cfg)
                    try:
                        skip_rows = self._skip_rows(file_object, expected_columns)
                    finally:
                        if hasattr(file_object, "close"):
                            file_object.close()
                    cfg['skiprows'] = skip_rows

                df = storage.read_csv(file_name, read_config=cfg)
                if df is not None and not df.empty:
                    return df
            except (UnicodeDecodeError, UnicodeError) as ue:
                last_error = ue
                continue
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise last_error
        raise ValueError(f"Could not read file {file_name} with supported encodings.")

    def _process_single_file(self, file_name: str) -> pd.DataFrame:
        try:
            storage = self._get_storage_provider()
            init_read_config = dict(self.account_processor.get_read_config())
            df = self._read_with_encoding_fallback(storage, file_name, init_read_config)
            df = df.reset_index(drop=True)
            df = self.account_processor.process_data(df, self.account)
            return self.account_processor.validate_dataframe(df)
        except Exception as e:
            logger.exception('Error processing file %s: %s', file_name, e)
            raise ValueError(f"Error processing file {file_name}: {str(e)}") from e

    def _process_all_files(self, target_path: str) -> List[pd.DataFrame]:
        storage = self._get_storage_provider()
        files = storage.list_files(target_path)
        return [self._process_single_file(f) for f in files if f.endswith('.csv')]

    def import_data_from_files(self, workflow_type: Union[WorkflowContextType, str],
                               file_names: Optional[List[str]] = None) -> pd.DataFrame:
        if isinstance(workflow_type, WorkflowContextType):
            match workflow_type:
                case WorkflowContextType.TRANSACTION_FILES:
                    target_path = TRANSACTION_DATA_FOLDER
                case _:
                    raise ValueError(f"Invalid workflow type: {workflow_type}")
        elif isinstance(workflow_type, str):
            target_path = workflow_type
        else:
            raise ValueError(f"Invalid workflow type: {workflow_type}")
        return self._load_data(file_names, target_path)

    def _get_storage_provider(self) -> StorageBackendContract:
        return self.storage_provider.get_provider(LOCAL_STORAGE if self.is_dev_env else GOOGLE_CLOUD_STORAGE)

