from rest_framework.exceptions import ValidationError


class ImportParamsValidator:
    @staticmethod
    def validate(params):
        errors = {}
        if 'account_id' not in params:
            errors['account_id'] = "Account ID is required."
        if 'files' not in params:
            errors['files'] = "File names are required."

        if errors:
            raise ValidationError(errors)
        return params
