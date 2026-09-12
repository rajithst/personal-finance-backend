import logging
import os
from typing import Any, Dict, List, Optional

import pandas as pd
from django.conf import settings
from django.core.files.storage import default_storage

from workflow.contracts.storage_backend_contract import StorageBackendContract


class LocalStorageHandler(StorageBackendContract):

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or settings.MEDIA_ROOT

    def upload_file(self, file: Any, file_name: str, content_type: Optional[str] = None) -> bool:
        file_path = os.path.join(self.base_path, file_name)
        try:
            parent_dir = os.path.dirname(file_path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

            with open(file_path, 'wb+') as destination:
                if hasattr(file, 'chunks'):
                    for chunk in file.chunks():
                        destination.write(chunk)
                elif hasattr(file, 'read'):
                    destination.write(file.read())
                elif isinstance(file, bytes):
                    destination.write(file)
                else:
                    destination.write(str(file).encode('utf-8'))
            return True
        except Exception as e:
            logging.exception(f'Failed to write file to local storage: {e}')
            return False

    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        data_path = os.path.join(self.base_path, prefix) if prefix else self.base_path
        if not os.path.exists(data_path):
            return []
        try:
            entries = []
            for root, _, files in os.walk(data_path):
                for f in files:
                    rel_path = os.path.relpath(os.path.join(root, f), self.base_path)
                    entries.append(rel_path)
            return entries
        except Exception as e:
            logging.exception(f'Failed to list files in local storage: {e}')
            return []

    def delete_file(self, file_name: str) -> bool:
        file_path = os.path.join(self.base_path, file_name)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logging.exception(f'Failed to delete file {file_name}: {e}')
            return False

    def read_file(self, file_name: str, read_config: Optional[Dict[str, Any]] = None):
        file_path = os.path.join(self.base_path, file_name)
        encoding = read_config.get('encoding') if read_config else None
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found in storage: {file_name}")
        return open(file_path, 'r', encoding=encoding)

    def read_all_files(self, prefix: str, read_config: Optional[Dict[str, Any]] = None) -> List[pd.DataFrame]:
        files = self.list_files(prefix)
        all_dfs = []
        for file in files:
            df = self.read_csv(file, read_config)
            if df is not None:
                all_dfs.append(df)
        return all_dfs

    def read_csv(self, file_name: str, read_config: Optional[Dict[str, Any]] = None) -> Optional[pd.DataFrame]:
        file_path = os.path.join(self.base_path, file_name)
        if not os.path.exists(file_path):
            return None
        config = read_config.copy() if read_config else {}
        return pd.read_csv(file_path, **config)


# Backward-compatible alias
LocalStorage = LocalStorageHandler


