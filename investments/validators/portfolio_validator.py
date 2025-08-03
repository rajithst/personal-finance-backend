from rest_framework.exceptions import ValidationError


class PortfolioValidator:
    @staticmethod
    def validate_request(params):
        errors = {}
        if not params.get('portfolio'):
            errors['portfolio'] = "Portfolio ID is required."
        if params.get('portfolio') == '0':
            errors['portfolio'] = "Portfolio not found."
        if errors:
            raise ValidationError(errors)
        return params
