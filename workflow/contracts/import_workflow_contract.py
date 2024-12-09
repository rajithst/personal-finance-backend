from abc import ABC, abstractmethod


class ImportWorkflowContract(ABC):

    @abstractmethod
    def get_read_config(self):
        pass

    @abstractmethod
    def process_data(self, data, account):
        pass

    @abstractmethod
    def validate_dataframe(self, dataframe):
        pass
