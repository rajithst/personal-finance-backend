# Graph Report - personalfinance  (2026-09-28)

## Corpus Check
- 181 files · ~37,973 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 5, .example 1, .ini 1)

## Summary
- 1047 nodes · 2086 edges · 112 communities (55 shown, 57 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 232 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1eb2ceb9`
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
- .import_transactions
- TestTransactionView
- rest_framework
- core/urls.py
- MonthlyPayslip
- CompensationHistory
- EmploymentSerializer
- CategoryService
- TransactionListService
- StorageBackendContract
- AnalyticsService
- import_workflow.py
- test_workflows.py
- Employment
- TestTransactionImportView
- career/admin.py
- TestCategorySettingsView
- ProfileSerializer
- django_db
- CompanyProfileSerializer
- TestPayeeView
- TransactionImportService
- TestAccountsView
- extract_payslip_data
- pytest
- CareerOverviewView
- test_analytics.py
- LocalStorageHandler
- User
- oauth/views.py
- oauth/models.py
- GCSHandler
- TestSpaServing
- test_audit_reports.py
- test_subscriptions.py
- ResponseTransactionSerializer
- ImportCsvWorkflow
- TestClientSettings
- Q: how does the dashboard service connect to the database layer
- conftest.py
- Q: how transaction import flow working
- TransactionCategory
- MonthlyPayslipSerializer
- TokenObtainPairSerializer
- career/views.py
- RequestManager
- TransactionBulkService
- .get_account_from_id
- generate_dev_token.py
- rules/graphify.md
- workflows/graphify.md
- core/__init__.py
- .get_subscriptions_radar
- career/__init__.py
- career/migrations/__init__.py
- settings.py
- Command

## God Nodes (most connected - your core abstractions)
1. `get_current_user()` - 35 edges
2. `CategoryService` - 31 edges
3. `Transaction` - 31 edges
4. `MonthlyPayslip` - 29 edges
5. `DashboardService` - 29 edges
6. `TransactionImportService` - 29 edges
7. `TransactionListService` - 29 edges
8. `AnalyticsService` - 25 edges
9. `Employment` - 24 edges
10. `CareerDocument` - 24 edges

## Surprising Connections (you probably didn't know these)
- `4. Client Review & Save Workflow` --references--> `Employment`  [INFERRED]
  docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md → finance/career/models.py
- `Global Constraints` --references--> `MonthlyPayslip`  [INFERRED]
  docs/superpowers/plans/2026-09-27-payslip-ingestion.md → finance/career/models.py
- `1. Executive Summary` --references--> `MonthlyPayslip`  [INFERRED]
  docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md → finance/career/models.py
- `3.1 Extraction Pipeline Flow (`POST /api/career/payslips/extract/`)` --references--> `MonthlyPayslip`  [INFERRED]
  docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md → finance/career/models.py
- `Task 2: AI Extraction Service` --references--> `extract_payslip_data()`  [INFERRED]
  docs/superpowers/plans/2026-09-27-payslip-ingestion.md → finance/career/services/payslip_extraction_service.py

## Import Cycles
- None detected.

## Communities (112 total, 57 thin omitted)

### Community 0 - "transaction_import_service.py"
Cohesion: 0.14
Nodes (16): calendar, collections, decimal, django_db_models, django_db_models_functions, django_utils, Meta, Transaction (+8 more)

### Community 1 - "card_loaders.py"
Cohesion: 0.06
Nodes (23): AccountProviders, AccountTypes, DataSource, Enum, BaseLoader, DocomoCardLoader, EposCardLoader, MizuhoBankLoader (+15 more)

### Community 2 - "SettingsService"
Cohesion: 0.11
Nodes (13): Account, Meta, AccountSerializer, Meta, ResponseAccountSerializer, AccountService, object, patch (+5 more)

### Community 3 - "DashboardService"
Cohesion: 0.11
Nodes (11): DashboardService, Get the monthly transaction summary. Args: transaction_type (str): The…, Get the monthly transaction category summary. Args: transaction_type (str): The…, Calculates income, expense, payment, and savings aggregated by month in a…, Get the account wise sum. Args: transaction_type (str): The transaction type.…, Get the top ten expenses. If year is provided, aggregates by destination with…, Get top ten aggregated expenses for the latest active month of the given year., Get the monthly payment destination wise sum. Args: transaction_type (str): The… (+3 more)

### Community 4 - "get_current_user"
Cohesion: 0.09
Nodes (12): clear_current_user(), get_current_user(), Middleware to make the current request globally accessible. Guarantees thread-…, ThreadLocalMiddleware, TestHealthCheckEndpoint, TestPasswordResetSecurity, TestThreadLocalSecurity, dummy_view() (+4 more)

### Community 5 - "PayeeService"
Cohesion: 0.12
Nodes (10): Meta, ResponseDestinationMapSerializer, PayeeService, Updates the payee. Args: request_data (dict): The request data. Returns: tuple:…, Gets the custom queryset for the payee. Returns: QuerySet: The custom queryset…, object, patch, TestPayeeService (+2 more)

### Community 6 - "django_apps"
Cohesion: 0.07
Nodes (19): AccountsConfig, AppConfig, ChangelogConfig, AppConfig, django_apps, CareerConfig, AppConfig, CategoriesConfig (+11 more)

### Community 7 - ".import_transactions"
Cohesion: 0.15
Nodes (5): Gets the payee map. Returns: DataFrame: The payee map., Gets the rewrite rules. Args: payee_maps (DataFrame): The payee maps. Returns:…, Finds the new payees. Args: payees (DataFrame): The payees. transactions…, Assigns the category IDs to the transactions. Args: payees (DataFrame): The…, Imports the transactions from the provided files. Args: import_params (dict):…

### Community 8 - "TestTransactionView"
Cohesion: 0.09
Nodes (6): mock_bulk_service(), mock_transaction_service(), django_db, fixture, TestTransactionBulkView, TestTransactionView

### Community 9 - "rest_framework"
Cohesion: 0.06
Nodes (32): CreditAccountView, APIView, ActionEnum, ChangeLog, SectionEnum, ChangeLogSerializer, Meta, get_changes() (+24 more)

### Community 10 - "core/urls.py"
Cohesion: 0.07
Nodes (22): ASGI config for personalfinance project. It exposes the ASGI callable as a…, URL configuration for personalfinance project. The `urlpatterns` list routes…, Serves the Single Page Application (SPA) entry point (index.html). All non-API…, spa_index_view(), WSGI config for personalfinance project. It exposes the WSGI callable as a…, django_conf_urls_static, django_contrib, django_contrib_auth_admin (+14 more)

### Community 11 - "MonthlyPayslip"
Cohesion: 0.10
Nodes (23): Global Constraints, Payslip Ingestion Implementation Plan, Review Focus, Task 1: GCS Storage Service, Task 2: AI Extraction Service, Task 3: Extraction API Endpoint, Task 4: Save Workflow API Endpoint, 1. Executive Summary (+15 more)

### Community 12 - "CompensationHistory"
Cohesion: 0.16
Nodes (7): CompensationHistory, Tracks multi-year compensation revisions, annual raises, promotions, and…, Monthly guaranteed pay = base salary + fixed allowances (normalized to monthly), Annual guaranteed base (固定年俸 / Base + Allowances * 12), Total expected annual package (総年収 / OTE) = (Base + Allowances) * 12 + Annual…, CompensationHistorySerializer, CompensationHistoryView

### Community 14 - "CategoryService"
Cohesion: 0.15
Nodes (7): CategoryService, Updates a category, deletes requested subcategories, and updates/creates…, object, patch, TestCategoryService, CategorySettingsView, APIView

### Community 15 - "TransactionListService"
Cohesion: 0.18
Nodes (3): TransactionListService, TestGroupByOptimization, TransactionView

### Community 16 - "StorageBackendContract"
Cohesion: 0.14
Nodes (9): Any, Upload a file or stream to the storage backend., Read a file and return a readable stream or file-like object., List file paths in storage matching the given prefix., Delete a file from the storage backend., Read all files matching the prefix into a list of file-like streams., Read a CSV file into a pandas DataFrame., Abstract contract defining file storage operations across different storage… (+1 more)

### Community 17 - "AnalyticsService"
Cohesion: 0.24
Nodes (5): AnalyticsService, AnalyticsView, AuditReportsView, APIView, SubscriptionRadarView

### Community 18 - "import_workflow.py"
Cohesion: 0.25
Nodes (8): django_core_files_storage, google_cloud, logging, pandas, time, typing, ABC, StorageBackendProvider

### Community 19 - "test_workflows.py"
Cohesion: 0.26
Nodes (5): WorkflowContextType, TestLocalStorage, TestUploadWorkflow, Any, UploadWorkflow

### Community 20 - "Employment"
Cohesion: 0.20
Nodes (16): CompanyProfile, Employment, Meta, Returns the latest compensation revision record, if any., Represents an employment tenure with an employer entity (legal contract and…, Represents a company entity (Direct Employer, Staffing/Dispatch Agency, or…, api_client(), django_db (+8 more)

### Community 21 - "TestTransactionImportView"
Cohesion: 0.11
Nodes (10): django_core_files_uploadedfile, api_client(), django_db, fixture, test_extract_endpoint_calls_service_and_returns_json(), test_extract_endpoint_returns_400_for_non_pdf(), mock_import_service(), django_db (+2 more)

### Community 22 - "career/admin.py"
Cohesion: 0.14
Nodes (17): CareerDocumentAdmin, CareerDocumentInline, CompanyProfileAdmin, CompensationHistoryAdmin, CompensationHistoryInline, DispatchAssignmentAdmin, DispatchAssignmentInline, EmploymentAdmin (+9 more)

### Community 23 - "TestCategorySettingsView"
Cohesion: 0.14
Nodes (4): mock_category_service(), django_db, fixture, TestCategorySettingsView

### Community 24 - "ProfileSerializer"
Cohesion: 0.18
Nodes (7): action, CreateModelMixin, GenericViewSet, ProfileSerializer, ProfileViewSet, RetrieveModelMixin, UpdateModelMixin

### Community 25 - "django_db"
Cohesion: 0.10
Nodes (17): Migration, Migration, django_conf, django_contrib_auth_models, django_contrib_auth_validators, django_db, django_db_models_deletion, django_utils_timezone (+9 more)

### Community 26 - "CompanyProfileSerializer"
Cohesion: 0.14
Nodes (7): CareerDocumentSerializer, CompanyProfileSerializer, Meta, CareerDocumentView, CompanyProfileView, PayslipSaveView, APIView

### Community 27 - "TestPayeeView"
Cohesion: 0.17
Nodes (4): mock_payee_service(), django_db, fixture, TestPayeeView

### Community 28 - "TransactionImportService"
Cohesion: 0.31
Nodes (5): TransactionImportService, APIView, TransactionBulkView, TransactionImportView, rest_framework_parsers

### Community 29 - "TestAccountsView"
Cohesion: 0.18
Nodes (4): mock_category_service(), django_db, fixture, TestAccountsView

### Community 30 - "extract_payslip_data"
Cohesion: 0.21
Nodes (15): BaseModel, dateutil, extract_payslip_data(), PayslipSchema, test_extract_payslip_data_fails_on_1_yen_mismatch(), test_extract_payslip_data_fallback(), test_extract_payslip_data_handles_nontaxable_commutation(), test_extract_payslip_data_includes_other_descriptions_and_notes() (+7 more)

### Community 31 - "pytest"
Cohesion: 0.18
Nodes (6): django_test, mock_dashboard_service(), django_db, fixture, TestDashboardView, pytest

### Community 32 - "CareerOverviewView"
Cohesion: 0.18
Nodes (6): DispatchAssignmentSerializer, TaxWithholdingSlipSerializer, CareerOverviewView, DispatchAssignmentView, Returns an aggregated summary for the Career Hub dashboard: - Current…, TaxWithholdingSlipView

### Community 33 - "test_analytics.py"
Cohesion: 0.22
Nodes (5): mock_analytics_service(), django_db, fixture, TestAnalyticsServiceDirect, TestAnalyticsView

### Community 34 - "LocalStorageHandler"
Cohesion: 0.33
Nodes (3): LocalStorageHandler, Any, DataFrame

### Community 35 - "User"
Cohesion: 0.18
Nodes (9): AbstractUser, django_core_management, generate_signed_url(), Generates a signed URL to view the document., test_generate_signed_url_enforces_user_ownership(), test_generate_signed_url_handles_local_scheme(), User, django_db (+1 more)

### Community 36 - "oauth/views.py"
Cohesion: 0.22
Nodes (8): base64, django_contrib_auth, django_contrib_auth_tokens, rest_framework_decorators, rest_framework_mixins, rest_framework_permissions, rest_framework_simplejwt_views, rest_framework_viewsets

### Community 37 - "oauth/models.py"
Cohesion: 0.28
Nodes (6): BaseUserCreateSerializer, djoser_serializers, Profile, Meta, UserCreateSerializer, rest_framework_simplejwt_serializers

### Community 38 - "GCSHandler"
Cohesion: 0.14
Nodes (9): GCSHandler, Reads a CSV file from the GCS bucket. Args: file_name (str): The name of the…, A handler for interacting with Google Cloud Storage (GCS). Provides methods for…, Initializes the GCSHandler with a specified bucket name. Args: bucket_name…, Uploads a file to the GCS bucket with retry logic. Args: file (file-like…, Lists files in the GCS bucket with optional filtering and pagination. Args:…, Deletes a file from the specified bucket., Reads a file from the GCS bucket. Args: file_name (str): The name of the file… (+1 more)

### Community 39 - "TestSpaServing"
Cohesion: 0.22
Nodes (3): django_db, fixture, TestSpaServing

### Community 40 - "test_audit_reports.py"
Cohesion: 0.25
Nodes (5): mock_analytics_service(), django_db, fixture, TestAuditReportsServiceDirect, TestAuditReportsView

### Community 41 - "test_subscriptions.py"
Cohesion: 0.25
Nodes (5): mock_analytics_service(), django_db, fixture, TestSubscriptionRadarService, TestSubscriptionRadarView

### Community 42 - "ResponseTransactionSerializer"
Cohesion: 0.22
Nodes (4): DateSerializeHelper, Meta, object, ResponseTransactionSerializer

### Community 43 - "ImportCsvWorkflow"
Cohesion: 0.23
Nodes (4): ImportCsvWorkflow, DataFrame, DummyProcessor, TestImportCsvWorkflow

### Community 44 - "TestClientSettings"
Cohesion: 0.25
Nodes (4): mock_settings_service(), django_db, fixture, TestClientSettings

### Community 45 - "Q: how does the dashboard service connect to the database layer"
Cohesion: 0.50
Nodes (3): Answer, Q: how does the dashboard service connect to the database layer, Source Nodes

### Community 46 - "conftest.py"
Cohesion: 0.33
Nodes (5): api_client(), authenticate(), fixture, model_bakery, rest_framework_test

### Community 47 - "Q: how transaction import flow working"
Cohesion: 0.50
Nodes (3): Answer, Q: how transaction import flow working, Source Nodes

### Community 48 - "TransactionCategory"
Cohesion: 0.37
Nodes (8): Meta, TransactionCategory, TransactionSubCategory, Meta, ResponseTransactionCategorySerializer, ResponseTransactionSubCategorySerializer, TransactionCategorySerializer, TransactionSubCategorySerializer

### Community 50 - "TokenObtainPairSerializer"
Cohesion: 0.33
Nodes (4): BaseTokenObtainPairSerializer, BaseTokenObtainPairView, TokenObtainPairSerializer, TokenObtainPairView

### Community 51 - "career/views.py"
Cohesion: 0.27
Nodes (9): datetime, django_core_exceptions, _safe_date_or_none(), Uploads a payslip PDF to GCS or Local Storage and returns the URI., upload_payslip_document(), test_upload_payslip_document_constructs_correct_path(), _safe_float(), _safe_float_or_none() (+1 more)

### Community 52 - "RequestManager"
Cohesion: 0.33
Nodes (5): DestinationMap, Meta, DestinationMapSerializer, TestRequestManagerSafety, RequestManager

### Community 53 - "TransactionBulkService"
Cohesion: 0.21
Nodes (4): TransactionBulkService, django_db, patch, TestTransactionServices

### Community 54 - ".get_account_from_id"
Cohesion: 0.25
Nodes (3): Uploads the transaction files. Args: upload_params (dict): The upload…, Gets the account from the provided account ID. Args: account_id (int): The…, Gets the applicable transactions. Args: transaction_data (DataFrame): The…

### Community 55 - "generate_dev_token.py"
Cohesion: 0.29
Nodes (4): django_core_management_base, Command, BaseCommand, rest_framework_simplejwt_tokens

### Community 110 - "settings.py"
Cohesion: 0.33
Nodes (5): Django settings for personalfinance project. Generated by 'django-admin…, decouple, dotenv, io, pathlib

## Knowledge Gaps
- **24 isolated node(s):** `Migration`, `Meta`, `Migration`, `Meta`, `Migration` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 393 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **57 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Transaction` connect `transaction_import_service.py` to `SettingsService`, `DashboardService`, `get_current_user`, `PayeeService`, `.import_transactions`, `rest_framework`, `ResponseTransactionSerializer`, `CategoryService`, `Command`, `TransactionCategory`, `AnalyticsService`, `TransactionListService`, `RequestManager`, `TransactionBulkService`, `django_db`, `TransactionImportService`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Why does `DashboardService` connect `DashboardService` to `transaction_import_service.py`, `rest_framework`, `SettingsService`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `RequestManager` connect `RequestManager` to `transaction_import_service.py`, `SettingsService`, `get_current_user`, `MonthlyPayslip`, `CompensationHistory`, `TransactionCategory`, `Employment`, `career/admin.py`, `django_db`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `CategoryService` (e.g. with `TransactionCategory` and `TransactionSubCategory`) actually correct?**
  _`CategoryService` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Transaction` (e.g. with `TestActivityView` and `ActivityView`) actually correct?**
  _`Transaction` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `MonthlyPayslip` (e.g. with `Global Constraints` and `Payslip Ingestion Implementation Plan`) actually correct?**
  _`MonthlyPayslip` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `DashboardService` (e.g. with `Transaction` and `TestDashboardService`) actually correct?**
  _`DashboardService` has 3 INFERRED edges - model-reasoned connections that need verification._