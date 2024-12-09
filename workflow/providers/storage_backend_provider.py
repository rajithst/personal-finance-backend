from common.constants import LOCAL_STORAGE, GOOGLE_CLOUD_STORAGE
from workflow.storage_backend.google_cloud_storage import GCSHandler
from workflow.storage_backend.local_storage import LocalStorageHandler


class StorageBackendProvider:
    @staticmethod
    def get_provider(provider):
        STORAGE_PROVIDERS = {
            LOCAL_STORAGE: LocalStorageHandler,
            GOOGLE_CLOUD_STORAGE: GCSHandler
        }
        if not provider:
            raise ValueError("Target is required for Cloud storage provider.")
        provider_class = STORAGE_PROVIDERS.get(provider)
        if not provider_class:
            raise ValueError(f"No provider found for provider {provider}.")
        return provider_class()
