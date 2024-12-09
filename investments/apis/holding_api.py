import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from investments.services.holding_service import HoldingService

logger = logging.getLogger(__name__)


class HoldingView(APIView):

    def get(self, request):
        service = HoldingService()
        return Response(service.get_current_holdings(), status=status.HTTP_200_OK)