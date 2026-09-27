from django.conf import settings
from django.db import models

from oauth.middleware import get_current_user
from oauth.util.request_manager import RequestManager


class CompanyProfile(models.Model):
    """
    Represents a company entity (Direct Employer, Staffing/Dispatch Agency, or Dispatched Client/Host).
    """
    COMPANY_TYPES = (
        ('direct_employer', 'Direct Employer (自社 / 直接雇用)'),
        ('dispatch_agency', 'Dispatch / Staffing Agency / SES Vendor (派遣元 / SES企業)'),
        ('client_host', 'Dispatched Client / Host Company (派遣先 / 常駐先 / 出向先)'),
        ('other', 'Other Company / Organization (その他)'),
    )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, help_text="Company Legal or Operating Name (e.g. Rakuten Group, Inc.)")
    name_local = models.CharField(max_length=255, blank=True, null=True, help_text="Local / Native Name (e.g. 楽天グループ株式会社)")
    short_name = models.CharField(max_length=100, blank=True, null=True, help_text="Display or Short Name (e.g. Rakuten)")
    company_type = models.CharField(max_length=30, choices=COMPANY_TYPES, default='direct_employer')
    industry = models.CharField(max_length=120, blank=True, null=True, help_text="e.g. FinTech, IT Services, Automotive")
    website = models.URLField(max_length=255, blank=True, null=True)
    headquarters = models.CharField(max_length=255, blank=True, null=True, help_text="City / Country (e.g. Tokyo, Japan)")
    corporate_number = models.CharField(max_length=50, blank=True, null=True, help_text="法人番号 (Corporate Number) or Tax ID")
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    logo_image = models.FileField(upload_to='company_logos/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    class Meta:
        db_table = 'career_company_profile'
        verbose_name = 'Company Profile'
        verbose_name_plural = 'Company Profiles'
        ordering = ['name']

    def __str__(self):
        return self.short_name or self.name

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        if self.company_type == 'direct':
            self.company_type = 'direct_employer'
        elif self.company_type in ('client', 'contractor'):
            self.company_type = 'client_host'
        super().save(*args, **kwargs)


class Employment(models.Model):
    """
    Represents an employment tenure with an employer entity (legal contract and payroll issuer).
    """
    EMPLOYMENT_TYPES = (
        ('full_time', 'Full-time Regular (正社員)'),
        ('contract', 'Contract / Fixed-term (契約社員)'),
        ('dispatched', 'Dispatched Worker (派遣社員)'),
        ('ses_subcontract', 'SES / Subcontract (業務委託 / SES)'),
        ('part_time', 'Part-time (パート / アルバイト)'),
        ('internship', 'Internship (インターン)'),
        ('freelance', 'Freelance / Sole Proprietor (フリーランス / 個人事業主)'),
    )

    SALARY_FREQUENCIES = (
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
        ('hourly', 'Hourly'),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.PROTECT,
        related_name='employments',
        help_text="The legal employer / payroll provider (e.g. Staffing Agency, Direct Company)"
    )
    job_title = models.CharField(max_length=255, help_text="e.g. Senior Software Engineer, Technical Consultant")
    department = models.CharField(max_length=255, blank=True, null=True)
    employment_type = models.CharField(max_length=30, choices=EMPLOYMENT_TYPES, default='full_time')

    # Flag indicating whether this role involves being dispatched / assigned to client companies
    is_dispatched = models.BooleanField(
        default=False,
        help_text="True if this employment involves client dispatches (派遣), SES, or client onsite assignments"
    )

    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    work_location = models.CharField(max_length=255, blank=True, null=True, help_text="e.g. Tokyo, Japan / Hybrid")

    responsibilities = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    class Meta:
        db_table = 'career_employment'
        verbose_name = 'Employment Record'
        verbose_name_plural = 'Employment Records'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.job_title} at {self.company.name} ({self.start_date} - {'Current' if self.is_current else self.end_date})"

    @property
    def current_compensation(self):
        """Returns the latest compensation revision record, if any."""
        return self.compensation_history.order_by('-effective_date').first()

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)


