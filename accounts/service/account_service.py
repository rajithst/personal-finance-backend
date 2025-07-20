from accounts.models import Account
from accounts.serializers import AccountSerializer, ResponseAccountSerializer


class CreditAccountService:

    def create_account(self, data):
        serializer = AccountSerializer(data=data)
        return self.handle_serializer(serializer)

    def update_account(self, data):
        account = Account.objects.get(pk=data.get('id'))
        serializer = AccountSerializer(account, data=data, partial=True)
        return self.handle_serializer(serializer)

    def handle_serializer(self, serializer):
        if serializer.is_valid(raise_exception=True):
            saved_item = serializer.save()
            response_serializer = ResponseAccountSerializer(saved_item)
            return response_serializer.data
        return serializer.errors
