from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.dashboard_service import DashboardService
from investments.services.portfolio_service import PortfolioService
from investments.services.settings_service import SettingsService
from investments.validators.dashboard_validator import DashboardValidator


class InvestmentPerformanceView(APIView):
    def get(self, request):
        try:
            DashboardValidator.validate_request(request.query_params.copy())
            dashboard_service = DashboardService(portfolio_id=request.query_params.get('portfolio'))
            monthly_invested_amount = dashboard_service.get_monthly_invested_amount()
            allocation = dashboard_service.get_portfolio_allocation()
            portfolio_performance = dashboard_service.get_performance()
            growth = dashboard_service.get_portfolio_growth_daily()
            sector_performance = dashboard_service.get_sector_wise_performance()
            return Response({'data': {
                'total_investment': portfolio_performance.get('total_investment'),
                'current_portfolio_value': portfolio_performance.get('current_portfolio_value'),
                'total_profit': portfolio_performance.get('total_profit'),
                'monthly_investment': monthly_invested_amount,
                'sector_allocation': allocation.get('sector_allocation'),
                'industry_allocation': allocation.get('industry_allocation'),
                'growth': growth,
                'sector_performance': sector_performance
            }, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ClientSettingsView(APIView):
    def get(self, request):
        try:
            service = SettingsService()
            broker_accounts = service.get_broker_accounts()
            portfolios = service.get_portfolios()
            return Response({'data': {
                'broker_accounts': broker_accounts,
                'portfolios': portfolios
            }, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
