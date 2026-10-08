# Graph Report - personalfinance  (2026-10-02)

## Corpus Check
- 184 files · ~39,469 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 5, .example 1, .ini 1)

## Summary
- 1083 nodes · 2175 edges · 104 communities (48 shown, 56 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 242 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e5e4d6ac`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TransactionBulkService
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
- MonthlyPayslip
- ImportWorkflowContract
- EmploymentSerializer
- transaction_import_service.py
- TransactionListService
- Any
- AnalyticsService
- django_conf
- test_workflows.py
- Employment
- TestTransactionImportView
- career/admin.py
- TestCategorySettingsView
- oauth/views.py
- django_db_models_deletion
- CompanyProfileSerializer
- TestPayeeView
- career/models.py
- TestAccountsView
- extract_payslip_data
- dashboard/tests/test_views.py
- career/views.py
- CareerDocument
- LocalStorageHandler
- User
- conftest.py
- generate_dev_token.py
- GCSHandler
- TestSpaServing
- TestTransactionServices
- test_payslip_views.py
- DateSerializeHelper
- ImportCsvWorkflow
- TestClientSettings
- Q: how does the dashboard service connect to the database layer
- manage.py
- Q: how transaction import flow working
- test_storage_service.py
- pytest
- rules/graphify.md
- workflows/graphify.md
- core/__init__.py
- career/__init__.py
- career/migrations/__init__.py
- settings.py

## God Nodes (most connected - your core abstractions)
1. `get_current_user()` - 35 edges
2. `CareerDocument` - 32 edges
3. `CategoryService` - 31 edges
4. `Transaction` - 31 edges
5. `MonthlyPayslip` - 29 edges
6. `DashboardService` - 29 edges
7. `TransactionImportService` - 29 edges
8. `TransactionListService` - 29 edges
9. `Employment` - 27 edges
10. `AnalyticsService` - 25 edges

## Surprising Connections (you probably didn't know these)
- `4. Client Review & Save Workflow` --references--> `Employment`  [INFERRED]
  docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md → finance/career/models.py
- `Payslip Ingestion Implementation Plan` --references--> `CareerDocument`  [INFERRED]
  docs/superpowers/plans/2026-09-27-payslip-ingestion.md → finance/career/models.py
- `Task 4: Save Workflow API Endpoint` --references--> `CareerDocument`  [INFERRED]
  docs/superpowers/plans/2026-09-27-payslip-ingestion.md → finance/career/models.py
- `4. Client Review & Save Workflow` --references--> `CareerDocument`  [INFERRED]
  docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md → finance/career/models.py
- `5. Security & Access Control` --references--> `CareerDocument`  [INFERRED]
  docs/superpowers/specs/2026-09-27-payslip-ingestion-design.md → finance/career/models.py

## Import Cycles
- None detected.

## Communities (104 total, 56 thin omitted)

### Community 0 - "TransactionBulkService"
Cohesion: 0.29
Nodes (5): TransactionBulkService, APIView, TransactionBulkView, TransactionImportView, rest_framework_parsers

### Community 1 - "card_loaders.py"
Cohesion: 0.09
Nodes (14): AccountProviders, AccountTypes, DataSource, Enum, BaseLoader, DocomoCardLoader, EposCardLoader, MizuhoBankLoader (+6 more)

### Community 2 - "SettingsService"
Cohesion: 0.12
Nodes (12): Account, Meta, AccountSerializer, Meta, ResponseAccountSerializer, AccountService, object, patch (+4 more)

### Community 3 - "DashboardService"
Cohesion: 0.11
Nodes (11): DashboardService, Get the monthly transaction summary. Args: transaction_type (str): The…, Get the monthly transaction category summary. Args: transaction_type (str): The…, Calculates income, expense, payment, and savings aggregated by month in a…, Get the account wise sum. Args: transaction_type (str): The transaction type.…, Get the top ten expenses. If year is provided, aggregates by destination with…, Get top ten aggregated expenses for the latest active month of the given year., Get the monthly payment destination wise sum. Args: transaction_type (str): The… (+3 more)

### Community 4 - "get_current_user"
Cohesion: 0.09
Nodes (13): django_http, clear_current_user(), get_current_user(), Middleware to make the current request globally accessible. Guarantees thread-…, ThreadLocalMiddleware, TestHealthCheckEndpoint, TestPasswordResetSecurity, TestThreadLocalSecurity (+5 more)

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
Cohesion: 0.06
Nodes (32): CreditAccountView, APIView, ActionEnum, ChangeLog, SectionEnum, ChangeLogSerializer, Meta, get_changes() (+24 more)

### Community 10 - "core/urls.py"
Cohesion: 0.12
Nodes (12): URL configuration for personalfinance project. The `urlpatterns` list routes…, Serves the Single Page Application (SPA) entry point (index.html). All non-API…, spa_index_view(), django_conf_urls_static, django_contrib, django_contrib_auth_admin, AccountAdmin, register (+4 more)

### Community 11 - "MonthlyPayslip"
Cohesion: 0.16
Nodes (13): Global Constraints, Payslip Ingestion Implementation Plan, 1. Executive Summary, 2.1 Storage Folder Hierarchy & Path Construction, 2.2 GCS Object Metadata, 2. Cloud Storage (GCS) Directory Architecture, 3.1 Extraction Pipeline Flow (`POST /api/career/payslips/extract/`), 3. Automated Extraction Engine (Stateless Flow) (+5 more)

### Community 12 - "ImportWorkflowContract"
Cohesion: 0.16
Nodes (9): ImportWorkflowContract, ABC, Any, DataFrame, Return pandas read_csv kwargs (e.g. encoding, skiprows, header)., Return list of expected column header names used to detect statement header row., Transform raw statement dataframe into standardized transaction dataframe., Validate and clean transaction dataframe before database persistence. (+1 more)

### Community 13 - "EmploymentSerializer"
Cohesion: 0.16
Nodes (5): CompensationHistorySerializer, EmploymentSerializer, Meta, CompensationHistoryView, EmploymentView

### Community 14 - "transaction_import_service.py"
Cohesion: 0.05
Nodes (45): calendar, Migration, collections, datetime, decimal, django_db, django_db_models, django_db_models_functions (+37 more)

### Community 15 - "TransactionListService"
Cohesion: 0.15
Nodes (5): Meta, ResponseTransactionSerializer, TransactionListService, TestGroupByOptimization, TransactionView

### Community 16 - "Any"
Cohesion: 0.22
Nodes (5): Any, Upload a file or stream to the storage backend., Read a file and return a readable stream or file-like object., Read all files matching the prefix into a list of file-like streams., Read a CSV file into a pandas DataFrame.

### Community 17 - "AnalyticsService"
Cohesion: 0.07
Nodes (21): AnalyticsService, Detects recurring contracts, subscriptions, utility bills, and cadences.…, mock_analytics_service(), django_db, fixture, TestAnalyticsServiceDirect, TestAnalyticsView, mock_analytics_service() (+13 more)

### Community 18 - "django_conf"
Cohesion: 0.20
Nodes (11): django_conf, django_core_files_storage, logging, pandas, time, typing, ABC, List file paths in storage matching the given prefix. (+3 more)

### Community 19 - "test_workflows.py"
Cohesion: 0.23
Nodes (5): WorkflowContextType, TestLocalStorage, TestUploadWorkflow, Any, UploadWorkflow

### Community 20 - "Employment"
Cohesion: 0.19
Nodes (17): CompanyProfile, Employment, Meta, Returns the latest compensation revision record, if any., Represents an employment tenure with an employer entity (legal contract and…, Represents a company entity (Direct Employer, Staffing/Dispatch Agency, or…, employment(), api_client() (+9 more)

### Community 21 - "TestTransactionImportView"
Cohesion: 0.14
Nodes (5): django_core_files_uploadedfile, mock_import_service(), django_db, fixture, TestTransactionImportView

### Community 22 - "career/admin.py"
Cohesion: 0.11
Nodes (18): CareerDocumentAdmin, CareerDocumentInline, CompanyProfileAdmin, CompensationHistoryAdmin, CompensationHistoryInline, DispatchAssignmentAdmin, DispatchAssignmentInline, EmploymentAdmin (+10 more)

### Community 23 - "TestCategorySettingsView"
Cohesion: 0.14
Nodes (4): mock_category_service(), django_db, fixture, TestCategorySettingsView

### Community 24 - "oauth/views.py"
Cohesion: 0.08
Nodes (25): action, base64, BaseTokenObtainPairSerializer, BaseTokenObtainPairView, BaseUserCreateSerializer, CreateModelMixin, django_contrib_auth, django_contrib_auth_tokens (+17 more)

### Community 25 - "django_db_models_deletion"
Cohesion: 0.11
Nodes (11): Migration, Migration, django_contrib_auth_models, django_contrib_auth_validators, django_db_models_deletion, django_utils_timezone, Migration, Migration (+3 more)

### Community 28 - "career/models.py"
Cohesion: 0.14
Nodes (10): DispatchAssignment, Tracks dispatched company assignments (dispatched company, start date, end…, Annual Withholding Tax Certificate (源泉徴収票 / Gensen-Choshu-Hyo). Matches the…, TaxWithholdingSlip, DispatchAssignmentSerializer, TaxWithholdingSlipSerializer, CareerOverviewView, DispatchAssignmentView (+2 more)

### Community 29 - "TestAccountsView"
Cohesion: 0.18
Nodes (4): mock_category_service(), django_db, fixture, TestAccountsView

### Community 30 - "extract_payslip_data"
Cohesion: 0.16
Nodes (19): BaseModel, dateutil, Review Focus, Task 1: GCS Storage Service, Task 2: AI Extraction Service, Task 3: Extraction API Endpoint, extract_payslip_data(), PayslipSchema (+11 more)

### Community 31 - "dashboard/tests/test_views.py"
Cohesion: 0.25
Nodes (4): mock_dashboard_service(), django_db, fixture, TestDashboardView

### Community 32 - "career/views.py"
Cohesion: 0.14
Nodes (13): CareerDocumentSerializer, MonthlyPayslipSerializer, _safe_date_or_none(), CareerDocumentDownloadView, CareerDocumentView, MonthlyPayslipView, PayslipExtractView, PayslipSaveView (+5 more)

### Community 33 - "CareerDocument"
Cohesion: 0.27
Nodes (11): CareerDocument, Pure Document Vault for career-related files: offer letters, employment…, auth_user(), client_authenticated(), django_db, fixture, test_career_document_download_authenticated(), test_career_document_download_forbidden_without_auth_or_sig() (+3 more)

### Community 34 - "LocalStorageHandler"
Cohesion: 0.33
Nodes (3): LocalStorageHandler, Any, DataFrame

### Community 35 - "User"
Cohesion: 0.20
Nodes (9): AbstractUser, django_core_management, generate_signed_url(), Generates a signed URL to view the document., test_generate_signed_url_enforces_user_ownership(), test_generate_signed_url_handles_local_scheme(), User, django_db (+1 more)

### Community 36 - "conftest.py"
Cohesion: 0.33
Nodes (5): api_client(), authenticate(), fixture, model_bakery, rest_framework_test

### Community 37 - "generate_dev_token.py"
Cohesion: 0.29
Nodes (4): django_core_management_base, Command, BaseCommand, rest_framework_simplejwt_tokens

### Community 38 - "GCSHandler"
Cohesion: 0.12
Nodes (10): StorageBackendProvider, GCSHandler, Reads a CSV file from the GCS bucket. Args: file_name (str): The name of the…, A handler for interacting with Google Cloud Storage (GCS). Provides methods for…, Initializes the GCSHandler with a specified bucket name. Args: bucket_name…, Uploads a file to the GCS bucket with retry logic. Args: file (file-like…, Lists files in the GCS bucket with optional filtering and pagination. Args:…, Deletes a file from the specified bucket. (+2 more)

### Community 39 - "TestSpaServing"
Cohesion: 0.22
Nodes (3): django_db, fixture, TestSpaServing

### Community 40 - "TestTransactionServices"
Cohesion: 0.29
Nodes (3): django_db, patch, TestTransactionServices

### Community 41 - "test_payslip_views.py"
Cohesion: 0.40
Nodes (5): api_client(), django_db, fixture, test_extract_endpoint_calls_service_and_returns_json(), test_extract_endpoint_returns_400_for_non_pdf()

### Community 43 - "ImportCsvWorkflow"
Cohesion: 0.23
Nodes (4): ImportCsvWorkflow, DataFrame, DummyProcessor, TestImportCsvWorkflow

### Community 44 - "TestClientSettings"
Cohesion: 0.25
Nodes (4): mock_settings_service(), django_db, fixture, TestClientSettings

### Community 45 - "Q: how does the dashboard service connect to the database layer"
Cohesion: 0.50
Nodes (3): Answer, Q: how does the dashboard service connect to the database layer, Source Nodes

### Community 46 - "manage.py"
Cohesion: 0.40
Nodes (4): main(), Django's command-line utility for administrative tasks., Run administrative tasks., sys

### Community 47 - "Q: how transaction import flow working"
Cohesion: 0.50
Nodes (3): Answer, Q: how transaction import flow working, Source Nodes

### Community 49 - "test_storage_service.py"
Cohesion: 0.10
Nodes (25): media_career_docs_fallback_view(), Fallback view for /media/career_docs/<path> in production. If the file exists…, django_core_exceptions, django_core_signing, django_utils_text, Task 4: Save Workflow API Endpoint, generate_document_download_url(), generate_download_signature() (+17 more)

### Community 51 - "pytest"
Cohesion: 0.33
Nodes (4): django_test, mock_payee_service(), fixture, pytest

### Community 110 - "settings.py"
Cohesion: 0.14
Nodes (11): ASGI config for personalfinance project. It exposes the ASGI callable as a…, Django settings for personalfinance project. Generated by 'django-admin…, WSGI config for personalfinance project. It exposes the WSGI callable as a…, decouple, django_core_asgi, django_core_wsgi, dotenv, google_cloud (+3 more)

## Knowledge Gaps
- **26 isolated node(s):** `Migration`, `Meta`, `Migration`, `Migration`, `Meta` (+21 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 402 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **56 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Transaction` connect `transaction_import_service.py` to `TransactionBulkService`, `SettingsService`, `DashboardService`, `get_current_user`, `PayeeService`, `TransactionImportService`, `rest_framework`, `TransactionListService`, `AnalyticsService`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `DashboardService` connect `DashboardService` to `rest_framework`, `transaction_import_service.py`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `TransactionImportService` connect `TransactionImportService` to `TransactionBulkService`, `card_loaders.py`, `SettingsService`, `GCSHandler`, `TestTransactionServices`, `ImportCsvWorkflow`, `transaction_import_service.py`, `test_workflows.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `CareerDocument` (e.g. with `media_career_docs_fallback_view()` and `Payslip Ingestion Implementation Plan`) actually correct?**
  _`CareerDocument` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `CategoryService` (e.g. with `TransactionCategory` and `TransactionSubCategory`) actually correct?**
  _`CategoryService` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `Transaction` (e.g. with `TestActivityView` and `ActivityView`) actually correct?**
  _`Transaction` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `MonthlyPayslip` (e.g. with `Global Constraints` and `Payslip Ingestion Implementation Plan`) actually correct?**
  _`MonthlyPayslip` has 19 INFERRED edges - model-reasoned connections that need verification._