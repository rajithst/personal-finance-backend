import logging

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
        category = request_data.get('category')
        category_id = category.get('id')
        existing_category = self.get_category_queryset({'id': category_id}).first()
        category_serializer = TransactionCategorySerializer(existing_category, data=category, partial=True)
        if category_serializer.is_valid(raise_exception=True):
            saved_category = category_serializer.save()
            if saved_category:
                return True, category_serializer.data
        return False, category_serializer.errors

    def update_subcategories(self, subcategories):
        subcategory_ids = [obj.get('id') for obj in subcategories]
        queryset = self.get_subcategory_queryset({'id__in': subcategory_ids})
        new_subcategories = []
        processed_subcategories = []
        for item in subcategories:
            subcategory_id = item.get('id')
            if subcategory_id:
                instance = queryset.get(id=subcategory_id)
                instance.name = item.get('name')
                instance.description = item.get('description')
                instance.save()
                processed_subcategories.append(instance)
            else:
                new_subcategories.append(item)
        if new_subcategories:
            for subcategory in new_subcategories:
                saved_item = self.create_new_subcategory(subcategory)
                if saved_item:
                    processed_subcategories.append(saved_item)

        return processed_subcategories

    def delete_category(self, category_id):
        try:
            self.get_subcategory_queryset({'category_id': category_id}).delete()
            self.get_category_queryset({'id': category_id}).delete()
            self.get_transaction_queryset({'category_id': category_id}).update(category=None, subcategory=None)
            return True
        except Exception as e:
            logging.exception(e)
            return False

    def delete_subcategories(self, subcategories):
        if not isinstance(subcategories, list):
            return False
        try:
            deleted_sub_category_ids = [obj.get('id') for obj in subcategories]
            self.get_subcategory_queryset({'id__in': deleted_sub_category_ids}).delete()
            self.get_transaction_queryset({'subcategory_id__in': deleted_sub_category_ids}).update(subcategory=None)
            # set transactions subcategories null
            return True
        except Exception as e:
            logging.exception(e)
            return False

    def create_new_subcategory(self, new_subcategories):
        subcategory_serializer = TransactionSubCategorySerializer(data=new_subcategories)
        if subcategory_serializer.is_valid(raise_exception=True):
            saved_items = subcategory_serializer.save()
            return saved_items
        return False

    def create_category(self, request_data):
        category_data = request_data.get('category')
        subcategories = request_data.get('subcategories')
        serializer = TransactionCategorySerializer(data=category_data)
        processed_subcategories = []
        saved_category = None
        if serializer.is_valid(raise_exception=True):
            saved_category = serializer.save()
            for subcategory in subcategories:
                subcategory['category'] = saved_category.id
                saved_subcategory = self.create_new_subcategory(subcategory)
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
