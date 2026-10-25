"""Neurology Insurance Solution — P&C Finance Ontology Explorer."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ontology import build_turtle, resolve_neighborhood


st.set_page_config(page_title="P&C Finance Ontology | Neurology Insurance", page_icon="🧠", layout="wide")

DATA_FILE = Path(__file__).parent / "data" / "PnC_Financial_Reporting_GL_CDM_Ontology.xlsx"


@st.cache_data(show_spinner=False)
def load_catalog(data: bytes) -> dict[str, pd.DataFrame]:
    with pd.ExcelFile(BytesIO(data)) as book:
        names = ["Overview", "Tables", "Columns", "Picklists", "Picklist Uses", "Ontology Nodes", "Ontology Edges", "Financial Controls", "Assumptions"]
        absent = set(names) - set(book.sheet_names)
        if absent:
            raise ValueError(f"Missing required worksheets: {', '.join(sorted(absent))}")
        return {name: pd.read_excel(book, sheet_name=name).fillna("") for name in names}


def graph_figure(nodes: pd.DataFrame, edges: pd.DataFrame, focus: str, hops: int) -> go.Figure:
    graph = nx.Graph()
    for row in nodes.itertuples(index=False):
        graph.add_node(str(row[0]), domain=str(row[1]))
    for row in edges.itertuples(index=False):
        src, _, dst = str(row[0]), str(row[1]), str(row[2])
        if src in graph and dst in graph:
            graph.add_edge(src, dst)
    subset = resolve_neighborhood(graph, focus, hops) if focus != "Entire model" else set(graph.nodes)
    graph = graph.subgraph(subset).copy()
    if not graph.nodes:
        return go.Figure().update_layout(title="No connected ontology entities")
    positions = nx.spring_layout(graph, seed=17, k=1.6 / max(1, len(graph.nodes)) ** 0.5, iterations=110)
    edge_x, edge_y = [], []
    for source, target in graph.edges:
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", hoverinfo="skip", line=dict(color="#97afc3", width=1), showlegend=False))
    domains = nx.get_node_attributes(graph, "domain")
    colors = {key: f"hsl({(i * 43 + 190) % 360},58%,47%)" for i, key in enumerate(sorted(set(domains.values())))}
    fig.add_trace(go.Scatter(
        x=[positions[n][0] for n in graph.nodes], y=[positions[n][1] for n in graph.nodes],
        text=list(graph.nodes), customdata=[domains[n] for n in graph.nodes],
        hovertemplate="<b>%{text}</b><br>Domain: %{customdata}<extra></extra>",
        mode="markers+text", textposition="top center", textfont=dict(size=10),
        marker=dict(size=[24 if n == focus else 14 for n in graph.nodes], color=[colors[domains[n]] for n in graph.nodes], line=dict(width=1, color="white")),
        showlegend=False,
    ))
    fig.update_layout(height=650, margin=dict(l=10, r=10, t=10, b=10), xaxis=dict(visible=False), yaxis=dict(visible=False), plot_bgcolor="#f7fafc", paper_bgcolor="#f7fafc", dragmode="pan")
    return fig


def show_data(df: pd.DataFrame, name: str) -> None:
    st.dataframe(df, width="stretch", hide_index=True, height=450)
    st.download_button(f"Download {name} CSV", df.to_csv(index=False).encode("utf-8"), file_name=name.lower().replace(" ", "_") + ".csv", mime="text/csv")


st.markdown("""<style>
.block-container {padding-top: 1.8rem;}
h1 {color: #15384e;} [data-testid="stMetricValue"] {color: #087c8c;}
</style>""", unsafe_allow_html=True)
st.title("🧠 P&C Financial Ontology Explorer")
st.caption("Neurology Insurance Solution · Saba Gobal, CPCU · Global Canonical Hub / AGI-OS")

with st.sidebar:
    st.header("Data source")
    uploaded = st.file_uploader("Optional replacement CDM workbook", type=["xlsx"], help="Must retain the nine named ontology/catalog worksheets.")
    st.info("The included workbook is a reference model. Changes uploaded here are session-only and are not saved to the server.")

try:
    data = uploaded.getvalue() if uploaded is not None else DATA_FILE.read_bytes()
    catalog = load_catalog(data)
except (FileNotFoundError, ValueError, OSError, ImportError) as exc:
    st.error(f"Cannot load ontology workbook: {exc}")
    st.stop()

tables = catalog["Tables"]
fields = catalog["Columns"]
picklists = catalog["Picklists"]
nodes = catalog["Ontology Nodes"]
edges = catalog["Ontology Edges"]
stats = st.columns(4)
for box, label, count in zip(stats, ["Logical tables", "Defined columns", "Picklist options", "Ontology relationships"], [len(tables), len(fields), len(picklists), len(edges)]):
    box.metric(label, f"{count:,}")

tabs = st.tabs(["Ontology graph", "Tables & columns", "Picklists", "Financial flow", "Rules & controls", "Export ontology", "About"])

with tabs[0]:
    st.subheader("Explore connected entities")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        focus = st.selectbox("Entity to explore", ["Entire model"] + sorted(nodes["Entity"].astype(str).tolist()), index=0)
    with c2:
        hops = st.slider("Relationship depth", 1, 3, 2, disabled=(focus == "Entire model"))
    with c3:
        kind = st.selectbox("Relationship status", ["All", "Modeled", "Semantic", "External or SME-defined", "External canonical hub"])
    scoped_edges = edges if kind == "All" else edges[edges["Status"] == kind]
    st.plotly_chart(graph_figure(nodes, scoped_edges, focus, hops), width="stretch")
    selected_edges = scoped_edges if focus == "Entire model" else scoped_edges[(scoped_edges["Source entity"] == focus) | (scoped_edges["Target entity"] == focus)]
    st.caption("Drag to pan, scroll to zoom. Choose an entity for a focused relationship table. Relationships marked external require mapping to your wider canonical hub.")
    show_data(selected_edges, "ontology_relationships")

with tabs[1]:
    c1, c2 = st.columns([1, 2])
    with c1:
        domain = st.selectbox("Module", ["All"] + sorted(tables["Module"].astype(str).unique()))
    with c2:
        term = st.text_input("Search table, column or definition")
    filtered = fields.merge(tables[["Table", "Module"]], on="Table", how="left")
    if domain != "All":
        filtered = filtered[filtered["Module"] == domain]
    if term:
        mask = filtered.astype(str).apply(lambda col: col.str.contains(term, case=False, regex=False)).any(axis=1)
        filtered = filtered[mask]
    chosen = st.selectbox("Inspect a table", ["All matching"] + sorted(filtered["Table"].unique().tolist()))
    if chosen != "All matching":
        filtered = filtered[filtered["Table"] == chosen]
    st.caption(f"{len(filtered)} matching columns across {filtered['Table'].nunique()} tables")
    show_data(filtered, "canonical_columns")

with tabs[2]:
    option = st.selectbox("Picklist domain", ["All"] + sorted(picklists["Domain"].unique().tolist()))
    choices = picklists if option == "All" else picklists[picklists["Domain"] == option]
    show_data(choices, "picklist_options")
    if option != "All":
        st.markdown("**Columns using this domain**")
        st.dataframe(catalog["Picklist Uses"][catalog["Picklist Uses"]["Picklist domain"] == option], hide_index=True, width="stretch")

with tabs[3]:
    st.subheader("Financial event to regulatory report")
    flow = ["FinancialEvent", "SubledgerEntry", "JournalBatch", "JournalHeader", "JournalLine", "GLBalance", "TrialBalance", "AccountReportMapping", "ReportLine", "FinancialFact", "ReportingRun", "RegulatoryFiling"]
    st.markdown(" → ".join(f"`{item}`" for item in flow))
    st.info("Illustrative semantic process path, not one uninterrupted foreign-key chain. Validations and approved posting rules control every accounting transition.")
    step = st.selectbox("Inspect financial flow entity", flow)
    st.dataframe(fields[fields["Table"] == step], width="stretch", hide_index=True)

with tabs[4]:
    st.subheader("Validation and reconciliation library")
    show_data(catalog["Financial Controls"], "financial_controls")

with tabs[5]:
    st.subheader("Export OWL-compatible RDF/Turtle")
    st.write("The generated ontology includes classes, data properties, relationship properties, and human-readable descriptions. Validate its semantics and governance before merging into an enterprise ontology.")
    ttl = build_turtle(nodes, fields, edges)
    st.download_button("Download financial_ontology.ttl", ttl.encode("utf-8"), file_name="financial_ontology.ttl", mime="text/turtle")
    st.download_button("Download source workbook", data, file_name="PnC_Financial_Reporting_GL_CDM_Ontology.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.code("\n".join(ttl.splitlines()[:23]), language="turtle")

with tabs[6]:
    st.markdown("""**Scope:** reference model for US P&C insurers, including statutory accounting, GAAP and management reporting.\n+
    **Not official regulatory content:** proposed account mappings, sample picklists and table designs require Finance/Controller, Actuarial, Compliance, IT Security and regulator-specific approval. NAIC Annual Statement blanks and instructions are not embedded.\n+
    **Integration:** map external Policy, Claim, BillingTransaction and ReinsuranceContract entities to your Global Canonical Hub. Add effective-dated rule approvals, reconciliation evidence and controlled migrations before production use.\n+
    **Privacy:** use synthetic demo data; do not upload policyholder or banking records to a public demonstration.\n+    """)
    show_data(catalog["Assumptions"], "design_assumptions")
