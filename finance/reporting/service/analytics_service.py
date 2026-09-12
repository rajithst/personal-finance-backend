import logging

from django.db.models import Sum

from finance.transactions.models import Transaction


class AnalyticsService:

    def get_queryset(self):
        return Transaction.objects.select_related('category', 'subcategory', 'account').filter(is_deleted=False)

    def get_analytics(self, request_params):
        start_date = request_params.get('start_date')
        end_date = request_params.get('end_date')
        transaction_type = int(request_params.get('target'))
        category = request_params.get('category', None)

        query_params = {}
        if start_date and end_date:
            query_params = {
                'date__lte': start_date,
                'date__gte': end_date
            }
        if transaction_type == 1:
            query_params['is_expense'] = True
        elif transaction_type == 2:
            query_params['is_income'] = True
        elif transaction_type == 3:
            query_params['is_saving'] = True
        elif transaction_type == 4:
            query_params['is_payment'] = True
        if category:
            query_params['category_id'] = int(category)

        queryset = (self.get_queryset().filter(**query_params)
                    .values('category_id', 'subcategory__id', 'category__category', 'subcategory__name')
                    .annotate(total_amount=Sum('amount'))
                    .order_by('total_amount')
                    )
        results = {}
        for item in queryset:
            category = item['category__category']
            if category is None:
                category = 'Uncategorized'
            category_object = {'total': item['total_amount'], 'category': category, 'category_id': item['category_id'],
                               'subcategory_id': item['subcategory__id'], 'subcategory': item['subcategory__name']}
            if not category in results:
                results[category] = {'total': 0, 'subcategories': []}
            results[category]['total'] = results[category]['total'] + category_object['total']
            results[category]['subcategories'].append(category_object)
        response = []
        for k, v in results.items():
            response.append({'category': k, 'total': v['total'], 'subcategories': v['subcategories']})
        return response
