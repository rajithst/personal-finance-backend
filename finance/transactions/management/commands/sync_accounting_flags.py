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
        parser.add_argument(
            "--year",
            type=int,
            default=None,
            help="Target a specific year (e.g. 2026). If omitted, applies to all years in the database.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        target_year = options.get("year")
        self.stdout.write(self.style.MIGRATE_HEADING("=== Accounting Flags Synchronization ==="))
        if target_year:
            self.stdout.write(f"Target Scope: Year {target_year}")
        else:
            self.stdout.write("Target Scope: All transactions across all years (2022–2026)")

        if dry_run:
            self.stdout.write(self.style.WARNING("Running in DRY-RUN mode. No changes will be committed."))

        with transaction.atomic():
            # 1. Update DestinationMap for bank debits:
            # Credit card settlements stay category_type=4 (Payment).
            # Direct bank living expenses align with their Expense category (category_type=1).
            living_payees = ['Rent Payment', 'BMW Car Payment', 'SUV Land', 'Housing Center', 'Direct Debit', 'SMBC（レオパレス２１', 'Paidy', 'Wise Remittance']
            card_payees = ['Rakuten Card Payment', 'EPOS Card Payment', 'Tokyu Card Payment', 'Docomo Card Payment', 'ATM Withdrawal']
            dest_rent_count = DestinationMap.objects.filter(destination__in=living_payees).count()
            dest_card_count = DestinationMap.objects.filter(destination__in=card_payees).count()
            DestinationMap.objects.filter(destination__in=living_payees).update(category_type=1)
            DestinationMap.objects.filter(destination__in=card_payees).update(category_type=4)

            # Ensure 'Internal Transfer' category & subcategories exist
            from finance.categories.models import TransactionCategory, TransactionSubCategory
            from common.constants import (
                ACCOUNT_TYPE_BANK_ACCOUNT,
                BANK_ACCOUNT_PROVIDER_JP_POST,
            )

            internal_transfer_cat, _ = TransactionCategory.objects.get_or_create(
                category='Internal Transfer',
                defaults={
                    'category_type': 4,
                    'description': 'Account-to-account and multi-currency internal transfers',
                    'can_rename': False,
                    'can_delete': False,
                    'user_id': 1,
                }
            )
            if internal_transfer_cat.category_type != 4:
                internal_transfer_cat.category_type = 4
                internal_transfer_cat.save()

            wise_subcat, _ = TransactionSubCategory.objects.get_or_create(
                category=internal_transfer_cat,
                name='Wise Transfer',
                defaults={
                    'description': 'Transfers between bank accounts and Wise wallet',
                    'can_rename': False,
                    'can_delete': False,
                    'user_id': 1,
                }
            )

            jp_post_subcat, _ = TransactionSubCategory.objects.get_or_create(
                category=internal_transfer_cat,
                name='JP Post Bank Transfer',
                defaults={
                    'description': 'Internal transfers to/from JP Post Bank account',
                    'can_rename': False,
                    'can_delete': False,
                    'user_id': 1,
                }
            )

            general_subcat, _ = TransactionSubCategory.objects.get_or_create(
                category=internal_transfer_cat,
                name='General Account Transfer',
                defaults={
                    'description': 'Transfers between personal bank accounts',
                    'can_rename': False,
                    'can_delete': False,
                    'user_id': 1,
                }
            )

            # Ensure JP Post Bank account exists
            jp_post_acc, _ = Account.objects.get_or_create(
                account_name='JP Post Bank',
                defaults={
                    'account_type': ACCOUNT_TYPE_BANK_ACCOUNT,
                    'provider': BANK_ACCOUNT_PROVIDER_JP_POST,
                    'description': 'Japan Post Bank (ゆうちょ銀行) Account',
                    'user_id': 1,
                }
            )

            # Configure comprehensive DestinationMap rules for Japanese bank statements
            dest_configs = {
                'Direct Debit': {'category_id': 14, 'subcategory_id': 58, 'category_type': 1, 'keywords': 'ＪＣＢデビット,ｼﾞｪｲｼｰﾋﾞｰﾃﾞﾋﾞｯﾄ,JCBデビット,J C B デビット'},
                'Rakuten Card Payment': {'category_id': 14, 'subcategory_id': 57, 'category_type': 4, 'keywords': 'ラクテンカード,ラクテンカ,ネット　ラクテンカード'},
                'Rakuten Securities': {'category_id': 6, 'subcategory_id': 28, 'category_type': 3, 'keywords': 'ネツト　ラクテンシヨウケン（カ,ラクテンシヨウケ（カ,ラクテンシヨウケン（カ,ネット　ラクテンシヨウケン（カ,ネット ラクテンシヨウケン（カ'},
                'Rakuten Securities Transfer (Internal)': {'category_id': internal_transfer_cat.id, 'subcategory_id': general_subcat.id, 'category_type': 4, 'keywords': '振込　ラクテンシヨウケン,振込 ラクテンシヨウケン'},
                'Housing Center': {'category_id': 1, 'subcategory_id': 2, 'category_type': 1, 'keywords': 'ハウジングセンター,ネット　ハウジングセンター'},
                'SMBC（レオパレス２１': {'category_id': 1, 'subcategory_id': 1, 'category_type': 1, 'keywords': 'レオパレス,SMBC（レオパレス２１,ＳＭＢＣ（レオパレス２１'},
                'Paidy': {'category_id': 14, 'subcategory_id': 58, 'category_type': 1, 'keywords': 'ペイディ,Paidy,ネット　ペイディ'},
                'Wise Remittance': {'category_id': 16, 'subcategory_id': 75, 'category_type': 1, 'keywords': 'ワイズ,Wise,トランスファーワイズ'},
                'Dinesh Suduhakuruge': {'category_id': 16, 'subcategory_id': 75, 'category_type': 1, 'keywords': 'スデュウ,Dinesh,Suduhakuruge'},
                'Nawaratna Mudiyanse': {'category_id': 16, 'subcategory_id': 75, 'category_type': 1, 'keywords': 'ナワラトナ,Nawaratna'},
                'Wise Transfer (Internal)': {'category_id': internal_transfer_cat.id, 'subcategory_id': wise_subcat.id, 'category_type': 4, 'keywords': 'ワイズ,Wise,トランスファーワイズ,ヒチナイドウ'},
                'JP Post Bank Transfer': {'category_id': internal_transfer_cat.id, 'subcategory_id': jp_post_subcat.id, 'category_type': 4, 'keywords': 'ゆうちょ銀行,ゆうちょ,ﾕｳﾁｮ,JP Post,テンナコン,テツナコ'},
                'General Account Transfer': {'category_id': internal_transfer_cat.id, 'subcategory_id': general_subcat.id, 'category_type': 4, 'keywords': '振替,口座振替,自口座'},
            }
            for d_name, d_conf in dest_configs.items():
                obj = DestinationMap.objects.filter(destination=d_name).first()
                if obj:
                    obj.category_id = d_conf['category_id']
                    obj.subcategory_id = d_conf['subcategory_id']
                    obj.category_type = d_conf['category_type']
                    existing_kws = [k.strip() for k in (obj.keywords or '').split(',') if k.strip()]
                    new_kws = [k.strip() for k in d_conf['keywords'].split(',') if k.strip()]
                    combined_kws = list(dict.fromkeys(existing_kws + new_kws))
                    obj.keywords = ','.join(combined_kws)
                    obj.save()
                else:
                    DestinationMap.objects.create(
                        destination=d_name,
                        destination_eng=d_name,
                        category_id=d_conf['category_id'],
                        subcategory_id=d_conf['subcategory_id'],
                        category_type=d_conf['category_type'],
                        keywords=d_conf['keywords'],
                    )

            # Ensure Rakuten Securities DestinationMap keywords do not contain inbound transfer terms
            rak_sec_dest = DestinationMap.objects.filter(destination='Rakuten Securities').first()
            if rak_sec_dest and rak_sec_dest.keywords:
                kws = [k.strip() for k in rak_sec_dest.keywords.split(',') if k.strip() and not k.strip().startswith('振込')]
                rak_sec_dest.keywords = ','.join(dict.fromkeys(kws))
                rak_sec_dest.save()

            self.stdout.write(f"1. DestinationMap category_types aligned: {dest_rent_count} living expense rules, {dest_card_count} payment rules")

            # 1b. Soft-delete accidental cross-year bank imports in 2024 from 2023 statement
            if target_year in [None, 2024]:
                dup_candidates = Transaction.objects.filter(
                    date__year=2024,
                    account__account_type='BANK_ACCOUNT',
                    created_at__gte='2026-10-11 02:00:00+00:00',
                    is_deleted=False
                )
                dup_count = dup_candidates.count()
                if dup_count > 0:
                    dup_candidates.update(is_deleted=True, delete_reason="Duplicate import from 2023 statement CSV")
                    self.stdout.write(f"1b. Soft-deleted duplicate 2024 bank records imported from 2023 statement: {dup_count} records")

            # 1c. Soft-delete duplicate 2023-12-25 ATM withdrawal (ID 3178, keeping ID 3176)
            dup_3178 = Transaction.objects.filter(
                id=3178,
                date='2023-12-25',
                amount=30000,
                is_deleted=False
            )
            if dup_3178.exists():
                dup_3178.update(
                    is_deleted=True,
                    delete_reason="Duplicate 2023-12-25 ATM withdrawal (ID 3176 is genuine)"
                )
                self.stdout.write("1c. Soft-deleted duplicate 2023-12-25 ATM withdrawal (ID 3178)")

            # 1c-1. Standardize 2023 Salaries from Robert Walters (2022/06/28 to 2023/12/11)
            rw_2023_salary_ids = [2879, 2886, 2888, 2891, 2894, 2897, 2901, 2905, 2908, 2912, 2915, 2917]
            Transaction.objects.filter(id__in=rw_2023_salary_ids).update(
                destination='Robert Walters',
                category_id=17,
                subcategory_id=65,
                is_income=True,
                is_payment=False,
                is_expense=False,
                is_saving=False,
                is_deleted=False,
                delete_reason=None,
            )
            # 1c-2. Standardize first Tech Mahindra paycheck (ID 15, 2024-01-25)
            Transaction.objects.filter(id=15).update(
                destination='Tech Mahindra',
                category_id=17,
                subcategory_id=65,
                is_income=True,
                is_payment=False,
                is_expense=False,
                is_saving=False,
            )
            self.stdout.write("1c-1. Standardized 2023 Salaries (Robert Walters) & 2024-01-25 (Tech Mahindra)")

            # 1d. Genuine Rakuten Securities transfers into Mizuho (Internal Transfer & Savings return)
            rak_sec_acc = Account.objects.filter(account_name__icontains='Rakuten Securities').first()
            rakuten_inflow_ids = [14, 1346, 1644, 2197, 2356]
            rakuten_inflow_qs = Transaction.objects.filter(id__in=rakuten_inflow_ids)
            if rakuten_inflow_qs.exists():
                r_restored = rakuten_inflow_qs.update(
                    is_deleted=False,
                    delete_reason=None,
                    destination='Rakuten Securities Transfer (Internal)',
                    counterparty_account=rak_sec_acc,
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=True
                )
                self.stdout.write(f"1d. Standardized {r_restored} Rakuten Securities inflows into Mizuho as Internal Transfers & Savings returns: IDs {rakuten_inflow_ids}")

            # Also ensure any other inbound transfers with '振込　ラクテンシヨウケン' are mapped to Internal Transfer & Savings return
            Transaction.objects.filter(
                Q(destination_original__icontains='振込　ラクテンシヨウケン') | Q(destination_original__icontains='振込 ラクテンシヨウケン')
            ).exclude(id__in=rakuten_inflow_ids).update(
                destination='Rakuten Securities Transfer (Internal)',
                counterparty_account=rak_sec_acc,
                category=internal_transfer_cat,
                subcategory=general_subcat,
                is_income=True,
                is_payment=False,
                is_expense=False,
                is_saving=True
            )

            # 1e. Reassign 2024-04-05 table tennis purchase (ID 235, ¥46,436) to EPOS Card
            t235_qs = Transaction.objects.filter(id=235, date='2024-04-05', amount=46436)
            if t235_qs.filter(account__account_type='BANK_ACCOUNT').exists():
                t235_qs.update(
                    account_id=3,
                    is_payment=False,
                    is_expense=True,
                    is_income=False,
                    is_saving=False
                )
                self.stdout.write("1e. Reassigned 2024-04-05 purchase (ID 235) from Mizuho to EPOS Card")

            # 1f. Correct 2024-07-19 ATM Cash Deposit (ID 83, ¥300,000)
            t83_qs = Transaction.objects.filter(id=83, date='2024-07-19', amount=300000)
            if t83_qs.exists():
                t83_qs.update(
                    destination='ATM Cash Deposit',
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False
                )
                self.stdout.write("1f. Corrected 2024-07-19 ATM transaction (ID 83) to Cash Deposit (+¥300,000)")

            # 1g. Reconcile 2024-10-07 PayPay Bank transfer & refund (IDs 115, 113, ¥60,000)
            t115_qs = Transaction.objects.filter(id=115, date='2024-10-07', amount=60000)
            if t115_qs.exists():
                t115_qs.update(
                    is_deleted=False,
                    delete_reason=None,
                    destination='PayPay Bank Transfer (Failed)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    is_income=False,
                    is_payment=True,
                    is_expense=False,
                    is_saving=False,
                )
            t113_qs = Transaction.objects.filter(id=113, date='2024-10-07', amount=60000)
            if t113_qs.exists():
                t113_qs.update(
                    is_deleted=False,
                    delete_reason=None,
                    destination='PayPay Bank Transfer Refund',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                )
            self.stdout.write("1g. Restored 2024-10-07 PayPay Bank transfer & refund (IDs 115, 113) as Internal Transfers")

            # 1h. Reconcile 2024-12 Dilum Mahesh ATM deposit (ID 136, +¥123k) and Toyota Finance payment (ID 139, -¥123k)
            t136_qs = Transaction.objects.filter(id=136, date='2024-12-30', amount=123000)
            if t136_qs.exists():
                t136_qs.update(
                    is_deleted=False,
                    delete_reason=None,
                    destination='Dilum Mahesh (Cash Deposit)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                )
            t139_qs = Transaction.objects.filter(id=139, date='2024-12-31', amount=122947)
            if t139_qs.exists():
                t139_qs.update(
                    is_deleted=False,
                    delete_reason=None,
                    destination='Toyota Finance (Dilum Mahesh)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    is_income=False,
                    is_payment=True,
                    is_expense=False,
                    is_saving=False,
                )
            self.stdout.write("1h. Reconciled 2024-12 Dilum Mahesh ATM deposit (ID 136, +¥123k) and Toyota Finance payment (ID 139, -¥123k)")

            # 1i. 2024-10-31 Mizuho ATM withdrawal (¥15,000) reconciling raw Oct/Nov query gap
            if target_year in [None, 2024]:
                mizuho_acc = Account.objects.filter(account_type='BANK_ACCOUNT').first()
                if mizuho_acc:
                    t_oct31, created_oct31 = Transaction.objects.get_or_create(
                        account=mizuho_acc,
                        date='2024-10-31',
                        amount=15000.00,
                        defaults={
                            'destination': 'ATM Withdrawal',
                            'destination_original': 'ＡＴＭ',
                            'category_id': 14,
                            'subcategory_id': 58,
                            'is_expense': True,
                            'is_payment': True,
                            'is_income': False,
                            'is_saving': False,
                            'notes': 'Created manually comparing remaining balance of 11/02 (Raw statement query ended on 10/30, opening balance on 11/01 was ¥177,898 vs ¥192,898 on 10/30)',
                            'user_id': 1,
                        }
                    )
                    if not created_oct31:
                        t_oct31.is_deleted = False
                        t_oct31.is_expense = True
                        t_oct31.is_payment = True
                        t_oct31.is_income = False
                        t_oct31.is_saving = False
                        t_oct31.save()
                    self.stdout.write("1i. Verified 2024-10-31 ATM Withdrawal (¥15,000) reconciling remaining balance gap")

            # 2025 Q1 Reconciliation Rules (1j - 1m)
            if target_year in [None, 2025]:
                # 1j. Restore Nextage transfer on 2025-01-17 to actual ¥300,000 & Nextage refund on 2025-02-14 (+¥12,800)
                Transaction.objects.filter(id=1355).update(
                    amount=300000.00,
                    destination='SUV Land (Nextage)',
                    category_id=2,
                    subcategory_id=5,
                    is_expense=True,
                    is_payment=True,
                    is_income=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=1366).update(
                    amount=12800.00,
                    destination='Nextage Refund (SUV Land)',
                    category_id=2,
                    subcategory_id=5,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1j. Reconciled 2025 Nextage purchase (ID 1355, -¥300k) and refund (ID 1366, +¥12.8k)")

                # 1k. Restore 2025-01-31 Chabotha Pathirana transfer (ID 1348, -¥15,000)
                Transaction.objects.filter(id=1348).update(
                    destination='Chabotha Pathirana',
                    category_id=16,
                    subcategory_id=75,
                    is_expense=True,
                    is_payment=True,
                    is_income=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1k. Restored 2025-01-31 Chabotha Pathirana transfer (ID 1348, -¥15k)")

                # 1l. Ensure both ¥220 ATM fees exist on 2025-02-01 (corresponding to two ¥5,000 ATM withdrawals)
                feb1_fees = Transaction.objects.filter(
                    account__account_type='BANK_ACCOUNT',
                    date='2025-02-01',
                    amount=220,
                    is_deleted=False
                )
                if feb1_fees.count() < 2:
                    mizuho_acc = Account.objects.filter(account_type='BANK_ACCOUNT').first()
                    Transaction.objects.create(
                        account=mizuho_acc,
                        date='2025-02-01',
                        amount=220.00,
                        destination='Transfer Fee',
                        destination_original='手数料',
                        category_id=16,
                        subcategory_id=62,
                        is_expense=True,
                        is_payment=True,
                        is_income=False,
                        is_saving=False,
                        notes='Second 7-Bank ATM fee on 2025-02-01',
                        user_id=1,
                    )
                    self.stdout.write("1l. Created missing second 7-Bank ATM fee (¥220) on 2025-02-01")

                # 1m. Restore 2025-03-11 ATM Cash Deposit from JP Post (ID 1469, +¥60,000)
                Transaction.objects.filter(id=1469).update(
                    destination='ATM Cash Deposit (JP Post)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1m. Restored 2025-03-11 ATM Cash Deposit from JP Post (ID 1469, +¥60k)")

                # 1n. Reconcile 2025-04-17 ATM Deposit (ID 1560, +¥250k) and Dinesh remittance (ID 1569, -¥250k)
                Transaction.objects.filter(id=1560).update(
                    amount=250000.00,
                    destination='ATM Cash Deposit (7-Bank)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=1569).update(
                    amount=250000.00,
                    destination='Dinesh Suduhakuruge',
                    category_id=16,
                    subcategory_id=75,
                    is_income=False,
                    is_payment=True,
                    is_expense=True,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1n. Reconciled 2025-04-17 ATM Deposit (ID 1560, +¥250k) and Dinesh remittance (ID 1569, -¥250k)")

                # 1o. Restore 2025-06-27 Rakuten Securities Outflow to actual bank debit (ID 1648, -¥150k)
                Transaction.objects.filter(id=1648).update(
                    amount=150000.00,
                    destination='Rakuten Securities',
                    category_id=6,
                    subcategory_id=28,
                    is_income=False,
                    is_payment=True,
                    is_expense=False,
                    is_saving=True,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1o. Restored 2025-06-27 Rakuten Securities Outflow (ID 1648, -¥150k)")

                # 1p. Restore 2025-08 Dinesh loan transfer (ID 1767, -¥10k) and repayment (ID 1758, +¥10k)
                Transaction.objects.filter(id=1767).update(
                    destination='Dinesh Suduhakuruge (Advance)',
                    category_id=16,
                    subcategory_id=75,
                    is_income=False,
                    is_payment=True,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=1758).update(
                    destination='Dinesh Suduhakuruge (Repayment)',
                    category_id=16,
                    subcategory_id=75,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1p. Restored 2025-08 Dinesh advance (ID 1767, -¥10k) and repayment (ID 1758, +¥10k)")

                # 1q. Restore 2025-09-25 Wise transfer (ID 1875, -¥50k) and refund (ID 1866, +¥50k)
                Transaction.objects.filter(id=1875).update(
                    destination='Wise Transfer (Internal)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    is_income=False,
                    is_payment=True,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=1866).update(
                    destination='Wise Refund (Internal)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1q. Restored 2025-09-25 Wise transfer (ID 1875, -¥50k) and refund (ID 1866, +¥50k)")

                # 1r. Restore 2025-09-29 EPOS Card Refund (ID 1865, +¥1,950)
                Transaction.objects.filter(id=1865).update(
                    amount=1950.00,
                    destination='EPOS Card Refund',
                    category_id=14,
                    subcategory_id=58,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1r. Restored 2025-09-29 EPOS Card Refund (ID 1865, +¥1,950)")

                # 1s. Standardize 2025-09-25 Salary destination (ID 1867) -> Astellas Pharma
                Transaction.objects.filter(id=1867).update(
                    destination='Astellas Pharma',
                    category_id=17,
                    subcategory_id=65,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1s. Standardized 2025-09-25 Salary destination to Astellas Pharma (ID 1867, +¥736,477)")

                # 1t. Restore 2025-10-12 Dissanayake deposit (ID 1938, +¥30k) and JP Post ATM withdrawal (ID 1947, -¥30k)
                Transaction.objects.filter(id=1938).update(
                    destination='Dissanayake (Deposit)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=1947).update(
                    destination='JP Post (Internal Transfer Out)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    is_income=False,
                    is_payment=True,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1t. Restored 2025-10-12 Dissanayake deposit (ID 1938, +¥30k) & JP Post ATM withdrawal (ID 1947, -¥30k)")

                # 1u. Correct 2025-10-14 EPOS Card Refund (ID 1937, +¥1,566)
                Transaction.objects.filter(id=1937).update(
                    amount=1566.00,
                    destination='EPOS Card Refund',
                    category_id=14,
                    subcategory_id=58,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1u. Corrected 2025-10-14 EPOS Card Refund (ID 1937, +¥1,566)")

                # 1v. Standardize 2025 Q4 Salary destinations (IDs 1936, 2007, 2104) -> Astellas Pharma
                Transaction.objects.filter(id__in=[1936, 2007, 2104]).update(
                    destination='Astellas Pharma',
                    category_id=17,
                    subcategory_id=65,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1v. Standardized 2025 Q4 Salaries to Astellas Pharma: Oct (ID 1936), Nov (ID 2007), Dec (ID 2104)")

            if target_year in [None, 2026]:
                # 1w. 2026-01-25 ATM Cash Deposit (ID 2199, +¥255k) and Wise remittance (ID 2210, -¥250k)
                Transaction.objects.filter(id=2199).update(
                    destination='ATM Cash Deposit (Family Remittance Funding)',
                    category_id=16,
                    subcategory_id=75,
                    amount=255000.00,
                    is_income=False,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_third_party=True,
                    on_behalf_of='Wife',
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=2210).update(
                    destination='Wise Remittance (On-behalf)',
                    category_id=16,
                    subcategory_id=75,
                    amount=250000.00,
                    is_income=False,
                    is_payment=True,
                    is_expense=False,
                    is_saving=False,
                    is_third_party=True,
                    on_behalf_of='Wife',
                    is_deleted=False,
                    delete_reason=None,
                )
                # 1w-2. 2026-01-26 ATM Deposit (ID 2198, +¥2k)
                Transaction.objects.filter(id=2198).update(
                    destination='ATM Cash Deposit',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    amount=2000.00,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                # 1w-3. 2026-01-30 Yamano Shinichi transfer (ID 2202, -¥77k)
                Transaction.objects.filter(id=2202).update(
                    destination='Yamano Shinichi (Advance)',
                    category_id=16,
                    subcategory_id=75,
                    is_income=False,
                    is_payment=True,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1w. Reconciled 2026-01 transactions (IDs 2199, 2210, 2198, 2202)")

                # 1x. 2026-03 Cash Deposit (ID 2357, +¥420k), Rakuten Securities (ID 2364, -¥420k), ATM Withdrawal (ID 2362, -¥500k)
                Transaction.objects.filter(id=2357).update(
                    destination='ATM Cash Deposit (Securities Funding)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    amount=420000.00,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=2364).update(
                    destination='Rakuten Securities',
                    category_id=6,
                    subcategory_id=28,
                    amount=420000.00,
                    is_income=False,
                    is_payment=True,
                    is_expense=False,
                    is_saving=True,
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=2362).update(
                    amount=500000.00,
                    destination='ATM Withdrawal',
                    is_income=False,
                    is_payment=True,
                    is_expense=True,
                )
                self.stdout.write("1x. Reconciled 2026-03 transactions (IDs 2357, 2364, 2362)")

                # 1y. 2026-04-13 JP Post Inbound Transfer (ID 2455, +¥40k)
                Transaction.objects.filter(id=2455).update(
                    destination='JP Post Bank Transfer (Inflow)',
                    category=internal_transfer_cat,
                    subcategory=jp_post_subcat,
                    amount=40000.00,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1y. Reconciled 2026-04 JP Post Bank Inbound Transfer (ID 2455, +¥40k)")

                # 1z. Standardize 2026 Salaries (IDs 2200, 2291, 2355, 2454) -> Astellas Pharma
                Transaction.objects.filter(id__in=[2200, 2291, 2355, 2454]).update(
                    destination='Astellas Pharma',
                    category_id=17,
                    subcategory_id=65,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1z. Standardized 2026 Salaries to Astellas Pharma: Jan, Feb, Mar, Apr")

                # 1aa. 2026-05 ATM Cash Deposit (ID 2529, +¥70k) and Wise Remittance (ID 2536, -¥70k)
                Transaction.objects.filter(id=2529).update(
                    destination='ATM Cash Deposit (Family Remittance Funding)',
                    category_id=16,
                    subcategory_id=75,
                    amount=70000.00,
                    is_income=False,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_third_party=True,
                    on_behalf_of='Wife',
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=2536).update(
                    destination='Wise Remittance (On-behalf)',
                    category_id=16,
                    subcategory_id=75,
                    amount=70000.00,
                    is_income=False,
                    is_payment=True,
                    is_expense=False,
                    is_saving=False,
                    is_third_party=True,
                    on_behalf_of='Wife',
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1aa. Reconciled 2026-05 ATM Deposit (ID 2529, +¥70k) & Wise Remittance (ID 2536, -¥70k)")

                # 1ab. 2026-06 ATM Deposit (ID 2630), Jayasinghe Repayment (ID 2628), Kelagara Repayment (ID 2629)
                Transaction.objects.filter(id=2630).update(
                    destination='ATM Cash Deposit',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    amount=3000.00,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=2628).update(
                    destination='Jayasinghe Mudiyanselage (Repayment Inflow)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    amount=500000.00,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=2629).update(
                    destination='Kelagara Arachchilage (Repayment)',
                    category=internal_transfer_cat,
                    subcategory=general_subcat,
                    amount=1839.00,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                self.stdout.write("1ab. Reconciled 2026-06 ATM Deposit (ID 2630), Jayasinghe (ID 2628), Kelagara (ID 2629)")

                # 1ac. 2026-07-18 Second Wise Remittance (-¥50k) & Japan Visa Support
                wise_txs_0718 = Transaction.objects.filter(
                    account__account_type='BANK_ACCOUNT',
                    date='2026-07-18',
                    amount=50000.00,
                    is_deleted=False
                )
                if wise_txs_0718.count() == 1:
                    mizuho_acc = Account.objects.filter(account_type='BANK_ACCOUNT').first()
                    Transaction.objects.create(
                        account=mizuho_acc,
                        date='2026-07-18',
                        amount=50000.00,
                        destination='Wise Remittance',
                        destination_original='ネツト　ワイズ　ペイメンツ　ジヤパン（カ',
                        category_id=16,
                        subcategory_id=75,
                        is_income=False,
                        is_payment=True,
                        is_expense=True,
                        is_saving=False,
                        notes='Second ¥50,000 Wise remittance on 2026-07-18 from raw bank statement'
                    )
                    self.stdout.write("1ac. Inserted missing second 2026-07-18 Wise Remittance (-¥50,000)")

                Transaction.objects.filter(id__in=[2644, 2726]).update(
                    destination='Japan Visa Support',
                    category_id=16,
                    subcategory_id=75,
                    is_income=False,
                    is_payment=True,
                    is_expense=True,
                    is_saving=False,
                )

                # 1ad. 2026-08 Dilhan Saritha & Naleen Kumara Disa remittances
                Transaction.objects.filter(id__in=[2721, 2720]).update(
                    destination='Dilhan Saritha',
                    category_id=16,
                    subcategory_id=75,
                    is_income=False,
                    is_payment=True,
                    is_expense=True,
                    is_saving=False,
                )
                Transaction.objects.filter(id=2718).update(
                    destination='Naleen Kumara Disa',
                    category_id=16,
                    subcategory_id=75,
                    is_income=False,
                    is_payment=True,
                    is_expense=True,
                    is_saving=False,
                )

                # 1ae. Standardize 2026 May-Sep Salaries and Bonus -> Astellas Pharma
                Transaction.objects.filter(id__in=[2530, 2627, 2641, 2712, 2828]).update(
                    destination='Astellas Pharma',
                    destination_original='給与',
                    category_id=17,
                    subcategory_id=65,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    is_deleted=False,
                    delete_reason=None,
                )
                Transaction.objects.filter(id=2643).update(
                    destination='Astellas Pharma (Bonus)',
                    destination_original='賞与',
                    category_id=17,
                    subcategory_id=71,
                    is_income=True,
                    is_payment=False,
                    is_expense=False,
                    is_saving=False,
                    delete_reason=None,
                )
                self.stdout.write("1ae. Standardized 2026 May-Sep Salaries & Bonus to Astellas Pharma")

            # Base transaction filters (active transactions only)
            base_tx = Transaction.objects.filter(is_deleted=False)
            if target_year:
                base_tx = base_tx.filter(date__year=target_year)

            # 2. Credit Card purchases: ensure is_payment is False
            cc_erroneous = base_tx.filter(
                account__account_type='CREDIT_CARD',
                is_payment=True,
            )
            cc_err_count = cc_erroneous.count()
            if cc_err_count > 0:
                cc_erroneous.update(is_payment=False)
            self.stdout.write(f"2. Credit Card rows with is_payment=True cleared: {cc_err_count} records")

            # 3. Bank debits: ensure all withdrawals have is_payment=True
            bank_debits = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                is_income=False,
                is_saving=False,
                is_payment=False,
            )
            bank_debit_count = bank_debits.count()
            if bank_debit_count > 0:
                bank_debits.update(is_payment=True)
            self.stdout.write(f"3. Bank debits updated to is_payment=True: {bank_debit_count} records")

            # 4. Standardize and remap unmapped/misassigned bank transactions:
            # 4a. Tokyu Card settlements
            misassigned_tokyu = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='トウキユウ　カ') | Q(destination_original__icontains='トウキユウ　ｶ')
            ).exclude(destination='Tokyu Card Payment')
            mis_tokyu_count = misassigned_tokyu.count()
            if mis_tokyu_count > 0:
                misassigned_tokyu.update(destination='Tokyu Card Payment', category_id=14, subcategory_id=57, is_expense=False, is_payment=True)
            self.stdout.write(f"4a. Remapped misassigned Tokyu Card settlements from bank: {mis_tokyu_count} records")

            # 4b. Rakuten Card settlements
            misassigned_rakuten = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='ラクテンカ') | Q(destination__icontains='ラクテンカード')
            ).exclude(destination='Rakuten Card Payment').exclude(destination__icontains='Securities').exclude(destination_original__icontains='シヨウケ')
            mis_rakuten_count = misassigned_rakuten.count()
            if mis_rakuten_count > 0:
                misassigned_rakuten.update(destination='Rakuten Card Payment', category_id=14, subcategory_id=57, is_expense=False, is_payment=True)
            self.stdout.write(f"4b. Remapped misassigned Rakuten Card settlements from bank: {mis_rakuten_count} records")

            # 4c. Direct Debit (JCB Debit card purchases)
            jcb_debit = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination__in=['ｼﾞｪｲｼｰﾋﾞｰﾃﾞﾋﾞｯﾄ', 'JCBデビット', 'J C B デビット'])
                | Q(destination_original__icontains='ＪＣＢデビット')
                | Q(destination_original__icontains='ｼﾞｪｲｼｰﾋﾞｰﾃﾞﾋﾞｯﾄ')
                | Q(destination_original__icontains='JCBデビット')
            ).exclude(destination='Direct Debit')
            jcb_count = jcb_debit.count()
            if jcb_count > 0:
                jcb_debit.update(destination='Direct Debit', category_id=14, subcategory_id=58, is_expense=True, is_payment=True)
            self.stdout.write(f"4c. Standardized JCB Debit card purchases to Direct Debit: {jcb_count} records")

            # 4d. Leopalace Rent
            leopalace = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='レオパレス') | Q(destination__icontains='レオパレス')
            ).filter(is_income=False).exclude(destination='SMBC（レオパレス２１')
            leo_count = leopalace.count()
            if leo_count > 0:
                leopalace.update(destination='SMBC（レオパレス２１', category_id=1, subcategory_id=1, is_expense=True, is_payment=True)
            self.stdout.write(f"4d. Standardized Leopalace Rent to SMBC（レオパレス２１: {leo_count} records")

            # 4e. Housing Center
            housing_cntr = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='ハウジングセンター') | Q(destination__icontains='ハウジングセンター')
            ).exclude(destination='Housing Center')
            hc_count = housing_cntr.count()
            if hc_count > 0:
                housing_cntr.update(destination='Housing Center', category_id=1, subcategory_id=2, is_expense=True, is_payment=True)
            self.stdout.write(f"4e. Standardized Housing Center: {hc_count} records")

            # 4f. Paidy
            paidy_tx = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='ペイディ') | Q(destination__icontains='ペイディ')
            ).exclude(destination='Paidy')
            paidy_count = paidy_tx.count()
            if paidy_count > 0:
                paidy_tx.update(destination='Paidy', category_id=14, subcategory_id=58, is_expense=True, is_payment=True)
            self.stdout.write(f"4f. Standardized Paidy payments: {paidy_count} records")

            # 4g. Wise Remittances & Internal Transfers
            # 4g-0. Soft-delete confirmed duplicate Wise record in 2023 (ID 2884)
            dup_2884 = Transaction.objects.filter(id=2884, is_deleted=False)
            dup_2884_count = dup_2884.count()
            if dup_2884_count > 0:
                dup_2884.update(
                    is_deleted=True,
                    delete_reason="Duplicate import from 2023 statement CSV (confirmed by actual bank balance ¥520,294 on 2023-02-27)"
                )
                self.stdout.write("4g-0. Soft-deleted duplicate Wise return record ID=2884 (+¥199,800)")

            # 4g-1. Mizuho transfers that funded Wise USD balance in Jan/Feb 2023 (Internal Transfer, NOT an expense)
            wise_funding = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='ワイズ') | Q(destination__icontains='Wise'),
                date__in=['2023-01-22', '2023-01-25', '2023-01-26', '2023-02-02'],
                amount__in=[130557, 131984, 130789, 129852],
            )
            wise_fund_count = wise_funding.count()
            if wise_fund_count > 0:
                wise_funding.update(
                    destination='Wise Transfer (Internal)',
                    category=internal_transfer_cat,
                    subcategory=wise_subcat,
                    is_expense=False,
                    is_payment=True,
                    is_income=False,
                    is_saving=False,
                )
            self.stdout.write(f"4g-1. Mapped Wise USD funding transfers (Internal Transfer): {wise_fund_count} records")

            # 4g-2. Genuine outbound family/overseas remittances (late March 2023, July 2024, etc.)
            wise_remit = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='ワイズ') | Q(destination__icontains='Wise'),
            ).filter(is_income=False).exclude(destination__icontains='Wise Transfer').exclude(destination__icontains='Wise Return').exclude(destination_original__icontains='REFUND').exclude(is_third_party=True).exclude(destination__icontains='On-behalf')
            wise_count = wise_remit.count()
            if wise_count > 0:
                wise_remit.update(
                    destination='Wise Remittance',
                    category_id=16,
                    subcategory_id=75,
                    is_expense=True,
                    is_payment=True,
                    is_income=False,
                )
            self.stdout.write(f"4g-2. Standardized genuine Wise Remittances: {wise_count} records")

            # 4g-3. Inbound funds returning from Wise to Mizuho in Feb 2023 (Internal Transfer: Wise -> Mizuho, NOT income, NOT expense)
            if target_year in [None, 2023]:
                wise_returns = base_tx.filter(
                    Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                    Q(destination_original__icontains='ヒチナイドウ') | Q(destination__icontains='ヒチナイドウ'),
                    date__year=2023,
                )
                wise_ret_count = wise_returns.count()
                if wise_ret_count > 0:
                    wise_returns.update(
                        destination='Wise Return (Internal)',
                        category=internal_transfer_cat,
                        subcategory=wise_subcat,
                        is_income=True,
                        is_expense=False,
                        is_payment=False,
                        is_saving=False,
                    )
                self.stdout.write(f"4g-3. Mapped Wise returned funds to Mizuho (Internal Transfer): {wise_ret_count} records")

            # 4g-3b. JP Post Bank transfers (restore un-deleted and map as Internal Transfer)
            Transaction.objects.filter(
                id=6,
                delete_reason='Transfer to JP Post'
            ).update(is_deleted=False, delete_reason=None)

            jp_post_txs = Transaction.objects.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='テンナコン') | Q(destination_original__icontains='テツナコ')
                | Q(destination__icontains='JP Post Bank Transfer')
            ).filter(is_deleted=False, is_income=False).exclude(destination__icontains='Sri Lanka').exclude(destination_original__icontains='RAJITH').exclude(destination__icontains='Inflow')

            if target_year:
                jp_post_txs = jp_post_txs.filter(date__year=target_year)

            jp_post_count = jp_post_txs.count()
            if jp_post_count > 0:
                jp_post_txs.update(
                    destination='JP Post Bank Transfer',
                    category=internal_transfer_cat,
                    subcategory=jp_post_subcat,
                    is_expense=False,
                    is_income=False,
                    is_payment=True,
                    is_saving=False,
                )
            self.stdout.write(f"4g-3b. Mapped JP Post Bank internal transfers (Internal Transfer): {jp_post_count} records")

            # 4g-4. Wise Account & Direct Wise USD expenditures (Airlines, remittances from USD balance)
            wise_acc, _ = Account.objects.get_or_create(
                account_name='Wise',
                defaults={
                    'account_type': 'PAYMENT_APP',
                    'provider': 'Wise',
                    'description': 'Wise Multi-Currency Digital Wallet',
                    'user_id': 1
                }
            )
            if target_year in [None, 2023]:
                wise_expenditures = [
                    {
                        'date': '2023-01-22',
                        'destination': 'Wise Card Fee',
                        'destination_original': 'For your Wise card',
                        'amount': 1200.00,
                        'category_id': 16,
                        'subcategory_id': 62,
                        'notes': 'Wise digital card order fee ($9.31 USD)',
                    },
                    {
                        'date': '2023-02-19',
                        'destination': 'Sri Lankan Airlines',
                        'destination_original': 'Sri Lankan Airlines Li',
                        'amount': 122190.00,
                        'category_id': 7,
                        'subcategory_id': 35,
                        'notes': 'Flight tickets paid via Wise USD balance ($915.36 USD)',
                    },
                    {
                        'date': '2023-03-19',
                        'destination': 'H.M sumanawathie',
                        'destination_original': 'H.M sumanawathie',
                        'amount': 39600.00,
                        'category_id': 16,
                        'subcategory_id': 75,
                        'notes': 'Family remittance sent from Wise USD balance ($300.00 USD / 100,524 LKR)',
                    },
                    {
                        'date': '2023-03-22',
                        'destination': 'Rajith Thennakoon (Sri Lanka)',
                        'destination_original': 'RAJITH THENNAKOON',
                        'amount': 32700.00,
                        'category_id': 16,
                        'subcategory_id': 75,
                        'notes': 'Personal remittance sent from Wise USD balance ($247.26 USD / 78,518 LKR)',
                    },
                ]
                wise_created = 0
                for exp_item in wise_expenditures:
                    t_obj, created = Transaction.objects.get_or_create(
                        account=wise_acc,
                        date=exp_item['date'],
                        destination=exp_item['destination'],
                        amount=exp_item['amount'],
                        defaults={
                            'destination_original': exp_item['destination_original'],
                            'category_id': exp_item['category_id'],
                            'subcategory_id': exp_item['subcategory_id'],
                            'is_expense': True,
                            'is_payment': True,
                            'is_income': False,
                            'is_saving': False,
                            'notes': exp_item['notes'],
                            'user_id': 1,
                        }
                    )
                    if created:
                        wise_created += 1
                self.stdout.write(f"4g-4. Verified Wise Account & direct USD expenditures ({wise_created} newly created)")

            # 4h-1. Dinesh Suduhakuruge - Outbound remittances / loan advances (Internet banking transfers OUT)
            dinesh_out = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='ネット') | Q(destination_original__icontains='ネツト') | Q(destination_original__icontains='スデュウ') | Q(destination_original__icontains='スデユ')
            ).filter(
                Q(destination_original__icontains='スデュウ') | Q(destination_original__icontains='スデユ') | Q(destination='Dinesh Suduhakuruge')
            ).exclude(
                destination_original__icontains='振込'
            ).exclude(id=2889)
            din_out_count = dinesh_out.count()
            if din_out_count > 0:
                dinesh_out.update(destination='Dinesh Suduhakuruge', category_id=16, subcategory_id=75, is_expense=True, is_payment=True, is_income=False)

            # 4h-2. Dinesh Suduhakuruge - Inbound loan repayments (Bank transfers IN: 振込)
            # Inflows returning borrowed money: must be is_income=True, is_expense=False, is_payment=False
            dinesh_in = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='振込') | Q(id=2889),
                Q(destination_original__icontains='スデュウ') | Q(destination_original__icontains='スデユ') | Q(destination__icontains='Dinesh') | Q(id=2889)
            )
            din_in_count = dinesh_in.count()
            if din_in_count > 0:
                dinesh_in.update(destination='Dinesh Suduhakuruge', category_id=16, subcategory_id=75, is_income=True, is_expense=False, is_payment=False)
            
            # Ensure ID 2889 specifically preserves correct description and flags
            Transaction.objects.filter(id=2889).update(
                destination_original='振込　スデュウ　ハクルゲ　デイネシユ',
                destination='Dinesh Suduhakuruge',
                is_income=True,
                is_expense=False,
                is_payment=False,
                category_id=16,
                subcategory_id=75
            )
            self.stdout.write(f"4h. Standardized Dinesh Suduhakuruge: {din_out_count} outbound remittances, {din_in_count} inbound repayments")

            # 4h-3. Inbound travel/merchant refunds (e.g. Agoda refunds into Mizuho)
            agoda_refunds = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='振込'),
                Q(destination_original__icontains='AGODA')
            )
            agoda_ref_count = agoda_refunds.count()
            if agoda_ref_count > 0:
                agoda_refunds.update(is_income=True, is_expense=False, is_payment=False)
                self.stdout.write(f"4h-3. Standardized inbound merchant refunds: {agoda_ref_count} records")

            # 4h-4. Nawaratna Mudiyanse - Personal loan advances & repayments
            nawaratna_out = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='ナワラトナ') | Q(destination__icontains='Nawaratna') | Q(id__in=[3030, 3081])
            ).filter(is_income=False)
            nawaratna_out.update(
                destination='Nawaratna Mudiyanse',
                category_id=16,
                subcategory_id=75,
                is_expense=True,
                is_payment=True,
                is_income=False
            )
            Transaction.objects.filter(id__in=[3030, 3081]).update(destination_original='ネツト　ナワラトナ　ムデイヤンセ…')

            nawaratna_in = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='ナワラトナ') | Q(destination__icontains='Nawaratna') | Q(id__in=[2900, 2907])
            ).filter(Q(destination_original__icontains='振込') | Q(id__in=[2900, 2907]))
            nawaratna_in.update(
                destination='Nawaratna Mudiyanse',
                category_id=16,
                subcategory_id=75,
                is_income=True,
                is_expense=False,
                is_payment=False
            )
            Transaction.objects.filter(id=2900).update(destination_original='振込　ナワラトナ　ムデイヤンセ…')
            Transaction.objects.filter(id=2907).update(destination_original='振込 ナワラトナ ムデイヤンセー…')
            self.stdout.write("4h-4. Standardized Nawaratna Mudiyanse: 2 outbound loans, 2 inbound repayments")

            # 4i. BMW Car Down Payment (Motoren Tomei Yokohama dealership)
            bmw_downpayment = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='モトーレン') | Q(destination_original__icontains='モトーレントウメイヨ') | Q(id__in=[3110, 3113])
            ).filter(is_income=False)
            bmw_down_count = bmw_downpayment.count()
            if bmw_down_count > 0:
                bmw_downpayment.update(
                    destination='BMW Car Payment',
                    category_id=2,
                    subcategory_id=5,
                    is_expense=True,
                    is_payment=True
                )
                Transaction.objects.filter(id__in=[3110, 3113]).update(destination_original='ネツト　カ）モトーレントウメイヨ…')
            self.stdout.write(f"4i. Standardized BMW Dealership Down Payments: {bmw_down_count} records")

            # 4j. Miscellaneous debits & friend remittances categorization
            # Kelagara Arachchilage (personal remittance)
            base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='ケラガラ') | Q(destination_original__icontains='１ロツク') | Q(destination__icontains='１ロツク') | Q(id__in=[3031, 3116])
            ).filter(is_income=False).exclude(id=2629).update(destination='Kelagara Arachchilage', category_id=16, subcategory_id=75, is_expense=True, is_payment=True, is_income=False)

            # Mohamed Najeeb (personal remittance)
            base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='モハメド') | Q(destination_original__icontains='コレンド') | Q(destination__icontains='コレンド') | Q(id=3117)
            ).filter(is_income=False).update(destination='Mohamed Najeeb', category_id=16, subcategory_id=75, is_expense=True, is_payment=True, is_income=False)

            # Astomos Retailing LP Gas (utility)
            base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='アストモス') | Q(destination_original__icontains='アステラスレステイング') | Q(destination__icontains='アステラスレステイング') | Q(id__in=[3075, 3105, 3124])
            ).filter(is_income=False).update(destination='Astomos Retailing (Gas)', category_id=4, subcategory_id=17, is_expense=True, is_payment=True, is_income=False)

            # Astellas Pharma (salary / company reimbursements)
            base_tx.filter(
                Q(destination_original__icontains='アステラスセイヤク') | Q(destination__icontains='アステラス製薬') | Q(id__in=[2290, 2453, 2642]),
                is_income=True
            ).update(destination='Astellas Pharma (Salary/Reimbursement)', category_id=17, subcategory_id=65, is_income=True, is_expense=False, is_payment=False)

            # ATM Late Night / Early Morning Surcharge Fee
            base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination_original__icontains='深夜早朝取扱') | Q(destination_original__icontains='メル早取扱') | Q(destination__icontains='メル早取扱') | Q(id=3155)
            ).update(destination='ATM Surcharge Fee', category_id=16, subcategory_id=62, is_expense=True, is_payment=True, is_income=False)

            # 5. Bank credit card bill settlements: ensure is_expense is False
            settlements = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                is_expense=True,
            ).filter(
                Q(destination__icontains='Card Payment')
                | Q(destination__in=['Rakuten Card Payment', 'EPOS Card Payment', 'Tokyu Card Payment', 'Docomo Card Payment'])
                | Q(destination_original__icontains='トウキユウ　カ')
                | Q(destination_original__icontains='トウキユウ　ｶ')
                | Q(destination_original__icontains='ラクテンカ')
                | Q(destination_original__icontains='エポスカ')
                | Q(destination_original__icontains='Ｄカード')
                | Q(destination_original__icontains='Ｄカ−ド')
            )
            settlement_count = settlements.count()
            if settlement_count > 0:
                settlements.update(is_expense=False, is_payment=True)
            self.stdout.write(f"5. Bank card settlements set to is_expense=False: {settlement_count} records")

            # 6. Savings / Securities transfers (outbound payments to Rakuten): ensure is_expense=False, is_saving=True, is_payment=True
            savings_tx = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                Q(destination='Rakuten Securities')
                | Q(destination_original__icontains='ラクテンシヨウケ')
                | Q(category_id=6)
                | Q(subcategory_id=28)
            ).filter(is_income=False).exclude(destination__icontains='Internal').filter(Q(is_expense=True) | Q(is_saving=False) | Q(is_payment=False))
            savings_count = savings_tx.count()
            if savings_count > 0:
                savings_tx.update(is_expense=False, is_saving=True, is_payment=True)
            self.stdout.write(f"6. Savings/Securities transfers set to is_expense=False, is_saving=True, is_payment=True: {savings_count} records")

            # 6b. Guard: Inbound deposits into bank account must NEVER be is_saving=True unless returning from an investment/savings account (Rakuten Securities)
            saving_inflow_count = base_tx.filter(is_income=True, is_saving=True).exclude(
                Q(counterparty_account__account_name__icontains='Rakuten Securities') |
                Q(counterparty_account_id=5) |
                Q(destination_original__icontains='ラクテンシヨウケン')
            ).count()
            if saving_inflow_count > 0:
                base_tx.filter(is_income=True, is_saving=True).exclude(
                    Q(counterparty_account__account_name__icontains='Rakuten Securities') |
                    Q(counterparty_account_id=5) |
                    Q(destination_original__icontains='ラクテンシヨウケン')
                ).update(is_saving=False)
                self.stdout.write(f"6b. Cleared is_saving=True from {saving_inflow_count} non-savings incoming deposit records")

            # 7. Bank direct living expenses: ensure is_expense is True
            bank_living = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
                is_expense=False,
                is_income=False,
                is_saving=False,
            ).filter(
                Q(destination__in=[
                    'Rent Payment', 'BMW Car Payment', 'SUV Land', 'Housing Center', 'Transfer Fee',
                    'Wise Remittance', 'Direct Debit', 'SMBC（レオパレス２１', 'Paidy', 'Dinesh Suduhakuruge',
                    '手数料', '振込手数料'
                ])
                | Q(destination__icontains='ヤチン')
                | Q(destination__icontains='家賃')
                | Q(destination_original__icontains='ヤチン')
                | Q(category__category_type=1)
            ).exclude(
                Q(destination__icontains='Card Payment')
                | Q(destination__in=['Rakuten Card Payment', 'EPOS Card Payment', 'Tokyu Card Payment', 'Docomo Card Payment'])
                | Q(destination_original__icontains='トウキユウ　カ')
                | Q(destination_original__icontains='トウキユウ　ｶ')
                | Q(destination_original__icontains='ラクテンカ')
                | Q(destination_original__icontains='エポスカ')
                | Q(destination_original__icontains='Ｄカード')
                | Q(destination_original__icontains='Ｄカ−ド')
                | Q(destination__icontains='Wise Transfer')
                | Q(destination__icontains='Wise Return')
                | Q(destination__icontains='JP Post Bank Transfer')
                | Q(destination__icontains='Internal Transfer')
                | Q(destination__icontains='On-behalf')
                | Q(is_third_party=True)
                | Q(category__category='Internal Transfer')
                | Q(category_id=internal_transfer_cat.id)
            )
            bank_living_count = bank_living.count()
            if bank_living_count > 0:
                bank_living.update(is_expense=True, is_payment=True)
            self.stdout.write(f"7. Bank direct living expenses set to is_expense=True: {bank_living_count} records")

            # 8. ATM Cash Withdrawals: ensure is_expense=True AND is_payment=True (Knowledge Section Rule)
            atm_withdrawals = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho'),
            ).filter(is_income=False).filter(
                Q(destination='ATM Withdrawal')
                | Q(destination__icontains='ATM')
                | Q(destination_original__icontains='ＡＴＭ')
                | Q(destination_original__icontains='７ＢＫ')
                | Q(destination='ゆうちょ銀行ATM提携')
            ).exclude(
                destination__icontains='手数料'
            ).exclude(
                destination='Cash Advance'
            ).exclude(
                destination__icontains='Internal'
            ).exclude(
                category__category='Internal Transfer'
            )
            atm_to_update = atm_withdrawals.filter(Q(is_expense=False) | Q(is_payment=False))
            atm_count = atm_to_update.count()
            if atm_count > 0:
                atm_to_update.update(is_expense=True, is_payment=True)
            self.stdout.write(f"8. ATM Cash Withdrawals updated to is_expense=True & is_payment=True: {atm_count} records")

            # 9. Automatic Counterparty Account Linking & Flag Harmonization
            self.stdout.write("\n=== 9. Automatic Counterparty Account Linking & Flag Harmonization ===")
            rak_sec_acc = Account.objects.filter(account_name__icontains='Rakuten Securities').first()
            jp_post_acc = Account.objects.filter(account_name__icontains='JP Post').first()
            wise_acc = Account.objects.filter(account_name__icontains='Wise').first()
            rak_card_acc = Account.objects.filter(account_name__icontains='Rakuten Card').first()
            epos_card_acc = Account.objects.filter(account_name__icontains='EPOS').first()
            docomo_card_acc = Account.objects.filter(account_name__icontains='Docomo').first()

            # 9a. Rakuten Securities Inbound Transfers (Returns to Bank: Inflow deposit, Internal Transfer & Savings return)
            base_tx.filter(
                Q(destination__icontains='Rakuten Securities Transfer (Internal)') |
                Q(destination_original__icontains='振込　ラクテンシヨウケン') |
                Q(destination_original__icontains='振込 ラクテンシヨウケン')
            ).update(
                counterparty_account=rak_sec_acc,
                category_id=internal_transfer_cat.id,
                subcategory_id=general_subcat.id,
                is_income=True,
                is_payment=False,
                is_expense=False,
                is_saving=True
            )

            # 9b. Rakuten Securities Outbound Investments (Savings debit exiting Bank)
            r_out = base_tx.filter(
                Q(destination__icontains='Rakuten Securities') | 
                Q(destination_original__icontains='ラクテンシヨウケン') |
                Q(destination__icontains='Rakuten Sec') |
                Q(subcategory_id=28, destination__icontains='Rakuten')
            ).exclude(
                Q(destination__icontains='Internal') |
                Q(destination_original__icontains='振込')
            )
            r_out.update(
                counterparty_account=rak_sec_acc,
                category_id=6,
                subcategory_id=28,
                is_saving=True,
                is_payment=True,
                is_income=False,
                is_expense=False
            )

            # 9c. JP Post Bank transfers (Inbound vs Outbound) - Bank accounts only (Mizuho <-> JP Post)
            jp_inflow = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho')
            ).filter(
                Q(destination__icontains='JP Post') | Q(destination_original__icontains='ユウチヨ') | Q(subcategory_id=81),
                Q(destination__icontains='Inflow') | Q(destination_original__icontains='振込')
            ).exclude(
                Q(destination__icontains='Postage') | Q(destination__icontains='EMS') | Q(destination__icontains='Post Office')
            )
            jp_inflow.update(
                counterparty_account=jp_post_acc,
                category_id=internal_transfer_cat.id,
                subcategory_id=jp_post_subcat.id,
                is_income=True,
                is_payment=False,
                is_expense=False,
                is_saving=False
            )

            jp_outflow = base_tx.filter(
                Q(account__account_type='BANK_ACCOUNT') | Q(account__account_name__icontains='Mizuho')
            ).filter(
                Q(destination__icontains='JP Post') | Q(destination_original__icontains='ユウチヨ') | Q(subcategory_id=81)
            ).exclude(
                Q(destination__icontains='Postage') | Q(destination__icontains='EMS') | Q(destination__icontains='Post Office') |
                Q(destination__icontains='Inflow') | Q(destination_original__icontains='振込')
            )
            jp_outflow.update(
                counterparty_account=jp_post_acc,
                category_id=internal_transfer_cat.id,
                subcategory_id=jp_post_subcat.id,
                is_income=False,
                is_payment=True,
                is_expense=False,
                is_saving=False
            )

            # 9c-2. Japan Post postal / package shipping on credit cards (ニツポンユウビン)
            base_tx.filter(
                account__account_type='CREDIT_CARD',
                destination_original__icontains='ニツポンユウビン'
            ).update(
                destination='Japan Post (Postal Service)',
                counterparty_account=None,
                category_id=16,
                subcategory_id=63,
                is_income=False,
                is_payment=False,
                is_expense=True,
                is_saving=False
            )

            # 9d. Wise transfers (Inbound vs Outbound)
            w_inflow = base_tx.filter(
                Q(destination__icontains='Wise Return') | Q(destination_original__icontains='ヒチナイドウ') |
                (Q(destination__icontains='Wise') & Q(destination_original__icontains='振込'))
            )
            w_inflow.update(
                counterparty_account=wise_acc,
                category_id=internal_transfer_cat.id,
                subcategory_id=wise_subcat.id,
                is_income=True,
                is_payment=False,
                is_expense=False,
                is_saving=False
            )

            w_outflow = base_tx.filter(
                Q(destination__icontains='Wise Transfer') | Q(subcategory_id=80)
            ).exclude(
                Q(destination__icontains='Return') | Q(destination_original__icontains='振込')
            )
            w_outflow.update(
                counterparty_account=wise_acc,
                category_id=internal_transfer_cat.id,
                subcategory_id=wise_subcat.id,
                is_income=False,
                is_payment=True,
                is_expense=False,
                is_saving=False
            )

            # 9e. Credit Card Bill Settlements (Bank debits paying card bills)
            if rak_card_acc:
                base_tx.filter(
                    Q(destination__icontains='Rakuten Card Payment') | Q(destination_original__icontains='ラクテンカード')
                ).update(counterparty_account=rak_card_acc, category_id=14, subcategory_id=60, is_payment=True, is_expense=False, is_income=False, is_saving=False)

            if epos_card_acc:
                base_tx.filter(
                    Q(destination__icontains='EPOS Card Payment') | Q(destination_original__icontains='エポス')
                ).update(counterparty_account=epos_card_acc, category_id=14, subcategory_id=60, is_payment=True, is_expense=False, is_income=False, is_saving=False)

            if docomo_card_acc:
                base_tx.filter(
                    Q(destination__icontains='Docomo Card Payment') | Q(destination_original__icontains='ドコモ')
                ).update(counterparty_account=docomo_card_acc, category_id=14, subcategory_id=60, is_payment=True, is_expense=False, is_income=False, is_saving=False)

            self.stdout.write("9. Successfully linked counterparties and harmonized flags.")

            # Calculate projected balances
            self.stdout.write("\n=== Projected Year Balances (Active Data) ===")
            years_to_show = [target_year] if target_year else [2023, 2024, 2025, 2026]
            for yr in years_to_show:
                qs = Transaction.objects.filter(is_deleted=False, date__year=yr)
                # Gross income excludes internal transfers to reflect genuine earned income / take-home
                inc = float(qs.filter(is_income=True).exclude(category_id=internal_transfer_cat.id).aggregate(s=Sum('amount'))['s'] or 0)
                exp = float(qs.filter(is_expense=True, is_saving=False).aggregate(s=Sum('amount'))['s'] or 0)
                pay = float(qs.filter(account__account_type='BANK_ACCOUNT', is_payment=True).aggregate(s=Sum('amount'))['s'] or 0)
                sav_out = float(qs.filter(is_saving=True, is_payment=True).aggregate(s=Sum('amount'))['s'] or 0)
                sav_in = float(qs.filter(is_saving=True, is_income=True).aggregate(s=Sum('amount'))['s'] or 0)
                sav = sav_out - sav_in
                surplus = inc - exp
                rate = round((surplus / inc * 100), 1) if inc > 0 else 0.0
                self.stdout.write(
                    f"Year {yr}: Gross Income: ¥{inc:,.0f} | Living Expenses: ¥{exp:,.0f} | "
                    f"Op. Surplus: ¥{surplus:,.0f} ({rate}%) | Bank Debits: ¥{pay:,.0f} | Net Savings: ¥{sav:,.0f}"
                )

            if dry_run:
                self.stdout.write(self.style.WARNING("\nDry run complete. Rolling back transaction."))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS("\nAll updates successfully committed to the database."))
