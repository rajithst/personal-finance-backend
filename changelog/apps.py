from django.apps import AppConfig


class ChangelogConfig(AppConfig):
    name = 'changelog'
    verbose_name = 'Changelog'

    def ready(self):
        # Import the signals module to ensure the signals are registered
        try:
            import changelog.signals.handler
        except ImportError as e:
            print(f"Error importing changelog signals: {e}")
        else:
            print("Changelog signals registered successfully.")
