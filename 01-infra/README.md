
## Audit map — every resource → its files

| Azure resource | Resource Name |
|---|---|
| **Resource Group** |  `rg-azure-dw` | 
| **Storage Account** | `stdportfolio` | 
| **Azure SQL** | `retailrocket-dw` |
| **Databricks** | `dbw-retailrocket` |
| **ADF** | `adf-retailrocket` |
| **Power BI** | - |


## CI/CD environments (branch → target)

The Databricks job has two **targets** in `databricks.yml` (repo root) — `dev` (intended to write the
`retailrocket_dev` schema) and `prod` (intended to write `retailrocket`). GitHub Actions routes by branch:

| Git branch | `ci.yml` deploys | Intended schema |
|---|---|---|
| `dev` | `databricks bundle deploy --target dev` | `retailrocket_dev` schema |
| `main` | `databricks bundle deploy --target prod` | `retailrocket` schema |

Develop on `dev`; open a PR to `main` when clean → the merge promotes to prod. This is the staging pattern — one workspace, zero extra cost.

> **Limitation:** the separation did not take effect. `databricks.yml` passes the parameter as `schema`, but `etl-silver-to-gold.ipynb` reads `target_schema`, falls back to `dbo`, and both targets write the same Azure SQL tables. See *Known Limitations* in the main README.
