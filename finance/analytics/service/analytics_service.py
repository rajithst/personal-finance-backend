import logging
import math
from datetime import datetime, date, timedelta
from collections import defaultdict
from django.db.models import Q, Sum, Count, Avg, Min, Max
from django.db.models.functions import (
    TruncMonth,
    TruncWeek,
    TruncDate,
    ExtractWeekDay,
    ExtractDay,
    ExtractYear,
    ExtractMonth,
)
from finance.transactions.models import Transaction
from finance.transactions.serializers import ResponseTransactionSerializer

logger = logging.getLogger(__name__)

DAY_NAMES = {
    1: 'Sun',
    2: 'Mon',
    3: 'Tue',
    4: 'Wed',
    5: 'Thu',
    6: 'Fri',
    7: 'Sat',
}

MONTH_NAMES = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
]


class AnalyticsService:

    def get_queryset(self):
        return Transaction.objects.filter(is_deleted=False)

    def parse_id_list(self, raw_val):
        if not raw_val:
            return []
        if isinstance(raw_val, list):
            return [int(x) for x in raw_val if str(x).isdigit()]
        if isinstance(raw_val, str):
            return [int(x.strip()) for x in raw_val.split(',') if x.strip().isdigit()]
        return []

    def get_analytics(self, params):
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        flow_type = params.get('flow_type', 'all')
        categories = self.parse_id_list(params.get('categories') or params.get('category_ids'))
        subcategories = self.parse_id_list(params.get('subcategories') or params.get('subcategory_ids'))
        accounts = self.parse_id_list(params.get('accounts') or params.get('account_ids'))
        min_amount = params.get('min_amount')
        max_amount = params.get('max_amount')
        search = params.get('search')
        interval = params.get('interval', 'month')

        # Base filtered queryset
        qs = self.get_queryset()

        if start_date:
            qs = qs.filter(date__gte=start_date)
        if end_date:
            qs = qs.filter(date__lte=end_date)
        if categories:
            qs = qs.filter(category_id__in=categories)
        if subcategories:
            qs = qs.filter(subcategory_id__in=subcategories)
        if accounts:
            qs = qs.filter(account_id__in=accounts)
        if min_amount is not None and str(min_amount).strip() != '':
            try:
                qs = qs.filter(amount__gte=float(min_amount))
            except ValueError:
                pass
        if max_amount is not None and str(max_amount).strip() != '':
            try:
                qs = qs.filter(amount__lte=float(max_amount))
            except ValueError:
                pass
        if search:
            clean_search = search.strip()
            qs = qs.filter(
                Q(destination__icontains=clean_search)
                | Q(destination_original__icontains=clean_search)
                | Q(notes__icontains=clean_search)
            )

        # Subset for categorical analysis based on flow_type
        if flow_type == 'expense':
            flow_qs = qs.filter(is_expense=True, is_saving=False)
        elif flow_type == 'income':
            flow_qs = qs.filter(is_income=True)
        elif flow_type == 'saving':
            flow_qs = qs.filter(is_saving=True)
        elif flow_type == 'payment':
            flow_qs = qs.filter(is_payment=True)
        else:
            flow_qs = qs.filter(is_expense=True, is_saving=False)

        # 1. Summary KPIs
        kpi_agg = qs.aggregate(
            total_income=Sum('amount', filter=Q(is_income=True)),
            total_expense=Sum('amount', filter=Q(is_expense=True, is_saving=False)),
            total_saving=Sum('amount', filter=Q(is_saving=True)),
            total_payment=Sum('amount', filter=Q(is_payment=True)),
            total_count=Count('id'),
            avg_amount=Avg('amount'),
            min_date=Min('date'),
            max_date=Max('date'),
        )

        total_income = float(kpi_agg['total_income'] or 0)
        total_expense = float(kpi_agg['total_expense'] or 0)
        total_saving = float(kpi_agg['total_saving'] or 0)
        total_payment = float(kpi_agg['total_payment'] or 0)
        total_count = kpi_agg['total_count'] or 0
        avg_amount = round(float(kpi_agg['avg_amount'] or 0), 2)
        net_savings = round(total_income - total_expense, 2)
        savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0

        days_count = 1
        if kpi_agg['min_date'] and kpi_agg['max_date']:
            days_count = max(1, (kpi_agg['max_date'] - kpi_agg['min_date']).days + 1)
        daily_burn = round(total_expense / days_count, 2)

        # Largest single expense in filtered range
        largest_expense_obj = (
            qs.filter(is_expense=True, is_saving=False)
            .order_by('-amount')
            .values('id', 'destination', 'amount', 'date')
            .first()
        )
        largest_expense = (
            {
                'id': largest_expense_obj['id'],
                'destination': largest_expense_obj['destination'] or 'Unknown',
                'amount': float(largest_expense_obj['amount']),
                'date': str(largest_expense_obj['date']),
            }
            if largest_expense_obj
            else None
        )

        kpis = {
            'total_income': total_income,
            'total_expense': total_expense,
            'total_saving': total_saving,
            'total_payment': total_payment,
            'net_savings': net_savings,
            'savings_rate': savings_rate,
            'total_count': total_count,
            'avg_amount': avg_amount,
            'daily_burn': daily_burn,
            'days_count': days_count,
            'largest_expense': largest_expense,
        }

        # 2. Time-Series Trajectory
        if interval == 'day':
            trunc_func = TruncDate('date')
            period_format = lambda d: d.strftime('%Y-%m-%d')
        elif interval == 'week':
            trunc_func = TruncWeek('date')
            period_format = lambda d: d.strftime('%Y-%m-%d')
        else:
            trunc_func = TruncMonth('date')
            period_format = lambda d: d.strftime('%Y-%m')

        ts_qs = (
            qs.annotate(period=trunc_func)
            .values('period')
            .annotate(
                income=Sum('amount', filter=Q(is_income=True)),
                expense=Sum('amount', filter=Q(is_expense=True, is_saving=False)),
                saving=Sum('amount', filter=Q(is_saving=True)),
                payment=Sum('amount', filter=Q(is_payment=True)),
                count=Count('id'),
            )
            .order_by('period')
        )

        time_series = []
        cumulative_savings = 0.0
        for item in ts_qs:
            p_date = item['period']
            if hasattr(p_date, 'strftime'):
                period_str = period_format(p_date)
            else:
                period_str = str(p_date)

            p_inc = float(item['income'] or 0)
            p_exp = float(item['expense'] or 0)
            p_sav = float(item['saving'] or 0)
            p_pay = float(item['payment'] or 0)
            p_net = round(p_inc - p_exp, 2)
            cumulative_savings = round(cumulative_savings + p_net, 2)

            time_series.append({
                'period': period_str,
                'income': p_inc,
                'expense': p_exp,
                'saving': p_sav,
                'payment': p_pay,
                'net': p_net,
                'cumulative_net': cumulative_savings,
                'count': item['count'],
            })

        # 3. Macro Category Breakdown
        cat_agg = (
            flow_qs.values('category__id', 'category__category')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )

        category_breakdown = []
        total_flow_amount = float(flow_qs.aggregate(t=Sum('amount'))['t'] or 0)
        for c in cat_agg:
            amt = float(c['total'] or 0)
            pct = round((amt / total_flow_amount * 100), 1) if total_flow_amount > 0 else 0.0
            category_breakdown.append({
                'category_id': c['category__id'],
                'category_name': c['category__category'] or 'Uncategorized',
                'amount': amt,
                'count': c['count'],
                'percentage': pct,
            })

        # 4. Micro Subcategory Breakdown
        sub_agg = (
            flow_qs.values(
                'category__id',
                'category__category',
                'subcategory__id',
                'subcategory__name',
            )
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )

        subcategory_breakdown = []
        for s in sub_agg:
            amt = float(s['total'] or 0)
            pct = round((amt / total_flow_amount * 100), 1) if total_flow_amount > 0 else 0.0
            subcategory_breakdown.append({
                'category_id': s['category__id'],
                'category_name': s['category__category'] or 'Uncategorized',
                'subcategory_id': s['subcategory__id'],
                'subcategory_name': s['subcategory__name'] or 'General',
                'amount': amt,
                'count': s['count'],
                'percentage': pct,
            })

        # 5. Day-of-Week Behavioral Distribution
        dow_raw = (
            flow_qs.annotate(dow=ExtractWeekDay('date'))
            .values('dow')
            .annotate(total=Sum('amount'), count=Count('id'), avg=Avg('amount'))
            .order_by('dow')
        )
        dow_dict = {d['dow']: d for d in dow_raw}

        # Order Monday (2) through Sunday (1)
        ordered_dow = [2, 3, 4, 5, 6, 7, 1]
        behavior_day_of_week = []
        weekday_total = 0.0
        weekday_count = 0
        weekend_total = 0.0
        weekend_count = 0

        for d in ordered_dow:
            record = dow_dict.get(d, {})
            tot = float(record.get('total') or 0)
            cnt = record.get('count') or 0
            avg_val = round(float(record.get('avg') or 0), 2)
            behavior_day_of_week.append({
                'day_num': d,
                'day_name': DAY_NAMES.get(d, str(d)),
                'amount': tot,
                'count': cnt,
                'avg': avg_val,
            })
            if d in (7, 1):  # Sat, Sun
                weekend_total += tot
                weekend_count += cnt
            else:  # Mon, Tue, Wed, Thu, Fri
                weekday_total += tot
                weekday_count += cnt

        weekday_daily_avg = round(weekday_total / 5.0, 2)
        weekend_daily_avg = round(weekend_total / 2.0, 2)
        total_behavior_amount = weekday_total + weekend_total

        weekday_share_pct = round((weekday_total / total_behavior_amount * 100), 1) if total_behavior_amount > 0 else 0.0
        weekend_share_pct = round((weekend_total / total_behavior_amount * 100), 1) if total_behavior_amount > 0 else 0.0

        impulse_ratio = round(weekend_daily_avg / weekday_daily_avg, 2) if weekday_daily_avg > 0 else (1.0 if weekend_daily_avg == 0 else 2.0)
        impulse_pct_diff = round(((weekend_daily_avg - weekday_daily_avg) / weekday_daily_avg * 100), 1) if weekday_daily_avg > 0 else 0.0

        weekday_vs_weekend = {
            'weekday_total': round(weekday_total, 2),
            'weekday_count': weekday_count,
            'weekday_daily_avg': weekday_daily_avg,
            'weekday_ticket_avg': round(weekday_total / weekday_count, 2) if weekday_count > 0 else 0.0,
            'weekday_share_pct': weekday_share_pct,
            'weekend_total': round(weekend_total, 2),
            'weekend_count': weekend_count,
            'weekend_daily_avg': weekend_daily_avg,
            'weekend_ticket_avg': round(weekend_total / weekend_count, 2) if weekend_count > 0 else 0.0,
            'weekend_share_pct': weekend_share_pct,
            'impulse_surge_ratio': impulse_ratio,
            'impulse_surge_pct': impulse_pct_diff,
        }

        # 6. Day-of-Month Velocity Curve (1 to 31)
        dom_raw = (
            flow_qs.annotate(dom=ExtractDay('date'))
            .values('dom')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('dom')
        )
        dom_dict = {d['dom']: d for d in dom_raw}

        behavior_day_of_month = []
        for day in range(1, 32):
            record = dom_dict.get(day, {})
            behavior_day_of_month.append({
                'day': day,
                'amount': float(record.get('total') or 0),
                'count': record.get('count') or 0,
            })

        # 7. Account & Payment Provider Distribution
        acc_raw = (
            qs.values(
                'account__id',
                'account__account_name',
                'account__provider',
                'account__account_type',
            )
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )
        total_acc_amount = float(qs.aggregate(t=Sum('amount'))['t'] or 0)

        account_breakdown = []
        for a in acc_raw:
            amt = float(a['total'] or 0)
            pct = round((amt / total_acc_amount * 100), 1) if total_acc_amount > 0 else 0.0
            account_breakdown.append({
                'account_id': a['account__id'],
                'account_name': a['account__account_name'] or 'Unknown Account',
                'provider': a['account__provider'] or 'Unknown',
                'account_type': a['account__account_type'] or 'BANK_ACCOUNT',
                'amount': amt,
                'count': a['count'],
                'percentage': pct,
            })

        # 8. Top Payees & Pareto Concentration
        payee_raw = (
            flow_qs.values('destination', 'category__category')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')[:15]
        )

        top_payees = []
        cum_amount = 0.0
        for p in payee_raw:
            amt = float(p['total'] or 0)
            cum_amount += amt
            pct = round((amt / total_flow_amount * 100), 1) if total_flow_amount > 0 else 0.0
            cum_pct = round((cum_amount / total_flow_amount * 100), 1) if total_flow_amount > 0 else 0.0
            top_payees.append({
                'destination': p['destination'] or 'Unknown Payee',
                'category_name': p['category__category'] or 'Uncategorized',
                'amount': amt,
                'count': p['count'],
                'percentage': pct,
                'cumulative_percentage': cum_pct,
            })

        # 9. Year-Over-Year Comparison (Overlay Jan-Dec across available years)
        yoy_raw = (
            flow_qs.annotate(year=ExtractYear('date'), month=ExtractMonth('date'))
            .values('year', 'month')
            .annotate(total=Sum('amount'))
            .order_by('month', 'year')
        )

        # Collect distinct years
        available_years = sorted(list({y['year'] for y in yoy_raw if y['year']}))
        current_year = date.today().year

        # Determine the latest month with available data per year
        latest_month_per_year = {}
        for yr in available_years:
            months_with_data = [y['month'] for y in yoy_raw if y['year'] == yr and y['total'] is not None]
            latest_month_per_year[yr] = max(months_with_data) if months_with_data else 0

        yoy_map = {}
        for y in yoy_raw:
            m = y['month']
            yr = y['year']
            if m not in yoy_map:
                yoy_map[m] = {}
            yoy_map[m][yr] = float(y['total'] or 0)

        yoy_comparison = []
        for m in range(1, 13):
            entry = {
                'month_num': m,
                'month_name': MONTH_NAMES[m - 1],
            }
            for yr in available_years:
                if yr >= current_year and m > latest_month_per_year.get(yr, 0):
                    entry[f'year_{yr}'] = None
                else:
                    entry[f'year_{yr}'] = yoy_map.get(m, {}).get(yr, 0.0)
            yoy_comparison.append(entry)

        # 10. Filtered Recent Transactions Sample
        recent_tx_qs = (
            qs.select_related('category', 'subcategory', 'account')
            .order_by('-date', '-id')[:60]
        )
        recent_transactions = ResponseTransactionSerializer(recent_tx_qs, many=True).data

        # 11. Spending Ticket Size Distribution & Outflow Magnitude Spectrum
        ticket_agg = flow_qs.aggregate(
            micro_cnt=Count('id', filter=Q(amount__lt=1500)),
            micro_sum=Sum('amount', filter=Q(amount__lt=1500)),
            routine_cnt=Count('id', filter=Q(amount__gte=1500, amount__lt=5000)),
            routine_sum=Sum('amount', filter=Q(amount__gte=1500, amount__lt=5000)),
            mid_cnt=Count('id', filter=Q(amount__gte=5000, amount__lt=20000)),
            mid_sum=Sum('amount', filter=Q(amount__gte=5000, amount__lt=20000)),
            major_cnt=Count('id', filter=Q(amount__gte=20000, amount__lt=50000)),
            major_sum=Sum('amount', filter=Q(amount__gte=20000, amount__lt=50000)),
            shock_cnt=Count('id', filter=Q(amount__gte=50000)),
            shock_sum=Sum('amount', filter=Q(amount__gte=50000)),
            tot_cnt=Count('id'),
            tot_sum=Sum('amount'),
            avg_amt=Avg('amount'),
        )
        tot_ticket_cnt = ticket_agg['tot_cnt'] or 0
        tot_ticket_sum = float(ticket_agg['tot_sum'] or 0)
        mean_ticket = round(float(ticket_agg['avg_amt'] or 0), 2)

        median_ticket = 0.0
        if tot_ticket_cnt > 0:
            median_idx = tot_ticket_cnt // 2
            median_obj = list(flow_qs.order_by('amount').values_list('amount', flat=True)[median_idx:median_idx+1])
            if median_obj:
                median_ticket = round(float(median_obj[0]), 2)
        skew_ratio = round(mean_ticket / median_ticket, 2) if median_ticket > 0 else 1.0

        def _calc_bracket(label, short_label, cnt, sm, min_amt, max_amt, color):
            c_val = cnt or 0
            s_val = float(sm or 0)
            c_pct = round((c_val / tot_ticket_cnt * 100), 1) if tot_ticket_cnt > 0 else 0.0
            s_pct = round((s_val / tot_ticket_sum * 100), 1) if tot_ticket_sum > 0 else 0.0
            return {
                'label': label,
                'short_label': short_label,
                'min_amount': min_amt,
                'max_amount': max_amt,
                'count': c_val,
                'count_percentage': c_pct,
                'total_amount': s_val,
                'amount_percentage': s_pct,
                'color': color,
            }

        ticket_brackets = [
            _calc_bracket('Micro Swipes (< ¥1,500)', 'Micro <1.5k', ticket_agg['micro_cnt'], ticket_agg['micro_sum'], 0, 1500, '#38bdf8'),
            _calc_bracket('Daily Routine (¥1,500 - ¥5,000)', 'Routine 1.5k-5k', ticket_agg['routine_cnt'], ticket_agg['routine_sum'], 1500, 5000, '#818cf8'),
            _calc_bracket('Mid Discretionary (¥5,000 - ¥20,000)', 'Mid 5k-20k', ticket_agg['mid_cnt'], ticket_agg['mid_sum'], 5000, 20000, '#c084fc'),
            _calc_bracket('Major Outflows (¥20,000 - ¥50,000)', 'Major 20k-50k', ticket_agg['major_cnt'], ticket_agg['major_sum'], 20000, 50000, '#f43f5e'),
            _calc_bracket('Capital Shocks (> ¥50,000)', 'Shock >50k', ticket_agg['shock_cnt'], ticket_agg['shock_sum'], 50000, None, '#fb7185'),
        ]

        ticket_size_distribution = {
            'brackets': ticket_brackets,
            'mean_ticket': mean_ticket,
            'median_ticket': median_ticket,
            'skew_ratio': skew_ratio,
            'total_expense_count': tot_ticket_cnt,
            'total_expense_amount': tot_ticket_sum,
        }

        # 12. Capital Allocation & 50/30/20 Engine (Needs vs Wants vs Savings)
        needs_q = (
            Q(category__category__in=['Housing', 'Utilities', 'Taxes', 'Healthcare', 'Insurance', 'Transportation'])
            | Q(category__category='Food', subcategory__name='Groceries')
        )
        wants_q = (
            Q(category__category__in=['Entertainment', 'Shopping', 'Clothing and Accessories', 'Personal Care', 'Miscellaneous'])
            | (Q(category__category='Food') & ~Q(subcategory__name='Groceries'))
        )

        alloc_agg = qs.aggregate(
            needs_sum=Sum('amount', filter=Q(is_expense=True, is_saving=False) & needs_q),
            needs_cnt=Count('id', filter=Q(is_expense=True, is_saving=False) & needs_q),
            wants_sum=Sum('amount', filter=Q(is_expense=True, is_saving=False) & wants_q),
            wants_cnt=Count('id', filter=Q(is_expense=True, is_saving=False) & wants_q),
            savings_sum=Sum('amount', filter=Q(is_saving=True)),
            savings_cnt=Count('id', filter=Q(is_saving=True)),
            other_exp_sum=Sum('amount', filter=Q(is_expense=True, is_saving=False) & ~needs_q & ~wants_q),
            other_exp_cnt=Count('id', filter=Q(is_expense=True, is_saving=False) & ~needs_q & ~wants_q),
            income_sum=Sum('amount', filter=Q(is_income=True)),
        )

        n_sum = float(alloc_agg['needs_sum'] or 0)
        w_sum = float(alloc_agg['wants_sum'] or 0)
        s_sum = float(alloc_agg['savings_sum'] or 0)
        o_sum = float(alloc_agg['other_exp_sum'] or 0)
        inc_sum = float(alloc_agg['income_sum'] or 0)

        deployed_capital = n_sum + w_sum + s_sum + o_sum
        base_alloc = inc_sum if inc_sum > 0 else deployed_capital
        base_alloc = max(base_alloc, 1.0)

        needs_pct = round(n_sum / base_alloc * 100, 1)
        wants_pct = round(w_sum / base_alloc * 100, 1)
        savings_pct = round(s_sum / base_alloc * 100, 1)
        other_pct = round(o_sum / base_alloc * 100, 1)

        tot_lifestyle_outflows = n_sum + w_sum + o_sum
        discretionary_burn_ratio = round((w_sum / tot_lifestyle_outflows * 100), 1) if tot_lifestyle_outflows > 0 else 0.0

        active_months_cnt = max(1, round(days_count / 30.4))
        baseline_survival_floor_monthly = round(n_sum / active_months_cnt, 2)

        needs_top = (
            qs.filter(Q(is_expense=True, is_saving=False) & needs_q)
            .values('category__category')
            .annotate(total=Sum('amount'))
            .order_by('-total')[:5]
        )
        needs_breakdown = [{'name': c['category__category'] or 'Other Needs', 'amount': float(c['total'] or 0)} for c in needs_top]

        wants_top = (
            qs.filter(Q(is_expense=True, is_saving=False) & wants_q)
            .values('category__category')
            .annotate(total=Sum('amount'))
            .order_by('-total')[:5]
        )
        wants_breakdown = [{'name': c['category__category'] or 'Other Wants', 'amount': float(c['total'] or 0)} for c in wants_top]

        capital_allocation = {
            'needs_amount': n_sum,
            'needs_percentage': needs_pct,
            'needs_count': alloc_agg['needs_cnt'] or 0,
            'wants_amount': w_sum,
            'wants_percentage': wants_pct,
            'wants_count': alloc_agg['wants_cnt'] or 0,
            'savings_amount': s_sum,
            'savings_percentage': savings_pct,
            'savings_count': alloc_agg['savings_cnt'] or 0,
            'other_amount': o_sum,
            'other_percentage': other_pct,
            'total_income': inc_sum,
            'total_deployed': deployed_capital,
            'discretionary_burn_ratio': discretionary_burn_ratio,
            'baseline_survival_floor_monthly': baseline_survival_floor_monthly,
            'benchmark': {'needs': 50, 'wants': 30, 'savings': 20},
            'needs_breakdown': needs_breakdown,
            'wants_breakdown': wants_breakdown,
        }

        # 13. Fixed Structural Commitments vs Variable Spending
        fixed_q = (
            Q(category__category__in=['Housing', 'Utilities', 'Insurance'])
            | Q(subcategory__name__in=['Car Payment', 'Auto Insurance', 'Subscriptions', 'Home Insurance'])
        )
        fixed_agg = flow_qs.aggregate(
            fixed_sum=Sum('amount', filter=fixed_q),
            fixed_cnt=Count('id', filter=fixed_q),
            var_sum=Sum('amount', filter=~fixed_q),
            var_cnt=Count('id', filter=~fixed_q),
        )
        fixed_amt = float(fixed_agg['fixed_sum'] or 0)
        var_amt = float(fixed_agg['var_sum'] or 0)
        tot_fv = fixed_amt + var_amt
        tot_fv_base = max(tot_fv, 1.0)

        fixed_pct = round(fixed_amt / tot_fv_base * 100, 1)
        var_pct = round(var_amt / tot_fv_base * 100, 1)
        flexibility_score = var_pct

        fixed_items_raw = (
            flow_qs.filter(fixed_q)
            .values('category__category', 'destination')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')[:6]
        )
        fixed_items = [
            {
                'name': f['destination'] or f['category__category'] or 'Fixed Commitment',
                'category': f['category__category'] or 'Inflexible',
                'amount': float(f['total'] or 0),
                'monthly_avg': round(float(f['total'] or 0) / active_months_cnt, 2),
            }
            for f in fixed_items_raw
        ]

        fixed_vs_variable = {
            'fixed_amount': fixed_amt,
            'fixed_percentage': fixed_pct,
            'fixed_count': fixed_agg['fixed_cnt'] or 0,
            'fixed_monthly_run_rate': round(fixed_amt / active_months_cnt, 2),
            'variable_amount': var_amt,
            'variable_percentage': var_pct,
            'variable_count': fixed_agg['var_cnt'] or 0,
            'variable_monthly_run_rate': round(var_amt / active_months_cnt, 2),
            'flexibility_score': flexibility_score,
            'fixed_items': fixed_items,
        }

        # 14. Cumulative Month Pacing & Daily Burn Trajectory (Day 1 - 31)
        total_monthly_spending_sum = sum(d['amount'] for d in behavior_day_of_month)
        cumulative_actual_burn = 0.0
        pacing_curve = []
        peak_day = 1
        peak_day_amount = 0.0

        for item in behavior_day_of_month:
            d_day = item['day']
            d_amt = item['amount']
            if d_amt > peak_day_amount:
                peak_day_amount = d_amt
                peak_day = d_day

            cumulative_actual_burn += d_amt
            linear_benchmark = round((total_monthly_spending_sum / 31.0) * d_day, 2)
            pace_variance = round(cumulative_actual_burn - linear_benchmark, 2)
            is_payday_zone = (25 <= d_day <= 28)

            pacing_curve.append({
                'day': d_day,
                'daily_amount': round(d_amt, 2),
                'cumulative_actual': round(cumulative_actual_burn, 2),
                'cumulative_linear': linear_benchmark,
                'pace_variance': pace_variance,
                'is_payday_zone': is_payday_zone,
            })

        cumulative_month_pacing = {
            'days': pacing_curve,
            'total_monthly_average': round(total_monthly_spending_sum, 2),
            'peak_burn_day': peak_day,
            'peak_burn_amount': round(peak_day_amount, 2),
            'payday_surge_pct': round(
                sum(d['daily_amount'] for d in pacing_curve if d['is_payday_zone']) / max(total_monthly_spending_sum, 1.0) * 100, 1
            ),
        }

        return {
            'kpis': kpis,
            'time_series': time_series,
            'category_breakdown': category_breakdown,
            'subcategory_breakdown': subcategory_breakdown,
            'behavior_day_of_week': behavior_day_of_week,
            'behavior_day_of_month': behavior_day_of_month,
            'account_breakdown': account_breakdown,
            'top_payees': top_payees,
            'yoy_comparison': yoy_comparison,
            'yoy_years': available_years,
            'recent_transactions': recent_transactions,
            'ticket_size_distribution': ticket_size_distribution,
            'capital_allocation': capital_allocation,
            'fixed_vs_variable': fixed_vs_variable,
            'cumulative_month_pacing': cumulative_month_pacing,
            'weekday_vs_weekend': weekday_vs_weekend,
            'filter_echo': {
                'start_date': start_date,
                'end_date': end_date,
                'flow_type': flow_type,
                'interval': interval,
                'categories': categories,
                'subcategories': subcategories,
                'accounts': accounts,
                'min_amount': min_amount,
                'max_amount': max_amount,
                'search': search,
            },
        }

    def get_audit_reports(self, params=None):
        params = params or {}
        year_param = params.get('year') if hasattr(params, 'get') else None
        qs_base = self.get_queryset()

        available_years = sorted(
            [y for y in qs_base.annotate(yr=ExtractYear('date')).values_list('yr', flat=True).distinct() if y is not None],
            reverse=True
        )

        try:
            selected_year = int(year_param) if year_param else (available_years[0] if available_years else datetime.now().year)
        except (ValueError, TypeError):
            selected_year = available_years[0] if available_years else datetime.now().year

        # Helper to compute macro metrics for a queryset
        cc_card_debit_q = (
            Q(subcategory__name__icontains='Credit Card')
            | Q(destination__icontains='Card Payment')
            | Q(destination__icontains='TOKYU')
        )

        def _calc_macro(qs):
            inc = float(qs.filter(is_income=True).aggregate(s=Sum('amount'))['s'] or 0)
            exp = float(qs.filter(is_expense=True, is_saving=False).aggregate(s=Sum('amount'))['s'] or 0)
            sur = round(inc - exp, 2)
            bank_deb = float(qs.filter(account__account_type='BANK_ACCOUNT', is_payment=True).aggregate(s=Sum('amount'))['s'] or 0)
            sec = float(qs.filter(is_saving=True).aggregate(s=Sum('amount'))['s'] or 0)
            tot_outflow = round(bank_deb + sec, 2)
            sav_rate = round((sur / inc * 100), 1) if inc > 0 else 0.0
            miz_in = float(qs.filter(account__account_type='BANK_ACCOUNT', is_income=True).aggregate(s=Sum('amount'))['s'] or 0)
            net_bank = round(miz_in - tot_outflow, 2)
            cc_spend = float(qs.filter(account__account_type='CREDIT_CARD', is_expense=True, is_saving=False).aggregate(s=Sum('amount'))['s'] or 0)
            cc_bills = float(qs.filter(account__account_type='BANK_ACCOUNT', is_payment=True).filter(cc_card_debit_q).aggregate(s=Sum('amount'))['s'] or 0)
            atm = float(qs.filter(account__account_type='BANK_ACCOUNT', is_payment=True, destination__icontains='ATM').aggregate(s=Sum('amount'))['s'] or 0)
            return {
                'income': inc,
                'exp': exp,
                'sur': sur,
                'bank_deb': bank_deb,
                'sec': sec,
                'tot_outflow': tot_outflow,
                'sav_rate': sav_rate,
                'net_bank': net_bank,
                'cc_spend': cc_spend,
                'cc_bills': cc_bills,
                'atm': atm,
            }

        # 1. Macro Comparison: 2025 vs 2026
        m25 = _calc_macro(qs_base.filter(date__year=2025))
        m26 = _calc_macro(qs_base.filter(date__year=2026))

        metric_defs = [
            ('Gross Income', 'income', 'Salary, bonuses, and deposits into Mizuho Bank', False),
            ('Living Expenses', 'exp', 'True living cost (CC purchases + Rent, Car Loan, etc.)', False),
            ('Operational Surplus', 'sur', 'Gross Income − Living Expenses (Net Savings)', False),
            ('Bank Debit Payments', 'bank_deb', 'Total cash and debits exiting Mizuho', False),
            ('Securities / Savings', 'sec', 'Transfers to SBI / Rakuten Securities', False),
            ('Total Bank Outflow', 'tot_outflow', 'Total cash exiting Mizuho (Debits + Securities)', False),
            ('Savings Rate (%)', 'sav_rate', 'Operational Surplus ÷ Gross Income', True),
            ('Net Bank Movement', 'net_bank', 'Mizuho Inflow − Total Bank Outflow', False),
            ('Credit Card Spending', 'cc_spend', 'Total purchases charged to credit cards', False),
            ('Credit Card Bills Paid', 'cc_bills', 'Total Mizuho debits paying card statements', False),
            ('ATM Cash Withdrawals', 'atm', 'Physical cash withdrawn from Mizuho ATM', False),
        ]

        macro_comparison = []
        for label, key, desc, is_rate in metric_defs:
            v25 = m25[key]
            v26 = m26[key]
            diff = round(v26 - v25, 2)
            pct = round((diff / v25 * 100), 1) if v25 != 0 else None
            macro_comparison.append({
                'label': label,
                'key': key,
                'description': desc,
                'is_rate': is_rate,
                'year_2025': v25,
                'year_2026': v26,
                'diff': diff,
                'diff_pct': pct,
            })

        # 2. Monthly Breakdown for selected_year
        MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        qs_year = qs_base.filter(date__year=selected_year)
        active_months = sorted(list(qs_year.annotate(m=ExtractMonth('date')).values_list('m', flat=True).distinct()))
        active_months_count = max(len(active_months), 1)

        monthly_breakdown = []
        for m in active_months:
            mqs = qs_year.filter(date__month=m)
            m_inc = float(mqs.filter(is_income=True).aggregate(s=Sum('amount'))['s'] or 0)
            m_exp = float(mqs.filter(is_expense=True, is_saving=False).aggregate(s=Sum('amount'))['s'] or 0)
            m_sur = round(m_inc - m_exp, 2)
            m_bank_deb = float(mqs.filter(account__account_type='BANK_ACCOUNT', is_payment=True).aggregate(s=Sum('amount'))['s'] or 0)
            m_sec = float(mqs.filter(is_saving=True).aggregate(s=Sum('amount'))['s'] or 0)
            m_tot_outflow = round(m_bank_deb + m_sec, 2)
            m_miz_in = float(mqs.filter(account__account_type='BANK_ACCOUNT', is_income=True).aggregate(s=Sum('amount'))['s'] or 0)
            m_net_bank = round(m_miz_in - m_tot_outflow, 2)
            m_cc_spend = float(mqs.filter(account__account_type='CREDIT_CARD', is_expense=True, is_saving=False).aggregate(s=Sum('amount'))['s'] or 0)
            m_cc_bills = float(mqs.filter(account__account_type='BANK_ACCOUNT', is_payment=True).filter(cc_card_debit_q).aggregate(s=Sum('amount'))['s'] or 0)
            m_atm = float(mqs.filter(account__account_type='BANK_ACCOUNT', is_payment=True, destination__icontains='ATM').aggregate(s=Sum('amount'))['s'] or 0)

            monthly_breakdown.append({
                'month_num': m,
                'month_key': f'{selected_year}-{m:02d}',
                'month_name': f'{MONTH_NAMES[m-1]} {selected_year}',
                'gross_income': m_inc,
                'living_expenses': m_exp,
                'operational_surplus': m_sur,
                'bank_debits': m_bank_deb,
                'securities_savings': m_sec,
                'total_mizuho_outflow': m_tot_outflow,
                'net_bank_movement': m_net_bank,
                'cc_spending': m_cc_spend,
                'cc_bills_paid': m_cc_bills,
                'atm_withdrawals': m_atm,
            })

        # Summary total & avg
        y_macro = _calc_macro(qs_year)
        monthly_summary = {
            'total': {
                'gross_income': y_macro['income'],
                'living_expenses': y_macro['exp'],
                'operational_surplus': y_macro['sur'],
                'bank_debits': y_macro['bank_deb'],
                'securities_savings': y_macro['sec'],
                'total_mizuho_outflow': y_macro['tot_outflow'],
                'net_bank_movement': y_macro['net_bank'],
                'cc_spending': y_macro['cc_spend'],
                'cc_bills_paid': y_macro['cc_bills'],
                'atm_withdrawals': y_macro['atm'],
            },
            'monthly_avg': {
                'gross_income': round(y_macro['income'] / active_months_count, 2),
                'living_expenses': round(y_macro['exp'] / active_months_count, 2),
                'operational_surplus': round(y_macro['sur'] / active_months_count, 2),
                'bank_debits': round(y_macro['bank_deb'] / active_months_count, 2),
                'securities_savings': round(y_macro['sec'] / active_months_count, 2),
                'total_mizuho_outflow': round(y_macro['tot_outflow'] / active_months_count, 2),
                'net_bank_movement': round(y_macro['net_bank'] / active_months_count, 2),
                'cc_spending': round(y_macro['cc_spend'] / active_months_count, 2),
                'cc_bills_paid': round(y_macro['cc_bills'] / active_months_count, 2),
                'atm_withdrawals': round(y_macro['atm'] / active_months_count, 2),
            },
            'active_months_count': active_months_count,
        }

        # 3. Bank Debit Payments
        bank_qs = qs_year.filter(account__account_type='BANK_ACCOUNT', is_payment=True)
        tot_bank_debits = y_macro['bank_deb']
        payee_agg = (
            bank_qs.values('destination', 'category__category', 'subcategory__name')
            .annotate(count=Count('id'), total_amount=Sum('amount'))
            .order_by('-total_amount')
        )
        bank_debit_payments = []
        for p in payee_agg:
            amt = float(p['total_amount'] or 0)
            pct = round((amt / tot_bank_debits * 100), 1) if tot_bank_debits > 0 else 0.0
            bank_debit_payments.append({
                'destination': p['destination'] or 'Unknown Destination',
                'category_name': p['category__category'] or 'Uncategorized',
                'subcategory_name': p['subcategory__name'] or 'General',
                'count': p['count'],
                'total_amount': amt,
                'percentage': pct,
                'monthly_avg': round(amt / active_months_count, 2),
            })

        # 4. Living Expenses by Category
        exp_qs = qs_year.filter(is_expense=True, is_saving=False)
        tot_exp = y_macro['exp']
        cat_agg = (
            exp_qs.values('category__id', 'category__category')
            .annotate(count=Count('id'), total_amount=Sum('amount'))
            .order_by('-total_amount')
        )
        living_expenses_by_category = []
        for c in cat_agg:
            amt = float(c['total_amount'] or 0)
            pct = round((amt / tot_exp * 100), 1) if tot_exp > 0 else 0.0
            cat_id = c['category__id']
            sub_agg = (
                exp_qs.filter(category_id=cat_id)
                .values('subcategory__id', 'subcategory__name')
                .annotate(count=Count('id'), total_amount=Sum('amount'))
                .order_by('-total_amount')
            )
            subs = []
            for s in sub_agg:
                s_amt = float(s['total_amount'] or 0)
                s_pct = round((s_amt / amt * 100), 1) if amt > 0 else 0.0
                subs.append({
                    'subcategory_id': s['subcategory__id'],
                    'subcategory_name': s['subcategory__name'] or 'General',
                    'count': s['count'],
                    'total_amount': s_amt,
                    'percentage': s_pct,
                })
            living_expenses_by_category.append({
                'category_id': cat_id,
                'category_name': c['category__category'] or 'Uncategorized',
                'count': c['count'],
                'total_amount': amt,
                'percentage': pct,
                'monthly_avg': round(amt / active_months_count, 2),
                'subcategories': subs,
            })

        # 5. Cash Reconciliation Bridge (Surplus vs Actual Bank Delta)
        theor_cash_retained = round(y_macro['sur'] - y_macro['sec'], 2)
        actual_bank_net_change = y_macro['net_bank']
        reconciliation_gap = round(theor_cash_retained - actual_bank_net_change, 2)

        tracked_cards = ['Rakuten Card Payment', 'EPOS Card Payment']
        bank_non_exp_qs = qs_year.filter(
            account__account_type='BANK_ACCOUNT',
            is_payment=True,
            is_expense=False
        ).exclude(destination__in=tracked_cards)

        atm_q = Q(destination__icontains='ATM') | Q(destination_original__icontains='ATM') | Q(destination_original__startswith='７ＢＫ')
        atm_total = float(bank_non_exp_qs.filter(atm_q).aggregate(s=Sum('amount'))['s'] or 0)

        # Dynamically resolve all non-expense bank payees from the database
        other_payees = (
            bank_non_exp_qs.exclude(atm_q)
            .values('destination')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )

        items = []
        if atm_total > 0:
            items.append({
                'category': 'ATM Cash Withdrawals',
                'amount': atm_total,
                'percentage_of_gap': round((atm_total / reconciliation_gap * 100), 1) if reconciliation_gap > 0 else 0.0,
                'description': 'Physical cash withdrawn from Mizuho ATMs; spent directly outside tracked credit card statements.',
                'source': 'Mizuho Bank Cash Debits',
                'type': 'atm',
            })

        for p in other_payees:
            p_name = p['destination'] or 'Direct Bank Transfer'
            p_amt = float(p['total'] or 0)
            p_pct = round((p_amt / reconciliation_gap * 100), 1) if reconciliation_gap > 0 else 0.0

            if any(w in p_name.lower() for w in ['card', 'カ−ド', 'カード']):
                desc = f'Monthly bank debit for {p_name}; individual statement purchases were not imported.'
                src = 'Unimported Card Debit'
                item_type = 'card'
            else:
                desc = f'Direct wire transfer from Mizuho Bank for {p_name}.'
                src = 'Mizuho Wire Transfer'
                item_type = 'transfer'

            items.append({
                'category': p_name,
                'amount': p_amt,
                'percentage_of_gap': p_pct,
                'description': desc,
                'source': src,
                'type': item_type,
            })

        cc_paid_mizuho = float(qs_year.filter(account__account_type='BANK_ACCOUNT', destination__in=tracked_cards).aggregate(s=Sum('amount'))['s'] or 0)
        cc_spend_cards = y_macro['cc_spend']
        cc_timing_lag = round(cc_paid_mizuho - cc_spend_cards, 2)

        if abs(cc_timing_lag) > 0.01:
            items.append({
                'category': 'Credit Card Timing Lag (27th Settlement vs Statement Date)',
                'amount': cc_timing_lag,
                'percentage_of_gap': round((cc_timing_lag / reconciliation_gap * 100), 1) if reconciliation_gap > 0 else 0.0,
                'description': 'Net carryover difference: 27th bank debits paying late previous-cycle bills vs current in-flight spend.',
                'source': 'Settlement Timing Carryover',
                'type': 'timing',
            })

        sum_explained = round(sum(i['amount'] for i in items), 2)
        unexplained_discrepancy = round(reconciliation_gap - sum_explained, 2)

        cash_reconciliation = {
            'operational_surplus': y_macro['sur'],
            'securities_invested': y_macro['sec'],
            'theoretical_cash_retained': theor_cash_retained,
            'actual_bank_net_change': actual_bank_net_change,
            'reconciliation_gap': reconciliation_gap,
            'sum_explained': sum_explained,
            'unexplained_discrepancy': unexplained_discrepancy,
            'items': items,
        }

        # 6. Credit Card 27th Settlement & 28th Cutoff Cycle Audit
        import datetime as dt_module
        card_billing_audit = []
        tot_cal_spend = 0
        tot_early_spend = 0
        tot_late_spend = 0
        tot_prev_late_spend = 0
        tot_cycle_spend = 0
        tot_bank_paid = 0

        for m in active_months:
            cal_start = dt_module.date(selected_year, m, 1)
            cal_end = dt_module.date(selected_year, m + 1, 1) - dt_module.timedelta(days=1) if m < 12 else dt_module.date(selected_year, 12, 31)
            early_end = dt_module.date(selected_year, m, 27)
            late_start = dt_module.date(selected_year, m, 28)

            if m == 1:
                prev_late_start = dt_module.date(selected_year - 1, 12, 28)
                prev_late_end = dt_module.date(selected_year - 1, 12, 31)
            else:
                prev_late_start = dt_module.date(selected_year, m - 1, 28)
                prev_late_end = cal_start - dt_module.timedelta(days=1)

            cards_q = Q(account__account_type='CREDIT_CARD', is_expense=True, is_saving=False)
            
            cal_s = float(qs_base.filter(cards_q, date__range=(cal_start, cal_end)).aggregate(s=Sum('amount'))['s'] or 0)
            early_s = float(qs_base.filter(cards_q, date__range=(cal_start, early_end)).aggregate(s=Sum('amount'))['s'] or 0)
            late_s = float(qs_base.filter(cards_q, date__range=(late_start, cal_end)).aggregate(s=Sum('amount'))['s'] or 0)
            prev_late_s = float(qs_base.filter(cards_q, date__range=(prev_late_start, prev_late_end)).aggregate(s=Sum('amount'))['s'] or 0)
            cycle_s = round(prev_late_s + early_s, 2)

            # Bank debits for credit cards in month m
            paid_s = float(qs_year.filter(
                account__account_type='BANK_ACCOUNT',
                destination__in=['Rakuten Card Payment', 'EPOS Card Payment'],
                date__month=m
            ).aggregate(s=Sum('amount'))['s'] or 0)

            # Individual card breakdown
            rakuten_cal = float(qs_base.filter(account_id=2, is_deleted=False, date__range=(cal_start, cal_end)).aggregate(s=Sum('amount'))['s'] or 0)
            rakuten_paid = float(qs_year.filter(account_id=1, destination='Rakuten Card Payment', date__month=m).aggregate(s=Sum('amount'))['s'] or 0)

            epos_cal = float(qs_base.filter(account_id=3, is_deleted=False, date__range=(cal_start, cal_end)).aggregate(s=Sum('amount'))['s'] or 0)
            epos_paid = float(qs_year.filter(account_id=1, destination='EPOS Card Payment', date__month=m).aggregate(s=Sum('amount'))['s'] or 0)

            timing_diff = round(paid_s - cal_s, 2)

            card_billing_audit.append({
                'month_num': m,
                'month_key': f'{selected_year}-{m:02d}',
                'month_name': f'{MONTH_NAMES[m-1]} {selected_year}',
                'cal_spend': cal_s,
                'early_spend': early_s,
                'late_spend': late_s,
                'prev_late_spend': prev_late_s,
                'cycle_spend': cycle_s,
                'bank_paid': paid_s,
                'timing_lag': timing_diff,
                'rakuten_spend': rakuten_cal,
                'rakuten_paid': rakuten_paid,
                'epos_spend': epos_cal,
                'epos_paid': epos_paid,
            })

            tot_cal_spend += cal_s
            tot_early_spend += early_s
            tot_late_spend += late_s
            tot_prev_late_spend += prev_late_s
            tot_cycle_spend += cycle_s
            tot_bank_paid += paid_s

        card_billing_summary = {
            'total_cal_spend': round(tot_cal_spend, 2),
            'total_early_spend': round(tot_early_spend, 2),
            'total_late_spend': round(tot_late_spend, 2),
            'total_prev_late_spend': round(tot_prev_late_spend, 2),
            'total_cycle_spend': round(tot_cycle_spend, 2),
            'total_bank_paid': round(tot_bank_paid, 2),
            'total_timing_lag': round(tot_bank_paid - tot_cal_spend, 2),
        }

        # 7. Month-by-Month Cash Flow Gap Decomposition
        card_debit_q = Q(destination__icontains='card') | Q(destination_original__icontains='カ−ド') | Q(destination_original__icontains='カード') | Q(destination_original__icontains='デビット')
        card_names_list = sorted(list(set(
            bank_non_exp_qs.filter(card_debit_q)
            .values_list('destination', flat=True)
        )))
        unimported_card_label = ', '.join(card_names_list) if card_names_list else 'Unimported Card Debits'

        monthly_reconciliation = []
        for m in active_months:
            mqs = qs_year.filter(date__month=m)
            m_inc = float(mqs.filter(account__account_type='BANK_ACCOUNT', is_income=True).aggregate(s=Sum('amount'))['s'] or 0)
            m_deb = float(mqs.filter(account__account_type='BANK_ACCOUNT', is_payment=True).aggregate(s=Sum('amount'))['s'] or 0)
            m_sec = float(mqs.filter(is_saving=True).aggregate(s=Sum('amount'))['s'] or 0)
            m_out = round(m_deb + m_sec, 2)
            m_actual_delta = round(m_inc - m_out, 2)

            m_exp = float(mqs.filter(is_expense=True, is_saving=False).aggregate(s=Sum('amount'))['s'] or 0)
            m_sur = round(m_inc - m_exp, 2)
            m_theor_delta = round(m_sur - m_sec, 2)
            m_gap = round(m_theor_delta - m_actual_delta, 2)

            m_bank_non_exp = mqs.filter(
                account__account_type='BANK_ACCOUNT',
                is_payment=True,
                is_expense=False
            ).exclude(destination__in=tracked_cards)
            m_atm = float(m_bank_non_exp.filter(atm_q).aggregate(s=Sum('amount'))['s'] or 0)
            m_cards = float(m_bank_non_exp.filter(card_debit_q).aggregate(s=Sum('amount'))['s'] or 0)
            m_other_trans = float(m_bank_non_exp.exclude(atm_q).exclude(card_debit_q).aggregate(s=Sum('amount'))['s'] or 0)

            m_cc_paid = float(mqs.filter(account__account_type='BANK_ACCOUNT', destination__in=tracked_cards).aggregate(s=Sum('amount'))['s'] or 0)
            m_cc_spend = float(mqs.filter(account__account_type='CREDIT_CARD', is_expense=True, is_saving=False).aggregate(s=Sum('amount'))['s'] or 0)
            m_cc_timing = round(m_cc_paid - m_cc_spend, 2)

            m_explained = round(m_atm + m_cards + m_other_trans + m_cc_timing, 2)
            m_discrepancy = round(m_gap - m_explained, 2)

            monthly_reconciliation.append({
                'month_num': m,
                'month_key': f'{selected_year}-{m:02d}',
                'month_name': f'{MONTH_NAMES[m-1]} {selected_year}',
                'mizuho_inflow': m_inc,
                'mizuho_outflow': m_out,
                'actual_bank_delta': m_actual_delta,
                'living_expenses': m_exp,
                'operational_surplus': m_sur,
                'theoretical_bank_delta': m_theor_delta,
                'monthly_gap': m_gap,
                'atm_cash': m_atm,
                'tokyu_card': m_cards,
                'unimported_cards': m_cards,
                'direct_transfers': m_other_trans,
                'cc_timing_lag': m_cc_timing,
                'discrepancy': m_discrepancy,
            })

        return {
            'available_years': available_years,
            'selected_year': selected_year,
            'macro_comparison': macro_comparison,
            'monthly_breakdown': monthly_breakdown,
            'monthly_summary': monthly_summary,
            'bank_debit_payments': bank_debit_payments,
            'living_expenses_by_category': living_expenses_by_category,
            'cash_reconciliation': cash_reconciliation,
            'card_billing_audit': card_billing_audit,
            'card_billing_summary': card_billing_summary,
            'monthly_reconciliation': monthly_reconciliation,
            'unimported_card_label': unimported_card_label,
        }

    def get_subscriptions_radar(self, query_params=None):
        """
        Detects recurring contracts, subscriptions, utility bills, and cadences.
        Identifies price hikes, tracks monthly & annualized burn rates, and forecasts upcoming renewals.
        """
        if query_params is None:
            query_params = {}

        status_filter = query_params.get('status', 'all')
        sub_type_filter = query_params.get('sub_type', 'all')
        cadence_filter = query_params.get('cadence', 'all')
        search_query = (query_params.get('search', '') or '').strip().lower()
        include_habits = query_params.get('include_habits', 'false').lower() in ('true', '1')

        # Genuine expense outflows (exclude credit card statement bill settlements & internal transfers)
        txs = (
            Transaction.objects.filter(is_deleted=False, is_expense=True)
            .exclude(destination__icontains='card payment')
            .select_related('category', 'subcategory', 'account')
            .order_by('destination', 'date')
        )

        payee_groups = defaultdict(list)
        for t in txs:
            name = (t.destination or t.destination_original or '').strip()
            if name:
                payee_groups[name].append({
                    'id': t.id,
                    'date': t.date,
                    'amount': float(t.amount),
                    'category': t.category.category if t.category else 'Uncategorized',
                    'subcategory': t.subcategory.name if t.subcategory else '',
                    'account': t.account.account_name if t.account else 'Default Account',
                    'original': t.destination_original or '',
                    'alias': t.alias or '',
                })

        today = date.today()
        max_db_date = txs.aggregate(m=Max('date'))['m']
        ref_date = max(today, max_db_date) if max_db_date else today

        all_detected = []

        for name, items in payee_groups.items():
            if len(items) < 2:
                continue

            items.sort(key=lambda x: x['date'])
            dates = [x['date'] for x in items]
            amounts = [x['amount'] for x in items]

            intervals = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
            if not intervals:
                continue

            avg_interval = sum(intervals) / len(intervals)

            # Determine cadence
            cadence = None
            cadence_days = 30
            cadence_label = 'Monthly'

            if 5 <= avg_interval <= 9:
                cadence = 'weekly'
                cadence_days = 7
                cadence_label = 'Weekly'
            elif 12 <= avg_interval <= 17:
                cadence = 'biweekly'
                cadence_days = 14
                cadence_label = 'Bi-Weekly'
            elif 22 <= avg_interval <= 38:
                cadence = 'monthly'
                cadence_days = 30
                cadence_label = 'Monthly'
            elif 75 <= avg_interval <= 110:
                cadence = 'quarterly'
                cadence_days = 90
                cadence_label = 'Quarterly'
            elif 330 <= avg_interval <= 400:
                cadence = 'annual'
                cadence_days = 365
                cadence_label = 'Annual'

            if not cadence:
                continue

            avg_amt = sum(amounts) / len(amounts)
            variance = sum((a - avg_amt) ** 2 for a in amounts) / len(amounts)
            std_amt = math.sqrt(variance)
            cv = std_amt / avg_amt if avg_amt > 0 else 0

            latest_amt = amounts[-1]
            first_amt = amounts[0]
            last_date = dates[-1]

            earlier_avg = sum(amounts[:-1]) / len(amounts[:-1]) if len(amounts) > 1 else first_amt
            price_hiked = bool(latest_amt > (earlier_avg * 1.04) and (latest_amt - earlier_avg) >= 50)
            hike_diff = round(latest_amt - earlier_avg, 2) if price_hiked else 0.0
            hike_pct = round((hike_diff / earlier_avg) * 100, 1) if (earlier_avg > 0 and price_hiked) else 0.0

            cat_str = (items[-1]['category'] or '').lower()
            name_lower = name.lower()

            is_atm = any(k in name_lower for k in ['atm', 'withdrawal', 'cash']) or 'cash' in cat_str

            is_utility = any(k in cat_str for k in ['utilit', 'electric', 'gas', 'water', 'telecom', 'mobile', 'phone', 'internet']) or \
                         any(k in name_lower for k in ['gas', 'electric', 'tepco', 'ntt', 'softbank', 'uq mobile', 'kddi', 'internet', 'itscom', 'cloud', 'aws', 'google cloud'])

            is_contract = (any(k in cat_str for k in ['rent', 'housing', 'loan', 'debt', 'car', 'auto', 'insurance', 'lease', 'transport', 'vehicle']) or \
                          any(k in name_lower for k in ['rent', 'bmw', 'suv', 'land', 'loan', 'insurance', 'mortgage', 'housing', 'quoq', 'cedyna', 'smbc', 'car payment', 'auto', 'financ'])) and not is_atm

            is_digital = cv < 0.08 or any(k in name_lower for k in ['app', 'software', 'netflix', 'spotify', 'dazn', 'apple', 'google', 'youtube', 'gym', 'subscription', 'onlyfans', 'patreon', 'adobe', 'chatgpt', 'openai', 'prime', 'icloud'])

            if is_atm:
                sub_type = 'habits'
                sub_type_label = 'Cash / ATM'
            elif is_contract:
                sub_type = 'contracts'
                sub_type_label = 'Contracts & Debt'
            elif is_utility:
                sub_type = 'utilities'
                sub_type_label = 'Utilities & Bills'
            elif is_digital:
                sub_type = 'digital'
                sub_type_label = 'Digital & Subscriptions'
            else:
                sub_type = 'habits'
                sub_type_label = 'Frequent Lifestyle'

            days_since_last = (ref_date - last_date).days

            # Active vs Stopped threshold:
            # 3 months (90 days) for regular cadences; 12 months (365 + 90 days) for annual cadences
            annual_cutoff = 365 + 90
            is_active = days_since_last <= (annual_cutoff if cadence == 'annual' else 90)
            status = 'active' if is_active else 'stopped'

            if is_active:
                next_expected = last_date + timedelta(days=cadence_days)
                while next_expected < ref_date:
                    next_expected += timedelta(days=cadence_days)
                days_until_renewal = (next_expected - ref_date).days
                next_expected_str = next_expected.isoformat()
            else:
                next_expected_str = None
                days_until_renewal = None

            if cadence == 'weekly':
                monthly_equiv = latest_amt * 4.33
            elif cadence == 'biweekly':
                monthly_equiv = latest_amt * 2.16
            elif cadence == 'monthly':
                monthly_equiv = latest_amt
            elif cadence == 'quarterly':
                monthly_equiv = latest_amt / 3.0
            elif cadence == 'annual':
                monthly_equiv = latest_amt / 12.0
            else:
                monthly_equiv = latest_amt

            charge_history = [
                {
                    'id': it['id'],
                    'date': it['date'].isoformat(),
                    'amount': it['amount'],
                    'account': it['account'],
                    'category': it['category'],
                }
                for it in items[-12:]
            ]

            all_detected.append({
                'id': name,
                'name': name,
                'destination_original': items[-1]['original'],
                'alias': items[-1]['alias'],
                'category': items[-1]['category'],
                'subcategory': items[-1]['subcategory'],
                'account': items[-1]['account'],
                'cadence': cadence,
                'cadence_label': cadence_label,
                'cadence_days': cadence_days,
                'avg_interval': round(avg_interval, 1),
                'sub_type': sub_type,
                'sub_type_label': sub_type_label,
                'is_fixed': cv < 0.08,
                'latest_amount': latest_amt,
                'first_amount': first_amt,
                'avg_amount': round(avg_amt, 2),
                'min_amount': min(amounts),
                'max_amount': max(amounts),
                'monthly_equivalent': round(monthly_equiv, 2),
                'annual_projected': round(monthly_equiv * 12.0, 2),
                'price_hiked': price_hiked,
                'hike_pct': hike_pct,
                'hike_diff': hike_diff,
                'status': status,
                'days_since_last': days_since_last,
                'transaction_count': len(items),
                'last_date': last_date.isoformat(),
                'next_expected': next_expected_str,
                'days_until_renewal': days_until_renewal,
                'charge_history': charge_history,
            })

        # Calculate high-level summary KPIs (using active commitments, omitting habits by default)
        active_commitments = [
            s for s in all_detected
            if s['status'] == 'active' and (include_habits or s['sub_type'] != 'habits')
        ]
        stopped_commitments = [
            s for s in all_detected
            if s['status'] == 'stopped' and (include_habits or s['sub_type'] != 'habits')
        ]
        monthly_burn = round(sum(s['monthly_equivalent'] for s in active_commitments), 2)
        annual_burn = round(monthly_burn * 12.0, 2)
        stopped_monthly_saved = round(sum(s['monthly_equivalent'] for s in stopped_commitments), 2)

        price_hiked_items = [
            s for s in active_commitments
            if s['price_hiked']
        ]
        monthly_creep = round(sum(s['hike_diff'] for s in price_hiked_items), 2)

        upcoming_7_days = [
            s for s in active_commitments
            if s['days_until_renewal'] is not None and 0 <= s['days_until_renewal'] <= 7
        ]
        upcoming_7_days_amount = round(sum(s['latest_amount'] for s in upcoming_7_days), 2)

        summary = {
            'total_active_count': len(active_commitments),
            'total_stopped_count': len(stopped_commitments),
            'total_stopped_monthly_saved': stopped_monthly_saved,
            'total_detected_count': len([s for s in all_detected if include_habits or s['sub_type'] != 'habits']),
            'monthly_recurring_burn': monthly_burn,
            'annual_projected_burn': annual_burn,
            'price_hike_count': len(price_hiked_items),
            'total_monthly_hike_creep': monthly_creep,
            'upcoming_7_days_count': len(upcoming_7_days),
            'upcoming_7_days_amount': upcoming_7_days_amount,
            'reference_date': ref_date.isoformat(),
        }

        # Upcoming renewals (next 45 days)
        upcoming_renewals = sorted(
            [s for s in active_commitments if s['days_until_renewal'] is not None and s['days_until_renewal'] >= 0],
            key=lambda x: x['days_until_renewal']
        )[:15]

        # Category Breakdown
        cat_map = defaultdict(lambda: {'count': 0, 'monthly_spend': 0.0})
        for s in active_commitments:
            cat = s['category'] or 'General'
            cat_map[cat]['count'] += 1
            cat_map[cat]['monthly_spend'] += s['monthly_equivalent']

        category_breakdown = [
            {
                'category': k,
                'count': v['count'],
                'monthly_spend': round(v['monthly_spend'], 2),
            }
            for k, v in sorted(cat_map.items(), key=lambda x: x[1]['monthly_spend'], reverse=True)
        ]

        # Filter subscriptions list according to query parameters
        filtered_subs = []
        for s in all_detected:
            if not include_habits and s['sub_type'] == 'habits' and sub_type_filter != 'habits':
                continue

            if status_filter == 'active' and s['status'] != 'active':
                continue
            if status_filter in ('stopped', 'lapsed') and s['status'] != 'stopped':
                continue
            if status_filter == 'hiked' and not s['price_hiked']:
                continue

            if sub_type_filter != 'all' and s['sub_type'] != sub_type_filter:
                continue

            if cadence_filter != 'all' and s['cadence'] != cadence_filter:
                continue

            if search_query:
                q = search_query
                match = (
                    q in s['name'].lower() or
                    q in s['destination_original'].lower() or
                    q in s['category'].lower() or
                    q in s['subcategory'].lower() or
                    q in s['account'].lower()
                )
                if not match:
                    continue

            filtered_subs.append(s)

        # Sort filtered list by monthly equivalent descending by default
        filtered_subs.sort(key=lambda x: x['monthly_equivalent'], reverse=True)

        return {
            'summary': summary,
            'subscriptions': filtered_subs,
            'upcoming_renewals': upcoming_renewals,
            'category_breakdown': category_breakdown,
        }


