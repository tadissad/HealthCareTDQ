from __future__ import annotations

import argparse
import csv
import importlib
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

CURRENT_DIR = Path(__file__).resolve().parent
SERVICE_ROOT = CURRENT_DIR.parent


DEFAULT_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
DEFAULT_USER = os.getenv("NEO4J_USER", "neo4j")
DEFAULT_PASSWORD = os.getenv("NEO4J_PASSWORD", "health123")


@dataclass(frozen=True)
class GraphStats:
    users: int
    products: int
    categories: int
    action_events: int
    sessions: int
    purchase_events: int
    review_events: int


def _require_pandas():
    try:
        return importlib.import_module("pandas")
    except ImportError as exc:  # pragma: no cover
        raise ImportError("pandas is required. Install it with: pip install pandas") from exc


def _read_dataset(csv_path: str):
    pd = _require_pandas()

    df = pd.read_csv(csv_path)
    required_columns = {
        "user_id",
        "product_id",
        "action",
        "timestamp",
        "category",
        "price",
        "rating",
        "session_duration",
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing columns: {sorted(missing)}")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["user_id", "timestamp", "product_id"]).reset_index(drop=True)
    return df


def _prepare_rows(df) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict], List[Dict]]:
    users = (
        df[["user_id"]]
        .drop_duplicates()
        .assign(name=lambda frame: frame["user_id"], user_id=lambda frame: frame["user_id"].astype(str))
        .to_dict("records")
    )

    products = (
        df[["product_id", "category", "price"]]
        .drop_duplicates()
        .rename(columns={"category": "category_code"})
        .to_dict("records")
    )

    categories = (
        df[["category"]]
        .drop_duplicates()
        .assign(
            name=lambda frame: frame["category"].str.replace("_", " ").str.title(),
            code=lambda frame: frame["category"],
            description=lambda frame: frame["category"].map(lambda value: f"Category {value} from synthetic assignment dataset"),
        )
        .to_dict("records")
    )

    events = []
    for index, row in df.iterrows():
        rating_value = row["rating"]
        if rating_value != rating_value:
            rating_value = None
        events.append(
            {
                "event_id": f"EV{index + 1:06d}",
                "user_id": row["user_id"],
                "product_id": row["product_id"],
                "action": row["action"],
                "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "price": int(row["price"]),
                "rating": None if rating_value is None else int(rating_value),
                "session_duration": int(row["session_duration"]),
                "category": row["category"],
            }
        )

    sessions = []
    session_groups = df.groupby("user_id")
    for user_id, group in session_groups:
        ordered = group.sort_values("timestamp")
        current_session = []
        session_index = 1
        for _, row in ordered.iterrows():
            current_session.append(row)
            if len(current_session) >= 5:
                start_time = current_session[0]["timestamp"]
                end_time = current_session[-1]["timestamp"]
                sessions.append(
                    {
                        "session_id": f"{user_id}_S{session_index:03d}",
                        "user_id": user_id,
                        "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "event_count": len(current_session),
                        "duration_total": int(sum(int(item["session_duration"]) for item in current_session)),
                    }
                )
                session_index += 1
                current_session = []

        if current_session:
            start_time = current_session[0]["timestamp"]
            end_time = current_session[-1]["timestamp"]
            sessions.append(
                {
                    "session_id": f"{user_id}_S{session_index:03d}",
                    "user_id": user_id,
                    "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "event_count": len(current_session),
                    "duration_total": int(sum(int(item["session_duration"]) for item in current_session)),
                }
            )

    purchases = df[df["action"] == "purchase"][ ["user_id", "product_id", "timestamp", "price"] ].copy()
    reviews = df[df["action"] == "review"][ ["user_id", "product_id", "timestamp", "rating"] ].copy()
    purchases["timestamp"] = purchases["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    reviews["timestamp"] = reviews["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return users, products, categories, events, sessions, purchases.to_dict("records"), reviews.to_dict("records")


def _require_graph_database():
    try:
        neo4j_module = importlib.import_module("neo4j")
        return neo4j_module.GraphDatabase
    except ImportError as exc:  # pragma: no cover
        raise ImportError("neo4j is required. Install it with: pip install neo4j") from exc


def _load_medical_payload(payload_path: str | None) -> Dict[str, Any]:
    if not payload_path:
        return {}

    payload_file = Path(payload_path)
    if not payload_file.exists():
        return {}

    try:
        return json.loads(payload_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _seed_medical_payload(session, payload: Dict[str, Any]) -> None:
    if not payload:
        return

    session.run("CREATE CONSTRAINT symptom_name IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE")
    session.run("CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE")

    for category in payload.get("categories", []):
        session.run(
            """
            MERGE (c:Category {code: $code})
            SET c.name = $name,
                c.source = 'unified_kb'
            """,
            code=category.get("code"),
            name=category.get("name"),
        )

    for product in payload.get("products", []):
        session.run(
            """
            MERGE (p:Product {name: $name})
            SET p.category_codes = $category_codes,
                p.semantic = true,
                p.source = 'unified_kb'
            """,
            name=product.get("name"),
            category_codes=product.get("category_codes", []),
        )

    for symptom in payload.get("symptoms", []):
        session.run(
            """
            MERGE (s:Symptom {name: $name})
            SET s.aliases = $aliases,
                s.source = 'unified_kb'
            """,
            name=symptom.get("name"),
            aliases=symptom.get("aliases", []),
        )

    for disease in payload.get("diseases", []):
        session.run(
            """
            MERGE (d:Disease {name: $name})
            SET d.icd_code = $icd_code,
                d.severity = $severity,
                d.description = $description,
                d.source = 'unified_kb'
            """,
            name=disease.get("name"),
            icd_code=disease.get("icd_code"),
            severity=disease.get("severity"),
            description=disease.get("description"),
        )

    relations = payload.get("relations", {})
    for edge in relations.get("symptom_indicates", []):
        session.run(
            """
            MATCH (s:Symptom {name: $symptom})
            MATCH (d:Disease {name: $disease})
            MERGE (s)-[r:INDICATES]->(d)
            SET r.source = $source
            """,
            symptom=edge.get("symptom"),
            disease=edge.get("disease"),
            source=edge.get("source", "unified_kb"),
        )

    for edge in relations.get("disease_treated_by", []):
        session.run(
            """
            MATCH (d:Disease {name: $disease})
            MATCH (p:Product {name: $product})
            MERGE (d)-[r:TREATED_BY]->(p)
            SET r.priority = $priority,
                r.source = $source
            """,
            disease=edge.get("disease"),
            product=edge.get("product"),
            priority=edge.get("priority", 2),
            source=edge.get("source", "unified_kb"),
        )

    for edge in relations.get("product_belongs_to", []):
        session.run(
            """
            MATCH (p:Product {name: $product})
            MATCH (c:Category {code: $category})
            MERGE (p)-[r:BELONGS_TO]->(c)
            SET r.source = $source
            """,
            product=edge.get("product"),
            category=edge.get("category"),
            source=edge.get("source", "unified_kb"),
        )


def seed_graph(
    csv_path: str,
    uri: str = DEFAULT_URI,
    user: str = DEFAULT_USER,
    password: str = DEFAULT_PASSWORD,
    kb_payload_path: str | None = None,
    clear_existing: bool = True,
) -> GraphStats:
    GraphDatabase = _require_graph_database()
    uri = uri or DEFAULT_URI
    user = user or DEFAULT_USER
    password = password or DEFAULT_PASSWORD

    df = _read_dataset(csv_path)
    users, products, categories, events, sessions, purchases, reviews = _prepare_rows(df)

    driver = GraphDatabase.driver(uri, auth=(user, password))
    driver.verify_connectivity()

    with driver.session() as session:
        if clear_existing:
            session.run("MATCH (n) DETACH DELETE n")

        session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
        session.run("CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE")
        session.run("CREATE CONSTRAINT category_code IF NOT EXISTS FOR (c:Category) REQUIRE c.code IS UNIQUE")
        session.run("CREATE CONSTRAINT session_id IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE")
        session.run("CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:ActionEvent) REQUIRE e.id IS UNIQUE")

        for record in categories:
            session.run(
                """
                MERGE (c:Category {code: $code})
                SET c.name = $name,
                    c.description = $description,
                    c.source = 'ai_service'
                """,
                **record,
            )

        for record in products:
            session.run(
                """
                MERGE (p:Product {id: $product_id})
                SET p.name = $product_id,
                    p.category_code = $category_code,
                    p.price = $price,
                    p.source = 'data_user500_tuned'
                WITH p
                MATCH (c:Category {code: $category_code})
                MERGE (p)-[:BELONGS_TO]->(c)
                """,
                **record,
            )

        for record in users:
            session.run(
                """
                MERGE (u:User {id: $user_id})
                SET u.name = $name,
                    u.source = 'data_user500_tuned'
                """,
                **record,
            )

        for record in sessions:
            session.run(
                """
                MERGE (s:Session {id: $session_id})
                SET s.start_time = datetime(replace($start_time, ' ', 'T')),
                    s.end_time = datetime(replace($end_time, ' ', 'T')),
                    s.event_count = $event_count,
                    s.duration_total = $duration_total,
                    s.source = 'ai_service'
                WITH s
                MATCH (u:User {id: $user_id})
                MERGE (u)-[:HAS_SESSION]->(s)
                """,
                **record,
            )

        for record in events:
            session.run(
                """
                MERGE (e:ActionEvent {id: $event_id})
                SET e.action = $action,
                    e.timestamp = datetime(replace($timestamp, ' ', 'T')),
                    e.price = $price,
                    e.rating = $rating,
                    e.session_duration = $session_duration,
                    e.source = 'data_user500_tuned'
                WITH e
                MATCH (u:User {id: $user_id})
                MATCH (p:Product {id: $product_id})
                MATCH (c:Category {code: $category})
                MERGE (u)-[:PERFORMED {timestamp: datetime(replace($timestamp, ' ', 'T')), action: $action}]->(e)
                MERGE (e)-[:ON_PRODUCT]->(p)
                MERGE (e)-[:IN_CATEGORY]->(c)
                """,
                **record,
            )

        for record in purchases:
            session.run(
                """
                MATCH (u:User {id: $user_id})
                MATCH (p:Product {id: $product_id})
                MERGE (u)-[:PURCHASED {timestamp: datetime(replace($timestamp, ' ', 'T')), price: $price}]->(p)
                """,
                **record,
            )

        for record in reviews:
            session.run(
                """
                MATCH (u:User {id: $user_id})
                MATCH (p:Product {id: $product_id})
                MERGE (u)-[:REVIEWED {timestamp: datetime(replace($timestamp, ' ', 'T')), rating: $rating}]->(p)
                """,
                **record,
            )

        session.run(
            """
            MATCH (p1:Product)<-[:ON_PRODUCT]-(e1:ActionEvent {action: 'purchase'})<-[:PERFORMED]-(u:User)-[:PERFORMED]->(e2:ActionEvent {action: 'purchase'})-[:ON_PRODUCT]->(p2:Product)
            WHERE p1.id <> p2.id
            MERGE (p1)-[r:CO_PURCHASED_WITH]->(p2)
            ON CREATE SET r.weight = 1
            ON MATCH SET r.weight = r.weight + 1
            """
        )

        medical_payload = _load_medical_payload(kb_payload_path)
        _seed_medical_payload(session, medical_payload)

    with driver.session() as session:
        users_count = session.run("MATCH (u:User) RETURN count(u) AS cnt").single()["cnt"]
        products_count = session.run("MATCH (p:Product) RETURN count(p) AS cnt").single()["cnt"]
        categories_count = session.run("MATCH (c:Category) RETURN count(c) AS cnt").single()["cnt"]
        events_count = session.run("MATCH (e:ActionEvent) RETURN count(e) AS cnt").single()["cnt"]
        sessions_count = session.run("MATCH (s:Session) RETURN count(s) AS cnt").single()["cnt"]
        purchase_events = session.run("MATCH ()-[r:PURCHASED]->() RETURN count(r) AS cnt").single()["cnt"]
        review_events = session.run("MATCH ()-[r:REVIEWED]->() RETURN count(r) AS cnt").single()["cnt"]

    driver.close()
    return GraphStats(
        users=users_count,
        products=products_count,
        categories=categories_count,
        action_events=events_count,
        sessions=sessions_count,
        purchase_events=purchase_events,
        review_events=review_events,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Neo4j knowledge graph")
    parser.add_argument("--data", default=str(SERVICE_ROOT / "data_user500.csv"), help="Input CSV dataset")
    parser.add_argument("--uri", default=DEFAULT_URI, help="Neo4j bolt URI")
    parser.add_argument("--user", default=DEFAULT_USER, help="Neo4j username")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Neo4j password")
    parser.add_argument(
        "--kb-payload",
        default=str(SERVICE_ROOT / "kb" / "neo4j_seed_payload.json"),
        help="Path to unified KB neo4j payload",
    )
    parser.add_argument("--no-clear", action="store_true", help="Do not delete existing graph data")
    parser.add_argument("--output", default=str(SERVICE_ROOT / "knowledge_graph_output"), help="Output folder for seed summary")
    args = parser.parse_args()

    stats = seed_graph(
        csv_path=args.data,
        uri=args.uri,
        user=args.user,
        password=args.password,
        kb_payload_path=args.kb_payload,
        clear_existing=not args.no_clear,
    )

    print("Knowledge graph seeding complete")
    print(f"Users: {stats.users}")
    print(f"Products: {stats.products}")
    print(f"Categories: {stats.categories}")
    print(f"Action events: {stats.action_events}")
    print(f"Sessions: {stats.sessions}")
    print(f"Purchase edges: {stats.purchase_events}")
    print(f"Review edges: {stats.review_events}")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
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
    (output_dir / "seed_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Seed summary saved to: {output_dir / 'seed_summary.json'}")


if __name__ == "__main__":
    main()
