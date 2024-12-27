from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.services.payee_service import PayeeService


class PayeeDetailView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            request_params = {
                'id': kwargs.get('id', None),
                'name': kwargs.get('name', None)
            }
            payee_service = PayeeService()
            payee_details = payee_service.get_payee_details(request_params)
            if payee_details.get('payee'):
                return Response({'data': payee_details, 'status': True, 'message': 'Success'},
                                status=status.HTTP_200_OK)
            return Response({'data': payee_details, 'status': False, 'message': 'Error'},
                            status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PayeeView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            request_params = {
                'id': kwargs.get('id', None)
            }
            payee_service = PayeeService()
            payee_details = payee_service.get_payees(request_params)
            return Response({'data': payee_details, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            payee_service = PayeeService()
            is_updated, response = payee_service.update_payee(request.data.copy())
            if is_updated:
                return Response({'data': response, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
            return Response({'data': response, 'status': False, 'message': 'Failed to update payee'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
