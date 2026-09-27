---
type: "query"
date: "2026-09-27T05:28:44.074820+00:00"
question: "how transaction import flow working"
contributor: "graphify"
source_nodes: ["ImportCsvWorkflow", "TransactionImportService", "UploadWorkflow"]
---

# Q: how transaction import flow working

## Answer

Expanded from original query via vocab: [transaction, import, flow]. Then traversed from ImportCsvWorkflow. 
The transaction import flow works through a pipeline of components:
1. Storage/Upload: The UploadWorkflow uses the StorageBackendProvider (local or GCS) to save transaction files (e.g., CSV).
2. Reading: The ImportCsvWorkflow uses the StorageBackendProvider to read the files. It handles parsing raw data, including falling back on encodings (_read_with_encoding_fallback) and skipping irrelevant header rows (_skip_rows).
3. Processing: The extracted dataframe is passed to TransactionImportService.
4. Business Logic (TransactionImportService): 
   - A TransactionProcessFactory picks a specific loader for the bank (like MizuhoBankLoader) to standardize the data.
   - It maps and deduplicates payees (find_new_payees, get_payee_map).
   - It applies regex or string replacement rules (get_rewrite_rules, apply_rewrite_rules).
   - It assigns transaction categories (assign_category_ids).
5. Persistence: The processed data is finally saved to the database as Transaction models.

## Source Nodes

- ImportCsvWorkflow
- TransactionImportService
- UploadWorkflow