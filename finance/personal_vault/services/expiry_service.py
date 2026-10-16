from datetime import date
from ..models import PersonalDocument, VehicleRecord, ResidenceRecord

def get_user_expiry_radar(user, reference_date=None):
    """
    Consolidates expiry dates across PersonalDocument, VehicleRecord, and ResidenceRecord.
    Returns a chronologically sorted list of upcoming/expired items with severity classification.
    """
    ref_date = reference_date or date.today()
    radar_items = []

    # 1. Personal Documents with expiry dates
    docs = PersonalDocument.objects.filter(user=user, expiry_date__isnull=False)
    for doc in docs:
        days_left = (doc.expiry_date - ref_date).days
        severity = classify_severity(days_left)
        radar_items.append({
            'id': f"doc-{doc.id}",
            'source_id': doc.id,
            'domain': doc.category,
            'doc_type': doc.doc_type,
            'title': doc.title,
            'entity_name': doc.document_number or doc.issuing_authority or '',
            'expiry_date': doc.expiry_date.isoformat(),
            'days_remaining': days_left,
            'severity': severity,
        })

    # 2. Vehicles with shaken or insurance expiry
    vehicles = VehicleRecord.objects.filter(user=user, status='active')
    for v in vehicles:
        if v.shaken_expiry_date:
            days_left = (v.shaken_expiry_date - ref_date).days
            radar_items.append({
                'id': f"veh-shaken-{v.id}",
                'source_id': v.id,
                'domain': 'vehicle',
                'doc_type': 'vehicle_shaken',
                'title': f"{v.make} {v.model} Shaken Inspection",
                'entity_name': v.license_plate,
                'expiry_date': v.shaken_expiry_date.isoformat(),
                'days_remaining': days_left,
                'severity': classify_severity(days_left),
            })
        if v.insurance_expiry_date:
            days_left = (v.insurance_expiry_date - ref_date).days
            radar_items.append({
                'id': f"veh-ins-{v.id}",
                'source_id': v.id,
                'domain': 'vehicle',
                'doc_type': 'vehicle_insurance',
                'title': f"{v.make} {v.model} Automobile Insurance",
                'entity_name': v.license_plate,
                'expiry_date': v.insurance_expiry_date.isoformat(),
                'days_remaining': days_left,
                'severity': classify_severity(days_left),
            })

    # 3. Current Residences with lease end date
    residences = ResidenceRecord.objects.filter(user=user, status='current', lease_end_date__isnull=False)
    for r in residences:
        days_left = (r.lease_end_date - ref_date).days
        radar_items.append({
            'id': f"res-lease-{r.id}",
            'source_id': r.id,
            'domain': 'residence',
            'doc_type': 'lease_agreement',
            'title': f"{r.property_name} Lease Renewal",
            'entity_name': r.landlord_or_agency or r.postal_code or '',
            'expiry_date': r.lease_end_date.isoformat(),
            'days_remaining': days_left,
            'severity': classify_severity(days_left),
        })

    # Sort chronologically by days_remaining ascending
    radar_items.sort(key=lambda x: x['days_remaining'])
    return radar_items


def classify_severity(days_left):
    """
    Categorizes urgency into 4 severity bands:
    - expired: days_left < 0
    - critical: 0 <= days_left <= 30
    - upcoming: 31 <= days_left <= 90
    - healthy: days_left > 90
    """
    if days_left < 0:
        return 'expired'
    elif days_left <= 30:
        return 'critical'
    elif days_left <= 90:
        return 'upcoming'
    return 'healthy'
