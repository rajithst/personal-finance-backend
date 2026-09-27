# Graph Report - personalfinance  (2026-09-27)

## Corpus Check
- 173 files · ~32,920 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 5, .example 1, .ini 1)

## Summary
- 981 nodes · 1905 edges · 108 communities (48 shown, 60 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 193 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6c519cd1`
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
- settings.py
- MonthlyPayslip
- career/views.py
- EmploymentSerializer
- ResponseTransactionSerializer
- TransactionListService
- Any
- AnalyticsService
- StorageBackendContract
- test_workflows.py
- CompensationHistorySerializer
- TestTransactionImportView
- career/admin.py
- TestCategorySettingsView
- ProfileSerializer
- django_conf
- CompanyProfileSerializer
- TestPayeeView
- transactions/views.py
- TestAccountsView
- core/urls.py
- pytest
- TaxWithholdingSlipSerializer
- test_analytics.py
- LocalStorageHandler
- User
- oauth/views.py
- oauth/models.py
- .read_all_files
- TestSpaServing
- test_audit_reports.py
- test_subscriptions.py
- DateSerializeHelper
- ImportCsvWorkflow
- TestClientSettings
- Q: how does the dashboard service connect to the database layer
- conftest.py
- Q: how transaction import flow working
- DispatchAssignmentSerializer
- CareerOverviewView
- TokenObtainPairSerializer
- transactions/admin.py
- oauth/admin.py
- TestTransactionServices
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
4. `DashboardService` - 29 edges
5. `TransactionImportService` - 29 edges
6. `TransactionListService` - 29 edges
7. `AnalyticsService` - 25 edges
8. `RequestManager` - 23 edges
9. `DestinationMap` - 22 edges
10. `PayeeService` - 22 edges

## Surprising Connections (you probably didn't know these)
- `4. Client Review & Save Workflow` --references--> `Employment`  [INFERRED]
  docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md → finance/career/models.py
- `1. Executive Summary` --references--> `MonthlyPayslip`  [INFERRED]
  docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md → finance/career/models.py
- `3.1 Extraction Pipeline Flow (`POST /api/career/payslips/extract/`)` --references--> `MonthlyPayslip`  [INFERRED]
  docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md → finance/career/models.py
- `4. Client Review & Save Workflow` --references--> `CareerDocument`  [INFERRED]
  docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md → finance/career/models.py
- `5. Security & Access Control` --references--> `CareerDocument`  [INFERRED]
  docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md → finance/career/models.py

## Import Cycles
- None detected.

## Communities (108 total, 60 thin omitted)

### Community 0 - "transaction_import_service.py"
Cohesion: 0.06
Nodes (43): calendar, collections, datetime, decimal, django_db, django_db_models, django_db_models_functions, django_utils (+35 more)

### Community 1 - "card_loaders.py"
Cohesion: 0.06
Nodes (23): AccountProviders, AccountTypes, DataSource, Enum, BaseLoader, DocomoCardLoader, EposCardLoader, MizuhoBankLoader (+15 more)

### Community 2 - "SettingsService"
Cohesion: 0.12
Nodes (12): Account, Meta, AccountSerializer, Meta, ResponseAccountSerializer, AccountService, object, patch (+4 more)

### Community 3 - "DashboardService"
Cohesion: 0.11
Nodes (11): DashboardService, Get the monthly transaction summary. Args: transaction_type (str): The…, Get the monthly transaction category summary. Args: transaction_type (str): The…, Calculates income, expense, payment, and savings aggregated by month in a…, Get the account wise sum. Args: transaction_type (str): The transaction type.…, Get the top ten expenses. If year is provided, aggregates by destination with…, Get top ten aggregated expenses for the latest active month of the given year., Get the monthly payment destination wise sum. Args: transaction_type (str): The… (+3 more)

### Community 4 - "get_current_user"
Cohesion: 0.08
Nodes (13): clear_current_user(), get_current_user(), Middleware to make the current request globally accessible. Guarantees thread-…, ThreadLocalMiddleware, TestHealthCheckEndpoint, TestPasswordResetSecurity, TestThreadLocalSecurity, dummy_view() (+5 more)

### Community 5 - "PayeeService"
Cohesion: 0.12
Nodes (10): Meta, ResponseDestinationMapSerializer, PayeeService, Updates the payee. Args: request_data (dict): The request data. Returns: tuple:…, Gets the custom queryset for the payee. Returns: QuerySet: The custom queryset…, object, patch, TestPayeeService (+2 more)

### Community 6 - "django_apps"
Cohesion: 0.07
Nodes (19): AccountsConfig, AppConfig, ChangelogConfig, AppConfig, django_apps, CareerConfig, AppConfig, CategoriesConfig (+11 more)

### Community 7 - "TransactionImportService"
Cohesion: 0.11
Nodes (10): Uploads the transaction files. Args: upload_params (dict): The upload…, Gets the account from the provided account ID. Args: account_id (int): The…, Gets the applicable transactions. Args: transaction_data (DataFrame): The…, Gets the payee map. Returns: DataFrame: The payee map., Gets the rewrite rules. Args: payee_maps (DataFrame): The payee maps. Returns:…, Finds the new payees. Args: payees (DataFrame): The payees. transactions…, Assigns the category IDs to the transactions. Args: payees (DataFrame): The…, Imports the transactions from the provided files. Args: import_params (dict):… (+2 more)

### Community 8 - "TestTransactionView"
Cohesion: 0.09
Nodes (6): mock_bulk_service(), mock_transaction_service(), django_db, fixture, TestTransactionBulkView, TestTransactionView

### Community 9 - "rest_framework"
Cohesion: 0.07
Nodes (31): CreditAccountView, APIView, ActionEnum, ChangeLog, SectionEnum, ChangeLogSerializer, Meta, get_changes() (+23 more)

### Community 10 - "settings.py"
Cohesion: 0.11
Nodes (15): ASGI config for personalfinance project. It exposes the ASGI callable as a…, Django settings for personalfinance project. Generated by 'django-admin…, WSGI config for personalfinance project. It exposes the WSGI callable as a…, decouple, django_core_asgi, django_core_wsgi, dotenv, google_cloud (+7 more)

### Community 11 - "MonthlyPayslip"
Cohesion: 0.16
Nodes (13): 1. Executive Summary, 2.1 Storage Folder Hierarchy & Path Construction, 2.2 GCS Object Metadata, 2. Cloud Storage (GCS) Directory Architecture, 3.1 Extraction Pipeline Flow (`POST /api/career/payslips/extract/`), 3. Automated Extraction Engine (Stateless Flow), 4. Client Review & Save Workflow, 5. Security & Access Control (+5 more)

### Community 12 - "career/views.py"
Cohesion: 0.14
Nodes (12): CompanyProfile, CompensationHistory, DispatchAssignment, Meta, Tracks multi-year compensation revisions, annual raises, promotions, and…, Monthly guaranteed pay = base salary + fixed allowances (normalized to monthly), Annual guaranteed base (固定年俸 / Base + Allowances * 12), Total expected annual package (総年収 / OTE) = (Base + Allowances) * 12 + Annual… (+4 more)

### Community 13 - "EmploymentSerializer"
Cohesion: 0.16
Nodes (5): Employment, Returns the latest compensation revision record, if any., Represents an employment tenure with an employer entity (legal contract and…, EmploymentSerializer, EmploymentView

### Community 14 - "ResponseTransactionSerializer"
Cohesion: 0.28
Nodes (3): Meta, ResponseTransactionSerializer, TransactionBulkService

### Community 16 - "Any"
Cohesion: 0.22
Nodes (5): Any, Upload a file or stream to the storage backend., Read a file and return a readable stream or file-like object., Read all files matching the prefix into a list of file-like streams., Read a CSV file into a pandas DataFrame.

### Community 17 - "AnalyticsService"
Cohesion: 0.24
Nodes (5): AnalyticsService, AnalyticsView, AuditReportsView, APIView, SubscriptionRadarView

### Community 18 - "StorageBackendContract"
Cohesion: 0.11
Nodes (17): django_core_files_storage, logging, pandas, time, typing, ABC, List file paths in storage matching the given prefix., Delete a file from the storage backend. (+9 more)

### Community 19 - "test_workflows.py"
Cohesion: 0.23
Nodes (5): WorkflowContextType, TestLocalStorage, TestUploadWorkflow, Any, UploadWorkflow

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

### Community 25 - "django_conf"
Cohesion: 0.14
Nodes (12): Migration, Migration, django_conf, django_contrib_auth_models, django_contrib_auth_validators, django_db_models_deletion, django_utils_timezone, Migration (+4 more)

### Community 27 - "TestPayeeView"
Cohesion: 0.17
Nodes (4): mock_payee_service(), django_db, fixture, TestPayeeView

### Community 28 - "transactions/views.py"
Cohesion: 0.31
Nodes (5): APIView, TransactionBulkView, TransactionImportView, TransactionView, rest_framework_parsers

### Community 29 - "TestAccountsView"
Cohesion: 0.18
Nodes (4): mock_category_service(), django_db, fixture, TestAccountsView

### Community 30 - "core/urls.py"
Cohesion: 0.32
Nodes (5): URL configuration for personalfinance project. The `urlpatterns` list routes…, Serves the Single Page Application (SPA) entry point (index.html). All non-API…, spa_index_view(), django_conf_urls_static, django_http

### Community 31 - "pytest"
Cohesion: 0.18
Nodes (6): django_test, mock_dashboard_service(), django_db, fixture, TestDashboardView, pytest

### Community 33 - "test_analytics.py"
Cohesion: 0.22
Nodes (5): mock_analytics_service(), django_db, fixture, TestAnalyticsServiceDirect, TestAnalyticsView

### Community 34 - "LocalStorageHandler"
Cohesion: 0.33
Nodes (3): LocalStorageHandler, Any, DataFrame

### Community 35 - "User"
Cohesion: 0.15
Nodes (9): AbstractUser, django_core_management, django_core_management_base, Command, BaseCommand, User, django_db, TestGenerateDevTokenCommand (+1 more)

### Community 36 - "oauth/views.py"
Cohesion: 0.18
Nodes (10): base64, BaseTokenObtainPairView, django_contrib_auth, django_contrib_auth_tokens, TokenObtainPairView, rest_framework_decorators, rest_framework_mixins, rest_framework_permissions (+2 more)

### Community 37 - "oauth/models.py"
Cohesion: 0.28
Nodes (6): BaseUserCreateSerializer, djoser_serializers, Profile, Meta, UserCreateSerializer, rest_framework_simplejwt_serializers

### Community 38 - ".read_all_files"
Cohesion: 0.33
Nodes (3): Reads a CSV file from the GCS bucket. Args: file_name (str): The name of the…, Lists files in the GCS bucket with optional filtering and pagination. Args:…, Reads all files in the GCS bucket with the specified prefix. Args: prefix…

### Community 39 - "TestSpaServing"
Cohesion: 0.22
Nodes (3): django_db, fixture, TestSpaServing

### Community 40 - "test_audit_reports.py"
Cohesion: 0.25
Nodes (5): mock_analytics_service(), django_db, fixture, TestAuditReportsServiceDirect, TestAuditReportsView

### Community 41 - "test_subscriptions.py"
Cohesion: 0.25
Nodes (5): mock_analytics_service(), django_db, fixture, TestSubscriptionRadarService, TestSubscriptionRadarView

### Community 43 - "ImportCsvWorkflow"
Cohesion: 0.21
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

### Community 48 - "DispatchAssignmentSerializer"
Cohesion: 0.19
Nodes (6): CareerDocumentSerializer, DispatchAssignmentSerializer, Meta, CareerDocumentView, DispatchAssignmentView, APIView

### Community 49 - "CareerOverviewView"
Cohesion: 0.29
Nodes (4): MonthlyPayslipSerializer, CareerOverviewView, MonthlyPayslipView, Returns an aggregated summary for the Career Hub dashboard: - Current…

### Community 51 - "transactions/admin.py"
Cohesion: 0.47
Nodes (4): AccountAdmin, register, TransactionAdmin, TransactionCategoryAdmin

### Community 52 - "oauth/admin.py"
Cohesion: 0.40
Nodes (4): django_contrib, django_contrib_auth_admin, register, UserAdmin

### Community 53 - "TestTransactionServices"
Cohesion: 0.29
Nodes (3): django_db, patch, TestTransactionServices

## Knowledge Gaps
- **22 isolated node(s):** `Migration`, `Meta`, `Migration`, `Meta`, `Migration` (+17 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 382 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **60 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Transaction` connect `transaction_import_service.py` to `SettingsService`, `DashboardService`, `get_current_user`, `PayeeService`, `TransactionImportService`, `rest_framework`, `ResponseTransactionSerializer`, `TransactionListService`, `AnalyticsService`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `RequestManager` connect `transaction_import_service.py` to `SettingsService`, `get_current_user`, `MonthlyPayslip`, `career/views.py`, `EmploymentSerializer`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `DashboardService` connect `DashboardService` to `transaction_import_service.py`, `rest_framework`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `CategoryService` (e.g. with `TransactionCategory` and `TransactionSubCategory`) actually correct?**
  _`CategoryService` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Transaction` (e.g. with `TestActivityView` and `ActivityView`) actually correct?**
  _`Transaction` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `DashboardService` (e.g. with `Transaction` and `TestDashboardService`) actually correct?**
  _`DashboardService` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `TransactionImportService` (e.g. with `Account` and `WorkflowContextType`) actually correct?**
  _`TransactionImportService` has 13 INFERRED edges - model-reasoned connections that need verification._