from rest_framework import status
from rest_framework.views import APIView
from transactions.services.transaction_list_service import TransactionListService, TransactionBulkService
from rest_framework.response import Response


class TransactionView(APIView):

    def get(self, request, *args, **kwargs):
        query_params = request.query_params
        list_service = TransactionListService()
        transactions = list_service.get_transactions(query_params)
        return Response({'payload': transactions}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        update_similar = data.get('update_similar')
        list_service = TransactionListService()
        if update_similar:
            list_service.update_similar_transactions(data)
        created, response = list_service.create_transaction(data)
        if created:
            return Response(response, status=status.HTTP_201_CREATED)
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        data = request.data
        update_similar = data.get('update_similar')
        merge_ids = data.get('merge_ids')
        list_service = TransactionListService()
        if merge_ids:
            list_service.merge_transactions(data)
        if update_similar:
            list_service.update_similar_transactions(data)

        updated, response = list_service.update_transaction(data)
        if updated:
            return Response(response, status=status.HTTP_200_OK)
        return Response(response, status=status.HTTP_400_BAD_REQUEST)


class TransactionBulkView(APIView):
    def put(self, request):
        data = request.data
        task = data.get('task')
        bulk_service = TransactionBulkService()
        is_success = False
        response = None
        if task == 'delete':
            is_success, response = bulk_service.bulk_delete(data)
        elif task == 'split':
            is_success, response = bulk_service.split_transactions(data)

        if is_success:
            return Response(response, status=status.HTTP_200_OK)
        return Response(response, status=status.HTTP_400_BAD_REQUEST)
