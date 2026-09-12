import logging

from django.db import transaction

from finance.categories.models import TransactionCategory, TransactionSubCategory
from finance.categories.serializers import TransactionCategorySerializer, TransactionSubCategorySerializer, \
    ResponseTransactionCategorySerializer, ResponseTransactionSubCategorySerializer
from finance.payees.models import DestinationMap
from finance.transactions.models import Transaction


class CategoryService:

    def get_category_queryset(self, params):
        return TransactionCategory.objects.filter(**params)

    def get_subcategory_queryset(self, params):
        return TransactionSubCategory.objects.select_related('category').filter(**params)

    def get_transaction_queryset(self, params):
        return Transaction.objects.select_related('category', 'subcategory', 'account').filter(**params).only('id',
                                                                                                              'category_id',
                                                                                                              'subcategory_id')

    def get_payee_queryset(self, params):
        return DestinationMap.objects.select_related('category', 'subcategory').filter(**params)

    def update_category(self, request_data):
        category = request_data.get('category') if isinstance(request_data, dict) else request_data
        category_id = category.get('id') if isinstance(category, dict) else None
        existing_category = self.get_category_queryset({'id': category_id}).first()
        if not existing_category:
            return False, {'id': f'Category with id {category_id} not found.'}
        category_serializer = TransactionCategorySerializer(existing_category, data=category, partial=True)
        if category_serializer.is_valid():
            with transaction.atomic():
                saved_category = category_serializer.save()
            return True, category_serializer.data
        return False, category_serializer.errors

    def update_subcategories(self, subcategories, category_id=None):
        if not subcategories:
            return []

        existing_items = [obj for obj in subcategories if obj.get('id')]
        new_items = [obj for obj in subcategories if not obj.get('id')]
        processed_subcategories = []

        if existing_items:
            existing_ids = [obj['id'] for obj in existing_items]
            items_by_id = {obj['id']: obj for obj in existing_items}
            db_instances = list(self.get_subcategory_queryset({'id__in': existing_ids}))
            for instance in db_instances:
                data = items_by_id.get(instance.id)
                if data:
                    if 'name' in data:
                        instance.name = data['name']
                    if 'description' in data:
                        instance.description = data.get('description', '')
            if db_instances:
                TransactionSubCategory.objects.bulk_update(db_instances, ['name', 'description'])
                processed_subcategories.extend(db_instances)

        if new_items:
            for subcategory in new_items:
                if category_id and 'category' not in subcategory:
                    subcategory['category'] = category_id
                saved_item = self.create_subcategory(subcategory)
                if saved_item:
                    processed_subcategories.append(saved_item)

        return processed_subcategories

    def update_category_aggregate(self, request_data):
        """
        Updates a category, deletes requested subcategories, and updates/creates subcategories
        within a single atomic transaction.
        """
        data = request_data.copy() if hasattr(request_data, 'copy') else dict(request_data)
        category = data.get('category')
        subcategories = data.get('subcategories')
        deleted_subcategories = data.get('deleted_sub_categories')
        category_id = category.get('id') if isinstance(category, dict) else None

        with transaction.atomic():
            is_updated, updated_category = self.update_category(data)
            if not is_updated:
                return False, {'category': None, 'subcategories': None, 'errors': updated_category}

            if deleted_subcategories:
                self.delete_subcategories(deleted_subcategories)

            if subcategories:
                self.update_subcategories(subcategories, category_id=category_id)

            all_subcategories = self.get_all_subcategories(category_id)
            return True, {'category': updated_category, 'subcategories': all_subcategories}

    def delete_category(self, category_id):
        try:
            with transaction.atomic():
                self.get_transaction_queryset({'category_id': category_id}).update(category=None, subcategory=None)
                self.get_subcategory_queryset({'category_id': category_id}).delete()
                self.get_category_queryset({'id': category_id}).delete()
            return True
        except Exception as e:
            logging.exception(e)
            return False

    def delete_subcategories(self, subcategories):
        if not isinstance(subcategories, list):
            return False
        try:
            with transaction.atomic():
                deleted_sub_category_ids = [obj.get('id') for obj in subcategories]
                self.get_transaction_queryset({'subcategory_id__in': deleted_sub_category_ids}).update(subcategory=None)
                self.get_subcategory_queryset({'id__in': deleted_sub_category_ids}).delete()
            return True
        except Exception as e:
            logging.exception(e)
            return False

    def create_subcategory(self, new_subcategories):
        subcategory_serializer = TransactionSubCategorySerializer(data=new_subcategories)
        if subcategory_serializer.is_valid(raise_exception=True):
            saved_items = subcategory_serializer.save()
            return saved_items
        return False

    def create_category(self, request_data):
        category_data = request_data.get('category')
        subcategories = request_data.get('subcategories', []) or []
        serializer = TransactionCategorySerializer(data=category_data)
        processed_subcategories = []
        if serializer.is_valid(raise_exception=True):
            with transaction.atomic():
                saved_category = serializer.save()
                for subcategory in subcategories:
                    subcategory['category'] = saved_category.id
                    saved_subcategory = self.create_subcategory(subcategory)
                    if saved_subcategory:
                        processed_subcategories.append(saved_subcategory)

            transaction_category_serializer = ResponseTransactionCategorySerializer(saved_category)
            transaction_subcategories_serializer = ResponseTransactionSubCategorySerializer(processed_subcategories,
                                                                                            many=True)
            return transaction_category_serializer.data, transaction_subcategories_serializer.data
        return False, False


    def get_all_subcategories(self, category_id):
        subcategories = TransactionSubCategory.objects.filter(category__id=category_id)
        subcategories_serializer = ResponseTransactionSubCategorySerializer(subcategories, many=True)
        return subcategories_serializer.data