class CompensationHistory(models.Model):
    """
    Tracks multi-year compensation revisions, annual raises, promotions, and starting offers.
    """
    REVISION_TYPES = (
        ('initial_offer', 'Initial Offer (入社時提示額)'),
        ('annual_raise', 'Annual Review / Raise (定期昇給 / ベースアップ)'),
        ('promotion', 'Promotion (昇格 / 役職手当)'),
        ('adjustment', 'Market / Inflation Adjustment (給与改定)'),
        ('other', 'Other Revision (その他)'),
    )

    SALARY_FREQUENCIES = (
        ('monthly', 'Monthly (月給)'),
        ('annual', 'Annual (年俸)'),
        ('hourly', 'Hourly (時給)'),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    employment = models.ForeignKey(
        Employment,
        on_delete=models.CASCADE,
        related_name='compensation_history',
        help_text="The employment tenure this compensation applies to"
    )
    effective_date = models.DateField(help_text="Date this compensation revision took effect (e.g. 2023-04-01)")
    revision_type = models.CharField(max_length=30, choices=REVISION_TYPES, default='annual_raise')
    base_salary = models.DecimalField(max_digits=14, decimal_places=2, help_text="Base salary amount")
    allowances = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Total fixed allowances (e.g. sum of housing, discretionary overtime, commuting, etc.)"
    )
    housing_allowance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Housing allowance / 家賃補助 / 住宅手当"
    )
    discretionary_allowance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Discretionary work or Minashi fixed overtime allowance / 裁量労働手当 / 固定残業代"
    )
    commuting_allowance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Commuting allowance / 通勤手当"
    )
    remote_work_allowance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Remote work / Telework allowance / 在宅勤務手当"
    )
    role_allowance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Role / Management allowance / 役職手当"
    )
    other_allowances = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Other fixed allowances / その他手当"
    )
    allowances_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Breakdown of fixed allowances (e.g. Housing ¥50k, Discretionary overtime ¥80k)"
    )
    salary_frequency = models.CharField(max_length=20, choices=SALARY_FREQUENCIES, default='monthly')
    currency = models.CharField(max_length=10, default='JPY')
    bonus_expected = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="Annual or per-cycle expected bonus")
    bonus_notes = models.TextField(blank=True, null=True, help_text="e.g. 2x annual bonus (June / December) or incentive scheme")
    notes = models.TextField(blank=True, null=True, help_text="e.g. Promoted to Senior Lead (+12% raise)")

    @property
    def total_monthly_guaranteed(self):
        """Monthly guaranteed pay = base salary + fixed allowances (normalized to monthly)"""
        base = float(self.base_salary or 0)
        allow = float(self.allowances or 0)
        if self.salary_frequency == 'monthly':
            return base + allow
        elif self.salary_frequency == 'annual':
            return (base + allow) / 12.0
        return base + allow

    @property
    def annual_base_guaranteed(self):
        """Annual guaranteed base (固定年俸 / Base + Allowances * 12)"""
        base = float(self.base_salary or 0)
        allow = float(self.allowances or 0)
        if self.salary_frequency == 'monthly':
            return (base + allow) * 12.0
        elif self.salary_frequency == 'annual':
            return base + allow
        return (base + allow) * 12.0

    @property
    def total_annual_expected(self):
        """Total expected annual package (総年収 / OTE) = (Base + Allowances) * 12 + Annual Bonus"""
        bonus = float(self.bonus_expected or 0)
        return self.annual_base_guaranteed + bonus

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    class Meta:
        db_table = 'career_compensation_history'
        verbose_name = 'Compensation Revision'
        verbose_name_plural = 'Compensation Revisions'
        ordering = ['-effective_date']

    def __str__(self):
        return f"{self.employment.company.name} - {self.effective_date}: {self.currency} {self.base_salary:,.0f} ({self.get_revision_type_display()})"

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()

        # Auto-compute allowances if itemized allowances are entered
        itemized = (
            float(self.housing_allowance or 0) +
            float(self.discretionary_allowance or 0) +
            float(self.commuting_allowance or 0) +
            float(self.remote_work_allowance or 0) +
            float(self.role_allowance or 0) +
            float(self.other_allowances or 0)
        )
        if itemized > 0:
            self.allowances = itemized

        super().save(*args, **kwargs)


