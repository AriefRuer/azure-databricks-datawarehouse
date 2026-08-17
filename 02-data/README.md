# 02-data — RetailRocket dataset

The full RetailRocket dataset lands in **Azure Blob Storage** (`raw/` container, private).
This folder carries **1,000-row samples** so every notebook in this repo runs without any
Azure access or credentials.

## What's here

| File | Full size | Sample rows | What it is |
|---|---|---|---|
| `events.csv` | ~94 MB | 1,000 | Every visitor action: `view`, `addtocart`, `transaction` |
| `category_tree.csv` | 14 KB | 1,000 | Category hierarchy (parent → child) |
| `item_properties.csv` | ~900 MB (2 parts) | 1,000 | Item attribute **change log** (enrichment only) |

## Why samples?

The full files live in Azure Blob for the pipeline to consume. Committing 1,000-row
samples instead of ~1 GB of CSVs keeps the repo light, keeps data private, and lets
anyone clone the repo and run the notebooks with **zero cloud setup**.

- Full data → `data-retailrocket/` (gitignored, local only) and the Blob `raw/` container
- Samples → `02-data/samples/` (committed, used by notebooks + CI)

## How to regenerate

```bash
python scripts/sample-data.py
```

Reads the full CSVs from `data-retailrocket/`, takes the first 1,000 rows of each
(streaming — it does not load 900 MB into memory), and writes the samples here.
`item_properties_part1.csv` + `part2.csv` are merged into one `item_properties.csv` sample.

## Data notes (what EDA found)

- **Timestamps are Unix milliseconds, not seconds** — 13 digits. Divide by 1000 before
  converting to dates (`pd.to_datetime(col, unit="ms")`, `from_unixtime(ts/1000)` in SQL).
- **`item_properties` is a change log, not a snapshot** — the same item appears many times
  as its attributes changed over time. 90%+ of values are hashed for privacy; only
  `categoryid` and `available` are readable.
- **`categoryid` is the only category source in the whole dataset** — it turns
  "item 1000" into "item 1000 in category X" and enables category drill-down in Power BI.
  See `02-data/eda/` for the full exploration.
