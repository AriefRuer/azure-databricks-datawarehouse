
## Audit map — every resource → its files

| Azure resource |
|---|
| **Resource Group** `rg-azure-dw` | 
| **Storage Account** `stdwportfolio` | 
| **Azure SQL** `retailrocket-dw` |
| **Databricks** `dbw-retailrocket` |
| **ADF** `adf-retailrocket` |
| **Power BI** | 


## CI/CD environments (branch → target)

The Databricks job has two **targets** in `03-etl/databricks.yml` — `dev` (writes the
`retailrocket_dev` schema) and `prod` (writes `retailrocket`). GitHub Actions routes by branch:

| Git branch | `ci.yml` deploys | Writes to |
|---|---|---|
| `dev` | `databricks bundle deploy --target dev` | `retailrocket_dev` schema |
| `main` | `databricks bundle deploy --target prod` | `retailrocket` schema |

Develop on `dev`; open a PR to `main` when clean → the merge promotes to prod. A bad commit on
`dev` never touches prod. This is the staging pattern — one workspace, zero extra cost.
