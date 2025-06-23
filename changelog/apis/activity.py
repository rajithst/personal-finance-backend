from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from changelog.models import ChangeLog
from changelog.serializers.serializers import ChangeLogSerializer
from transactions.models import Transaction


class ActivityView(APIView):

    def get(self, request, *args, **kwargs):
        """
        Handle GET requests to retrieve activity data.
        """
        # Placeholder for actual implementation
        content_type = ContentType.objects.get_for_model(Transaction)
        queryset = (ChangeLog.objects
                    .select_related('user')
                    .filter(content_type=content_type, user_id=request.user.id)
                    .order_by('-timestamp'))
        serializer = ChangeLogSerializer(queryset, many=True)
        return Response({'data': serializer.data, 'message': 'Success', 'status': True}, status=status.HTTP_200_OK)
