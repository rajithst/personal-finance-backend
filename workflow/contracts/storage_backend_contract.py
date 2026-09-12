from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class StorageBackendContract(ABC):
    """
    Abstract contract defining file storage operations across different storage backends
    (e.g., Local filesystem, Google Cloud Storage, S3).
    """

    @abstractmethod
    def upload_file(self, file: Any, file_name: str, content_type: Optional[str] = None) -> bool:
        """Upload a file or stream to the storage backend."""
        pass

    @abstractmethod
    def read_file(self, file_name: str, read_config: Optional[Dict[str, Any]] = None) -> Any:
        """Read a file and return a readable stream or file-like object."""
        pass

    @abstractmethod
    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        """List file paths in storage matching the given prefix."""
        pass

    @abstractmethod
    def delete_file(self, file_name: str) -> bool:
        """Delete a file from the storage backend."""
        pass

    @abstractmethod
    def read_all_files(self, prefix: str, read_config: Optional[Dict[str, Any]] = None) -> List[Any]:
        """Read all files matching the prefix into a list of file-like streams."""
        pass

    @abstractmethod
    def read_csv(self, file_name: str, read_config: Optional[Dict[str, Any]] = None) -> Any:
        """Read a CSV file into a pandas DataFrame."""
        pass
