from rest_framework.views import APIView

from investments.services.portfolio_service import PortfolioService, PortfolioGrowthService

from rest_framework import status
from rest_framework.response import Response

from oauth.permissions import AppEngineCronPermission


class PortfolioSettingsView(APIView):

    def post(self, request):
        try:
            data = request.data
            service = PortfolioService()
            response = service.create_portfolio(data)
            return Response({'data': response, 'status': True, 'message': 'Success'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            data = request.data
            service = PortfolioService()
            response = service.update_portfolio(data)
            return Response({'data': response, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PortfolioGrowthDaemonView(APIView):
    permission_classes = [AppEngineCronPermission]

    def get(self, request):
        try:
            task = request.query_params.get('task', None)
            portfolio_id = request.query_params.get('portfolio')
            service = PortfolioGrowthService(portfolio_id=portfolio_id)
            response = service.update_portfolio_growth(request.query_params.copy())
            return Response({'data': response, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
