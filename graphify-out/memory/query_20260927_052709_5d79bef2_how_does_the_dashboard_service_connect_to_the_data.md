---
type: "query"
date: "2026-09-27T05:27:09.306148+00:00"
question: "how does the dashboard service connect to the database layer"
contributor: "graphify"
source_nodes: ["DashboardService", "Transaction"]
---

# Q: how does the dashboard service connect to the database layer

## Answer

Expanded from original query via vocab: [dashboard, service, connection, database]. Then traversed from DashboardService. The DashboardService directly connects to the database layer through the Django ORM by using the Transaction model (finance/transactions/models.py). It implements methods like get_queryset(), get_income(), and get_top_ten_expenses() to query this model.

## Source Nodes

- DashboardService
- Transaction