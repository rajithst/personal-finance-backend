import logging

from transactions.models import TransactionCategory, TransactionSubCategory, Transaction, DestinationMap
from transactions.serializers.response_serializers import ResponseTransactionCategorySerializer, \
    ResponseTransactionSubCategorySerializer
from transactions.serializers.serializers import TransactionCategorySerializer, TransactionSubCategorySerializer


class CategoryService:

    def get_category_queryset(self, params):
        """
        Gets the category queryset with the provided parameters.

        Args:
            params (dict): The parameters to filter the queryset.

        Returns:
            QuerySet: The filtered category queryset.
        """
        return TransactionCategory.objects.filter(**params)

    def get_subcategory_queryset(self, params):
        """
        Gets the subcategory queryset with the provided parameters.

        Args:
            params (dict): The parameters to filter the queryset.

        Returns:
            QuerySet: The filtered subcategory queryset.
        """
        return TransactionSubCategory.objects.select_related('category').filter(**params)

    def get_transaction_queryset(self, params):
        """
        Gets the transaction queryset with the provided parameters.

        Args:
            params (dict): The parameters to filter the queryset.

        Returns:
            QuerySet: The filtered transaction queryset.
        """
        return Transaction.objects.select_related('category', 'subcategory', 'account').filter(**params).only('id',
                                                                                                              'category_id',
                                                                                                              'subcategory_id')

    def get_payee_queryset(self, params):
        """
        Gets the payee queryset with the provided parameters.

        Args:
            params (dict): The parameters to filter the queryset.

        Returns:
            QuerySet: The filtered payee queryset.
        """
        return DestinationMap.objects.select_related('category', 'subcategory').filter(**params)

    def update_category(self, request_data):
        """
        Updates the category with the provided request data.

        Args:
            request_data (dict): The data containing the category information to be updated.

        Returns:
            tuple: A tuple containing a boolean indicating success or failure, and the updated category data or errors.
        """
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
        """
        Updates the subcategories with the provided request data.

        Args:
            subcategories (list): The list of subcategories to be updated.

        Returns:
            list: The list of updated subcategories.
        """
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
        """
        Deletes the category with the provided category ID.

        Args:
            category_id (int): The ID of the category to be deleted.

        Returns:
            bool: A boolean indicating success or failure.
        """
        try:
            self.get_subcategory_queryset({'category_id': category_id}).delete()
            self.get_category_queryset({'id': category_id}).delete()
            self.get_transaction_queryset({'category_id': category_id}).update(category=None, subcategory=None)
            return True
        except Exception as e:
            logging.exception(e)
            return False

    def delete_subcategories(self, subcategories):
        """
        Deletes the subcategories with the provided subcategory IDs.

        Args:
            subcategories (list): The list of subcategories to be deleted.

        Returns:
            bool: A boolean indicating success or failure.
        """
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
        """
        Creates a new subcategory with the provided data.

        Args:
            new_subcategories (dict): The data containing the subcategory information to be created.

        Returns:
            dict: The created subcategory data.
        """
        subcategory_serializer = TransactionSubCategorySerializer(data=new_subcategories)
        if subcategory_serializer.is_valid(raise_exception=True):
            saved_items = subcategory_serializer.save()
            return saved_items
        return False

    def create_category(self, request_data):
        """
        Creates a new category with the provided data.

        Args:
            request_data (dict): The data containing the category information to be created.

        Returns:
            tuple: A tuple containing the created category data and the created subcategories data.
        """
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
        """
        Gets all subcategories for the provided category ID.

        Args:
            category_id (int): The ID of the category.

        Returns:
            list: The list of subcategories.
        """
        subcategories = TransactionSubCategory.objects.filter(category__id=category_id)
        subcategories_serializer = ResponseTransactionSubCategorySerializer(subcategories, many=True)
        return subcategories_serializer.data
