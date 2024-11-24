from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.company_service import CompanyService


class CompanyValueUpdaterView(APIView):

    def get(self, request):
        query_params = request.query_params
        tickers = query_params.get('tickers', None)
        if not tickers:
            raise ValueError('Company tickers not provided')
        tickers = tickers.split(',')
        request_data = {
            'tickers': tickers
        }
        service = CompanyService()
        is_success, response = service.get_company(request_data)
        if is_success:
            return Response(response, status=status.HTTP_200_OK)
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
