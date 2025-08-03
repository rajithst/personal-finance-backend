from rest_framework.exceptions import ValidationError


class CreateHoldingValidator:
    @staticmethod
    def validate(params):
        errors = {}
        if not params.get('company'):
            errors['company'] = "Company symbol is required."
        if not params.get('portfolio'):
            errors['portfolio'] = "Portfolio is required."
        if not params.get('quantity') or not params.get('purchase_price'):
            errors['quantity'] = "Quantity and purchase price are required."

        if errors:
            raise ValidationError(errors)
        return params
