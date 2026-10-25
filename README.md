# P&C Financial Reporting and General Ledger Ontology Explorer

Neurology Insurance Solution — Saba Gobal, CPCU

An interactive reference-model demonstration built on the 49-table financial CDM workbook, including 575 column definitions, 306 picklist options, and 106 relationship entries.

The **Enterprise Ontology Factory** tab adds a structured Excel proof of concept for **United States → Florida → Homeowners → HO3 → All Modules**. It includes an editable synthetic template with 19 entities, 79 field definitions, 20 ontology relationships, 24 picklist options, and five proposed controls.

## Features

- Search tables, columns, definitions and picklist options.
- Explore ontology as a filterable network graph, including focused one-to-three-hop neighborhoods.
- Follow the financial event → subledger → GL → trial balance → financial reporting pathway.
- Download RDF/Turtle (`.ttl`), catalog CSVs, and the source Excel workbook.
- Upload an updated Excel catalog with the same nine worksheets to explore it during the session.
- Inspect financial posting, reconciliation and filing controls.
- Download or upload a structured insurer CDM workbook; select country, state, LOB, product and module; validate scope and graph; export scoped RDF/Turtle.

## Run locally

Python 3.11+ recommended.

```bash
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Publish with GitHub and Streamlit Community Cloud

1. Create a **private** GitHub repository, e.g. `pnc-financial-ontology-demo`.
2. Upload the *contents* of this folder to the repository root, including `.streamlit/config.toml` and `data/`.
3. Open [share.streamlit.io](https://share.streamlit.io), connect your GitHub account, and select the repository and branch.
4. Set main file path to `app.py`, then deploy. Configure access according to your Streamlit hosting plan and privacy needs.
5. Confirm the application loads all counts and test the graph, search, and Turtle export.

GitHub repository and public URL **have not been created automatically** in this delivery.

## Data and governance

This is an insurer-facing **reference architecture**, not official NAIC reporting content or a production ledger. Picklist options and financial mappings are illustrative. Obtain and validate current statutory reporting instructions, approved company chart of accounts and regulatory filing definitions. Do not upload real client records or private policyholder/financial data to a public demo.

The ontology exporter creates OWL classes, datatype properties, relationship properties and descriptive annotations for **modeled local classes**. The ontology does not automatically infer regulatory obligations, accounting treatments, or externally referenced policy/claim entities.

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Streamlit UI and graph explorer |
| `ontology.py` | Ontology construction and RDF/Turtle export |
| `factory.py` | Scoping, reference validation and ontology-frame conversion |
| `data/*.xlsx` | Canonical tables, columns, picklists, ontology and validations |
| `requirements.txt` | Python dependencies |
| `.streamlit/config.toml` | App theme and server configuration |

## HO3 multi-module proof of concept

1. Open **Enterprise Ontology Factory** and select United States / Florida / Homeowners / HO3 / All Modules.
2. Download `FL_HO3_All_Modules_Ontology_POC.xlsx` and inspect its `Entities`, `Fields`, `Relationships`, `Picklists`, and `Rules` sheets.
3. Optionally add insurer-approved definitions while preserving the column headers. Reupload the workbook.
4. Review structural validation. A referenced entity or picklist domain outside the scope is flagged; unapproved entity records are marked for SME review.
5. Explore the resulting graph and download its RDF/Turtle file. Scope filtering is exact or recognizes `ALL` / `*` applicability entries.

This proof of concept **does not** turn arbitrary unstructured Excel sheets into a trustworthy ontology automatically, persist SME approvals, or execute rating and posting rules. The workbook schema is the controlled intake contract. The current selector is intentionally scoped to Florida HO3; additional product catalogs can be added in later iterations.

