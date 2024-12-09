from rest_framework.exceptions import ValidationError

class ImportParamsValidator:
    @staticmethod
    def validate(params):
        errors = {}
        if 'account' not in params:
            errors['account'] = "Account ID is required."
        if 'portfolio' not in params:
            errors['portfolio'] = "Portfolio ID is required."
        if 'files' not in params:
            errors['files'] = "File names are required."

        if errors:
            raise ValidationError(errors)
        return params
