from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.dashboard_service import DashboardService, PortfolioService


class InvestmentPerformanceView(APIView):
    def get(self, request):
        year = request.query_params.get('year', 2024)
        dashboard_service = DashboardService()
        monthly_invested_amount = dashboard_service.get_monthly_invested_amount(year)
        allocation = dashboard_service.get_portfolio_allocation()
        portfolio_performance = dashboard_service.get_performance()
        return Response({
            'total_investment': portfolio_performance.get('total_investment'),
            'current_portfolio_value': portfolio_performance.get('current_portfolio_value'),
            'total_profit': portfolio_performance.get('total_profit'),
            'monthly_investment': monthly_invested_amount,
            'sector_allocation': allocation.get('sector_allocation'),
            'industry_allocation': allocation.get('industry_allocation'),
        }, status=status.HTTP_200_OK)


class PortfolioView(APIView):
    def get(self, request):
        service = PortfolioService()
        portfolios = service.get_portfolios()
        return Response(portfolios, status=status.HTTP_200_OK)
