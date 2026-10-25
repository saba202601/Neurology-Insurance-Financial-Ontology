"""Scoped, reviewable ontology assembly from an insurer-supplied Excel catalog."""
from __future__ import annotations

from io import BytesIO

import pandas as pd


REQUIRED = {
    "Entities": ["EntityID", "EntityName", "Domain", "Description", "Module", "Country", "State", "LineOfBusiness", "Product", "ApprovalStatus"],
    "Fields": ["EntityID", "EntityName", "FieldName", "DataType", "BusinessDefinition", "KeyType", "PicklistDomain", "Country", "State", "LineOfBusiness", "Product", "Module", "ApprovalStatus"],
    "Relationships": ["RelationshipID", "SourceEntityID", "Predicate", "TargetEntityID", "Cardinality", "Description", "Country", "State", "LineOfBusiness", "Product", "Module", "ApprovalStatus"],
    "Picklists": ["PicklistDomain", "OptionCode", "OptionLabel", "Description", "Country", "State", "LineOfBusiness", "Product", "Module", "ApprovalStatus", "SortOrder"],
    "Rules": ["RuleID", "RuleName", "EntityID", "RuleType", "RuleExpression", "Country", "State", "LineOfBusiness", "Product", "Module", "ApprovalStatus"],
}
SCOPE = {"Country": "United States", "State": "Florida", "LineOfBusiness": "Homeowners", "Product": "HO3", "Module": "All Modules"}


def load_factory_workbook(data: bytes) -> dict[str, pd.DataFrame]:
    with pd.ExcelFile(BytesIO(data)) as xl:
        absent = set(REQUIRED) - set(xl.sheet_names)
        if absent:
            raise ValueError(f"Missing sheets: {', '.join(sorted(absent))}")
        tables = {name: pd.read_excel(xl, sheet_name=name, dtype=str).fillna("") for name in REQUIRED}
    for name, required in REQUIRED.items():
        missing = set(required) - set(tables[name].columns)
        if missing:
            raise ValueError(f"{name} sheet missing columns: {', '.join(sorted(missing))}")
        tables[name] = tables[name].apply(lambda c: c.str.strip())
    return tables


def apply_scope(df: pd.DataFrame, selected: dict[str, str]) -> pd.DataFrame:
    result = df
    for key, choice in selected.items():
        if choice == "All Modules" and key == "Module":
            continue
        allowed = {choice.casefold(), "all", "*"}
        if key == "Module":
            allowed.add("all modules")
        result = result[result[key].str.casefold().isin(allowed)]
    return result.copy()


def assemble_catalog(tables: dict[str, pd.DataFrame], selected: dict[str, str]):
    scoped = {name: apply_scope(frame, selected) for name, frame in tables.items()}
    entities = scoped["Entities"]
    ids = set(entities["EntityID"])
    # Remove fields, rules and relationships outside the selected entity universe.
    scoped["Fields"] = scoped["Fields"][scoped["Fields"]["EntityID"].isin(ids)].copy()
    scoped["Rules"] = scoped["Rules"][scoped["Rules"]["EntityID"].isin(ids)].copy()
    rel = scoped["Relationships"]
    scoped["Relationships"] = rel[rel["SourceEntityID"].isin(ids) & rel["TargetEntityID"].isin(ids)].copy()
    return scoped


def validate_catalog(tables: dict[str, pd.DataFrame], selected: dict[str, str]) -> pd.DataFrame:
    findings = []
    def add(severity, sheet, record, message):
        findings.append({"Severity": severity, "Sheet": sheet, "Record": str(record), "Finding": message})
    ent = apply_scope(tables["Entities"], selected)
    ids = set(ent["EntityID"])
    if ent.empty:
        add("ERROR", "Entities", "Scope", "No entities match this selection")
    if ent["EntityID"].duplicated().any():
        add("ERROR", "Entities", "EntityID", "Duplicate entity identifiers within selected scope")
    if ent["EntityName"].duplicated().any():
        add("ERROR", "Entities", "EntityName", "Duplicate entity names within selected scope")
    for row in ent.itertuples(index=False):
        if not row.Description:
            add("WARNING", "Entities", row.EntityID, "Business definition is missing")
        if row.ApprovalStatus.casefold() != "approved":
            add("REVIEW", "Entities", row.EntityID, "SME approval pending")
    selected_fields = apply_scope(tables["Fields"], selected)
    for row in selected_fields.itertuples(index=False):
        if row.EntityID not in ids:
            add("ERROR", "Fields", f"{row.EntityID}.{row.FieldName}", "Field references an entity missing from the selected scope")
        if not row.BusinessDefinition:
            add("WARNING", "Fields", f"{row.EntityID}.{row.FieldName}", "Field definition is missing")
    if selected_fields.duplicated(subset=["EntityID", "FieldName"]).any():
        add("ERROR", "Fields", "EntityID+FieldName", "Duplicate scoped field definitions")
    domains = set(apply_scope(tables["Picklists"], selected)["PicklistDomain"])
    for row in selected_fields.itertuples(index=False):
        if row.PicklistDomain and row.PicklistDomain not in domains:
            add("ERROR", "Fields", f"{row.EntityID}.{row.FieldName}", f"Missing picklist domain {row.PicklistDomain}")
    for row in apply_scope(tables["Relationships"], selected).itertuples(index=False):
        if row.SourceEntityID not in ids or row.TargetEntityID not in ids:
            add("WARNING", "Relationships", row.RelationshipID, "Relationship endpoint is outside selected ontology; link omitted")
        if not row.Predicate:
            add("ERROR", "Relationships", row.RelationshipID, "Relationship predicate is missing")
    if not findings:
        add("PASS", "Catalog", "Scope", "No structural issues detected; SME sign-off still required")
    return pd.DataFrame(findings)


def to_rdf_frames(catalog: dict[str, pd.DataFrame]):
    ent = catalog["Entities"]
    id_to_name = dict(zip(ent["EntityID"], ent["EntityName"]))
    nodes = pd.DataFrame({"Entity": ent["EntityName"], "Domain": ent["Domain"], "Meaning": ent["Description"], "Node type": "Table/entity"})
    raw = catalog["Relationships"]
    edges = pd.DataFrame({
        "Source entity": raw["SourceEntityID"].map(id_to_name),
        "Source field": raw["Predicate"],
        "Target entity": raw["TargetEntityID"].map(id_to_name),
        "Cardinality": raw["Cardinality"],
        "Relationship meaning": raw["Description"],
        "Status": "Modeled",
    })
    f = catalog["Fields"]
    columns = pd.DataFrame({
        "Table": f["EntityID"].map(id_to_name),
        "Column": f["FieldName"],
        "Suggested SQL type": f["DataType"],
        "Key": f["KeyType"],
        "Picklist": f["PicklistDomain"].ne("").map({True: "Yes", False: "No"}),
        "Picklist domain": f["PicklistDomain"],
        "Business definition": f["BusinessDefinition"],
    })
    return nodes, edges, columns
