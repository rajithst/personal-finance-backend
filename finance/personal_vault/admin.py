from django.contrib import admin
from .models import (
    PersonalDocument,
    IdentityProfile,
    EducationRecord,
    VehicleRecord,
    ResidenceRecord,
)

@admin.register(PersonalDocument)
class PersonalDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'doc_type', 'expiry_date', 'created_at')
    list_filter = ('category', 'doc_type')
    search_fields = ('title', 'document_number', 'notes')

@admin.register(IdentityProfile)
class IdentityProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_legal_name', 'nationality', 'date_of_birth')
    search_fields = ('full_legal_name', 'nationality')

@admin.register(EducationRecord)
class EducationRecordAdmin(admin.ModelAdmin):
    list_display = ('institution_name', 'user', 'qualification_type', 'field_of_study', 'start_date', 'end_date')
    search_fields = ('institution_name', 'field_of_study')

@admin.register(VehicleRecord)
class VehicleRecordAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'license_plate', 'user', 'status', 'shaken_expiry_date')
    list_filter = ('status', 'make')
    search_fields = ('make', 'model', 'license_plate', 'vin_or_chassis')

@admin.register(ResidenceRecord)
class ResidenceRecordAdmin(admin.ModelAdmin):
    list_display = ('property_name', 'user', 'status', 'move_in_date', 'lease_end_date')
    list_filter = ('status', 'residence_type')
    search_fields = ('property_name', 'address_full', 'landlord_or_agency')
