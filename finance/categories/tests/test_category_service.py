from unittest.mock import MagicMock, patch
from finance.categories.service.category_service import CategoryService


class TestCategoryService:
    @patch.object(CategoryService, "get_category_queryset")
    def test_update_category_not_found(self, mock_qs):
        mock_qs.return_value.first.return_value = None
        service = CategoryService()
        success, errors = service.update_category({'id': 999})
        assert success is False
        assert "not found" in errors['id']

    @patch("finance.categories.service.category_service.TransactionSubCategory.objects.bulk_update")
    @patch.object(CategoryService, "get_subcategory_queryset")
    @patch.object(CategoryService, "create_subcategory")
    def test_update_subcategories_bulk_and_create(self, mock_create_sub, mock_get_sub_qs, mock_bulk_update):
        # 1 existing subcategory, 1 new subcategory
        mock_instance = MagicMock()
        mock_instance.id = 10
        mock_instance.name = "Old Sub"
        mock_instance.description = "Old Desc"
        mock_get_sub_qs.return_value = [mock_instance]

        mock_new_instance = MagicMock()
        mock_new_instance.id = 11
        mock_create_sub.return_value = mock_new_instance

        subcategories_input = [
            {'id': 10, 'name': 'Updated Sub', 'description': 'Updated Desc'},
            {'name': 'New Sub', 'description': 'New Desc'},
        ]

        service = CategoryService()
        processed = service.update_subcategories(subcategories_input, category_id=5)

        # Verify bulk_update called for existing
        mock_bulk_update.assert_called_once_with([mock_instance], ['name', 'description'])
        assert mock_instance.name == 'Updated Sub'
        assert mock_instance.description == 'Updated Desc'

        # Verify create_subcategory called for new
        mock_create_sub.assert_called_once_with({'name': 'New Sub', 'description': 'New Desc', 'category': 5})
        assert len(processed) == 2

    @patch("finance.categories.service.category_service.transaction.atomic")
    @patch.object(CategoryService, "update_category")
    @patch.object(CategoryService, "delete_subcategories")
    @patch.object(CategoryService, "update_subcategories")
    @patch.object(CategoryService, "get_all_subcategories")
    def test_update_category_aggregate(self, mock_get_all, mock_update_sub, mock_del_sub, mock_update_cat, mock_atomic):
        mock_update_cat.return_value = (True, {'id': 1, 'name': 'Cat'})
        mock_get_all.return_value = [{'id': 10, 'name': 'Sub'}]

        payload = {
            'category': {'id': 1, 'name': 'Cat'},
            'subcategories': [{'id': 10, 'name': 'Sub'}],
            'deleted_sub_categories': [{'id': 99}],
        }

        service = CategoryService()
        success, result = service.update_category_aggregate(payload)

        assert success is True
        assert result['category'] == {'id': 1, 'name': 'Cat'}
        assert result['subcategories'] == [{'id': 10, 'name': 'Sub'}]
        mock_del_sub.assert_called_once_with([{'id': 99}])
        mock_update_sub.assert_called_once_with([{'id': 10, 'name': 'Sub'}], category_id=1)
