from investments.models import Portfolio
from investments.serializers.response_serializers import ResponsePortfolioSerializer
from investments.serializers.serializers import PortfolioSerializer
from oauth.middleware import get_current_user


class PortfolioService:

    def create_portfolio(self, data):
        if 'user' not in data:
            user = get_current_user()
            data['user'] = user.id
        serializer = PortfolioSerializer(data=data)
        return self.handle_serializer(serializer)

    def update_portfolio(self, data):
        account = Portfolio.objects.get(pk=data.get('id'))
        serializer = PortfolioSerializer(account, data=data, partial=True)
        return self.handle_serializer(serializer)

    def handle_serializer(self, serializer):
        if serializer.is_valid(raise_exception=True):
            saved_item = serializer.save()
            response_serializer = ResponsePortfolioSerializer(saved_item)
            return response_serializer.data
        return serializer.errors
