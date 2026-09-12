from abc import ABC, abstractmethod
from typing import Any, Dict, List
import pandas as pd


class ImportWorkflowContract(ABC):
    """
    Contract for statement loaders (e.g., credit card and bank account loaders).
    Standardizes configuration, expected column headers, data transformations, and validation.
    """

    @abstractmethod
    def get_read_config(self) -> Dict[str, Any]:
        """Return pandas read_csv kwargs (e.g. encoding, skiprows, header)."""
        pass

    def get_expected_columns(self) -> List[str]:
        """Return list of expected column header names used to detect statement header row."""
        return []

    @abstractmethod
    def process_data(self, data: pd.DataFrame, account: Any) -> pd.DataFrame:
        """Transform raw statement dataframe into standardized transaction dataframe."""
        pass

    @abstractmethod
    def validate_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Validate and clean transaction dataframe before database persistence."""
        pass
