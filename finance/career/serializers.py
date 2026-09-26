from rest_framework import serializers
from finance.career.models import (
    CompanyProfile,
    Employment,
    DispatchAssignment,
    CareerDocument,
    CompensationHistory,
    MonthlyPayslip,
    TaxWithholdingSlip,
)


class CompanyProfileSerializer(serializers.ModelSerializer):
    company_type_display = serializers.CharField(source='get_company_type_display', read_only=True)
    employments_count = serializers.SerializerMethodField()
    client_dispatches_count = serializers.SerializerMethodField()

    class Meta:
        model = CompanyProfile
        fields = [
            'id',
            'name',
            'name_local',
            'short_name',
            'company_type',
            'company_type_display',
            'industry',
            'website',
            'headquarters',
            'corporate_number',
            'logo_url',
            'logo_image',
            'description',
            'is_active',
            'employments_count',
            'client_dispatches_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_employments_count(self, obj):
        return obj.employments.count()

    def get_client_dispatches_count(self, obj):
        return obj.dispatches.count()

    def to_internal_value(self, data):
        data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'company_type' in data:
            mapping = {
                'direct': 'direct_employer',
                'client': 'client_host',
                'contractor': 'client_host',
                'dispatch': 'dispatch_agency',
                'agency': 'dispatch_agency',
            }
            data['company_type'] = mapping.get(data['company_type'], data['company_type'])
        return super().to_internal_value(data)

    def validate_company_type(self, value):
        valid_choices = [c[0] for c in CompanyProfile.COMPANY_TYPES]
        if value not in valid_choices:
            raise serializers.ValidationError(f'"{value}" is not a valid choice.')
        return value


class DispatchAssignmentSerializer(serializers.ModelSerializer):
    dispatched_company_name = serializers.CharField(source='dispatched_company.name', read_only=True)
    dispatched_company_short_name = serializers.CharField(source='dispatched_company.short_name', read_only=True)
    dispatched_company_logo = serializers.SerializerMethodField()
    employer_company_name = serializers.CharField(source='employment.company.name', read_only=True)

    class Meta:
        model = DispatchAssignment
        fields = [
            'id',
            'employment',
            'dispatched_company',
            'dispatched_company_name',
            'dispatched_company_short_name',
            'dispatched_company_logo',
            'employer_company_name',
            'start_date',
            'end_date',
            'is_current',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_dispatched_company_logo(self, obj):
        if obj.dispatched_company.logo_image:
            return obj.dispatched_company.logo_image.url
        return obj.dispatched_company.logo_url


class CareerDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = CareerDocument
        fields = [
            'id',
            'company',
            'company_name',
            'employment',
            'dispatch_assignment',
            'document_type',
            'document_type_display',
            'title',
            'file',
            'file_url',
            'file_name_original',
            'file_size',
            'mime_type',
            'issue_date',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None


class CompensationHistorySerializer(serializers.ModelSerializer):
    revision_type_display = serializers.CharField(source='get_revision_type_display', read_only=True)
    salary_frequency_display = serializers.CharField(source='get_salary_frequency_display', read_only=True)
    company_name = serializers.CharField(source='employment.company.name', read_only=True)
    job_title = serializers.CharField(source='employment.job_title', read_only=True)
    total_monthly_guaranteed = serializers.FloatField(read_only=True)
    annual_base_guaranteed = serializers.FloatField(read_only=True)
    total_annual_expected = serializers.FloatField(read_only=True)

    class Meta:
        model = CompensationHistory
        fields = [
            'id',
            'employment',
            'company_name',
            'job_title',
            'effective_date',
            'revision_type',
            'revision_type_display',
            'base_salary',
            'allowances',
            'housing_allowance',
            'discretionary_allowance',
            'commuting_allowance',
            'remote_work_allowance',
            'role_allowance',
            'other_allowances',
            'allowances_notes',
            'salary_frequency',
            'salary_frequency_display',
            'currency',
            'bonus_expected',
            'bonus_notes',
            'total_monthly_guaranteed',
            'annual_base_guaranteed',
            'total_annual_expected',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'total_monthly_guaranteed',
            'annual_base_guaranteed',
            'total_annual_expected',
        ]


class MonthlyPayslipSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='employment.company.name', read_only=True)
    job_title = serializers.CharField(source='employment.job_title', read_only=True)
    document_file_url = serializers.SerializerMethodField()
    document_title = serializers.CharField(source='document.title', read_only=True)

    class Meta:
        model = MonthlyPayslip
        fields = [
            'id',
            'employment',
            'company_name',
            'job_title',
            'document',
            'document_title',
            'document_file_url',
            'year',
            'month',
            'is_bonus',
            'payment_date',
            'pay_period_start',
            'pay_period_end',
            # Earnings
            'base_salary',
            'housing_allowance',
            'discretionary_allowance',
            'remote_work_allowance',
            'commutation_allowance',
            'overtime_pay',
            'late_night_overtime_pay',
            'holiday_work_pay',
            'special_allowance',
            'other_allowances',
            'gross_pay',
            # Social Insurance
            'health_insurance',
            'nursing_insurance',
            'pension',
            'employment_insurance',
            'social_insurance_total',
            # Tax & Adjustments
            'taxable_amount',
            'income_tax',
            'resident_tax',
            'year_end_tax_adjustment',
            'total_tax',
            # Other Deductions
            'union_fee',
            'mutual_aid_fee',
            'meal_deduction',
            'other_deductions',
            'total_deductions',
            # Net & Bank Transfer
            'net_pay',
            'bank_transfer_amount',
            'bank_name',
            'bank_account',
            'currency',
            # Work metrics & Attendance
            'working_days',
            'total_work_hours',
            'overtime_hours',
            'late_night_hours',
            'holiday_work_hours',
            'absent_days',
            'loss_of_pay_days',
            'paid_leave_days_used',
            'remaining_paid_leave_days',
            # Standard Remuneration
            'std_remuneration_health',
            'std_remuneration_pension',
            # YTD Cumulative
            'ytd_gross_pay',
            'ytd_social_insurance',
            'ytd_income_tax',
            # Notes & timestamps
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_document_file_url(self, obj):
        if obj.document and obj.document.file:
            return obj.document.file.url
        return None


class TaxWithholdingSlipSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='employment.company.name', read_only=True)
    document_file_url = serializers.SerializerMethodField()
    document_title = serializers.CharField(source='document.title', read_only=True)

    class Meta:
        model = TaxWithholdingSlip
        fields = [
            'id',
            'employment',
            'company_name',
            'document',
            'document_title',
            'document_file_url',
            'tax_year',
            'issue_date',
            # Japanese Box Values
            'total_payment',
            'income_after_deduction',
            'total_income_deductions',
            'withholding_tax',
            # Detailed Deductions
            'social_insurance_deduction',
            'life_insurance_deduction',
            'earthquake_insurance_deduction',
            'housing_loan_deduction',
            'basic_deduction',
            'spouse_deduction',
            'dependents_count',
            'currency',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_document_file_url(self, obj):
        if obj.document and obj.document.file:
            return obj.document.file.url
        return None


class EmploymentSerializer(serializers.ModelSerializer):
    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_short_name = serializers.CharField(source='company.short_name', read_only=True)
    company_logo = serializers.SerializerMethodField()
    dispatch_assignments = DispatchAssignmentSerializer(many=True, read_only=True)
    compensation_history = CompensationHistorySerializer(many=True, read_only=True)
    current_compensation = serializers.SerializerMethodField()
    documents_count = serializers.SerializerMethodField()
    payslips_count = serializers.SerializerMethodField()
    tax_slips_count = serializers.SerializerMethodField()

    class Meta:
        model = Employment
        fields = [
            'id',
            'company',
            'company_name',
            'company_short_name',
            'company_logo',
            'job_title',
            'department',
            'employment_type',
            'employment_type_display',
            'is_dispatched',
            'start_date',
            'end_date',
            'is_current',
            'work_location',
            'responsibilities',
            'notes',
            'dispatch_assignments',
            'compensation_history',
            'current_compensation',
            'documents_count',
            'payslips_count',
            'tax_slips_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_company_logo(self, obj):
        if obj.company.logo_image:
            return obj.company.logo_image.url
        return obj.company.logo_url

    def get_current_compensation(self, obj):
        latest = obj.current_compensation
        if latest:
            return CompensationHistorySerializer(latest).data
        return None

    def get_documents_count(self, obj):
        return obj.documents.count()

    def get_payslips_count(self, obj):
        return obj.payslips.count()

    def get_tax_slips_count(self, obj):
        return obj.tax_slips.count()
