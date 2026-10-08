# Graph Report - personalfinance  (2026-10-07)

## Corpus Check
- 197 files · ~50,236 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 5, .example 1, .ini 1)

## Summary
- 1208 nodes · 2389 edges · 114 communities (57 shown, 57 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 287 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4343e5c9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- CareerDocument
- card_loaders.py
- career/views.py
- DashboardService
- get_current_user
- PayeeService
- django_apps
- TransactionImportService
- TestTransactionView
- rest_framework
- core/urls.py
- MonthlyPayslip
- Career Hub: Payroll, Tax & Pension Intelligence Architecture
- EmploymentSerializer
- CategoryService
- TransactionListService
- Any
- AnalyticsService
- StorageBackendContract
- test_workflows.py
- Employment
- TestTransactionImportView
- career/admin.py
- TestCategorySettingsView
- oauth/views.py
- django_db
- CompanyProfileSerializer
- TestPayeeView
- CareerOverviewView
- TestAccountsView
- extract_payslip_data
- dashboard/tests/test_views.py
- MonthlyPayslipSerializer
- test_career_document_views.py
- LocalStorageHandler
- User
- conftest.py
- generate_dev_token.py
- GCSHandler
- TestSpaServing
- Knowledge Hub Redesign & Comprehensive Japan Tax Guide Architecture Specification
- career/serializers.py
- Transaction
- ImportCsvWorkflow
- Career Hub: Japanese Withholding Tax Slip (源泉徴収票) AI Extraction & Cloud Vault Ingestion
- Q: how does the dashboard service connect to the database layer
- payslip_extraction_service.py
- Q: how transaction import flow working
- test_payslip_analytics_view.py
- test_storage_service.py
- Tasks
- pytest
- DestinationMap
- extract_tax_slip_data
- settings.py
- Review Focus
- rules/graphify.md
- workflows/graphify.md
- core/__init__.py
- DummyProcessor
- career/__init__.py
- career/migrations/__init__.py
- os
- RequestManager
- transaction_import_service.py
- SDD ledger — plan: docs/superpowers/plans/2026-10-04-japan-tax-knowledge-guide.md

## God Nodes (most connected - your core abstractions)
1. `CareerDocument` - 39 edges
2. `MonthlyPayslip` - 35 edges
3. `get_current_user()` - 35 edges
4. `Employment` - 34 edges
5. `CategoryService` - 31 edges
6. `Transaction` - 31 edges
7. `CompanyProfile` - 29 edges
8. `DashboardService` - 29 edges
9. `TransactionImportService` - 29 edges
10. `TransactionListService` - 29 edges

## Surprising Connections (you probably didn't know these)
- `1. Executive Summary` --references--> `MonthlyPayslip`  [INFERRED]
  docs/superpowers/specs/2026-10-03-payroll-analytics-design.md → finance/career/models.py
- `5. Security, Validation & Error Handling` --references--> `TaxWithholdingSlip`  [INFERRED]
  docs/superpowers/specs/2026-10-03-tax-slip-ai-extraction-design.md → finance/career/models.py
- `6. Interactive "Your Numbers" Calculation Panel` --references--> `TaxWithholdingSlip`  [INFERRED]
  docs/superpowers/specs/2026-10-04-japan-tax-knowledge-guide-design.md → finance/career/models.py
- `Task 1: Backend Analytics Aggregation Endpoint & Service` --references--> `PayslipAnalyticsView`  [INFERRED]
  docs/superpowers/plans/2026-10-03-payroll-analytics.md → finance/career/views.py
- `Global Constraints` --references--> `RequestManager`  [INFERRED]
  docs/superpowers/plans/2026-10-03-payroll-analytics.md → oauth/util/request_manager.py

## Import Cycles
- None detected.

## Communities (114 total, 57 thin omitted)

### Community 0 - "CareerDocument"
Cohesion: 0.12
Nodes (22): Global Constraints, Review Focus, Task 2: Tax Slip Extract & Save API Views, Task 3: Frontend API & `TaxSlipModal` Integration, Task 4: End-to-End Test Suite & Verification, Tax Slip AI Extraction & Cloud Vault Ingestion Implementation Plan, 1. Executive Summary, 3.3 Atomic Save Endpoint (`TaxSlipSaveView`) (+14 more)

### Community 1 - "card_loaders.py"
Cohesion: 0.07
Nodes (22): AccountProviders, DataSource, BaseLoader, DocomoCardLoader, EposCardLoader, MizuhoBankLoader, RakutenCardLoader, TransactionProcessFactory (+14 more)

### Community 2 - "career/views.py"
Cohesion: 0.17
Nodes (11): TaxWithholdingSlipSerializer, _safe_date_or_none(), CareerDocumentDownloadView, PayslipAnalyticsView, PayslipSaveView, APIView, Streams/downloads career documents from GCS or Local Storage. Supports…, Dedicated analytical aggregation endpoint for MonthlyPayslip records. Provides… (+3 more)

### Community 3 - "DashboardService"
Cohesion: 0.11
Nodes (11): DashboardService, Get the monthly transaction summary. Args: transaction_type (str): The…, Get the monthly transaction category summary. Args: transaction_type (str): The…, Calculates income, expense, payment, and savings aggregated by month in a…, Get the account wise sum. Args: transaction_type (str): The transaction type.…, Get the top ten expenses. If year is provided, aggregates by destination with…, Get top ten aggregated expenses for the latest active month of the given year., Get the monthly payment destination wise sum. Args: transaction_type (str): The… (+3 more)

### Community 4 - "get_current_user"
Cohesion: 0.10
Nodes (11): clear_current_user(), get_current_user(), Middleware to make the current request globally accessible. Guarantees thread-…, ThreadLocalMiddleware, TestHealthCheckEndpoint, TestPasswordResetSecurity, TestThreadLocalSecurity, dummy_view() (+3 more)

### Community 5 - "PayeeService"
Cohesion: 0.12
Nodes (10): Meta, ResponseDestinationMapSerializer, PayeeService, Updates the payee. Args: request_data (dict): The request data. Returns: tuple:…, Gets the custom queryset for the payee. Returns: QuerySet: The custom queryset…, object, patch, TestPayeeService (+2 more)

### Community 6 - "django_apps"
Cohesion: 0.07
Nodes (19): AccountsConfig, AppConfig, ChangelogConfig, AppConfig, django_apps, CareerConfig, AppConfig, CategoriesConfig (+11 more)

### Community 7 - "TransactionImportService"
Cohesion: 0.09
Nodes (13): Uploads the transaction files. Args: upload_params (dict): The upload…, Gets the account from the provided account ID. Args: account_id (int): The…, Gets the applicable transactions. Args: transaction_data (DataFrame): The…, Gets the payee map. Returns: DataFrame: The payee map., Gets the rewrite rules. Args: payee_maps (DataFrame): The payee maps. Returns:…, Finds the new payees. Args: payees (DataFrame): The payees. transactions…, Assigns the category IDs to the transactions. Args: payees (DataFrame): The…, Imports the transactions from the provided files. Args: import_params (dict):… (+5 more)

### Community 8 - "TestTransactionView"
Cohesion: 0.09
Nodes (6): mock_bulk_service(), mock_transaction_service(), django_db, fixture, TestTransactionBulkView, TestTransactionView

### Community 9 - "rest_framework"
Cohesion: 0.05
Nodes (36): CreditAccountView, APIView, ActionEnum, ChangeLog, SectionEnum, ChangeLogSerializer, Meta, get_changes() (+28 more)

### Community 10 - "core/urls.py"
Cohesion: 0.10
Nodes (17): media_career_docs_fallback_view(), URL configuration for personalfinance project. The `urlpatterns` list routes…, Fallback view for /media/career_docs/<path> in production. If the file exists…, Serves the Single Page Application (SPA) entry point (index.html). All non-API…, spa_index_view(), django_conf_urls_static, django_contrib, django_contrib_auth_admin (+9 more)

### Community 11 - "MonthlyPayslip"
Cohesion: 0.12
Nodes (19): Global Constraints, Payslip Ingestion Implementation Plan, Review Focus, Task 1: GCS Storage Service, Task 2: AI Extraction Service, Task 3: Extraction API Endpoint, Task 4: Save Workflow API Endpoint, 1. Executive Summary (+11 more)

### Community 12 - "Career Hub: Payroll, Tax & Pension Intelligence Architecture"
Cohesion: 0.11
Nodes (18): 1. Executive Summary, 2. System Architecture & Data Flow, 3.1 Endpoint Definition, 3.2 Response Payload Schema, 3. Backend Specification, 4.1 Navigation & Placement, 4.2 Top Control Deck, 4.3 High-Impact KPI Ribbon (5 Metric Cards) (+10 more)

### Community 14 - "CategoryService"
Cohesion: 0.07
Nodes (27): Account, Meta, AccountSerializer, Meta, ResponseAccountSerializer, AccountService, object, patch (+19 more)

### Community 15 - "TransactionListService"
Cohesion: 0.14
Nodes (6): TransactionListService, TestGroupByOptimization, APIView, TransactionBulkView, TransactionView, rest_framework_parsers

### Community 16 - "Any"
Cohesion: 0.22
Nodes (5): Any, Upload a file or stream to the storage backend., Read a file and return a readable stream or file-like object., Read all files matching the prefix into a list of file-like streams., Read a CSV file into a pandas DataFrame.

### Community 17 - "AnalyticsService"
Cohesion: 0.07
Nodes (21): AnalyticsService, Detects recurring contracts, subscriptions, utility bills, and cadences.…, mock_analytics_service(), django_db, fixture, TestAnalyticsServiceDirect, TestAnalyticsView, mock_analytics_service() (+13 more)

### Community 18 - "StorageBackendContract"
Cohesion: 0.19
Nodes (10): django_core_files_storage, logging, time, typing, ABC, List file paths in storage matching the given prefix., Delete a file from the storage backend., Abstract contract defining file storage operations across different storage… (+2 more)

### Community 19 - "test_workflows.py"
Cohesion: 0.20
Nodes (7): AccountTypes, WorkflowContextType, Enum, TestLocalStorage, TestUploadWorkflow, Any, UploadWorkflow

### Community 20 - "Employment"
Cohesion: 0.20
Nodes (16): CompanyProfile, Employment, Meta, Returns the latest compensation revision record, if any., Represents an employment tenure with an employer entity (legal contract and…, Represents a company entity (Direct Employer, Staffing/Dispatch Agency, or…, api_client(), django_db (+8 more)

### Community 21 - "TestTransactionImportView"
Cohesion: 0.11
Nodes (10): django_core_files_uploadedfile, api_client(), django_db, fixture, test_extract_endpoint_calls_service_and_returns_json(), test_extract_endpoint_returns_400_for_non_pdf(), mock_import_service(), django_db (+2 more)

### Community 22 - "career/admin.py"
Cohesion: 0.21
Nodes (13): CareerDocumentAdmin, CareerDocumentInline, CompanyProfileAdmin, CompensationHistoryAdmin, CompensationHistoryInline, DispatchAssignmentAdmin, DispatchAssignmentInline, EmploymentAdmin (+5 more)

### Community 23 - "TestCategorySettingsView"
Cohesion: 0.14
Nodes (4): mock_category_service(), django_db, fixture, TestCategorySettingsView

### Community 24 - "oauth/views.py"
Cohesion: 0.08
Nodes (24): action, base64, BaseTokenObtainPairSerializer, BaseTokenObtainPairView, BaseUserCreateSerializer, CreateModelMixin, django_contrib_auth_tokens, djoser_serializers (+16 more)

### Community 25 - "django_db"
Cohesion: 0.07
Nodes (23): Migration, Migration, Migration, django_conf, django_contrib_auth_models, django_contrib_auth_validators, django_db, django_db_models_deletion (+15 more)

### Community 27 - "TestPayeeView"
Cohesion: 0.17
Nodes (4): mock_payee_service(), django_db, fixture, TestPayeeView

### Community 28 - "CareerOverviewView"
Cohesion: 0.23
Nodes (6): DispatchAssignment, Tracks dispatched company assignments (dispatched company, start date, end…, DispatchAssignmentSerializer, CareerOverviewView, DispatchAssignmentView, Returns an aggregated summary for the Career Hub dashboard: - Current…

### Community 29 - "TestAccountsView"
Cohesion: 0.18
Nodes (4): mock_category_service(), django_db, fixture, TestAccountsView

### Community 30 - "extract_payslip_data"
Cohesion: 0.38
Nodes (10): extract_payslip_data(), PayslipSchema, BaseModel, test_extract_payslip_data_fails_on_1_yen_mismatch(), test_extract_payslip_data_fallback(), test_extract_payslip_data_handles_nontaxable_commutation(), test_extract_payslip_data_includes_other_descriptions_and_notes(), test_extract_payslip_data_success() (+2 more)

### Community 31 - "dashboard/tests/test_views.py"
Cohesion: 0.25
Nodes (4): mock_dashboard_service(), django_db, fixture, TestDashboardView

### Community 32 - "MonthlyPayslipSerializer"
Cohesion: 0.20
Nodes (5): CareerDocumentSerializer, Meta, MonthlyPayslipSerializer, CareerDocumentView, MonthlyPayslipView

### Community 33 - "test_career_document_views.py"
Cohesion: 0.24
Nodes (12): generate_download_signature(), Generates a secure timestamped signature for downloading a career document., auth_user(), client_authenticated(), employment(), django_db, fixture, test_career_document_download_authenticated() (+4 more)

### Community 34 - "LocalStorageHandler"
Cohesion: 0.33
Nodes (3): LocalStorageHandler, Any, DataFrame

### Community 35 - "User"
Cohesion: 0.17
Nodes (10): AbstractUser, generate_document_download_url(), generate_signed_url(), Generates a signed URL to view the document., Returns the backend download URL with signature for direct viewing/downloading., test_generate_signed_url_enforces_user_ownership(), test_generate_signed_url_handles_local_scheme(), User (+2 more)

### Community 36 - "conftest.py"
Cohesion: 0.33
Nodes (5): api_client(), authenticate(), fixture, model_bakery, rest_framework_test

### Community 37 - "generate_dev_token.py"
Cohesion: 0.29
Nodes (4): django_core_management_base, Command, BaseCommand, rest_framework_simplejwt_tokens

### Community 38 - "GCSHandler"
Cohesion: 0.14
Nodes (9): GCSHandler, Reads a CSV file from the GCS bucket. Args: file_name (str): The name of the…, A handler for interacting with Google Cloud Storage (GCS). Provides methods for…, Initializes the GCSHandler with a specified bucket name. Args: bucket_name…, Uploads a file to the GCS bucket with retry logic. Args: file (file-like…, Lists files in the GCS bucket with optional filtering and pagination. Args:…, Deletes a file from the specified bucket., Reads a file from the GCS bucket. Args: file_name (str): The name of the file… (+1 more)

### Community 39 - "TestSpaServing"
Cohesion: 0.22
Nodes (3): django_db, fixture, TestSpaServing

### Community 40 - "Knowledge Hub Redesign & Comprehensive Japan Tax Guide Architecture Specification"
Cohesion: 0.12
Nodes (16): 1. Executive Summary, 2024 Rules (`2024.ts`), 2025 Reform Rules (`2025.ts`), 2. System Architecture & Navigational Data Flow, 3.1 Sidebar Expandable Sub-Navigation, 3.2 Main Layout & Header Synchronization, 3. Sidebar Navigation & Layout Redesign, 4. Knowledge Article Registry Architecture (+8 more)

### Community 41 - "career/serializers.py"
Cohesion: 0.17
Nodes (7): CompensationHistory, Tracks multi-year compensation revisions, annual raises, promotions, and…, Monthly guaranteed pay = base salary + fixed allowances (normalized to monthly), Annual guaranteed base (固定年俸 / Base + Allowances * 12), Total expected annual package (総年収 / OTE) = (Base + Allowances) * 12 + Annual…, CompensationHistorySerializer, CompensationHistoryView

### Community 42 - "Transaction"
Cohesion: 0.11
Nodes (16): calendar, collections, decimal, django_db_models, django_db_models_functions, django_utils, Meta, Transaction (+8 more)

### Community 44 - "Career Hub: Japanese Withholding Tax Slip (源泉徴収票) AI Extraction & Cloud Vault Ingestion"
Cohesion: 0.14
Nodes (13): 2.1 Pydantic Extraction Contract (`TaxSlipSchema`), 2.2 Era Conversion & Deterministic Normalization, 2. Extraction Schema & Japanese Tax Box Mapping, 3.1 Service Layer (`finance/career/services/tax_slip_extraction_service.py`), 3.2 Extract Endpoint (`TaxSlipExtractView`), 3. Backend Architecture & Endpoints, 4.1 Client Service (`careerService.ts`), 4.2 Modal Component (`TaxSlipModal.tsx`) (+5 more)

### Community 45 - "Q: how does the dashboard service connect to the database layer"
Cohesion: 0.50
Nodes (3): Answer, Q: how does the dashboard service connect to the database layer, Source Nodes

### Community 46 - "payslip_extraction_service.py"
Cohesion: 0.26
Nodes (10): datetime, dateutil, decouple, Converts Japanese imperial year or integer year to 4-digit Gregorian year., _resolve_japanese_year(), _safe_date_or_none(), google, google_genai (+2 more)

### Community 47 - "Q: how transaction import flow working"
Cohesion: 0.50
Nodes (3): Answer, Q: how transaction import flow working, Source Nodes

### Community 48 - "test_payslip_analytics_view.py"
Cohesion: 0.20
Nodes (7): django_contrib_auth, auth_user(), client_authenticated(), other_user(), django_db, fixture, TestPayslipAnalyticsView

### Community 49 - "test_storage_service.py"
Cohesion: 0.16
Nodes (16): django_core_exceptions, django_core_signing, django_utils_text, Uploads a payslip PDF to GCS or Local Storage and returns the URI., Uploads a career document (contract, offer letter, tax slip, etc.) to GCS…, Verifies a timestamped signature for downloading a career document (default 24…, upload_career_document(), upload_payslip_document() (+8 more)

### Community 50 - "Tasks"
Cohesion: 0.17
Nodes (11): Global Constraints, Payroll, Tax & Pension Intelligence Implementation Plan, Review Focus, Task 1: Backend Analytics Aggregation Endpoint & Service, Task 2: Frontend TypeScript Contracts & API Client, Task 3: KPI Header & Filter Deck Components, Task 4: Analytical Lenses 1 & 2 (Friction/Waterfall & Pension Vault), Task 5: Analytical Lenses 3 & 4 (Tax Dynamics & Multi-Year Trajectory) (+3 more)

### Community 51 - "pytest"
Cohesion: 0.40
Nodes (3): django_test, pytest, unittest_mock

### Community 52 - "DestinationMap"
Cohesion: 0.27
Nodes (5): DestinationMap, Meta, DestinationMapSerializer, Command, BaseCommand

### Community 53 - "extract_tax_slip_data"
Cohesion: 0.42
Nodes (7): Task 1: Tax Slip AI Extraction Service, extract_tax_slip_data(), BaseModel, TaxSlipSchema, test_extract_tax_slip_data_basic_deduction_default(), test_extract_tax_slip_data_converts_era_and_fields(), test_extract_tax_slip_data_model_fallback()

### Community 54 - "settings.py"
Cohesion: 0.25
Nodes (6): Django settings for personalfinance project. Generated by 'django-admin…, django_core_management, dotenv, google_cloud, io, pathlib

### Community 55 - "Review Focus"
Cohesion: 0.25
Nodes (7): Global Constraints, Knowledge Hub Redesign & Comprehensive Japan Tax Guide Implementation Plan, Review Focus, Task 1: Pure Tax Calculation Engine & Year-by-Year Statutory Rules, Task 2: Sidebar Navigation Redesign & Knowledge Article Registry, Task 3: Reusable UI Components & Content Sections for Japan Tax Guide, Task 4: Interactive "Your Numbers" Calculation Panel & Full Integration

### Community 110 - "os"
Cohesion: 0.17
Nodes (9): ASGI config for personalfinance project. It exposes the ASGI callable as a…, WSGI config for personalfinance project. It exposes the WSGI callable as a…, django_core_asgi, django_core_wsgi, main(), Django's command-line utility for administrative tasks., Run administrative tasks., os (+1 more)

### Community 111 - "RequestManager"
Cohesion: 0.38
Nodes (3): TestRequestManagerSafety, CronManager, RequestManager

### Community 112 - "transaction_import_service.py"
Cohesion: 0.60
Nodes (3): ImportParamsValidator, UploadParamsValidator, rest_framework_exceptions

### Community 113 - "SDD ledger — plan: docs/superpowers/plans/2026-10-04-japan-tax-knowledge-guide.md"
Cohesion: 0.50
Nodes (3): Completed Deliverables:, SDD ledger — plan: docs/superpowers/plans/2026-10-04-japan-tax-knowledge-guide.md, Status: COMPLETE

## Knowledge Gaps
- **71 isolated node(s):** `Migration`, `Meta`, `Migration`, `Migration`, `Meta` (+66 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 461 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **57 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Transaction` connect `Transaction` to `DashboardService`, `get_current_user`, `PayeeService`, `TransactionImportService`, `rest_framework`, `CategoryService`, `RequestManager`, `transaction_import_service.py`, `AnalyticsService`, `TransactionListService`, `DestinationMap`, `django_db`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `RequestManager` connect `RequestManager` to `CareerDocument`, `get_current_user`, `career/serializers.py`, `Transaction`, `MonthlyPayslip`, `Career Hub: Payroll, Tax & Pension Intelligence Architecture`, `CategoryService`, `Tasks`, `Employment`, `DestinationMap`, `django_db`, `CareerOverviewView`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Why does `TaxWithholdingSlip` connect `CareerDocument` to `career/views.py`, `get_current_user`, `Knowledge Hub Redesign & Comprehensive Japan Tax Guide Architecture Specification`, `career/serializers.py`, `Career Hub: Japanese Withholding Tax Slip (源泉徴収票) AI Extraction & Cloud Vault Ingestion`, `RequestManager`, `Employment`, `extract_tax_slip_data`, `career/admin.py`, `CareerOverviewView`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `CareerDocument` (e.g. with `media_career_docs_fallback_view()` and `Payslip Ingestion Implementation Plan`) actually correct?**
  _`CareerDocument` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `MonthlyPayslip` (e.g. with `Global Constraints` and `Payslip Ingestion Implementation Plan`) actually correct?**
  _`MonthlyPayslip` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `Employment` (e.g. with `Task 2: Tax Slip Extract & Save API Views` and `4. Client Review & Save Workflow`) actually correct?**
  _`Employment` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `CategoryService` (e.g. with `TransactionCategory` and `TransactionSubCategory`) actually correct?**
  _`CategoryService` has 10 INFERRED edges - model-reasoned connections that need verification._