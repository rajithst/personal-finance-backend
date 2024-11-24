from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from transactions.serializers.response_serializers import ResponseTransactionCategorySerializer, \
    ResponseTransactionSubCategorySerializer
from transactions.services.category_service import CategoryService


class CategorySettingsView(APIView):
    def put(self, request):
        data = request.data.copy()
        category = data.get('category')
        subcategories = data.get('subcategories')
        deleted_subcategories = data.get('deleted_sub_categories')
        delete_category = data.get('delete_category')
        category_id = category.get('id')

        category_service = CategoryService()
        updated_category = None
        if delete_category:
            deleted = category_service.delete_category(category_id)
            if deleted:
                return Response({'category': None, 'subcategories': []}, status=status.HTTP_200_OK)
            return Response({'category': None, 'subcategories': None}, status=status.HTTP_400_BAD_REQUEST)
        else:
            is_updated, updated_category = category_service.update_category(data)
            if deleted_subcategories:
                category_service.delete_subcategories(deleted_subcategories)
            if subcategories:
                category_service.update_subcategories(subcategories)
            all_subcategories = category_service.get_all_subcategories(category_id)

            if updated_category:
                return Response({'category': updated_category, 'subcategories': all_subcategories}, status=status.HTTP_200_OK)
            return Response({'category': None, 'subcategories': None}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        data = request.data.copy()
        category_service = CategoryService()
        category, subcategories = category_service.create_category(data)
        if category:
            return Response({'category': category, 'subcategories': subcategories}, status=status.HTTP_201_CREATED)
        return Response({'category': None, 'subcategories': None}, status=status.HTTP_400_BAD_REQUEST)
