from django.contrib import admin
from finance.career.models import (
    CompanyProfile,
    Employment,
    DispatchAssignment,
    CareerDocument,
    CompensationHistory,
    MonthlyPayslip,
    TaxWithholdingSlip,
)


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'company_type', 'industry', 'headquarters', 'is_active')
    list_filter = ('company_type', 'is_active', 'industry')
    search_fields = ('name', 'name_local', 'short_name', 'corporate_number')


class CompensationHistoryInline(admin.TabularInline):
    model = CompensationHistory
    extra = 0
    fk_name = 'employment'


class DispatchAssignmentInline(admin.TabularInline):
    model = DispatchAssignment
    extra = 0
    fk_name = 'employment'


class MonthlyPayslipInline(admin.TabularInline):
    model = MonthlyPayslip
    extra = 0
    fk_name = 'employment'
    fields = ('year', 'month', 'is_bonus', 'gross_pay', 'social_insurance_total', 'total_tax', 'net_pay')


class TaxWithholdingSlipInline(admin.TabularInline):
    model = TaxWithholdingSlip
    extra = 0
    fk_name = 'employment'
    fields = ('tax_year', 'total_payment', 'income_after_deduction', 'total_income_deductions', 'withholding_tax')


class CareerDocumentInline(admin.TabularInline):
    model = CareerDocument
    extra = 0
    fk_name = 'employment'


@admin.register(Employment)
class EmploymentAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'company', 'employee_id', 'work_email', 'employment_type', 'is_dispatched', 'start_date', 'end_date', 'is_current')
    list_filter = ('employment_type', 'is_dispatched', 'is_current')
    search_fields = ('job_title', 'company__name', 'department', 'employee_id', 'work_email')
    inlines = [CompensationHistoryInline, DispatchAssignmentInline, MonthlyPayslipInline, TaxWithholdingSlipInline, CareerDocumentInline]


@admin.register(CompensationHistory)
class CompensationHistoryAdmin(admin.ModelAdmin):
    list_display = ('employment', 'effective_date', 'revision_type', 'base_salary', 'salary_frequency', 'currency', 'bonus_expected')
    list_filter = ('revision_type', 'salary_frequency', 'currency')
    search_fields = ('employment__company__name', 'employment__job_title', 'notes')


@admin.register(DispatchAssignment)
class DispatchAssignmentAdmin(admin.ModelAdmin):
    list_display = ('dispatched_company', 'employment', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)
    search_fields = ('dispatched_company__name', 'employment__company__name')


@admin.register(MonthlyPayslip)
class MonthlyPayslipAdmin(admin.ModelAdmin):
    list_display = ('employment', 'year', 'month', 'is_bonus', 'gross_pay', 'social_insurance_total', 'total_tax', 'net_pay', 'currency', 'payment_date')
    list_filter = ('year', 'is_bonus')
    search_fields = ('employment__company__name', 'employment__job_title', 'notes')


@admin.register(TaxWithholdingSlip)
class TaxWithholdingSlipAdmin(admin.ModelAdmin):
    list_display = ('employment', 'tax_year', 'total_payment', 'income_after_deduction', 'total_income_deductions', 'withholding_tax', 'currency', 'issue_date')
    list_filter = ('tax_year',)
    search_fields = ('employment__company__name', 'employment__job_title', 'notes')


@admin.register(CareerDocument)
class CareerDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'document_type', 'company', 'employment', 'issue_date', 'file_size', 'created_at')
    list_filter = ('document_type',)
    search_fields = ('title', 'company__name', 'notes')