class DispatchAssignment(models.Model):
    """
    Tracks dispatched company assignments (dispatched company, start date, end date, is_current).
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    employment = models.ForeignKey(
        Employment,
        on_delete=models.CASCADE,
        related_name='dispatch_assignments',
        help_text="The parent employment record with the employer / dispatch agency"
    )
    dispatched_company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.PROTECT,
        related_name='dispatches',
        help_text="The company dispatched to"
    )
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    class Meta:
        db_table = 'career_dispatch_assignment'
        verbose_name = 'Dispatch Assignment'
        verbose_name_plural = 'Dispatch Assignments'
        ordering = ['-start_date']

    def __str__(self):
        return f"Dispatched to {self.dispatched_company.name} ({self.start_date} - {'Current' if self.is_current else self.end_date})"

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)


class CareerDocument(models.Model):
    """
    Pure Document Vault for career-related files: offer letters, employment contracts,
    leaving certificates, NDAs, payslip PDFs, tax slip PDFs, visas, etc.
    """
    DOCUMENT_TYPES = (
        ('offer_letter', 'Offer Letter (内定通知書 / 採用通知書)'),
        ('employment_contract', 'Employment Contract / Terms (雇用契約書 / 労働条件通知書)'),
        ('leaving_certificate', 'Leaving Certificate / Separation (離職票 / 退職証明書)'),
        ('resignation_acceptance', 'Resignation Acceptance (退職届控 / 退職合意書)'),
        ('nda', 'NDA / Non-Disclosure Agreement (秘密保持誓約書)'),
        ('appraisal', 'Appraisal / Performance Review (人事評価・査定書)'),
        ('recommendation', 'Certificate of Employment / Recommendation (在職証明書 / 推薦状)'),
        ('visa_document', 'Visa Sponsorship Document (就労ビザ関連書類)'),
        ('payslip_pdf', 'Monthly Payslip PDF (給与明細書)'),
        ('bonus_slip_pdf', 'Bonus Statement PDF (賞与明細書)'),
        ('tax_slip_pdf', 'Withholding Tax Slip PDF (源泉徴収票)'),
        ('other', 'Other Document (その他)'),
    )

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='documents',
        help_text="Company relevant to this document"
    )
    employment = models.ForeignKey(
        Employment,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='documents',
        help_text="Employment tenure associated with this document"
    )
    dispatch_assignment = models.ForeignKey(
        DispatchAssignment,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='documents',
        help_text="Optional: specific dispatch client assignment this document relates to"
    )

    document_type = models.CharField(max_length=40, choices=DOCUMENT_TYPES, default='other')
    title = models.CharField(max_length=255, help_text="e.g. 2024-05 Salary Statement, Offer Letter")
    file = models.FileField(upload_to='career_docs/%Y/%m/')
    file_name_original = models.CharField(max_length=255, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True, help_text="File size in bytes")
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    issue_date = models.DateField(blank=True, null=True, help_text="Date document was issued")
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    class Meta:
        db_table = 'career_document'
        verbose_name = 'Career Document'
        verbose_name_plural = 'Career Documents'
        ordering = ['-issue_date', '-created_at']

    def __str__(self):
        return f"{self.get_document_type_display()}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        if self.employment and not self.company:
            self.company = self.employment.company
        super().save(*args, **kwargs)

    @property
    def file_url(self):
        if not self.file or not self.file.name:
            return None
        name = str(self.file.name)
        if name.startswith('/media/local:/') or name.startswith('/media/local://'):
            clean_path = name.split('local:', 1)[-1].lstrip('/')
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            return f"{media_url}{clean_path}"
        if name.startswith('local://') or name.startswith('local:/'):
            clean_path = name.split('local:', 1)[-1].lstrip('/')
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            return f"{media_url}{clean_path}"
        if name.startswith('gs://'):
            try:
                from finance.career.services.storage_service import generate_signed_url
                return generate_signed_url(name, self.user_id, self.user)
            except Exception:
                return f"https://storage.googleapis.com/{name[5:]}"
        if name.startswith('http://') or name.startswith('https://'):
            return name
        try:
            return self.file.url
        except Exception:
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            return f"{media_url}{name.lstrip('/')}"


class MonthlyPayslip(models.Model):
    """
    Structured Monthly Payroll & Deduction Breakdown.
    Tracks earnings, allowances, social insurance, national/local taxes, year-end adjustments,
    miscellaneous deductions, net take-home, attendance/hours, YTD totals, and standard remuneration brackets.
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    employment = models.ForeignKey(
        Employment,
        on_delete=models.CASCADE,
        related_name='payslips',
        help_text="Employment tenure this payslip belongs to"
    )
    document = models.ForeignKey(
        CareerDocument,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='payslip_record',
        help_text="Optional linked scanned PDF/image in the vault"
    )

    year = models.IntegerField(help_text="Payroll year e.g. 2025")
    month = models.IntegerField(help_text="Payroll month (1-12)")
    is_bonus = models.BooleanField(default=False, help_text="True if this is a separate seasonal/special bonus statement")
    payment_date = models.DateField(blank=True, null=True, help_text="Payday date e.g. 2025-10-25")
    pay_period_start = models.DateField(blank=True, null=True, help_text="Pay period start date")
    pay_period_end = models.DateField(blank=True, null=True, help_text="Pay period end date")

    # 1. Earnings Breakdown
    base_salary = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Base / Job pay")
    housing_allowance = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Housing / Rent allowance")
    discretionary_allowance = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Discretionary work allowance")
    remote_work_allowance = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Remote / Telework allowance")
    commutation_allowance = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Commuting allowance")
    overtime_pay = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Overtime / Early-overtime pay")
    late_night_overtime_pay = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Late night shift allowance")
    holiday_work_pay = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Holiday work pay")
    special_allowance = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Special / Role allowance")
    other_allowances = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Other miscellaneous allowances")
    other_allowances_description = models.CharField(max_length=255, blank=True, null=True, help_text="Description or breakdown of other allowances")
    gross_pay = models.DecimalField(max_digits=14, decimal_places=2, help_text="Total Gross Pay")

    # 2. Social Insurance Deductions
    health_insurance = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Health insurance")
    nursing_insurance = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Nursing care insurance (age 40+)")
    pension = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Welfare pension insurance")
    employment_insurance = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Employment insurance")
    social_insurance_total = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Total social insurance deductions")

    # 3. Taxes & Adjustments
    taxable_amount = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="Taxable base amount for withholding")
    income_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="National income tax withheld")
    resident_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Local inhabitant / resident tax")
    year_end_tax_adjustment = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Year-end tax adjustment (+ deduction or - refund)")
    total_tax = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Total taxes withheld")

    # 4. Other / Miscellaneous Deductions
    union_fee = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Labor union dues")
    mutual_aid_fee = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Mutual aid / benefit society fee")
    meal_deduction = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Cafeteria / meal deduction")
    other_deductions = models.DecimalField(max_digits=14, decimal_places=2, default=0, help_text="Other miscellaneous deductions")
    other_deductions_description = models.CharField(max_length=255, blank=True, null=True, help_text="Description or breakdown of other deductions")
    total_deductions = models.DecimalField(max_digits=14, decimal_places=2, help_text="Total gross deductions")

    # 5. Net Take-Home & Bank Transfer
    net_pay = models.DecimalField(max_digits=14, decimal_places=2, help_text="Net take-home pay")
    bank_transfer_amount = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="Actual deposit into bank account")
    bank_name = models.CharField(max_length=100, blank=True, null=True, help_text="Deposit bank name e.g. Mizuho")
    bank_account = models.CharField(max_length=50, blank=True, null=True, help_text="Deposit bank account number e.g. 3016702")
    currency = models.CharField(max_length=10, default='JPY')

    # 6. Attendance & Hours
    working_days = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="Working / payable days")
    total_work_hours = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Total base work hours (e.g. 160.0)")
    overtime_hours = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Overtime / early-overtime hours")
    late_night_hours = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Late night hours")
    holiday_work_hours = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, help_text="Holiday work hours")
    absent_days = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="Absent / unworked days")
    loss_of_pay_days = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="LOP (Loss of pay) days")
    paid_leave_days_used = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="Paid leave days taken")
    remaining_paid_leave_days = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True, help_text="Remaining annual paid leave balance")

    # 7. Standard Monthly Remuneration (標準報酬月額 brackets)
    std_remuneration_health = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="Health insurance standard monthly remuneration")
    std_remuneration_pension = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="Welfare pension standard monthly remuneration")

    # 8. YTD Cumulative Totals (reported on payslips)
    ytd_gross_pay = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="Year-to-date gross / taxable payment total")
    ytd_social_insurance = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="Year-to-date social insurance deductions total")
    ytd_income_tax = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="Year-to-date income tax deductions total")

    # 9. Notes
    notes = models.TextField(blank=True, null=True, help_text="Communication notes or comments")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    class Meta:
        db_table = 'career_monthly_payslip'
        verbose_name = 'Monthly Payslip'
        verbose_name_plural = 'Monthly Payslips'
        ordering = ['-year', '-month']
        unique_together = ('employment', 'year', 'month', 'is_bonus')

    def __str__(self):
        bonus_flag = " (Bonus)" if self.is_bonus else ""
        return f"{self.employment.company.name} - {self.year}/{self.month:02d}{bonus_flag}: Net {self.currency} {self.net_pay:,.0f}"

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()

        # Auto-compute social insurance total if omitted
        calc_social = (self.health_insurance or 0) + (self.nursing_insurance or 0) + (self.pension or 0) + (self.employment_insurance or 0)
        if not self.social_insurance_total:
            self.social_insurance_total = calc_social

        # Auto-compute tax total if omitted (including year-end adjustment)
        calc_tax = (self.income_tax or 0) + (self.resident_tax or 0) + (self.year_end_tax_adjustment or 0)
        if not self.total_tax:
            self.total_tax = calc_tax

        # Auto-compute gross pay if omitted
        if not self.gross_pay:
            self.gross_pay = (
                (self.base_salary or 0)
                + (self.housing_allowance or 0)
                + (self.discretionary_allowance or 0)
                + (self.remote_work_allowance or 0)
                + (self.commutation_allowance or 0)
                + (self.overtime_pay or 0)
                + (self.late_night_overtime_pay or 0)
                + (self.holiday_work_pay or 0)
                + (self.special_allowance or 0)
                + (self.other_allowances or 0)
            )

        # Auto-compute other deductions total if union, mutual aid, meal etc are specified
        calc_other_ded = (self.union_fee or 0) + (self.mutual_aid_fee or 0) + (self.meal_deduction or 0) + (self.other_deductions or 0)

        calc_deductions = self.social_insurance_total + self.total_tax + calc_other_ded
        if not self.total_deductions:
            self.total_deductions = calc_deductions

        if not self.net_pay and self.gross_pay is not None:
            self.net_pay = (self.gross_pay or 0) - self.total_deductions

        if not self.bank_transfer_amount and self.net_pay is not None:
            self.bank_transfer_amount = self.net_pay

        super().save(*args, **kwargs)


