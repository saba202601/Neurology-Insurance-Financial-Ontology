"""Build a small interoperable RDF/OWL representation of the CDM schema."""
from __future__ import annotations

import re

import networkx as nx
import pandas as pd
from rdflib import Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef, XSD

FIN = Namespace("https://neurologyinsurance.example/ontology/finance#")


def uri_part(value: object) -> str:
    """Conservative URI local names for identifiers in the catalog."""
    return re.sub(r"[^A-Za-z0-9_]", "_", str(value))


def resolve_neighborhood(graph: nx.Graph, focus: str, hops: int) -> set[str]:
    if focus not in graph:
        return set()
    lengths = nx.single_source_shortest_path_length(graph, focus, cutoff=hops)
    return set(lengths)


def build_turtle(nodes: pd.DataFrame, columns: pd.DataFrame, edges: pd.DataFrame) -> str:
    graph = Graph()
    graph.bind("fin", FIN)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    graph.add((URIRef(str(FIN).rstrip("#")), RDF.type, OWL.Ontology))
    present = set(nodes["Entity"].astype(str))
    for row in nodes.itertuples(index=False):
        entity, domain, meaning = str(row[0]), str(row[1]), str(row[2])
        node = FIN[uri_part(entity)]
        graph.add((node, RDF.type, OWL.Class))
        graph.add((node, RDFS.label, Literal(entity)))
        graph.add((node, RDFS.comment, Literal(meaning)))
        graph.add((node, FIN.businessDomain, Literal(domain)))
    for row in columns.itertuples(index=False):
        table, name = str(row[0]), str(row[1])
        if table not in present:
            continue
        prop = FIN[uri_part(f"{table}_{name}")]
        graph.add((prop, RDF.type, OWL.DatatypeProperty))
        graph.add((prop, RDFS.domain, FIN[uri_part(table)]))
        graph.add((prop, RDFS.label, Literal(name)))
        graph.add((prop, RDFS.comment, Literal(str(row[6]))))
        dtype = str(row[2]).upper()
        if dtype.startswith("DECIMAL"):
            graph.add((prop, RDFS.range, XSD.decimal))
        elif dtype == "INTEGER":
            graph.add((prop, RDFS.range, XSD.integer))
        elif dtype == "BOOLEAN":
            graph.add((prop, RDFS.range, XSD.boolean))
        elif dtype == "DATETIME":
            graph.add((prop, RDFS.range, XSD.dateTime))
        else:
            graph.add((prop, RDFS.range, XSD.string))
    for row in edges.itertuples(index=False):
        source, field, target, cardinality, desc = map(str, row[:5])
        if source not in present or target not in present:
            continue  # external concepts are cataloged, but not falsely declared as local classes
        prop = FIN[uri_part(f"rel_{source}_{field}_{target}")]
        graph.add((prop, RDF.type, OWL.ObjectProperty))
        graph.add((prop, RDFS.domain, FIN[uri_part(source)]))
        graph.add((prop, RDFS.range, FIN[uri_part(target)]))
        graph.add((prop, RDFS.label, Literal(f"{source} {field} {target}")))
        graph.add((prop, RDFS.comment, Literal(desc)))
        graph.add((prop, FIN.cardinalityHint, Literal(cardinality)))
    value = graph.serialize(format="turtle")
    return value.decode("utf-8") if isinstance(value, bytes) else value
