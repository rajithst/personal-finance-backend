from rest_framework.exceptions import ValidationError

class UploadParamsValidator:
    @staticmethod
    def validate(params):
        errors = {}
        if 'account_id' not in params:
            errors['account_id'] = "Account ID is required."
        if 'upload_files' not in params:
            errors['upload_files'] = "Upload files are required."

        if errors:
            raise ValidationError(errors)
        return params
