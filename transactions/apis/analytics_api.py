from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.services.analytics_service import AnalyticsService


class AnalyticsView(APIView):
    def get(self, request, **kwargs):
        try:
            service = AnalyticsService()
            analytics = service.get_analytics(request.query_params.copy())
            return Response({'data': analytics, 'status': True, 'message': 'Success'},
                            status=status.HTTP_200_OK)
        except:
            return Response({'data': None, 'status': True, 'message': 'Success'},
                            status=status.HTTP_400_BAD_REQUEST)