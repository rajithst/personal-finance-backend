from rest_framework.exceptions import ValidationError


class DashboardValidator:
    @staticmethod
    def validate_request(params):
        errors = {}
        if not params.get('portfolio'):
            errors['portfolio'] = "Portfolio ID is required."

        if errors:
            raise ValidationError(errors)
        return params