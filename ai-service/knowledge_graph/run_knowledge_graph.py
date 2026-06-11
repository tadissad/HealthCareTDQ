from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
SERVICE_ROOT = CURRENT_DIR.parent
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from knowledge_graph.query_neo4j import main as query_main
from knowledge_graph.seed_neo4j import seed_graph


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the knowledge graph pipeline")
    parser.add_argument("--data", default=str(SERVICE_ROOT / "data_user500.csv"), help="Input CSV dataset")
    parser.add_argument("--output", default=str(SERVICE_ROOT / "knowledge_graph_output"), help="Output folder")
    parser.add_argument("--uri", default=None, help="Neo4j bolt URI")
    parser.add_argument("--user", default=None, help="Neo4j username")
    parser.add_argument("--password", default=None, help="Neo4j password")
    parser.add_argument(
        "--kb-payload",
        default=str(SERVICE_ROOT / "kb" / "neo4j_seed_payload.json"),
        help="Path to unified KB Neo4j payload",
    )
    args, unknown = parser.parse_known_args()

    print("[1/2] Seeding Neo4j graph...")
    stats = seed_graph(
        csv_path=args.data,
        uri=args.uri or None,
        user=args.user or None,
        password=args.password or None,
        kb_payload_path=args.kb_payload,
        clear_existing=True,
    )
    print(f"Seeded {stats.users} users, {stats.products} products, {stats.action_events} events")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    seed_summary = {
        "dataset": args.data,
        "neo4j_uri": args.uri,
        "users": stats.users,
        "products": stats.products,
        "categories": stats.categories,
        "action_events": stats.action_events,
        "sessions": stats.sessions,
        "purchase_events": stats.purchase_events,
        "review_events": stats.review_events,
    }
    (output_dir / "seed_summary.json").write_text(json.dumps(seed_summary, indent=2), encoding="utf-8")

    print("[2/2] Running queries and exporting report...")
    import sys

    sys.argv = [
        "query_neo4j.py",
        "--output",
        args.output,
    ] + unknown
    query_main()

    print("Knowledge graph pipeline completed successfully.")
    print(f"Artifacts saved in: {Path(args.output)}")


if __name__ == "__main__":
    main()
