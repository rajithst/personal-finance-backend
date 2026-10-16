from django.db import models
from django.conf import settings

class PersonalDocument(models.Model):
    CATEGORY_CHOICES = [
        ('identity', 'Identity & Legal'),
        ('education', 'Education & Degrees'),
        ('vehicle', 'Vehicles & Mobility'),
        ('residence', 'Housing & Residences'),
        ('general', 'General Personal'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='personal_documents')
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, db_index=True)
    doc_type = models.CharField(max_length=64, db_index=True)
    document_number = models.CharField(max_length=128, blank=True)
    issuing_authority = models.CharField(max_length=255, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    file_uri = models.CharField(max_length=512)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(default=0)
    mime_type = models.CharField(max_length=128, default='application/pdf')
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)

    # Optional relational links to parent life entities
    education_record = models.ForeignKey('EducationRecord', null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')
    vehicle_record = models.ForeignKey('VehicleRecord', null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')
    residence_record = models.ForeignKey('ResidenceRecord', null=True, blank=True, on_delete=models.SET_NULL, related_name='documents')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.category})"


class IdentityProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='identity_profile')
    full_legal_name = models.CharField(max_length=255)
    full_legal_name_kana = models.CharField(max_length=255, blank=True)
    nationality = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    place_of_birth = models.CharField(max_length=255, blank=True)
    blood_type = models.CharField(max_length=10, blank=True)
    emergency_contact_name = models.CharField(max_length=255, blank=True)
    emergency_contact_phone = models.CharField(max_length=64, blank=True)
    emergency_contact_relationship = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"IdentityProfile(user={self.user.username}, name={self.full_legal_name})"


class EducationRecord(models.Model):
    QUALIFICATION_CHOICES = [
        ('bachelor', "Bachelor's Degree"),
        ('master', "Master's Degree"),
        ('doctorate', 'Doctorate / PhD'),
        ('diploma', 'Higher Diploma / Associate'),
        ('certification', 'Professional Certification'),
        ('high_school', 'High School / Secondary'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='education_records')
    institution_name = models.CharField(max_length=255)
    institution_location = models.CharField(max_length=255, blank=True)
    qualification_type = models.CharField(max_length=32, choices=QUALIFICATION_CHOICES, default='bachelor')
    field_of_study = models.CharField(max_length=255)
    grade_or_gpa = models.CharField(max_length=64, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_in_progress = models.BooleanField(default=False)
    credential_id_or_url = models.CharField(max_length=512, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.field_of_study} at {self.institution_name}"


class VehicleRecord(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active / In Possession'),
        ('sold', 'Sold / Transferred'),
        ('leased', 'Active Lease'),
        ('scrapped', 'Scrapped / Deregistered'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vehicles')
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    model_year = models.PositiveSmallIntegerField(null=True, blank=True)
    license_plate = models.CharField(max_length=64)
    vin_or_chassis = models.CharField(max_length=128, blank=True)
    color = models.CharField(max_length=64, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    sale_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='active')
    shaken_expiry_date = models.DateField(null=True, blank=True, db_index=True)
    insurance_expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.make} {self.model} ({self.license_plate})"


class ResidenceRecord(models.Model):
    RESIDENCE_TYPE_CHOICES = [
        ('rented_apartment', 'Rented Apartment / Condo'),
        ('owned_condo', 'Owned Condo'),
        ('house', 'House'),
        ('temporary', 'Temporary / Dormitory'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('current', 'Current Residence'),
        ('past', 'Past Residence'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='residences')
    property_name = models.CharField(max_length=255)
    address_full = models.TextField()
    postal_code = models.CharField(max_length=32, blank=True)
    residence_type = models.CharField(max_length=32, choices=RESIDENCE_TYPE_CHOICES, default='rented_apartment')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='current')
    move_in_date = models.DateField()
    move_out_date = models.DateField(null=True, blank=True)
    lease_start_date = models.DateField(null=True, blank=True)
    lease_end_date = models.DateField(null=True, blank=True, db_index=True)
    monthly_rent_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    key_money_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    landlord_or_agency = models.CharField(max_length=255, blank=True)
    agent_contact_phone = models.CharField(max_length=64, blank=True)
    agent_contact_email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-move_in_date']

    def __str__(self):
        return f"{self.property_name} ({self.status})"
