from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.dashboard.service.dashboard_service import DashboardService
from investments.validators.portfolio_validator import PortfolioValidator

import logging
class InvestmentDashboardView(APIView):
    def get(self, request):
        try:
            PortfolioValidator.validate_request(request.query_params.copy())
            portfolio_id = request.query_params.get('portfolio')
            dashboard_service = DashboardService(portfolio_id=portfolio_id)

            monthly_invested_amount = dashboard_service.get_monthly_invested_amount()
            allocation = dashboard_service.get_portfolio_allocation()
            portfolio_performance = dashboard_service.get_performance()
            growth = dashboard_service.get_portfolio_growth_daily()
            sector_performance = dashboard_service.get_sector_wise_performance()
            passive_income = dashboard_service.get_passive_income()
            return Response({'data': {
                'total_investment': portfolio_performance.get('total_investment'),
                'current_portfolio_value': portfolio_performance.get('current_portfolio_value'),
                'total_profit': portfolio_performance.get('total_profit'),
                'monthly_investment': monthly_invested_amount,
                'sector_allocation': allocation.get('sector_allocation'),
                'industry_allocation': allocation.get('industry_allocation'),
                'passive_income': passive_income,
                'growth': growth,
                'sector_performance': sector_performance
            }, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except ValidationError as e:
            logging.exception('Validation error in dividend income request', exc_info=e)
            return Response({'data': None, 'message': str(e), 'status': False},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
