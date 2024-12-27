from rest_framework.exceptions import ValidationError


class DividendValidator:
    @staticmethod
    def validate_request(params):
        errors = {}
        if not params.get('company'):
            errors['company'] = "Company symbol is required."

        if errors:
            raise ValidationError(errors)
        return params


class DividendPaymentValidator:
    @staticmethod
    def validate_request(params):
        errors = {}
        if not params.get('portfolio'):
            errors['portfolio'] = "Portfolio ID is required."

        if errors:
            raise ValidationError(errors)
        return params