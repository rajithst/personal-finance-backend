from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from finance.analytics.service.analytics_service import AnalyticsService


class AnalyticsView(APIView):

    def get(self, request):
        try:
            service = AnalyticsService()
            data = service.get_analytics(request.query_params)
            return Response(
                {'data': data, 'status': True, 'message': 'Success'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'data': None, 'status': False, 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuditReportsView(APIView):

    def get(self, request):
        try:
            service = AnalyticsService()
            data = service.get_audit_reports(request.query_params)
            return Response(
                {'data': data, 'status': True, 'message': 'Success'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'data': None, 'status': False, 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscriptionRadarView(APIView):

    def get(self, request):
        try:
            service = AnalyticsService()
            data = service.get_subscriptions_radar(request.query_params)
            return Response(
                {'data': data, 'status': True, 'message': 'Success'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'data': None, 'status': False, 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


