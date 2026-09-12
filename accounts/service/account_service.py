from accounts.models import Account
from accounts.serializers import AccountSerializer, ResponseAccountSerializer


class AccountService:

    def create_account(self, data):
        serializer = AccountSerializer(data=data)
        return self.handle_serializer(serializer)

    def update_account(self, data):
        account_id = data.get('id') if isinstance(data, dict) else None
        account = Account.objects.filter(pk=account_id).first()
        if not account:
            raise Account.DoesNotExist(f"Account with id {account_id} does not exist.")
        serializer = AccountSerializer(account, data=data, partial=True)
        return self.handle_serializer(serializer)

    def handle_serializer(self, serializer):
        serializer.is_valid(raise_exception=True)
        saved_item = serializer.save()
        response_serializer = ResponseAccountSerializer(saved_item)
        return response_serializer.data


# Backward-compatible alias for existing imports
CreditAccountService = AccountService
