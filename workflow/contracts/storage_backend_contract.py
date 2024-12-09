from abc import ABC, abstractmethod


class StorageBackendContract(ABC):
    @abstractmethod
    def upload_file(self, file, file_name, content_type=None):
        pass

    @abstractmethod
    def read_file(self, file_name, read_config, file_type=None):
        pass

    @abstractmethod
    def list_files(self, prefix=None):
        pass

    @abstractmethod
    def delete_file(self, file_name):
        pass

    @abstractmethod
    def read_all_files(self, prefix, read_config):
        pass
