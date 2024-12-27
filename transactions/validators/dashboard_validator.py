from rest_framework.exceptions import ValidationError


class DashboardValidator:
    @staticmethod
    def validate(params):
        errors = {}
        if 'year' not in params:
            errors['year'] = "Year is required."

        if errors:
            raise ValidationError(errors)
        return params