class TaxWithholdingSlip(models.Model):
    """
    Annual Withholding Tax Certificate (源泉徴収票 / Gensen-Choshu-Hyo).
    Matches the official National Tax Agency (国税庁) annual statement 1-to-1.
    """
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    employment = models.ForeignKey(
        Employment,
        on_delete=models.CASCADE,
        related_name='tax_slips',
        help_text="Employment tenure this annual tax slip belongs to"
    )
    document = models.ForeignKey(
        CareerDocument,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='tax_slip_record',
        help_text="Optional linked scanned Gensen-Choshu-Hyo PDF in the vault"
    )

    tax_year = models.IntegerField(help_text="Tax Year e.g. 2024 (令和6年)")
    issue_date = models.DateField(blank=True, null=True, help_text="Date issued (typically December or retirement)")

    # Official Japanese Box Values
    total_payment = models.DecimalField(max_digits=14, decimal_places=2, help_text="支払金額 (Total Annual Gross Pay before deductions)")
    income_after_deduction = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="給与所得控除後の金額 (Income after salary earner deduction)")
    total_income_deductions = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="所得控除の額の合計額 (Total allowable deductions)")
    withholding_tax = models.DecimalField(max_digits=14, decimal_places=2, help_text="源泉徴収税額 (Final National Income Tax withheld)")

    # Detailed Deduction Breakdown
    social_insurance_deduction = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="社会保険料等の金額 (Annual social insurance paid)")
    life_insurance_deduction = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="生命保険料の控除額")
    earthquake_insurance_deduction = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="地震保険料の控除額")
    housing_loan_deduction = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="住宅借入金等特別控除の額 (Mortgage tax credit)")
    basic_deduction = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="基礎控除の額")
    spouse_deduction = models.DecimalField(max_digits=14, decimal_places=2, blank=True, null=True, help_text="配偶者(特別)控除の額")
    dependents_count = models.IntegerField(default=0, help_text="扶養親族の数")
    currency = models.CharField(max_length=10, default='JPY')

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = RequestManager()

    class Meta:
        db_table = 'career_tax_withholding_slip'
        verbose_name = 'Withholding Tax Slip (源泉徴収票)'
        verbose_name_plural = 'Withholding Tax Slips (源泉徴収票)'
        ordering = ['-tax_year']
        unique_together = ('employment', 'tax_year')

    def __str__(self):
        return f"{self.employment.company.name} - {self.tax_year} 源泉徴収票: Gross {self.currency} {self.total_payment:,.0f} (Tax {self.currency} {self.withholding_tax:,.0f})"

    def save(self, *args, **kwargs):
        if not self.user:
            self.user = get_current_user()
        super().save(*args, **kwargs)
