# 01-infra — Azure resource shells as code

This folder holds the **shell** (config) of every Azure resource in the project, exported
from the Portal as **Bicep** via the built-in **Export template** button. The **content**
(code + data) of each resource lives in its own phase folder — the mapping is below.

> **Mental model:** the Portal is the workshop (where you click); this folder + the phase
> folders are the showroom (what a reviewer sees). Shell = Bicep here; content = the code
> in `02-data/`, `03-etl/`, `04-warehouse/`, `05-orchestration/`, `06-powerbi/`.

## Audit map — every resource → its files

| Azure resource | Shell → this folder | Content → where | Exported when |
|---|---|---|---|
| **Resource Group** `rg-azure-dw` | `rg-azure-dw.bicep` (whole stack in one export) | — | Phase 1 (re-export after any config change) |
| **Storage Account** `stdwportfolio` | `storage-stdwportfolio.bicep` (tier, LRS, network rules) | Samples + EDA → `02-data/` (full CSVs stay in Azure) | Phase 1 |
| **Azure SQL** `retailrocket-dw` | `sql-retailrocket.bicep` (server + DB config) | Schema SQL → `04-warehouse/schema/` | Phase 1 (config) / Phase 5 (schema) |
| **Databricks** `dbw-retailrocket` | `databricks-dbw-retailrocket.bicep` (workspace shell) | Notebooks (live via Repos) + job bundle → `03-etl/` | Phase 1 (shell) / Phase 3 (content) |
| **ADF** `adf-retailrocket` | ⚠️ generic export does NOT support ADF → its own export | Pipeline JSON → `05-orchestration/pipeline-json/` | Phase 4 |
| **Power BI** | — (no shell) | `.pbix` + measures → `06-powerbi/` | Phase 6 |

## How to export (2 min each)

1. Portal → open the resource → left menu → **Export template**
2. Toggle **Bicep** (prettier) or **ARM Template** (raw JSON)
3. **Download** → commit here as `01-infra/<resource>.bicep`

## Caveats (Microsoft's own)

- **Export is a snapshot, not maintained IaC** — captures current state, needs light cleanup
  before reuse, and **strips secrets** (keys/tokens are never in these files — correct).
- **Re-export after any Portal config change** so the repo stays honest.
- Redeployable via **Deploy a custom template** or `az deployment group create` if you ever
  want to recreate the stack — but that's optional; these files are primarily evidence + config.

## Related

- Phase 3: Databricks content (notebooks + `databricks.yml` bundle + CI/CD) — see `03-etl/`
- Phase 4: ADF pipeline export — see `05-orchestration/pipeline-json/`
- Full walkthrough: `PORTAL-STEPS.md` → Appendix (Git Audit & CI/CD)

## CI/CD environments (branch → target)

The Databricks job has two **targets** in `03-etl/databricks.yml` — `dev` (writes the
`retailrocket_dev` schema) and `prod` (writes `retailrocket`). GitHub Actions routes by branch:

| Git branch | `ci.yml` deploys | Writes to |
|---|---|---|
| `dev` | `databricks bundle deploy --target dev` | `retailrocket_dev` schema |
| `main` | `databricks bundle deploy --target prod` | `retailrocket` schema |

Develop on `dev`; open a PR to `main` when clean → the merge promotes to prod. A bad commit on
`dev` never touches prod. This is the staging pattern — one workspace, zero extra cost.
