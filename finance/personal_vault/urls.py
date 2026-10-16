from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PersonalVaultOverviewView,
    IdentityProfileView,
    EducationRecordViewSet,
    VehicleRecordViewSet,
    ResidenceRecordViewSet,
    PersonalDocumentViewSet,
    PersonalDocumentUploadView,
    PersonalDocumentDownloadView,
)

router = DefaultRouter()
router.register(r'education', EducationRecordViewSet, basename='vault-education')
router.register(r'vehicles', VehicleRecordViewSet, basename='vault-vehicles')
router.register(r'residences', ResidenceRecordViewSet, basename='vault-residences')
router.register(r'documents', PersonalDocumentViewSet, basename='vault-documents')

urlpatterns = [
    path('overview/', PersonalVaultOverviewView.as_view(), name='vault-overview'),
    path('identity/', IdentityProfileView.as_view(), name='vault-identity'),
    path('documents/upload/', PersonalDocumentUploadView.as_view(), name='vault-document-upload'),
    path('documents/<int:pk>/view/', PersonalDocumentDownloadView.as_view(), {'action': 'view'}, name='vault-document-view'),
    path('documents/<int:pk>/download/', PersonalDocumentDownloadView.as_view(), {'action': 'download'}, name='vault-document-download'),
    path('', include(router.urls)),
]
