
from rest_framework.views import APIView

from investments.models import StockPurchaseHistory
from investments.services.dashboard_service import DashboardService


class DashboardView(APIView):
    def get(self, request):
        year = request.query_params.get('year', 2024)
        dashboard_service = DashboardService()
        monthly_invested_amount = dashboard_service.get_monthly_invested_amount(year)
        allocation = dashboard_service.get_portfolio_allocation()


