from abc import ABC, abstractmethod

import pandas as pd

from utils.file_reader import BaseReader
from rest_framework.exceptions import AuthenticationFailed
from oauth.middleware import get_current_user


class ServiceLoader(ABC):

    @abstractmethod
    def get_read_config(self):
        pass

    @abstractmethod
    def process_data(self, data, account):
        pass

    @abstractmethod
    def validate_dataframe(self, dataframe):
        pass


class ImportServiceWorker(BaseReader):

    def __init__(self, account, account_processor: ServiceLoader):
        super().__init__()
        self.account = account
        self.account_processor = account_processor

    def load_data(self, file_names, account, target_path):
        if file_names:
            formatted_dfs = []
            for file_name in file_names:
                df = self.read_single_file(file_name, read_config=self.account_processor.get_read_config())
                formatted_data = self.account_processor.process_data(df, account)
                validated_data = self.account_processor.validate_dataframe(formatted_data)
                formatted_dfs.append(validated_data)
            processed_data = pd.concat(formatted_dfs, ignore_index=True)
        else:
            processed_data = self.read_all_files(target_path, read_config=self.account_processor.get_read_config())
        return processed_data

    def load_transactions(self, file_names=None):
        processed_data = self._handle_import_process(file_names, target_path='finance')
        return processed_data

    def load_stock_trades(self, file_names=None):
        processed_data = self._handle_import_process(file_names, target_path='investments')
        return processed_data

    def _handle_import_process(self, file_names, target_path):
        user = get_current_user()
        account = self.account
        if not user:
            raise AuthenticationFailed('Unauthenticated import.')
        data_path = f'user_{user.id}/{target_path}/acc_{account.id}/'
        processed_data = self.load_data(file_names, account, data_path)
        return processed_data
