from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q, Sum
from finance.transactions.models import Transaction
from accounts.models import Account
from finance.payees.models import DestinationMap


class Command(BaseCommand):
    help = (
        "Synchronize production transaction accounting flags (is_payment, is_expense, is_saving) "
        "and destination map category types to ensure zero double-counting and accurate bank debit reporting."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate the updates without saving changes to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        self.stdout.write(self.style.MIGRATE_HEADING("=== Accounting Flags Synchronization ==="))
        if dry_run:
            self.stdout.write(self.style.WARNING("Running in DRY-RUN mode. No changes will be committed."))

        with transaction.atomic():
            # 1. Update DestinationMap for bank debits -> category_type = 4 (Payment)
            bank_living_dests = [
                'Rent Payment',
                'BMW Car Payment',
                'SUV Land',
                'Housing Center',
                'Transfer Fee',
                'Wise Remmitance',
                'Tokyu Card Payment',
            ]
            dm_to_update = DestinationMap.objects.filter(destination__in=bank_living_dests).exclude(category_type=4)
            dm_count = dm_to_update.count()
            if not dry_run and dm_count > 0:
                dm_to_update.update(category_type=4)
            self.stdout.write(f"1. DestinationMap category_type=4 updates: {dm_count} records")

            # 2. Credit Card purchases: ensure is_payment is False
            cc_erroneous = Transaction.objects.filter(
                account__account_type='CREDIT_CARD',
                is_payment=True,
            )
            cc_err_count = cc_erroneous.count()
            if not dry_run and cc_err_count > 0:
                cc_erroneous.update(is_payment=False)
            self.stdout.write(f"2. Credit Card rows with is_payment=True cleared: {cc_err_count} records")

            # 3. Mizuho Bank debits: ensure all withdrawals have is_payment=True
            mizuho_debits = Transaction.objects.filter(
                account__account_name__icontains='Mizuho',
                is_income=False,
                is_saving=False,
                is_payment=False,
            )
            miz_debit_count = mizuho_debits.count()
            if not dry_run and miz_debit_count > 0:
                mizuho_debits.update(is_payment=True)
            self.stdout.write(f"3. Mizuho Bank debits updated to is_payment=True: {miz_debit_count} records")

            # 4. Bank credit card bill settlements: ensure is_expense is False (transfers only, purchases tracked on card statements)
            settlements = Transaction.objects.filter(
                account__account_name__icontains='Mizuho',
                is_expense=True,
            ).filter(
                Q(destination__icontains='Card Payment')
                | Q(destination__in=['Rakuten Card Payment', 'EPOS Card Payment', 'Tokyu Card Payment', 'Docomo Card Payment', 'Direct Debit'])
            )
            settlement_count = settlements.count()
            if not dry_run and settlement_count > 0:
                settlements.update(is_expense=False)
            self.stdout.write(f"4. Bank card settlements set to is_expense=False: {settlement_count} records")

            # 5. Bank direct living expenses: ensure is_expense is True
            bank_living = Transaction.objects.filter(
                account__account_name__icontains='Mizuho',
                destination__in=['Rent Payment', 'BMW Car Payment', 'SUV Land', 'Housing Center', 'Transfer Fee', 'Wise Remmitance'],
                is_expense=False,
            )
            bank_living_count = bank_living.count()
            if not dry_run and bank_living_count > 0:
                bank_living.update(is_expense=True)
            self.stdout.write(f"5. Bank direct living expenses (Rent, Car, etc.) set to is_expense=True: {bank_living_count} records")

            # 6. ATM Cash Withdrawals: ensure is_expense=True AND is_payment=True (Knowledge Section Rule)
            atm_withdrawals = Transaction.objects.filter(
                account__account_name__icontains='Mizuho',
                is_deleted=False,
            ).filter(
                Q(destination='ATM Withdrawal')
                | Q(destination__icontains='ATM')
                | Q(destination_original__icontains='ＡＴＭ')
                | Q(destination_original__icontains='７ＢＫ')
                | Q(destination='ゆうちょ銀行ATM提携')
            ).exclude(
                destination__icontains='手数料'
            ).exclude(
                destination='Cash Advance'
            )
            atm_to_update = atm_withdrawals.filter(Q(is_expense=False) | Q(is_payment=False))
            atm_count = atm_to_update.count()
            if not dry_run and atm_count > 0:
                atm_to_update.update(is_expense=True, is_payment=True)
            self.stdout.write(f"6. ATM Cash Withdrawals updated to is_expense=True & is_payment=True: {atm_count} records")

            if dry_run:
                self.stdout.write(self.style.WARNING("\nDry run complete. Rolling back transaction."))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS("\nAll updates successfully committed to the database."))

        # Print current verification status
        self.stdout.write("\n=== Current Year Balances (Active Data) ===")
        for yr in [2025, 2026]:
            qs = Transaction.objects.filter(is_deleted=False, date__year=yr)
            inc = float(qs.filter(is_income=True).aggregate(s=Sum('amount'))['s'] or 0)
            exp = float(qs.filter(is_expense=True, is_saving=False).aggregate(s=Sum('amount'))['s'] or 0)
            pay = float(qs.filter(account__account_type='BANK_ACCOUNT', is_payment=True).aggregate(s=Sum('amount'))['s'] or 0)
            sav = float(qs.filter(is_saving=True).aggregate(s=Sum('amount'))['s'] or 0)
            surplus = inc - exp
            rate = round((surplus / inc * 100), 1) if inc > 0 else 0.0
            self.stdout.write(
                f"Year {yr}: Gross Income: ¥{inc:,.0f} | Living Expenses: ¥{exp:,.0f} | "
                f"Op. Surplus: ¥{surplus:,.0f} ({rate}%) | Bank Debits: ¥{pay:,.0f} | Securities: ¥{sav:,.0f}"
            )
