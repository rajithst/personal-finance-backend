# Graph Report - personalfinance  (2026-09-27)

## Corpus Check
- 182 files · ~50,601 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 4, .example 1, .ini 1)

## Summary
- 993 nodes · 1915 edges · 110 communities (49 shown, 61 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 191 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1c100b24`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- transaction_import_service.py
- card_loaders.py
- SettingsService
- DashboardService
- get_current_user
- PayeeService
- django_apps
- TransactionImportService
- TestTransactionView
- rest_framework
- core/urls.py
- RequestManager
- career/views.py
- CareerOverviewView
- Transaction
- TransactionListService
- StorageBackendContract
- AnalyticsService
- GCSHandler
- upload_workflow.py
- CompensationHistory
- TestTransactionImportView
- career/admin.py
- TestCategorySettingsView
- ProfileSerializer
- Google Cloud Run Deployment Guide
- CompanyProfileSerializer
- TestPayeeView
- transactions/views.py
- TestAccountsView
- logging
- pytest
- import_workflow.py
- test_analytics.py
- LocalStorageHandler
- User
- oauth/views.py
- oauth/models.py
- handler.py
- TestSpaServing
- test_audit_reports.py
- test_subscriptions.py
- CareerDocument
- ImportCsvWorkflow
- TestClientSettings
- DummyProcessor
- conftest.py
- transaction_list_service.py
- DispatchAssignmentSerializer
- MonthlyPayslipSerializer
- TokenObtainPairSerializer
- transactions/admin.py
- oauth/admin.py
- TestTransactionServices
- TestGenerateDevTokenCommand
- TestLocalStorage
- rules/graphify.md
- workflows/graphify.md
- core/__init__.py
- .get_subscriptions_radar
- career/__init__.py
- career/migrations/__init__.py

## God Nodes (most connected - your core abstractions)
1. `get_current_user()` - 35 edges
2. `CategoryService` - 31 edges
3. `Transaction` - 31 edges
4. `TransactionImportService` - 30 edges
5. `DashboardService` - 29 edges
6. `TransactionListService` - 29 edges
7. `AnalyticsService` - 25 edges
8. `RequestManager` - 24 edges
9. `DestinationMap` - 22 edges
10. `PayeeService` - 22 edges

## Surprising Connections (you probably didn't know these)
- `5. Security & Access Control` --references--> `CareerDocument`  [INFERRED]
  docs/career_hub_payslip_ingestion_and_storage_plan.md → finance/career/models.py
- `1. Executive Summary` --references--> `MonthlyPayslip`  [INFERRED]
  docs/career_hub_payslip_ingestion_and_storage_plan.md → finance/career/models.py
- `5. Security & Access Control` --references--> `MonthlyPayslip`  [INFERRED]
  docs/career_hub_payslip_ingestion_and_storage_plan.md → finance/career/models.py
- `5. Security & Access Control` --references--> `RequestManager`  [INFERRED]
  docs/career_hub_payslip_ingestion_and_storage_plan.md → oauth/util/request_manager.py
- `Account` --uses--> `RequestManager`  [INFERRED]
  accounts/models.py → oauth/util/request_manager.py

## Import Cycles
- None detected.

## Communities (110 total, 61 thin omitted)

### Community 0 - "transaction_import_service.py"
Cohesion: 0.05
Nodes (43): Migration, Migration, django_conf, django_contrib_auth_models, django_contrib_auth_validators, django_db, django_db_models, django_db_models_deletion (+35 more)

### Community 1 - "card_loaders.py"
Cohesion: 0.07
Nodes (22): AccountProviders, DataSource, BaseLoader, DocomoCardLoader, EposCardLoader, MizuhoBankLoader, RakutenCardLoader, TransactionProcessFactory (+14 more)

### Community 2 - "SettingsService"
Cohesion: 0.06
Nodes (23): Account, Meta, AccountSerializer, Meta, ResponseAccountSerializer, AccountService, object, patch (+15 more)

### Community 3 - "DashboardService"
Cohesion: 0.09
Nodes (14): datetime, django_db_models_functions, django_utils, DashboardService, Get the monthly transaction summary. Args: transaction_type (str): The…, Get the monthly transaction category summary. Args: transaction_type (str): The…, Calculates income, expense, payment, and savings aggregated by month in a…, Get the account wise sum. Args: transaction_type (str): The transaction type.… (+6 more)

### Community 4 - "get_current_user"
Cohesion: 0.09
Nodes (12): clear_current_user(), get_current_user(), Middleware to make the current request globally accessible. Guarantees thread-…, ThreadLocalMiddleware, TestHealthCheckEndpoint, TestPasswordResetSecurity, TestThreadLocalSecurity, dummy_view() (+4 more)

### Community 5 - "PayeeService"
Cohesion: 0.12
Nodes (10): Meta, ResponseDestinationMapSerializer, PayeeService, Updates the payee. Args: request_data (dict): The request data. Returns: tuple:…, Gets the custom queryset for the payee. Returns: QuerySet: The custom queryset…, object, patch, TestPayeeService (+2 more)

### Community 6 - "django_apps"
Cohesion: 0.07
Nodes (19): AccountsConfig, AppConfig, ChangelogConfig, AppConfig, django_apps, CareerConfig, AppConfig, CategoriesConfig (+11 more)

### Community 7 - "TransactionImportService"
Cohesion: 0.10
Nodes (14): Uploads the transaction files. Args: upload_params (dict): The upload…, Gets the account from the provided account ID. Args: account_id (int): The…, Gets the applicable transactions. Args: transaction_data (DataFrame): The…, Gets the payee map. Returns: DataFrame: The payee map., Gets the rewrite rules. Args: payee_maps (DataFrame): The payee maps. Returns:…, Finds the new payees. Args: payees (DataFrame): The payees. transactions…, Assigns the category IDs to the transactions. Args: payees (DataFrame): The…, Imports the transactions from the provided files. Args: import_params (dict):… (+6 more)

### Community 8 - "TestTransactionView"
Cohesion: 0.09
Nodes (6): mock_bulk_service(), mock_transaction_service(), django_db, fixture, TestTransactionBulkView, TestTransactionView

### Community 9 - "rest_framework"
Cohesion: 0.17
Nodes (13): ActionEnum, ChangeLog, SectionEnum, ChangeLogSerializer, Meta, django_db, TestActivityView, ActivityView (+5 more)

### Community 10 - "core/urls.py"
Cohesion: 0.11
Nodes (14): ASGI config for personalfinance project. It exposes the ASGI callable as a…, URL configuration for personalfinance project. The `urlpatterns` list routes…, Serves the Single Page Application (SPA) entry point (index.html). All non-API…, spa_index_view(), WSGI config for personalfinance project. It exposes the WSGI callable as a…, django_conf_urls_static, django_core_asgi, django_core_wsgi (+6 more)

### Community 11 - "RequestManager"
Cohesion: 0.12
Nodes (16): 1. Executive Summary, 2.1 Storage Folder Hierarchy, 2.2 Storage Path Construction Rule, 2.3 GCS Object Metadata, 2. Cloud Storage (GCS) Directory Architecture, 3.1 Extraction Pipeline Flow, 3.2 Target Extraction Schema (Pydantic / DRF Mapping), 3. Automated Extraction Engine (Gemini AI + Schema Guard) (+8 more)

### Community 12 - "career/views.py"
Cohesion: 0.18
Nodes (9): CompanyProfile, DispatchAssignment, Meta, Tracks dispatched company assignments (dispatched company, start date, end…, Annual Withholding Tax Certificate (源泉徴収票 / Gensen-Choshu-Hyo). Matches the…, Represents a company entity (Direct Employer, Staffing/Dispatch Agency, or…, TaxWithholdingSlip, TaxWithholdingSlipSerializer (+1 more)

### Community 13 - "CareerOverviewView"
Cohesion: 0.14
Nodes (8): Employment, Returns the latest compensation revision record, if any., Represents an employment tenure with an employer entity (legal contract and…, EmploymentSerializer, CareerOverviewView, EmploymentView, APIView, Returns an aggregated summary for the Career Hub dashboard: - Current…

### Community 14 - "Transaction"
Cohesion: 0.15
Nodes (9): calendar, collections, Meta, Transaction, DateSerializeHelper, object, ResponseTransactionSerializer, TransactionBulkService (+1 more)

### Community 15 - "TransactionListService"
Cohesion: 0.21
Nodes (4): Meta, TransactionSerializer, TransactionListService, TestGroupByOptimization

### Community 16 - "StorageBackendContract"
Cohesion: 0.14
Nodes (9): Any, Upload a file or stream to the storage backend., Read a file and return a readable stream or file-like object., List file paths in storage matching the given prefix., Delete a file from the storage backend., Read all files matching the prefix into a list of file-like streams., Read a CSV file into a pandas DataFrame., Abstract contract defining file storage operations across different storage… (+1 more)

### Community 17 - "AnalyticsService"
Cohesion: 0.24
Nodes (5): AnalyticsService, AnalyticsView, AuditReportsView, APIView, SubscriptionRadarView

### Community 18 - "GCSHandler"
Cohesion: 0.14
Nodes (9): GCSHandler, Reads a CSV file from the GCS bucket. Args: file_name (str): The name of the…, A handler for interacting with Google Cloud Storage (GCS). Provides methods for…, Initializes the GCSHandler with a specified bucket name. Args: bucket_name…, Uploads a file to the GCS bucket with retry logic. Args: file (file-like…, Lists files in the GCS bucket with optional filtering and pagination. Args:…, Deletes a file from the specified bucket., Reads a file from the GCS bucket. Args: file_name (str): The name of the file… (+1 more)

### Community 19 - "upload_workflow.py"
Cohesion: 0.27
Nodes (7): AccountTypes, WorkflowContextType, Enum, time, TestUploadWorkflow, Any, UploadWorkflow

### Community 20 - "CompensationHistory"
Cohesion: 0.17
Nodes (7): CompensationHistory, Tracks multi-year compensation revisions, annual raises, promotions, and…, Monthly guaranteed pay = base salary + fixed allowances (normalized to monthly), Annual guaranteed base (固定年俸 / Base + Allowances * 12), Total expected annual package (総年収 / OTE) = (Base + Allowances) * 12 + Annual…, CompensationHistorySerializer, CompensationHistoryView

### Community 21 - "TestTransactionImportView"
Cohesion: 0.14
Nodes (5): django_core_files_uploadedfile, mock_import_service(), django_db, fixture, TestTransactionImportView

### Community 22 - "career/admin.py"
Cohesion: 0.21
Nodes (13): CareerDocumentAdmin, CareerDocumentInline, CompanyProfileAdmin, CompensationHistoryAdmin, CompensationHistoryInline, DispatchAssignmentAdmin, DispatchAssignmentInline, EmploymentAdmin (+5 more)

### Community 23 - "TestCategorySettingsView"
Cohesion: 0.14
Nodes (4): mock_category_service(), django_db, fixture, TestCategorySettingsView

### Community 24 - "ProfileSerializer"
Cohesion: 0.18
Nodes (7): action, CreateModelMixin, GenericViewSet, ProfileSerializer, ProfileViewSet, RetrieveModelMixin, UpdateModelMixin

### Community 25 - "Google Cloud Run Deployment Guide"
Cohesion: 0.17
Nodes (11): 1. Architecture on Cloud Run, 2. Prerequisites, 3. Environment Variables & Database Setup, 4. Deploying to Cloud Run, 5. Verifying Deployment, 6. How Environment Variables Work in Django, A. Get Cloud SQL Instance Connection Name, Alternative 1: Using `--set-env-vars` CLI flag (+3 more)

### Community 26 - "CompanyProfileSerializer"
Cohesion: 0.21
Nodes (3): CompanyProfileSerializer, Meta, CompanyProfileView

### Community 27 - "TestPayeeView"
Cohesion: 0.17
Nodes (4): mock_payee_service(), django_db, fixture, TestPayeeView

### Community 28 - "transactions/views.py"
Cohesion: 0.24
Nodes (5): APIView, TransactionBulkView, TransactionImportView, TransactionView, rest_framework_parsers

### Community 29 - "TestAccountsView"
Cohesion: 0.18
Nodes (4): mock_category_service(), django_db, fixture, TestAccountsView

### Community 30 - "logging"
Cohesion: 0.22
Nodes (8): Django settings for personalfinance project. Generated by 'django-admin…, decouple, django_core_management, dotenv, google_cloud, io, logging, pathlib

### Community 31 - "pytest"
Cohesion: 0.18
Nodes (6): django_test, mock_dashboard_service(), django_db, fixture, TestDashboardView, pytest

### Community 32 - "import_workflow.py"
Cohesion: 0.31
Nodes (4): django_core_files_storage, typing, ABC, StorageBackendProvider

### Community 33 - "test_analytics.py"
Cohesion: 0.22
Nodes (5): mock_analytics_service(), django_db, fixture, TestAnalyticsServiceDirect, TestAnalyticsView

### Community 34 - "LocalStorageHandler"
Cohesion: 0.33
Nodes (3): LocalStorageHandler, Any, DataFrame

### Community 35 - "User"
Cohesion: 0.25
Nodes (6): AbstractUser, django_core_management_base, Command, BaseCommand, User, rest_framework_simplejwt_tokens

### Community 36 - "oauth/views.py"
Cohesion: 0.22
Nodes (8): base64, django_contrib_auth, django_contrib_auth_tokens, rest_framework_decorators, rest_framework_mixins, rest_framework_permissions, rest_framework_simplejwt_views, rest_framework_viewsets

### Community 37 - "oauth/models.py"
Cohesion: 0.28
Nodes (6): BaseUserCreateSerializer, djoser_serializers, Profile, Meta, UserCreateSerializer, rest_framework_simplejwt_serializers

### Community 38 - "handler.py"
Cohesion: 0.36
Nodes (7): get_changes(), log_change_handler(), prepare_json_fields(), save_changes(), django_dispatch, django_forms, receiver

### Community 39 - "TestSpaServing"
Cohesion: 0.22
Nodes (3): django_db, fixture, TestSpaServing

### Community 40 - "test_audit_reports.py"
Cohesion: 0.25
Nodes (5): mock_analytics_service(), django_db, fixture, TestAuditReportsServiceDirect, TestAuditReportsView

### Community 41 - "test_subscriptions.py"
Cohesion: 0.25
Nodes (5): mock_analytics_service(), django_db, fixture, TestSubscriptionRadarService, TestSubscriptionRadarView

### Community 42 - "CareerDocument"
Cohesion: 0.31
Nodes (4): CareerDocument, Pure Document Vault for career-related files: offer letters, employment…, CareerDocumentSerializer, CareerDocumentView

### Community 44 - "TestClientSettings"
Cohesion: 0.25
Nodes (4): mock_settings_service(), django_db, fixture, TestClientSettings

### Community 46 - "conftest.py"
Cohesion: 0.33
Nodes (5): api_client(), authenticate(), fixture, model_bakery, rest_framework_test

### Community 47 - "transaction_list_service.py"
Cohesion: 0.38
Nodes (3): copy, decimal, TransactionListValidator

### Community 50 - "TokenObtainPairSerializer"
Cohesion: 0.33
Nodes (4): BaseTokenObtainPairSerializer, BaseTokenObtainPairView, TokenObtainPairSerializer, TokenObtainPairView

### Community 51 - "transactions/admin.py"
Cohesion: 0.47
Nodes (4): AccountAdmin, register, TransactionAdmin, TransactionCategoryAdmin

### Community 52 - "oauth/admin.py"
Cohesion: 0.40
Nodes (4): django_contrib, django_contrib_auth_admin, register, UserAdmin

## Knowledge Gaps
- **34 isolated node(s):** `Migration`, `Meta`, `Migration`, `Meta`, `Migration` (+29 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 394 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **61 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Transaction` connect `Transaction` to `transaction_import_service.py`, `SettingsService`, `DashboardService`, `get_current_user`, `PayeeService`, `TransactionImportService`, `rest_framework`, `RequestManager`, `TransactionListService`, `transaction_list_service.py`, `AnalyticsService`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Why does `RequestManager` connect `RequestManager` to `transaction_import_service.py`, `SettingsService`, `get_current_user`, `CareerDocument`, `career/views.py`, `CareerOverviewView`, `Transaction`, `CompensationHistory`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `TransactionImportService` connect `TransactionImportService` to `transaction_import_service.py`, `card_loaders.py`, `SettingsService`, `import_workflow.py`, `ImportCsvWorkflow`, `Transaction`, `transaction_list_service.py`, `upload_workflow.py`, `TestTransactionServices`, `transactions/views.py`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `CategoryService` (e.g. with `TransactionCategory` and `TransactionSubCategory`) actually correct?**
  _`CategoryService` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Transaction` (e.g. with `TestActivityView` and `ActivityView`) actually correct?**
  _`Transaction` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `TransactionImportService` (e.g. with `Account` and `WorkflowContextType`) actually correct?**
  _`TransactionImportService` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `DashboardService` (e.g. with `Transaction` and `TestDashboardService`) actually correct?**
  _`DashboardService` has 3 INFERRED edges - model-reasoned connections that need verification._