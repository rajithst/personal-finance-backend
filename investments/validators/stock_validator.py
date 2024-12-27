from rest_framework.exceptions import ValidationError


class TickerValidator:
    @staticmethod
    def validate(params):
        errors = {}
        if 'company' not in params:
            errors['company'] = "Company symbol is required."

        if errors:
            raise ValidationError(errors)
        return params


class BulkTickerValidator:
    @staticmethod
    def validate(params):
        errors = {}
        if 'companies' not in params:
            errors['companies'] = "Company symbols are required."
        if params.get('companies') and not isinstance(params.get('companies'), str):
            errors['companies'] = "Company symbols must be a comma-separated string."

        if errors:
            raise ValidationError(errors)
        return params


class SyncHistoricalDataValidator:
    @staticmethod
    def validate(params):
        errors = {}
        if 'companies' not in params:
            errors['companies'] = "Company symbols are required."

        if errors:
            raise ValidationError(errors)
        return params


class PurchaseHistoryValidator:
    @staticmethod
    def validate(params):
        errors = {}
        if 'portfolio' not in params:
            errors['portfolio'] = "Portfolio ID is required."
        if errors:
            raise ValidationError(errors)
        return params
