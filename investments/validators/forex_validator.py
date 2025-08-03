from rest_framework.exceptions import ValidationError


class ForexValidator:
    @staticmethod
    def validate_request(params):
        errors = {}
        if not params.get('currency'):
            errors['currency'] = "Currency is required."

        if errors:
            raise ValidationError(errors)
        return params
