from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, time
from pathlib import Path
from typing import Dict, List

CURRENT_DIR = Path(__file__).resolve().parent
SERVICE_ROOT = CURRENT_DIR.parent

GraphDatabase = None


DEFAULT_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
DEFAULT_USER = os.getenv("NEO4J_USER", "neo4j")
DEFAULT_PASSWORD = os.getenv("NEO4J_PASSWORD", "health123")


def _run_query(driver, title: str, cypher: str, params: Dict | None = None) -> List[Dict]:
    with driver.session() as session:
        result = session.run(cypher, params or {})
        rows = [_make_json_safe(record.data()) for record in result]
    return rows


def _make_json_safe(value):
    if isinstance(value, dict):
        return {key: _make_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_make_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_make_json_safe(item) for item in value]
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if hasattr(value, "iso_format"):
        return value.iso_format()
    return value


def build_queries() -> Dict[str, Dict[str, str]]:
    return {
        "overview": {
            "title": "Graph Overview",
            "cypher": """
            CALL {
                MATCH (u:User)
                RETURN count(u) AS users
            }
            CALL {
                MATCH (p:Product)
                RETURN count(p) AS products
            }
            CALL {
                MATCH (c:Category)
                RETURN count(c) AS categories
            }
            CALL {
                MATCH (e:ActionEvent)
                RETURN count(e) AS events
            }
            RETURN users, products, categories, events
            """,
        },
        "top_categories": {
            "title": "Top Categories by Event Count",
            "cypher": """
            MATCH (c:Category)<-[:IN_CATEGORY]-(e:ActionEvent)
            RETURN c.code AS category, count(e) AS event_count
            ORDER BY event_count DESC
            LIMIT 10
            """,
        },
        "top_products": {
            "title": "Top Products by Purchase Count",
            "cypher": """
            MATCH (p:Product)<-[:ON_PRODUCT]-(e:ActionEvent {action: 'purchase'})
            RETURN p.id AS product_id, p.category_code AS category, count(e) AS purchase_count
            ORDER BY purchase_count DESC, product_id ASC
            LIMIT 10
            """,
        },
        "user_journey": {
            "title": "User Journey Sample",
            "cypher": """
            MATCH (u:User {id: $user_id})-[:PERFORMED]->(e:ActionEvent)-[:ON_PRODUCT]->(p:Product)
            RETURN u.id AS user_id, e.action AS action, e.timestamp AS timestamp, p.id AS product_id, p.category_code AS category
            ORDER BY e.timestamp ASC
            LIMIT 20
            """,
        },
        "co_purchase": {
            "title": "Co-purchase Network",
            "cypher": """
            MATCH (p1:Product)-[r:CO_PURCHASED_WITH]->(p2:Product)
            RETURN p1.id AS source, p2.id AS target, r.weight AS weight
            ORDER BY weight DESC, source ASC
            LIMIT 20
            """,
        },
    }


def export_results(results: Dict[str, List[Dict]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in results.items():
        with (output_dir / f"{name}.json").open("w", encoding="utf-8") as handle:
            json.dump(rows, handle, ensure_ascii=False, indent=2)


def print_markdown_report(results: Dict[str, List[Dict]]) -> str:
    lines = ["# Knowledge Graph Report", ""]
    for name, rows in results.items():
        lines.append(f"## {name}")
        lines.append("")
        if not rows:
            lines.append("No rows returned.")
            lines.append("")
            continue
        headers = list(rows[0].keys())
        lines.append(" | ".join(headers))
        lines.append(" | ".join(["---"] * len(headers)))
        for row in rows[:10]:
            lines.append(" | ".join(str(row.get(header, "")) for header in headers))
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    global GraphDatabase
    if GraphDatabase is None:
        try:
            from neo4j import GraphDatabase as _GraphDatabase
        except ImportError as exc:  # pragma: no cover
            raise ImportError("neo4j is required. Install it with: pip install neo4j") from exc
        GraphDatabase = _GraphDatabase

    parser = argparse.ArgumentParser(description="Run Neo4j queries for the knowledge graph")
    parser.add_argument("--uri", default=DEFAULT_URI, help="Neo4j bolt URI")
    parser.add_argument("--user", default=DEFAULT_USER, help="Neo4j username")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Neo4j password")
    parser.add_argument("--user-id", default="U264", help="User id for journey sample")
    parser.add_argument("--output", default=str(SERVICE_ROOT / "knowledge_graph_output"), help="Output folder")
    args = parser.parse_args()

    driver = GraphDatabase.driver(args.uri, auth=(args.user, args.password))
    driver.verify_connectivity()

    queries = build_queries()
    results: Dict[str, List[Dict]] = {}

    for name, spec in queries.items():
        cypher = spec["cypher"]
        params = {"user_id": args.user_id} if name == "user_journey" else None
        results[name] = _run_query(driver, spec["title"], cypher, params)

    driver.close()

    output_dir = Path(args.output)
    export_results(results, output_dir)
    report_text = print_markdown_report(results)
    (output_dir / "graph_report.md").write_text(report_text, encoding="utf-8")

    compact_summary = {
        "overview": results["overview"],
        "top_categories": results["top_categories"][:5],
        "top_products": results["top_products"][:5],
        "user_journey_rows": len(results["user_journey"]),
        "co_purchase_rows": len(results["co_purchase"]),
    }
    (output_dir / "graph_summary.json").write_text(json.dumps(compact_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(report_text)
    print(f"\nSaved JSON and report files to: {output_dir}")
    print(f"Saved compact summary to: {output_dir / 'graph_summary.json'}")


if __name__ == "__main__":
    main()
