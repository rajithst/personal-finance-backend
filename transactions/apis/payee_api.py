from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.services.payee_service import PayeeService


class PayeeDetailView(APIView):
    def get(self, request, *args, **kwargs):
        request_params = {
            'id': kwargs.get('id', None),
            'name': kwargs.get('name', None)
        }
        payee_service = PayeeService()
        payee_details = payee_service.get_payee_details(request_params)
        if payee_details.get('payee'):
            return Response(payee_details, status=status.HTTP_200_OK)
        return Response(payee_details, status=status.HTTP_404_NOT_FOUND)


class PayeeView(APIView):
    def get(self, request, *args, **kwargs):
        request_params = {
            'id': kwargs.get('id', None)
        }
        payee_service = PayeeService()
        payee_details = payee_service.get_payees(request_params)
        return Response({'payees': payee_details}, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        data = request.data
        payee_service = PayeeService()
        is_updated, response = payee_service.update_payee(data)
        if is_updated:
            return Response(response, status=status.HTTP_200_OK)
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
