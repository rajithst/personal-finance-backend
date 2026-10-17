import os
from datetime import date
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import (
    PersonalDocument,
    IdentityProfile,
    EducationRecord,
    VehicleRecord,
    ResidenceRecord,
)
from .serializers import (
    PersonalDocumentSerializer,
    PersonalDocumentSummarySerializer,
    IdentityProfileSerializer,
    EducationRecordSerializer,
    VehicleRecordSerializer,
    ResidenceRecordSerializer,
)
from .services.storage_service import (
    upload_personal_document,
    validate_vault_file,
    generate_vault_signature,
    verify_vault_signature,
)
from .services.expiry_service import get_user_expiry_radar


class PersonalVaultOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        total_docs = PersonalDocument.objects.filter(user=user).count()
        active_vehicles = VehicleRecord.objects.filter(user=user, status='active').count()
        active_leases = ResidenceRecord.objects.filter(user=user, status='current').count()
        degrees = EducationRecord.objects.filter(user=user).count()

        expiry_radar = get_user_expiry_radar(user)
        expiring_soon_count = sum(1 for item in expiry_radar if item['severity'] in ('critical', 'expired'))

        recent_docs = PersonalDocument.objects.filter(user=user).order_by('-created_at')[:5]
        recent_docs_data = PersonalDocumentSummarySerializer(recent_docs, many=True).data

        return Response({
            'status': True,
            'data': {
                'metrics': {
                    'total_documents': total_docs,
                    'active_vehicles': active_vehicles,
                    'active_leases': active_leases,
                    'academic_degrees': degrees,
                    'expiring_soon': expiring_soon_count,
                },
                'expiry_radar': expiry_radar,
                'recent_uploads': recent_docs_data,
            }
        })


class IdentityProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = IdentityProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_legal_name': request.user.get_full_name() or request.user.username, 'nationality': ''}
        )
        serializer = IdentityProfileSerializer(profile)
        return Response({'status': True, 'data': serializer.data})

    def put(self, request):
        profile, _ = IdentityProfile.objects.get_or_create(
            user=request.user,
            defaults={'full_legal_name': request.user.get_full_name() or request.user.username, 'nationality': ''}
        )
        serializer = IdentityProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': True, 'data': serializer.data})
        return Response({'status': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class EducationRecordViewSet(viewsets.ModelViewSet):
    serializer_class = EducationRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EducationRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response({'status': True, 'data': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'status': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({'status': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'status': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class VehicleRecordViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VehicleRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response({'status': True, 'data': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'status': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({'status': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'status': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ResidenceRecordViewSet(viewsets.ModelViewSet):
    serializer_class = ResidenceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ResidenceRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response({'status': True, 'data': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'status': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response({'status': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'status': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class PersonalDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = PersonalDocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = PersonalDocument.objects.filter(user=self.request.user)
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        doc_type = self.request.query_params.get('doc_type')
        if doc_type:
            qs = qs.filter(doc_type=doc_type)
        search = self.request.query_params.get('search')
        if search:
            from django.db.models import Q
            qs = qs.filter(Q(title__icontains=search) | Q(document_number__icontains=search) | Q(notes__icontains=search))
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        return Response({'status': True, 'data': serializer.data})

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'status': True, 'data': serializer.data})


class PersonalDocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'status': False, 'message': 'No file attached.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            val_info = validate_vault_file(file_obj)
        except Exception as e:
            return Response({'status': False, 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        category = request.data.get('category', 'general')
        doc_type = request.data.get('doc_type', 'other')
        title = request.data.get('title') or val_info['safe_name']

        try:
            file_uri = upload_personal_document(
                file_obj=file_obj,
                user_id=request.user.id,
                category=category,
                doc_type=doc_type,
                original_filename=val_info['safe_name']
            )
        except Exception as e:
            return Response({'status': False, 'message': f'Storage upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Optional parent entity links
        edu_id = request.data.get('education_record_id')
        veh_id = request.data.get('vehicle_record_id')
        res_id = request.data.get('residence_record_id')

        doc = PersonalDocument.objects.create(
            user=request.user,
            title=title,
            category=category,
            doc_type=doc_type,
            document_number=request.data.get('document_number', ''),
            issuing_authority=request.data.get('issuing_authority', ''),
            issue_date=request.data.get('issue_date') or None,
            expiry_date=request.data.get('expiry_date') or None,
            file_uri=file_uri,
            original_filename=val_info['safe_name'],
            file_size=val_info['size'],
            mime_type=val_info['mime_type'],
            notes=request.data.get('notes', ''),
            education_record_id=edu_id or None,
            vehicle_record_id=veh_id or None,
            residence_record_id=res_id or None,
        )

        serializer = PersonalDocumentSerializer(doc)
        return Response({'status': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)


@method_decorator(xframe_options_exempt, name='dispatch')
class PersonalDocumentDownloadView(APIView):
    """Handles preview or download of vault files with security verification."""
    permission_classes = [AllowAny]

    def get(self, request, pk, action='view'):
        user = request.user

        # 1. Try JWT from query param if not authenticated by header
        if not user or not user.is_authenticated:
            token = request.query_params.get('token')
            if token:
                from rest_framework_simplejwt.tokens import AccessToken
                from django.contrib.auth import get_user_model
                try:
                    access_token = AccessToken(token)
                    user_id = access_token.get('user_id')
                    User = get_user_model()
                    user = User.objects.get(pk=user_id)
                except Exception:
                    user = None

        # 2. Try signature if present
        sig = request.query_params.get('sig')
        sig_doc_id = None
        sig_user_id = None
        if sig:
            try:
                sig_doc_id, sig_user_id = verify_vault_signature(sig)
            except Exception:
                pass

        doc = get_object_or_404(PersonalDocument, pk=pk)

        # Verify access authorization
        is_authorized = False
        if user and user.is_authenticated and doc.user_id == user.id:
            is_authorized = True
        elif sig_doc_id == doc.id and (sig_user_id == doc.user_id or (user and user.id == sig_user_id)):
            is_authorized = True

        if not is_authorized:
            return Response({'status': False, 'message': 'Authentication required or permission denied.'}, status=status.HTTP_401_UNAUTHORIZED)

        if doc.file_uri.startswith('local://'):
            rel_path = doc.file_uri.replace('local://', '')
            media_root = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
            full_path = os.path.join(media_root, rel_path)
            if not os.path.exists(full_path):
                raise Http404("Document file not found on local storage.")

            as_attachment = (action == 'download')
            response = FileResponse(open(full_path, 'rb'), content_type=doc.mime_type)
            disposition = 'attachment' if as_attachment else 'inline'
            response['Content-Disposition'] = f'{disposition}; filename="{doc.original_filename}"'
            return response

        # GCS / Cloud signed URL
        bucket_name = getattr(settings, 'GCP_STORAGE_BUCKET', None) or 'personal-finance-dev'
        from google.cloud import storage
        import datetime
        try:
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            blob_path = doc.file_uri.replace(f"gs://{bucket_name}/", "")
            blob = bucket.blob(blob_path)
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=15),
                method="GET"
            )
            if request.query_params.get('json') == 'true':
                return Response({'status': True, 'url': signed_url})
            return HttpResponseRedirect(signed_url)
        except Exception as e:
            return Response({'status': False, 'message': f'Storage access failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
