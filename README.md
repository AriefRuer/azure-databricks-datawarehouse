# RetailRocket Data Warehouse using Azure Cloud Services

An end-to-end data warehouse project built on the Microsoft Azure stack, using the [RetailRocket e-commerce dataset](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset) — 2,756,101 event rows plus a 20,275,902-row item-property change log — to enable downstream BI analytics in Azure SQL. The pipeline follows a medallion architecture (bronze → silver → gold), models the data as a Kimball star schema (5 dimensions + 1 fact), and is deployed with CI/CD via GitHub Actions. An Azure Data Factory trigger was configured, but no scheduled run was captured — the execution evidence in this repo comes from a manual Databricks job run. A serverless rebuild of this warehouse on BigQuery followed this project: [retailrocket-bigquery-warehouse](https://github.com/AriefRuer/retailrocket-bigquery-warehouse).

**Status:** 🗄️ **Archived** (30 September 2026)
**Stack:** Azure Blob Storage · Azure Databricks (PySpark) · Azure SQL Database · GitHub Actions · Azure Data Factory

> **Why archived?** Access to Azure and Databricks was lost on 30 September 2026. The ETL pipeline was fully working before access loss; The repository is retained as a **case study** and **rebuild reference**.

---

## The RetailRocket Dataset

[RetailRocket](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset) is an anonymized **clickstream log from a real-world e-commerce website**, published by Retail Rocket (retailrocket.io, a real-time recommendation platform) to *"motivate researchers in the field of recommender systems with implicit feedback."* It records what visitors **did** — views, add-to-carts, purchases — not what the shop sold. All values are hashed for confidentiality except two readable properties: `categoryid` and `available` (so no price analysis is possible — by the publisher's design). The publisher's own tasks warn that browsing logs can carry *"up to 40% abnormal traffic"*, which is why this project profiles heavy visitors before trusting any per-user metric.

| File | Rows | What it holds |
|---|---|---|
| `events.csv` | 2,756,101 | One row per action: `timestamp, visitorid, event, itemid, transactionid` |
| `item_properties_part1+2.csv` | 20,275,902 | **Change log** of item attributes (was weekly snapshots >200M rows; publisher merged constant runs ~10× smaller). 417,053 items, 1,104 distinct property keys |
| `category_tree.csv` | 1,669 | Child→parent category hierarchy (empty parent = root) |

**Event mix:** `view` 2,664,312 · `addtocart` 69,332 · `transaction` 22,457 (spelled one word in the data). **Window:** May 3 – Sep 18, 2015 — 139 calendar dates (138-day span), 1,407,580 unique visitors. **License:** [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

---

## What This Project Demonstrates

- **Medallion ETL architecture** — bronze (raw) → silver (cleansed) → gold (star schema), with clear separation of concerns
- **Kimball dimensional modeling** — 5 conformed dimensions + 1 fact table at the grain of one user action
- **PySpark transformations** — window functions for SCD Type 1, deterministic surrogate keys, `.cache()` discipline to prevent key regeneration
- **Environment separation** — `dev` branch → `retailrocket_dev` schema; `main` branch → `retailrocket` schema
- **CI/CD** — GitHub Actions workflow deploying via `databricks bundle deploy --target <dev|prod>`
- **Security hygiene** — Databricks secrets scope for all credentials; read-only SQL user for BI (planned); firewall restricted to the developer laptop
- **Data quality validation** — dedicated verification notebook for referential integrity and row-count assertions

---

## Architecture

```
Kaggle RetailRocket CSV
        │
        ▼  manual upload
Azure Blob Storage  (raw/data-retailrocket/)
        │
        ▼  Databricks PySpark
Bronze  ──  raw Delta tables, typed, null-filtered
        │
        ▼  dedup + clean
Silver  ──  cleansed Delta tables, deduplicated, FK-consistent
        │
        ▼  star-schema build
Gold    ──  dim_date, dim_users, dim_items, dim_categories,
        │    dim_event_type, fact_events
        │
        ▼  JDBC bulk load
Azure SQL Database  (retailrocket-dw)
```

**Orchestration:** Databricks Jobs (via `databricks.yml` bundle) · **CI/CD:** GitHub Actions on push to `dev` / `main`

---

## Tech Stack

| Layer | Service | Purpose | Status |
|---|---|---|---|
| Storage | Azure Blob Storage (`stdportfolio`) | Landing zone for raw CSVs (`raw/data-retailrocket/`) | ✅ Built |
| Compute | Azure Databricks (`dbw-retailrocket`) | PySpark notebook execution for ETL | ✅ Built |
| Transformation orchestration | Databricks Jobs (`databricks.yml`) | Executes the ETL notebooks (bronze → silver → gold → verification) in order | ✅ Built |
| Scheduling | Azure Data Factory (`adf-retailrocket`) | Pipeline configured (resource provisioned, pipeline JSON documented) | ⚙️ Configured; run not captured |
| Serving | Azure SQL Database (`retailrocket-dw`) | Star schema for BI consumption | ✅ Built |
| CI/CD | GitHub Actions (`.github/workflows/ci.yml`) | Deploy databricks bundle on push via `databricks bundle deploy` to keep databricks jobs up to date  | Non-functional as of 30/9/26 — depends on Databricks |
| Secrets | Databricks secrets scope (`retailrocket`) | `storage-key`, `sql-password` | ✅ Built |


---

## Star Schema

### Dimensions

| Table            | Grain                     | Key Columns                                                                                                      |
| ---------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `dim_date`       | One row per calendar date | `date_sk`, `full_date`, `year`, `month`, `day`, `day_of_week`, `day_name`, `is_weekend`, `month_name`, `quarter` |
| `dim_users`      | One row per `visitorid`   | `user_sk`, `visitorid`, `first_event_ts`, `last_event_ts`, `total_events`, `total_purchases`, `has_purchased`    |
| `dim_items`      | One row per `itemid`      | `item_sk`, `itemid`, `category_sk`                                                                               |
| `dim_categories` | One row per category      | `category_sk`, `category_id`, `parent_id`, `parent_sk`                                                           |
| `dim_event_type` | One row per event type    | `event_type_sk`, `event_type` (`view` / `addtocart` / `transaction`)                                             |

### Fact

| Table         | Grain                   | Columns                                                                       |
| ------------- | ----------------------- | ----------------------------------------------------------------------------- |
| `fact_events` | One row per user action | `event_sk`, `date_sk`, `user_sk`, `item_sk`, `event_type_sk`, `transactionid` |

---

## ETL Pipeline

| Notebook                        | Location  | Purpose                                                           |
| ------------------------------- | --------- | ----------------------------------------------------------------- |
| `EDA.ipynb`                     | `03-eda/` | Full dataset exploration — distributions, null rates, cardinality |
| `etl-bronze-to-silver.ipynb`    | `04-etl/` | Load CSVs → bronze Delta tables; cleanse and dedup → silver       |
| `etl-silver-to-gold.ipynb`      | `04-etl/` | Build star schema; load gold tables into Azure SQL via JDBC       |
| `etl-verification-checks.ipynb` | `04-etl/` | Referential integrity, row-count assertions, orphan-key checks    |

**Execution order is strict:** EDA → bronze-to-silver → silver-to-gold → verification. Each notebook must be run top-to-bottom; individual cells must never be re-run out of order (see Lessons Learned).

---

## Transformations by Layer — What and Why

Landing asks *did the bytes arrive intact?* Bronze: *are types trustworthy?* Silver: *is every row one real, unique event?* Gold: *does this answer a business question?*

### Load → Bronze: type enforcement (`etl-bronze-to-silver.ipynb`, §1)

| Transformation | Why |
|---|---|
| CSV read with `inferSchema=false` on events/item_properties, then `timestamp.cast(LongType())` → `timestamp_ms`, `event_timestamp = to_timestamp(ms/1000)` | Source unit is Unix **milliseconds**; a seconds/millis mix-up silently shifts every date. Casting once at bronze means downstream layers never re-derive types. |
| `visitorid/itemid/transactionid` cast to `long`; `filter(visitorid.isNotNull()).filter(itemid.isNotNull())` | Null keys can't join any dimension — removed early with intent documented. Verified: 0 rows removed (the raw file has no null keys), so the guard is free. |
| Written as **Delta** with `mode("overwrite")` | Delta gives schema tracking + time-travel on the raw layer; overwrite makes the notebook re-runnable from scratch. |

### Bronze → Silver: one row = one real event (§2)

| Transformation | Why |
|---|---|
| `events.filter(timestamp_ms.isNotNull()).dropDuplicates(["timestamp_ms","visitorid","itemid","event"])` | Natural identity of an event = *(when, who, what item, what action)*; repeats are logging artifacts. **Verified: removes 460 duplicate rows (0.017%)** — same key the BigQuery successor uses (it adds an explicit `ORDER BY transactionid DESC` so transaction rows are guaranteed to win ties). |
| `item_properties.filter(property.isin("categoryid","available")).dropDuplicates([...])` | Everything else is publisher-hashed and unreadable — keeps the analyzable **2,291,853 rows (11.3%)** out of 20.3M instead of carrying dead weight into gold. |
| `category_tree` passed through unchanged | Already clean — no transformation is a decision, not an omission. |

### Silver → Gold: star schema (`etl-silver-to-gold.ipynb`)

| Transformation | Why |
|---|---|
| `DROP TABLE IF EXISTS` all six gold tables first | Handles nullable-schema drift between runs (Engineering Challenge #6) — rebuild is clean, never a partial merge. |
| `dim_date`: distinct dates + calendar attributes + `monotonically_increasing_id()` **+ `.cache()`** | Date spine from data covers exactly the 139 active dates. `.cache()` pins the surrogate keys so a later Spark re-evaluation can't regenerate them — the core fix of Engineering Challenge #1 (keys must survive the fact-table join). |
| `dim_users`: `groupBy visitorid` → first/last event, totals, `has_purchased`, key + `.cache()` | Session noise rolled into one analyzable row per visitor. |
| `dim_items`: `row_number() OVER (PARTITION BY itemid ORDER BY timestamp_ms DESC) = 1` picks latest category; starts from `DISTINCT itemid IN events`, LEFT JOINs categories | SCD Type 1 (one row per item, latest category wins) **and** the Engineering Challenge #2 fix: starting from events guarantees every fact item exists in the dimension — 78.8% get a category, 21.2% keep NULL instead of orphaning fact rows. |
| `fact_events`: LEFT JOINs to all four dims, `monotonically_increasing_id()` key | Produces the fact at one-row-per-action grain; referential integrity is then **checked, not assumed**, by `etl-verification-checks.ipynb` (row counts, orphan keys, `transactionid` discipline). *(The BigQuery successor hardens this to INNER joins + in-pipeline assertions.)* |
| JDBC load: `connectRetryCount=3;connectRetryInterval=10`, `write_with_retry` (3 attempts, 10 s sleep), secrets-scoped `etl_loader` password | Intermittent Azure SQL load-balancer drops mid-write corrupted partial loads (Engineering Challenge #4) — retries make the load self-healing; the credential never appears in code (secrets scope `retailrocket`). |

---

## The Data at a Glance (Analyst Notes)

Profiled in `03-eda/EDA.ipynb` on the full dataset (the 1,000-row samples in `02-data/samples/` exist only so the repo runs without cloud access).

**Per-layer row counts** — recomputed locally from the full Kaggle CSVs using the same cleaning rules the notebooks apply; silver/gold counts independently confirmed by the Azure SQL screenshot below:

| Layer | Rows | Change |
|---|---|---|
| Landing | 2,756,101 | — (matches Kaggle exactly) |
| Bronze | 2,756,101 | null-key filter removed 0 rows (no null keys in the raw file) |
| Silver | 2,755,641 | 460 duplicate rows removed (0.017%) |
| Gold `fact_events` | 2,755,641 | star-schema joins + verification notebook pass — no rows lost |

What the data looks like:

- **Timestamps are Unix milliseconds** (13 digits), not seconds.
- **`item_properties` is a change log, not a snapshot:** of 20,275,902 rows only **2,291,853 (11.3%)** carry readable values — 90%+ of property values are hashed, so silver keeps only `categoryid` and `available` (`available` ∈ {0: 863,086, 1: 640,553}). **1,104 distinct property keys** exist.
- **Category coverage is incomplete, by design.** Of 235,061 items in events, **185,246 (78.8%)** resolve to a latest category; **49,815 (21.2%)** keep `category_sk = NULL` rather than being dropped (the fix from Engineering Challenge #2).
- **`transactionid` discipline in the source:** all 22,457 non-null values sit on transaction rows — zero violations; `etl-verification-checks.ipynb` re-asserts this in the warehouse.
- **A small heavy-visitor tail skews per-user stats:** median 1 event/visitor, p99 = 13, busiest visitor 7,757 events; the 30 visitors with >1,000 events hold **2.2% of all events** — filter them for per-user analysis. (The publisher warns such logs can carry "up to 40% abnormal traffic".)
- **Funnel on full data:** 2.60% of views reach add-to-cart, 32.4% of carts reach purchase, 0.84% overall.
- **`dim_date` = 139 rows** (139 calendar dates with activity; the elapsed span first→last event is 138 days).

## What This Model Can Answer

The schema supports these questions — capabilities only, no findings are asserted here:

- View → add-to-cart → transaction funnel rates by category, item, or time period
- Repeat-purchase behaviour per user (`has_purchased`, `total_purchases`)
- Category performance including the 21.2% uncategorized segment as its own slice
- Event volume rhythm across the 139-day window (`is_weekend`, `day_of_week`)
- Item popularity and category-mix shifts over the covered period

---

## Pipeline Evidence

Because the original Azure environment is no longer accessible, the screenshots below are the visual record of the pipeline running end-to-end. They are stored in [`docs/screenshots/`](docs/screenshots/) and are embedded here in the order the work was performed.

### 1. Azure resource provisioning

![Azure resource group creation](docs/screenshots/azure_resource_group_creation.png)

All Azure resources provisioned under `rg-azure-dw` — storage account `stdportfolio`, Databricks workspace `dbw-retailrocket`, SQL server `dw-retailrocket1` / database `retailrocket-dw`, and the NAT Gateway required for Secure Cluster Connectivity.

### 2. Star schema design

![Star schema](docs/screenshots/azure_dw_schema.png)

The Kimball dimensional model — 5 conformed dimensions (`dim_date`, `dim_users`, `dim_items`, `dim_categories`, `dim_event_type`) and 1 fact table (`fact_events`) at the grain of one user action.

### 3. Databricks cluster running

![Databricks cluster in use](docs/screenshots/db_cluster_use.png)

The D4ds_v4 cluster in a running state with the 30-minute auto-terminate setting turned on. This was captured while the cluster was functional.

### 4. Secrets scope configuration

![Databricks secret scoping](docs/screenshots/databricks_secret_scoping.png)

The Databricks secrets scope `retailrocket` holding two keys — `storage-key` (Blob account key) and `sql-password` (Azure SQL password). Values are not shown. Demonstrates the security hygiene principle: no credentials in code, all secrets accessed via `dbutils.secrets.get(scope, key)` via Databricks.

### 5. EDA summary

![EDA summary in Databricks](docs/screenshots/eda_summary_in_databricks.png)

`EDA.ipynb` output cells — row counts per source file, null-rate summary for `visitorid` / `itemid` / `timestamp`, distribution of event types (`view` / `addtocart` / `transaction`), and confirmation of the timestamp range (May 3 – September 18, 2015). This profiling preceded any transformation and informed the silver-layer cleansing rules.

### 6. Silver → Gold transformation

![Silver to Gold load](docs/screenshots/db_silver_to_gold_load.png)

The gold star-schema build — dimensions and fact table materialized from silver Delta tables. `dim_items` starts from *all* items in `events` (LEFT JOIN to categories) and applies SCD Type 1 for the latest category per item. Wide dimensions (`day_name`, `is_weekend`, `has_purchased`) are populated here.

### 7. ETL job pipeline

![ETL job pipeline](docs/screenshots/ETL_job_pipeline.png)

The Databricks Job pipeline view — a manual run (13 September 2026, 12m18s): bronze → silver and silver → gold completed; verification was still queued when the capture was taken. Task-level status configured via `databricks.yml` with branch-routed targets (`dev` → `retailrocket_dev`, `main` → `retailrocket`). Note: launched manually, not by a trigger.

### 8. Azure SQL — gold tables loaded

![Azure SQL verify DW](docs/screenshots/azure_sql_verify_dw.png)

Azure SQL Query editor (`retailrocket-dw`) showing the six gold tables created in the `retailrocket` schema. The JDBC bulk load from Databricks succeeded — data is now in the serving layer, ready for BI consumption.

### 9. Azure SQL — row count verification

![Azure SQL verify row counts](docs/screenshots/azure_sql_verify_dw_row_counts.png)

A row-count query running against each gold table, confirming the loads matched expected cardinality: `dim_date` 139, `dim_users` 1,407,580, `dim_items` 235,061, `dim_categories` 1,669, `dim_event_type` 3, `fact_events` 2,755,641. (`dim_date` = 139 calendar dates with activity; the span between first and last event is 138 days.)

### 10. Azure SQL — fact table verification

![Azure SQL verify fact table](docs/screenshots/azure_sql_verify_fact_table.png)

A sample analytical query against `fact_events` — showing the fact table populated at the correct grain, with `transactionid` populated only for transaction events. Confirms the warehouse is queryable and supports the analytical patterns the dashboard would have used.

### What was *not* captured

Being honest about gaps:


- **Full CI/CD on `main`** — the `dev` → `main` PR was opened after access loss, so no GitHub Actions instance deployed alongside the PR.
- **ADF scheduled run** — the resource (`adf-retailrocket`) and pipeline exist, but no trigger run was ever captured; the ETL job evidence above is a manual launch.
- **CI/CD on `main` with green output** — the workflow validated and deployed job definitions on `dev` before access loss, but no end-to-end post-merge deployment was recorded.


## What Was Built

### Built
- Medallion ETL (bronze → silver → gold) running from Databricks into Azure SQL Database via Databricks Jobs — executed end-to-end to a fully populated serving layer (manual run captured; ADF trigger configured but not captured)
- Star schema with 5 dims + 1 fact at the correct grain inside of Azure SQL Database
- Referential-integrity verification notebook (validation)
- GitHub Actions workflow configured for branch-based deploys, successfully validated and updated databricks job definitions prior to access loss.


## Engineering Challenges & Solutions

### 1. Surrogate keys regenerating on every Spark evaluation

`monotonically_increasing_id()` is **non-deterministic** — Spark is lazy, and each `.write()` re-evaluates the entire pipeline from source. Without intervention, the dimension tables get new keys on every write while `fact_events` retains the keys from a previous run. The result: **silent referential integrity breakage**.

**Fix:** call `.cache()` on every dimension DataFrame immediately after assigning the surrogate key. This forces materialization and pins the keys for the rest of the session. All five dimensions in `etl-silver-to-gold.ipynb` end with `.cache()  # Prevent different IDs generated when joining with fact_events.`

### 2. `dim_items` missing uncategorized items

Initial build only included items that appeared in `item_properties` with a `categoryid`. Items without a category were dropped — producing orphan `item_sk` values in `fact_events` for events on those items.

**Fix:** start from `SELECT DISTINCT itemid FROM events`, then LEFT JOIN to categories. Unmatched items get `category_sk = NULL` but retain their `item_sk`.

### 3. SCD Type 1 for category

Items can change categories over time, but `dim_items` should have exactly one row per item.

**Fix:** use a window function to pick the latest `categoryid` per item:
```sql
ROW_NUMBER() OVER (PARTITION BY itemid ORDER BY timestamp_ms DESC) = 1
```

### 4. Azure SQL transient connection failures during JDBC writes

Random "access denied" errors occurred during load-balancing reconfiguration — often mid-write, corrupting partial loads.

**Fix:** add retry parameters to the JDBC URL:
```
connectRetryCount=3;connectRetryInterval=10
```

### 5. Contained database users avoid the master-database requirement

Initial attempts to create `etl_loader` failed with *"User must be in master database."*

**Fix:** Azure SQL supports **contained users** — `CREATE USER ... WITH PASSWORD` runs directly in the target database. No master access required.

### 6. Delta schema merges fail on nullability changes

Changing a column from non-nullable to nullable broke Delta's schema merge (`DELTA_FAILED_TO_MERGE_FIELDS`).

**Fix:** drop the target table before writing when the schema changes:
```python
spark.sql("DROP TABLE IF EXISTS gold.<table_name>")
```

---

## Lessons Learned

### Platform & Infrastructure

- **Cluster-based platforms introduce failures unrelated to the data engineering.** The East Asia region experienced vCPU quota exhaustion, DS3_v2 capacity stockout, and SKU availability grey-out. The cluster worked when it ran; it frequently couldn't be provisioned.
- **Auto-termination is a cost control, not a reliability control.** The 15-minute setting was rejected by the platform — and when it did work, it terminated clusters mid-work, forcing restarts.
- **NAT Gateway is a hidden recurring cost.** Secure Cluster Connectivity required one at ~$1.08/day — the single largest cost line in a project whose total spend stayed around $30–40.
- **A quota is a ceiling; a stockout is a wall.** The free-tier limits (14-day DBUs, 250 DTU SQL) were sufficient on paper, but capacity constraints prevented provisioning.
- **Cloud resources are rented, not owned.** Azure and Databricks access was lost on 30 September 2026. Only the GitHub repository survived. Version-control everything for reproducibility.

### ETL Methodology (Medallion)

- **Silver is not optional.** Bronze = raw load. Silver = clean & dedup. Gold = business logic. Skipping silver leaked cleansing logic into gold.
- **Always run the entire notebook top-to-bottom.** Re-running a single cell regenerates surrogate keys with different values. The fact table retains old keys while dimensions get new ones — silent integrity break.
- **Wide dimensions are a Kimball best practice.** Include deterministic derived attributes (`day_name`, `is_weekend`, `has_purchased`) in the dimension. Keep business logic (segments, thresholds) downstream in the BI layer.
- **Referential-integrity checks are mandatory.** Orphan surrogate keys break Power BI relationships. `etl-verification-checks.ipynb` exists specifically for this.

### Data Characteristics

- **Timestamps are Unix milliseconds, not seconds.** 13-digit values. Divide by 1000 before conversion.
- **`item_properties` is a change log, not a snapshot.** The same item appears many times as attributes change. 90%+ of values are hashed for privacy; only `categoryid` and `available` are readable.
- **`categoryid` is the only category source in the dataset.** It enables category drill-down in downstream BI.

### Security & Process

- **Secrets never belong in code.** All credentials lived in a Databricks secrets scope, accessed via `dbutils.secrets.get(scope, key)`.
- **Contained database users avoid master-database dependency.** `CREATE USER ... WITH PASSWORD` works directly in the target DB.
- **CI/CD coupled to a cloud service dies when the service dies.** The GitHub Actions workflow depends on a live Databricks workspace and a valid PAT. When access was lost, the workflow became non-functional.

---

## Repository Structure

```
azure-databricks-datawarehouse/
├── README.md
├── databricks.yml                       # Databricks bundle config (jobs + targets)
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml                       # ⚠️ Non-functional — depends on Databricks
│
├── 01-infra/
│   ├── README.md                        # Audit map: resource shells + content map
│   └── *.bicep                          # Exported resource snapshots from Portal
│
├── 02-data/
│   ├── README.md
│   └── samples/                         # 1,000-row CSVs (runnable without cloud)
│
├── 03-eda/
│   └── EDA.ipynb                        # Full dataset exploration
│
├── 04-etl/
│   ├── etl-bronze-to-silver.ipynb       # Bronze load + silver clean/dedup
│   ├── etl-silver-to-gold.ipynb         # Star schema + Azure SQL load
│   └── etl-verification-checks.ipynb    # Data quality validation
│
└── docs/
    └── screenshots/                     # Pipeline evidence (embedded above)
        ├── azure_resource_group_creation.png
        ├── azure_dw_schema.png
        ├── db_cluster_use.png
        ├── databricks_secret_scoping.png
        ├── eda_summary_in_databricks.png
        ├── db_silver_to_gold_load.png
        ├── ETL_job_pipeline.png
        ├── azure_sql_verify_dw.png
        ├── azure_sql_verify_dw_row_counts.png
        └── azure_sql_verify_fact_table.png
```

**Branch note:** All work lives on the `dev` branch. The `dev` → `main` PR was never opened, so `main` is incomplete.

---

## Rebuild Guide

If access is restored or a fresh Azure subscription is used, the project can be rebuilt from this repo.

### Prerequisites
- Azure subscription (or Azure for Students)
- Databricks workspace (Premium tier, East Asia region)
- Raw CSVs from [Kaggle](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset) — stored locally as backup

### Setup steps

1. **Azure resources** — resource group `rg-azure-dw`; storage account `stdportfolio` with `raw/data-retailrocket/` container; SQL server `dw-retailrocket1` with database `retailrocket-dw`
2. **Databricks** — workspace `dbw-retailrocket`; job cluster per `databricks.yml` = single-node `Standard_D4s_v3`, Photon, DBR 19.x; the interactive dev cluster ran `Standard_D4ds_v4` (16 GB / 4 cores, 19 ML Runtime) with 30-min auto-terminate
3. **Secrets** — create scope `retailrocket`; add `storage-key` (Blob account key) and `sql-password` (SQL password)
4. **Azure SQL** — enable firewall rule *"Allow Azure services and resources to access this server"*; create contained user:
   ```sql
   CREATE USER etl_loader WITH PASSWORD='<password>';
   ALTER ROLE db_datawriter ADD MEMBER etl_loader;
   ALTER ROLE db_datareader ADD MEMBER etl_loader;
   ALTER ROLE db_ddladmin   ADD MEMBER etl_loader;
   ```
5. **GitHub** — generate a fine-grained PAT (Contents Read/Write); connect Databricks Git folder to this repo
6. **CI/CD** — set repository secrets `DATABRICKS_HOST` and `DATABRICKS_TOKEN` to the new workspace URL and PAT
7. **Run ETL** — execute notebooks in order: `EDA.ipynb` → `etl-bronze-to-silver.ipynb` → `etl-silver-to-gold.ipynb` → `etl-verification-checks.ipynb`
8. **Power BI** *(future implementation)* — connect to Azure SQL, import gold tables, build dashboards for conversion funnel analytics

### Known gotchas

| Symptom                                | Fix                                                                                                           |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `SCHEMA_NOT_FOUND`                     | Run `spark.sql("CREATE SCHEMA IF NOT EXISTS bronze")` before writing                                          |
| `wasbs://` path errors                 | Confirm storage account name is `stdportfolio` (no `w`)                                                       |
| JDBC "access denied" (intermittent)    | Add `connectRetryCount=3;connectRetryInterval=10` to the JDBC URL                                             |
| `User must be in master database`      | Use contained-user auth — `CREATE USER ... WITH PASSWORD` in the target DB                                    |
| `DELTA_FAILED_TO_MERGE_FIELDS`         | Drop the target table first: `spark.sql("DROP TABLE IF EXISTS gold.<table>")`                                 |
| Orphan surrogate keys in `fact_events` | Confirm every dimension DataFrame has `.cache()` after `monotonically_increasing_id()`                        |
| CI/CD workflow fails on push           | Expected — Databricks access lost. Re-provision a workspace and update `DATABRICKS_HOST` / `DATABRICKS_TOKEN` |

---

## Cost

| Resource                     | Approx. Cost            | Notes                                                      |
| ---------------------------- | ----------------------- | ---------------------------------------------------------- |
| Azure Databricks             | Free tier (14-day DBUs) | Auto-terminate clusters aggressively                       |
| Azure SQL Database           | Free tier (250 DTU)     | Basic tier is sufficient                                   |
| Azure Blob Storage           | Negligible              | ~988 MB total (events 94 MB + item properties 893 MB in 2 parts + categories 14 KB) |
| NAT Gateway                  | ~$1.08/day (~$32/mo)    | Required for Secure Cluster Connectivity; delete when idle |
| **Total (project duration)** | **~$30–40**             | —                                                          |

---

## Acknowledgments

- **Dataset:** [RetailRocket Recommender System](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset) — 2,756,101 events and 20,275,902 item-property rows, May 3 – September 18, 2015 (no country is stated on the dataset page; an earlier "Netherlands" note here was unverified and removed). License: CC BY-NC-SA 4.0. The third event value is spelled `addtocart`.
- **Modeling approach:** Kimball dimensional modeling — wide dimensions, SCD Type 1, surrogate keys

---

## Related

Rebuilt serverless on Google BigQuery after the Azure subscription expired: [retailrocket-bigquery-warehouse](https://github.com/AriefRuer/retailrocket-bigquery-warehouse) — same star schema, same dataset, Dataform instead of notebooks, assertions instead of a verification notebook, $0/month.

## License

MIT