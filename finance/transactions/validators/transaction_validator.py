from rest_framework.exceptions import ValidationError


class TransactionListValidator:
    @staticmethod
    def validate(params):
        errors = {}
        if 'year' not in params:
            errors['year'] = "Year is required."
        if 'target' not in params:
            errors['target'] = "Query target is required."

        if errors:
            raise ValidationError(errors)
        return params
