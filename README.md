# P&C Financial Reporting and General Ledger Ontology Explorer

Neurology Insurance Solution — Saba Gobal, CPCU

An interactive reference-model demonstration built on the 49-table financial CDM workbook, including 575 column definitions, 306 picklist options, and 106 relationship entries.

## Features

- Search tables, columns, definitions and picklist options.
- Explore ontology as a filterable network graph, including focused one-to-three-hop neighborhoods.
- Follow the financial event → subledger → GL → trial balance → financial reporting pathway.
- Download RDF/Turtle (`.ttl`), catalog CSVs, and the source Excel workbook.
- Upload an updated Excel catalog with the same nine worksheets to explore it during the session.
- Inspect financial posting, reconciliation and filing controls.

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
| `data/*.xlsx` | Canonical tables, columns, picklists, ontology and validations |
| `requirements.txt` | Python dependencies |
| `.streamlit/config.toml` | App theme and server configuration |

