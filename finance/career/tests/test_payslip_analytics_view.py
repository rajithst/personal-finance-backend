import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from finance.career.models import CompanyProfile, Employment, MonthlyPayslip

User = get_user_model()

@pytest.fixture
def auth_user():
    return User.objects.create_user(username='analytics_user', email='analytics@test.com', password='password123')

@pytest.fixture
def other_user():
    return User.objects.create_user(username='other_user', email='other@test.com', password='password123')

@pytest.fixture
def client_authenticated(auth_user):
    client = APIClient()
    client.force_authenticate(user=auth_user)
    return client

@pytest.mark.django_db
class TestPayslipAnalyticsView:
    def test_analytics_aggregations_and_ratios(self, client_authenticated, auth_user):
        company = CompanyProfile.objects.create(user=auth_user, name="Astellas Pharma")
        employment = Employment.objects.create(
            user=auth_user, company=company, job_title="Engineer",
            start_date="2024-01-01", is_current=True
        )
        MonthlyPayslip.objects.create(
            user=auth_user, employment=employment, year=2024, month=5,
            gross_pay=1000000, net_pay=800000, pension=90000, health_insurance=50000,
            employment_insurance=5000, income_tax=40000, resident_tax=20000, total_tax=60000,
            social_insurance_total=145000, total_deductions=200000, is_bonus=False,
            std_remuneration_pension=1000000, std_remuneration_health=1000000
        )
        MonthlyPayslip.objects.create(
            user=auth_user, employment=employment, year=2024, month=6,
            gross_pay=1000000, net_pay=800000, pension=90000, health_insurance=50000,
            employment_insurance=5000, income_tax=40000, resident_tax=20000, total_tax=60000,
            social_insurance_total=145000, total_deductions=200000, is_bonus=True,
            std_remuneration_pension=1000000, std_remuneration_health=1000000
        )

        url = reverse('career-payslips-analytics')
        response = client_authenticated.get(url)
        assert response.status_code == 200
        payload = response.json()
        assert payload['status'] is True
        data = payload['data']

        summary = data['summary']
        assert summary['total_gross_pay'] == 2000000.0
        assert summary['total_net_pay'] == 1600000.0
        assert summary['total_pension_employee'] == 180000.0
        assert summary['total_pension_system_contribution'] == 360000.0  # 50/50 match
        assert summary['overall_take_home_ratio'] == 80.0
        assert summary['payslips_count'] == 2

        assert len(data['monthly_timeline']) == 2
        assert len(data['yearly_comparisons']) == 1
        assert len(data['deduction_composition']) > 0

    def test_analytics_filters(self, client_authenticated, auth_user):
        c1 = CompanyProfile.objects.create(user=auth_user, name="Company A")
        c2 = CompanyProfile.objects.create(user=auth_user, name="Company B")
        e1 = Employment.objects.create(user=auth_user, company=c1, job_title="Dev", start_date="2023-01-01")
        e2 = Employment.objects.create(user=auth_user, company=c2, job_title="Lead", start_date="2024-01-01")

        MonthlyPayslip.objects.create(
            user=auth_user, employment=e1, year=2023, month=12,
            gross_pay=500000, net_pay=400000, pension=45000, health_insurance=25000,
            income_tax=20000, resident_tax=10000, total_tax=30000,
            social_insurance_total=70000, total_deductions=100000, is_bonus=False
        )
        MonthlyPayslip.objects.create(
            user=auth_user, employment=e2, year=2024, month=6,
            gross_pay=600000, net_pay=480000, pension=54000, health_insurance=30000,
            income_tax=24000, resident_tax=12000, total_tax=36000,
            social_insurance_total=84000, total_deductions=120000, is_bonus=True
        )

        url = reverse('career-payslips-analytics')

        # Filter company
        resp = client_authenticated.get(f"{url}?company_id={c1.id}")
        assert resp.status_code == 200
        assert resp.json()['data']['summary']['total_gross_pay'] == 500000.0

        # Filter year
        resp = client_authenticated.get(f"{url}?year=2024")
        assert resp.status_code == 200
        assert resp.json()['data']['summary']['total_gross_pay'] == 600000.0
        assert resp.json()['data']['available_years'] == [2024, 2023]

        # Filter bonus excluded
        resp = client_authenticated.get(f"{url}?include_bonus=false")
        assert resp.status_code == 200
        assert resp.json()['data']['summary']['total_gross_pay'] == 500000.0
        assert resp.json()['data']['summary']['payslips_count'] == 1

    def test_analytics_zero_records(self, client_authenticated):
        url = reverse('career-payslips-analytics')
        resp = client_authenticated.get(url)
        assert resp.status_code == 200
        data = resp.json()['data']
        assert data['summary']['payslips_count'] == 0
        assert data['summary']['total_gross_pay'] == 0.0
        assert data['summary']['overall_take_home_ratio'] == 0.0
        assert data['monthly_timeline'] == []
        assert data['yearly_comparisons'] == []
        assert data['deduction_composition'] == []

    def test_analytics_user_isolation(self, client_authenticated, auth_user, other_user):
        c_other = CompanyProfile.objects.create(user=other_user, name="Other Inc")
        e_other = Employment.objects.create(user=other_user, company=c_other, job_title="Dev", start_date="2024-01-01")
        MonthlyPayslip.objects.create(
            user=other_user, employment=e_other, year=2024, month=5,
            gross_pay=9999999, net_pay=8888888, pension=900000, health_insurance=500000,
            income_tax=400000, resident_tax=200000, total_tax=600000,
            social_insurance_total=1400000, total_deductions=2000000, is_bonus=False
        )

        url = reverse('career-payslips-analytics')
        resp = client_authenticated.get(url)
        assert resp.status_code == 200
        assert resp.json()['data']['summary']['total_gross_pay'] == 0.0
