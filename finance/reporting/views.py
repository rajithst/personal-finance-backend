from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.reporting.service.analytics_service import AnalyticsService


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


class AnalyticsPromptView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, **kwargs):
        try:
            data = request.data.copy()

            service = AnalyticsService()
            query = service.parse_prompt(data.copy())
            return Response({'data': query, 'status': True, 'message': 'Success'},
                            status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)