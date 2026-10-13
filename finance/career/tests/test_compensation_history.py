import pytest
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth import get_user_model
from finance.career.models import CompanyProfile, Employment, CompensationHistory

User = get_user_model()


@pytest.fixture
def auth_user():
    return User.objects.create_user(username='comp_user', email='comp@test.com', password='password123')


@pytest.fixture
def client_authenticated(auth_user):
    client = APIClient()
    client.force_authenticate(user=auth_user)
    return client


@pytest.fixture
def employment(auth_user):
    company = CompanyProfile.objects.create(name='Acme Corp', user=auth_user)
    return Employment.objects.create(user=auth_user, company=company, job_title='Engineer', start_date='2022-01-01')


@pytest.mark.django_db
class TestCompensationHistory:
    def test_annual_salary_with_monthly_allowances(self, employment):
        # 2,760,000 JPY annual base offer with 25,000 JPY monthly housing allowance
        comp = CompensationHistory.objects.create(
            employment=employment,
            effective_date='2022-04-01',
            revision_type='initial_offer',
            base_salary=2760000,
            allowances=25000,
            housing_allowance=25000,
            salary_frequency='annual',
            bonus_expected=0,
        )
        # Monthly guaranteed = (2,760,000 / 12) + 25,000 = 230,000 + 25,000 = 255,000
        assert comp.total_monthly_guaranteed == 255000.0
        # Annual base guaranteed = 2,760,000 + (25,000 * 12) = 2,760,000 + 300,000 = 3,060,000
        assert comp.annual_base_guaranteed == 3060000.0
        assert comp.total_annual_expected == 3060000.0

    def test_monthly_salary_with_monthly_allowances(self, employment):
        # 230,000 JPY monthly base with 25,000 JPY monthly housing allowance
        comp = CompensationHistory.objects.create(
            employment=employment,
            effective_date='2022-04-01',
            revision_type='initial_offer',
            base_salary=230000,
            allowances=25000,
            housing_allowance=25000,
            salary_frequency='monthly',
            bonus_expected=400000,
        )
        # Monthly guaranteed = 230,000 + 25,000 = 255,000
        assert comp.total_monthly_guaranteed == 255000.0
        # Annual base guaranteed = (230,000 + 25,000) * 12 = 3,060,000
        assert comp.annual_base_guaranteed == 3060000.0
        # Total annual expected (OTE) = 3,060,000 + 400,000 = 3,460,000
        assert comp.total_annual_expected == 3460000.0

    def test_compensation_api_create_and_read(self, client_authenticated, employment):
        url = reverse('career-compensations-list')
        payload = {
            'employment': employment.id,
            'effective_date': '2022-04-01',
            'revision_type': 'initial_offer',
            'base_salary': 2760000,
            'allowances': 25000,
            'housing_allowance': 25000,
            'salary_frequency': 'annual',
            'currency': 'JPY',
        }
        res = client_authenticated.post(url, data=payload, format='json')
        assert res.status_code == 201
        data = res.json()['data']
        assert data['total_monthly_guaranteed'] == 255000.0
        assert data['annual_base_guaranteed'] == 3060000.0
