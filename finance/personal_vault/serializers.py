from rest_framework import serializers
from .models import (
    PersonalDocument,
    IdentityProfile,
    EducationRecord,
    VehicleRecord,
    ResidenceRecord,
)

class PersonalDocumentSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalDocument
        fields = [
            'id', 'title', 'category', 'doc_type', 'document_number',
            'expiry_date', 'file_size', 'mime_type', 'created_at',
        ]


class PersonalDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalDocument
        fields = [
            'id', 'title', 'category', 'doc_type', 'document_number',
            'issuing_authority', 'issue_date', 'expiry_date', 'file_uri',
            'original_filename', 'file_size', 'mime_type', 'notes', 'tags',
            'education_record', 'vehicle_record', 'residence_record',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'file_uri', 'file_size', 'mime_type', 'created_at', 'updated_at']


class IdentityProfileSerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = IdentityProfile
        fields = [
            'id', 'full_legal_name', 'full_legal_name_kana', 'nationality',
            'date_of_birth', 'place_of_birth', 'blood_type',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'documents', 'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']

    def get_documents(self, obj):
        docs = PersonalDocument.objects.filter(user=obj.user, category='identity')
        return PersonalDocumentSummarySerializer(docs, many=True).data


class EducationRecordSerializer(serializers.ModelSerializer):
    documents = PersonalDocumentSummarySerializer(many=True, read_only=True)

    class Meta:
        model = EducationRecord
        fields = [
            'id', 'institution_name', 'institution_location', 'qualification_type',
            'field_of_study', 'grade_or_gpa', 'start_date', 'end_date',
            'is_in_progress', 'credential_id_or_url', 'notes', 'documents',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class VehicleRecordSerializer(serializers.ModelSerializer):
    documents = PersonalDocumentSummarySerializer(many=True, read_only=True)
    days_until_shaken = serializers.SerializerMethodField()
    days_until_insurance = serializers.SerializerMethodField()

    class Meta:
        model = VehicleRecord
        fields = [
            'id', 'make', 'model', 'model_year', 'license_plate',
            'vin_or_chassis', 'color', 'purchase_date', 'sale_date',
            'status', 'shaken_expiry_date', 'insurance_expiry_date',
            'notes', 'documents', 'days_until_shaken', 'days_until_insurance',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_days_until_shaken(self, obj):
        from datetime import date
        if obj.shaken_expiry_date:
            return (obj.shaken_expiry_date - date.today()).days
        return None

    def get_days_until_insurance(self, obj):
        from datetime import date
        if obj.insurance_expiry_date:
            return (obj.insurance_expiry_date - date.today()).days
        return None


class ResidenceRecordSerializer(serializers.ModelSerializer):
    documents = PersonalDocumentSummarySerializer(many=True, read_only=True)
    days_until_lease_renewal = serializers.SerializerMethodField()

    class Meta:
        model = ResidenceRecord
        fields = [
            'id', 'property_name', 'address_full', 'postal_code',
            'residence_type', 'status', 'move_in_date', 'move_out_date',
            'lease_start_date', 'lease_end_date', 'monthly_rent_amount',
            'deposit_amount', 'key_money_amount', 'landlord_or_agency',
            'agent_contact_phone', 'agent_contact_email', 'notes',
            'documents', 'days_until_lease_renewal', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_days_until_lease_renewal(self, obj):
        from datetime import date
        if obj.lease_end_date:
            return (obj.lease_end_date - date.today()).days
        return None
