from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.portfolio_service import PortfolioService, PortfolioGrowthService, \
    PortfolioGrowthDaemonService
from oauth.permissions import AppEngineCronPermission, AppEngineTaskPermission


class PortfolioSettingsView(APIView):

    def post(self, request):
        try:
            service = PortfolioService()
            response = service.create_portfolio(request.data.copy())
            return Response({'data': response, 'status': True, 'message': 'Success'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        try:
            service = PortfolioService()
            response = service.update_portfolio(request.data.copy())
            return Response({'data': response, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PortfolioGrowthRefreshView(APIView):
    permission_classes = [AppEngineTaskPermission]

    def get(self, request):
        try:
            portfolio_id = request.query_params.get('portfolio')
            if not portfolio_id:
                raise ValueError("Portfolio ID is required.")
            service = PortfolioGrowthService(portfolio_id=portfolio_id)
            response = service.update_portfolio_growth(request.query_params.copy())
            return Response({'data': response, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PortfolioGrowthDaemonView(APIView):
    permission_classes = [AppEngineCronPermission]

    def get(self, request):
        try:
            service = PortfolioGrowthDaemonService()
            response = service.enqueue_portfolio_growth_refresh_tasks()
            return Response({'data': response, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
