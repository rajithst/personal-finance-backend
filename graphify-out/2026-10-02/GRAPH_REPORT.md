# Graph Report - personalfinance  (2026-10-02)

## Corpus Check
- 183 files · ~38,127 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 5, .example 1, .ini 1)

## Summary
- 1051 nodes · 2090 edges · 100 communities (44 shown, 56 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 232 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c764f142`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Transaction
- card_loaders.py
- AccountService
- DashboardService
- get_current_user
- PayeeService
- django_apps
- TransactionImportService
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
- User
- career/admin.py
- TestCategorySettingsView
- oauth/views.py
- transaction_import_service.py
- CompanyProfileSerializer
- TestPayeeView
- career/serializers.py
- TestAccountsView
- extract_payslip_data
- TestDashboardView
- career/views.py
- 0002_alter_changelog_section.py
- LocalStorageHandler
- CareerDocumentSerializer
- test_security.py
- GCSHandler
- TestSpaServing
- ImportCsvWorkflow
- TestClientSettings
- Q: how does the dashboard service connect to the database layer
- Q: how transaction import flow working
- test_storage_service.py
- pytest
- DestinationMap
- rules/graphify.md
- workflows/graphify.md
- core/__init__.py
- career/__init__.py
- career/migrations/__init__.py
- settings.py

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

## Communities (100 total, 56 thin omitted)

### Community 0 - "Transaction"
Cohesion: 0.10
Nodes (14): calendar, decimal, Meta, Transaction, DateSerializeHelper, Meta, object, ResponseTransactionSerializer (+6 more)

### Community 1 - "card_loaders.py"
Cohesion: 0.07
Nodes (23): AccountProviders, AccountTypes, DataSource, Enum, BaseLoader, DocomoCardLoader, EposCardLoader, MizuhoBankLoader (+15 more)

### Community 2 - "AccountService"
Cohesion: 0.28
Nodes (6): AccountSerializer, Meta, ResponseAccountSerializer, AccountService, object, patch

### Community 3 - "DashboardService"
Cohesion: 0.11
Nodes (11): DashboardService, Get the monthly transaction summary. Args: transaction_type (str): The…, Get the monthly transaction category summary. Args: transaction_type (str): The…, Calculates income, expense, payment, and savings aggregated by month in a…, Get the account wise sum. Args: transaction_type (str): The transaction type.…, Get the top ten expenses. If year is provided, aggregates by destination with…, Get top ten aggregated expenses for the latest active month of the given year., Get the monthly payment destination wise sum. Args: transaction_type (str): The… (+3 more)

### Community 4 - "get_current_user"
Cohesion: 0.12
Nodes (7): get_current_user(), Middleware to make the current request globally accessible. Guarantees thread-…, ThreadLocalMiddleware, TestThreadLocalSecurity, dummy_view(), exploding_view(), CronManager

### Community 5 - "PayeeService"
Cohesion: 0.12
Nodes (10): Meta, ResponseDestinationMapSerializer, PayeeService, Updates the payee. Args: request_data (dict): The request data. Returns: tuple:…, Gets the custom queryset for the payee. Returns: QuerySet: The custom queryset…, object, patch, TestPayeeService (+2 more)

### Community 6 - "django_apps"
Cohesion: 0.07
Nodes (19): AccountsConfig, AppConfig, ChangelogConfig, AppConfig, django_apps, CareerConfig, AppConfig, CategoriesConfig (+11 more)

### Community 7 - "TransactionImportService"
Cohesion: 0.11
Nodes (11): Uploads the transaction files. Args: upload_params (dict): The upload…, Gets the account from the provided account ID. Args: account_id (int): The…, Gets the applicable transactions. Args: transaction_data (DataFrame): The…, Gets the payee map. Returns: DataFrame: The payee map., Gets the rewrite rules. Args: payee_maps (DataFrame): The payee maps. Returns:…, Finds the new payees. Args: payees (DataFrame): The payees. transactions…, Assigns the category IDs to the transactions. Args: payees (DataFrame): The…, Imports the transactions from the provided files. Args: import_params (dict):… (+3 more)

### Community 8 - "TestTransactionView"
Cohesion: 0.09
Nodes (6): mock_bulk_service(), mock_transaction_service(), django_db, fixture, TestTransactionBulkView, TestTransactionView

### Community 9 - "rest_framework"
Cohesion: 0.07
Nodes (31): CreditAccountView, APIView, ActionEnum, ChangeLog, SectionEnum, ChangeLogSerializer, Meta, get_changes() (+23 more)

### Community 10 - "core/urls.py"
Cohesion: 0.12
Nodes (13): URL configuration for personalfinance project. The `urlpatterns` list routes…, Serves the Single Page Application (SPA) entry point (index.html). All non-API…, spa_index_view(), django_conf_urls_static, django_contrib, django_contrib_auth_admin, django_http, AccountAdmin (+5 more)

### Community 11 - "MonthlyPayslip"
Cohesion: 0.12
Nodes (20): Global Constraints, Payslip Ingestion Implementation Plan, Review Focus, Task 1: GCS Storage Service, Task 2: AI Extraction Service, Task 3: Extraction API Endpoint, Task 4: Save Workflow API Endpoint, 1. Executive Summary (+12 more)

### Community 12 - "CompensationHistory"
Cohesion: 0.16
Nodes (7): CompensationHistory, Tracks multi-year compensation revisions, annual raises, promotions, and…, Monthly guaranteed pay = base salary + fixed allowances (normalized to monthly), Annual guaranteed base (固定年俸 / Base + Allowances * 12), Total expected annual package (総年収 / OTE) = (Base + Allowances) * 12 + Annual…, CompensationHistorySerializer, CompensationHistoryView

### Community 14 - "CategoryService"
Cohesion: 0.09
Nodes (18): Meta, TransactionCategory, TransactionSubCategory, Meta, ResponseTransactionCategorySerializer, ResponseTransactionSubCategorySerializer, TransactionCategorySerializer, TransactionSubCategorySerializer (+10 more)

### Community 15 - "TransactionListService"
Cohesion: 0.13
Nodes (8): TransactionListService, TestGroupByOptimization, patch, APIView, TransactionBulkView, TransactionImportView, TransactionView, rest_framework_parsers

### Community 16 - "StorageBackendContract"
Cohesion: 0.13
Nodes (10): ABC, Any, Upload a file or stream to the storage backend., Read a file and return a readable stream or file-like object., List file paths in storage matching the given prefix., Delete a file from the storage backend., Read all files matching the prefix into a list of file-like streams., Read a CSV file into a pandas DataFrame. (+2 more)

### Community 17 - "AnalyticsService"
Cohesion: 0.07
Nodes (21): AnalyticsService, Detects recurring contracts, subscriptions, utility bills, and cadences.…, mock_analytics_service(), django_db, fixture, TestAnalyticsServiceDirect, TestAnalyticsView, mock_analytics_service() (+13 more)

### Community 18 - "import_workflow.py"
Cohesion: 0.30
Nodes (6): django_core_files_storage, logging, pandas, time, typing, StorageBackendProvider

### Community 19 - "test_workflows.py"
Cohesion: 0.26
Nodes (5): WorkflowContextType, TestLocalStorage, TestUploadWorkflow, Any, UploadWorkflow

### Community 20 - "Employment"
Cohesion: 0.20
Nodes (16): CompanyProfile, Employment, Meta, Returns the latest compensation revision record, if any., Represents an employment tenure with an employer entity (legal contract and…, Represents a company entity (Direct Employer, Staffing/Dispatch Agency, or…, api_client(), django_db (+8 more)

### Community 21 - "User"
Cohesion: 0.05
Nodes (28): AbstractUser, api_client(), authenticate(), fixture, django_core_files_uploadedfile, django_core_management, django_core_management_base, generate_signed_url() (+20 more)

### Community 22 - "career/admin.py"
Cohesion: 0.21
Nodes (13): CareerDocumentAdmin, CareerDocumentInline, CompanyProfileAdmin, CompensationHistoryAdmin, CompensationHistoryInline, DispatchAssignmentAdmin, DispatchAssignmentInline, EmploymentAdmin (+5 more)

### Community 23 - "TestCategorySettingsView"
Cohesion: 0.14
Nodes (4): mock_category_service(), django_db, fixture, TestCategorySettingsView

### Community 24 - "oauth/views.py"
Cohesion: 0.06
Nodes (29): action, base64, BaseTokenObtainPairSerializer, BaseTokenObtainPairView, BaseUserCreateSerializer, CreateModelMixin, django_contrib_auth, django_contrib_auth_tokens (+21 more)

### Community 25 - "transaction_import_service.py"
Cohesion: 0.13
Nodes (19): Migration, Account, Meta, Migration, django_conf, django_contrib_auth_models, django_contrib_auth_validators, django_db (+11 more)

### Community 27 - "TestPayeeView"
Cohesion: 0.17
Nodes (4): mock_payee_service(), django_db, fixture, TestPayeeView

### Community 28 - "career/serializers.py"
Cohesion: 0.27
Nodes (4): DispatchAssignment, Tracks dispatched company assignments (dispatched company, start date, end…, DispatchAssignmentSerializer, DispatchAssignmentView

### Community 29 - "TestAccountsView"
Cohesion: 0.18
Nodes (4): mock_category_service(), django_db, fixture, TestAccountsView

### Community 30 - "extract_payslip_data"
Cohesion: 0.21
Nodes (15): BaseModel, dateutil, extract_payslip_data(), PayslipSchema, test_extract_payslip_data_fails_on_1_yen_mismatch(), test_extract_payslip_data_fallback(), test_extract_payslip_data_handles_nontaxable_commutation(), test_extract_payslip_data_includes_other_descriptions_and_notes() (+7 more)

### Community 32 - "career/views.py"
Cohesion: 0.16
Nodes (13): Annual Withholding Tax Certificate (源泉徴収票 / Gensen-Choshu-Hyo). Matches the…, TaxWithholdingSlip, TaxWithholdingSlipSerializer, _safe_date_or_none(), CareerOverviewView, PayslipExtractView, PayslipSaveView, APIView (+5 more)

### Community 33 - "0002_alter_changelog_section.py"
Cohesion: 0.11
Nodes (5): Migration, Migration, Migration, Migration, Migration

### Community 34 - "LocalStorageHandler"
Cohesion: 0.33
Nodes (3): LocalStorageHandler, Any, DataFrame

### Community 35 - "CareerDocumentSerializer"
Cohesion: 0.38
Nodes (3): CareerDocumentSerializer, Meta, CareerDocumentView

### Community 36 - "test_security.py"
Cohesion: 0.29
Nodes (3): clear_current_user(), TestHealthCheckEndpoint, TestRequestManagerSafety

### Community 38 - "GCSHandler"
Cohesion: 0.14
Nodes (9): GCSHandler, Reads a CSV file from the GCS bucket. Args: file_name (str): The name of the…, A handler for interacting with Google Cloud Storage (GCS). Provides methods for…, Initializes the GCSHandler with a specified bucket name. Args: bucket_name…, Uploads a file to the GCS bucket with retry logic. Args: file (file-like…, Lists files in the GCS bucket with optional filtering and pagination. Args:…, Deletes a file from the specified bucket., Reads a file from the GCS bucket. Args: file_name (str): The name of the file… (+1 more)

### Community 39 - "TestSpaServing"
Cohesion: 0.18
Nodes (4): django_db, fixture, TestSpaServing, django_test

### Community 43 - "ImportCsvWorkflow"
Cohesion: 0.23
Nodes (4): ImportCsvWorkflow, DataFrame, DummyProcessor, TestImportCsvWorkflow

### Community 44 - "TestClientSettings"
Cohesion: 0.25
Nodes (4): mock_settings_service(), django_db, fixture, TestClientSettings

### Community 45 - "Q: how does the dashboard service connect to the database layer"
Cohesion: 0.50
Nodes (3): Answer, Q: how does the dashboard service connect to the database layer, Source Nodes

### Community 47 - "Q: how transaction import flow working"
Cohesion: 0.50
Nodes (3): Answer, Q: how transaction import flow working, Source Nodes

### Community 49 - "test_storage_service.py"
Cohesion: 0.19
Nodes (8): django_core_exceptions, MonthlyPayslipSerializer, Uploads a payslip PDF to GCS or Local Storage and returns the URI., upload_payslip_document(), django_db, test_career_document_and_payslip_file_url_resolution(), test_upload_payslip_document_constructs_correct_path(), MonthlyPayslipView

### Community 51 - "pytest"
Cohesion: 0.14
Nodes (11): TestAccountService, collections, datetime, django_db_models, django_db_models_functions, django_utils, mock_dashboard_service(), fixture (+3 more)

### Community 52 - "DestinationMap"
Cohesion: 0.27
Nodes (5): DestinationMap, Meta, DestinationMapSerializer, Command, BaseCommand

### Community 110 - "settings.py"
Cohesion: 0.11
Nodes (15): ASGI config for personalfinance project. It exposes the ASGI callable as a…, Django settings for personalfinance project. Generated by 'django-admin…, WSGI config for personalfinance project. It exposes the WSGI callable as a…, decouple, django_core_asgi, django_core_wsgi, dotenv, google_cloud (+7 more)

## Knowledge Gaps
- **26 isolated node(s):** `Migration`, `Meta`, `Migration`, `Migration`, `Meta` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 395 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **56 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Transaction` connect `Transaction` to `DashboardService`, `get_current_user`, `PayeeService`, `TransactionImportService`, `rest_framework`, `CategoryService`, `TransactionListService`, `AnalyticsService`, `pytest`, `DestinationMap`, `transaction_import_service.py`?**
  _High betweenness centrality (0.120) - this node is a cross-community bridge._
- **Why does `DashboardService` connect `DashboardService` to `Transaction`, `rest_framework`, `pytest`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `RequestManager` connect `transaction_import_service.py` to `career/views.py`, `Transaction`, `test_security.py`, `get_current_user`, `MonthlyPayslip`, `CompensationHistory`, `CategoryService`, `Employment`, `DestinationMap`, `career/serializers.py`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `CategoryService` (e.g. with `TransactionCategory` and `TransactionSubCategory`) actually correct?**
  _`CategoryService` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Transaction` (e.g. with `TestActivityView` and `ActivityView`) actually correct?**
  _`Transaction` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `MonthlyPayslip` (e.g. with `Global Constraints` and `Payslip Ingestion Implementation Plan`) actually correct?**
  _`MonthlyPayslip` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `DashboardService` (e.g. with `Transaction` and `TestDashboardService`) actually correct?**
  _`DashboardService` has 3 INFERRED edges - model-reasoned connections that need verification._