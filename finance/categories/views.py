from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.categories.service.category_service import CategoryService


class CategorySettingsView(APIView):
    def put(self, request):
        try:
            data = request.data.copy()
            category = data.get('category')
            subcategories = data.get('subcategories')
            deleted_subcategories = data.get('deleted_sub_categories')
            category_id = category.get('id')

            category_service = CategoryService()
            is_updated, updated_category = category_service.update_category(data)
            if deleted_subcategories:
                category_service.delete_subcategories(deleted_subcategories)
            if subcategories:
                category_service.update_subcategories(subcategories)
            all_subcategories = category_service.get_all_subcategories(category_id)

            if updated_category:
                return Response(
                    {'data': {'category': updated_category, 'subcategories': all_subcategories}, 'status': True,
                     'message': 'Success'}, status=status.HTTP_200_OK)
            return Response({'data': {'category': None, 'subcategories': None}, 'status': False, 'message': 'Error'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': {'category': None, 'subcategories': None}, 'status': False, 'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            category_id = pk
            category_service = CategoryService()
            deleted = category_service.delete_category(category_id)
            if deleted:
                return Response({'data': deleted, 'status': True, 'message': 'Success'}, status=status.HTTP_200_OK)
            return Response({'data': deleted, 'status': False, 'message': 'Error'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'data': None, 'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            data = request.data.copy()
            category_service = CategoryService()
            category, subcategories = category_service.create_category(data)
            if category:
                return Response({
                    'data': {'category': category, 'subcategories': subcategories},
                    'status': True,
                    'message': 'Success'
                }, status=status.HTTP_201_CREATED)
            return Response({
                'data': {'category': None, 'subcategories': None},
                'status': False,
                'message': 'Error'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'data': {'category': None, 'subcategories': None},
                'status': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
