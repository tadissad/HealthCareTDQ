from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import pandas as pd

try:
    from domain.category import CATEGORIES
except ImportError:  # pragma: no cover - fallback when running inside folder
    from category import CATEGORIES

ACTIONS: List[str] = [
    "view",
    "click",
    "add_to_cart",
    "purchase",
    "wishlist",
    "review",
    "share",
    "compare",
]

ACTION_TRANSITION_WEIGHTS: Dict[str, Dict[str, float]] = {
    "view": {
        "click": 0.45,
        "compare": 0.15,
        "wishlist": 0.10,
        "add_to_cart": 0.15,
        "share": 0.10,
        "view": 0.05,
    },
    "click": {
        "add_to_cart": 0.35,
        "view": 0.20,
        "compare": 0.15,
        "wishlist": 0.10,
        "share": 0.10,
        "click": 0.10,
    },
    "add_to_cart": {
        "purchase": 0.35,
        "view": 0.15,
        "wishlist": 0.15,
        "compare": 0.10,
        "share": 0.10,
        "add_to_cart": 0.15,
    },
    "purchase": {
        "review": 0.40,
        "view": 0.25,
        "share": 0.15,
        "wishlist": 0.10,
        "purchase": 0.10,
    },
    "wishlist": {
        "view": 0.30,
        "click": 0.20,
        "add_to_cart": 0.20,
        "share": 0.15,
        "compare": 0.15,
    },
    "review": {
        "view": 0.35,
        "share": 0.25,
        "compare": 0.10,
        "wishlist": 0.10,
        "click": 0.20,
    },
    "share": {
        "view": 0.35,
        "click": 0.20,
        "wishlist": 0.20,
        "compare": 0.15,
        "add_to_cart": 0.10,
    },
    "compare": {
        "click": 0.35,
        "add_to_cart": 0.20,
        "view": 0.25,
        "wishlist": 0.10,
        "share": 0.10,
    },
}

PERSONA_TYPES: Sequence[str] = ("buyer", "researcher", "social", "balanced")

PERSONA_CATEGORY_WEIGHTS: Dict[str, Dict[str, float]] = {
    "buyer": {
        "ulcer_hp_support": 1.6,
        "reflux_heartburn": 1.5,
        "consultation_package": 1.2,
        "elderly_weak_digestion": 1.4,
    },
    "researcher": {
        "test_kit_home": 1.8,
        "equipment_device": 1.4,
        "probiotic_digestion": 1.3,
        "vitamin_mineral": 1.2,
    },
    "social": {
        "herbal_extract": 1.5,
        "stomach_nutrition": 1.4,
        "probiotic_digestion": 1.4,
        "vitamin_mineral": 1.2,
    },
    "balanced": {},
}

PERSONA_ACTION_BOOST: Dict[str, Dict[str, float]] = {
    "buyer": {"add_to_cart": 1.45, "purchase": 1.9, "review": 1.8},
    "researcher": {"compare": 1.8, "wishlist": 1.35, "purchase": 0.8},
    "social": {"share": 1.8, "wishlist": 1.5, "review": 1.35},
    "balanced": {},
}


@dataclass(frozen=True)
class ProductInfo:
    product_id: str
    category: str
    price: int


@dataclass(frozen=True)
class UserProfile:
    user_id: str
    persona: str


def _weighted_choice(weights: Dict[str, float], rng: random.Random) -> str:
    actions = list(weights.keys())
    probs = list(weights.values())
    return rng.choices(actions, weights=probs, k=1)[0]


def _generate_product_catalog(rng: random.Random, total_products: int = 100) -> Dict[str, ProductInfo]:
    catalog: Dict[str, ProductInfo] = {}
    for idx in range(1, total_products + 1):
        product_id = f"P{idx:03d}"
        category = CATEGORIES[(idx - 1) % len(CATEGORIES)]

        base_price = rng.randint(20_000, 500_000)
        if category in {"consultation_package", "equipment_device"}:
            base_price = min(500_000, max(80_000, base_price + 50_000))

        catalog[product_id] = ProductInfo(
            product_id=product_id,
            category=category,
            price=base_price,
        )
    return catalog


def _index_catalog_by_category(catalog: Dict[str, ProductInfo]) -> Dict[str, List[str]]:
    by_category: Dict[str, List[str]] = {category: [] for category in CATEGORIES}
    for pid, info in catalog.items():
        by_category[info.category].append(pid)
    return by_category


def _choose_persona(rng: random.Random) -> str:
    return rng.choices(PERSONA_TYPES, weights=[0.35, 0.25, 0.20, 0.20], k=1)[0]


def _choose_category_for_user(profile: UserProfile, rng: random.Random) -> str:
    base = {category: 1.0 for category in CATEGORIES}
    boosts = PERSONA_CATEGORY_WEIGHTS.get(profile.persona, {})
    for category, factor in boosts.items():
        base[category] *= factor
    return rng.choices(list(base.keys()), weights=list(base.values()), k=1)[0]


def _get_action_transition(prev_action: str, profile: UserProfile, rng: random.Random) -> str:
    weights = dict(ACTION_TRANSITION_WEIGHTS[prev_action])
    boost = PERSONA_ACTION_BOOST.get(profile.persona, {})
    for action, factor in boost.items():
        if action in weights:
            weights[action] *= factor
    return _weighted_choice(weights, rng)


def generate_data_user500(seed: int = 20260420, users: int = 500) -> pd.DataFrame:
    """Generate user behavior data for 500 users and 8 actions."""
    rng = random.Random(seed)

    product_catalog = _generate_product_catalog(rng)
    products_by_category = _index_catalog_by_category(product_catalog)

    start_time = datetime(2026, 1, 1, 8, 0, 0)
    end_time = datetime(2026, 4, 20, 23, 0, 0)
    max_offset_seconds = int((end_time - start_time).total_seconds())

    records: List[Dict[str, Optional[object]]] = []

    for user_index in range(1, users + 1):
        profile = UserProfile(user_id=f"U{user_index:03d}", persona=_choose_persona(rng))

        first_offset = rng.randint(0, max_offset_seconds - 86_400)
        current_time = start_time + timedelta(seconds=first_offset)
        prev_action = rng.choice(["view", "click", "wishlist", "compare"])

        sessions = rng.randint(3, 5)
        for _ in range(sessions):
            session_len = rng.randint(6, 9)
            session_category = _choose_category_for_user(profile, rng)
            session_products = products_by_category.get(session_category) or [next(iter(product_catalog.keys()))]
            active_product = rng.choice(session_products)
            has_cart = False
            has_purchase = False

            for step in range(session_len):
                if step == 0:
                    action = "view"
                else:
                    # Keep a realistic checkout funnel for better sequence signal.
                    remaining = session_len - step
                    if prev_action == "add_to_cart" and not has_purchase and rng.random() < 0.7:
                        action = "purchase"
                    elif prev_action == "purchase" and rng.random() < 0.65:
                        action = "review"
                    elif remaining <= 2 and not has_cart and rng.random() < 0.6:
                        action = "add_to_cart"
                    elif remaining <= 1 and has_cart and not has_purchase and rng.random() < 0.65:
                        action = "purchase"
                    else:
                        action = _get_action_transition(prev_action, profile, rng)

                # Keep product continuity in a session, occasionally branch out.
                if rng.random() < 0.72:
                    product_id = active_product
                else:
                    product_id = rng.choice(session_products)
                    active_product = product_id

                # For compare/view flow, user may jump within same category.
                if action in {"compare", "view"} and rng.random() < 0.25:
                    product_id = rng.choice(session_products)
                    active_product = product_id

                # For purchase/review, reinforce single-item funnel behavior.
                if action in {"purchase", "review"}:
                    product_id = active_product

                if action == "add_to_cart":
                    has_cart = True
                if action == "purchase":
                    has_purchase = True

                product = product_catalog[product_id]

                price_variation = rng.uniform(0.9, 1.1)
                price = int(max(20_000, min(500_000, product.price * price_variation)))
                session_duration = rng.randint(30, 1_500)

                rating: Optional[int] = None
                if action == "review":
                    rating = rng.randint(3, 5)
                elif action == "purchase" and rng.random() < 0.35:
                    rating = rng.randint(3, 5)

                records.append(
                    {
                        "user_id": profile.user_id,
                        "product_id": product_id,
                        "action": action,
                        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "category": product.category,
                        "price": price,
                        "rating": rating,
                        "session_duration": session_duration,
                    }
                )

                prev_action = action
                current_time += timedelta(minutes=rng.randint(5, 90))
                if current_time > end_time:
                    current_time = end_time - timedelta(minutes=rng.randint(1, 30))

            # Gap between sessions.
            current_time += timedelta(hours=rng.randint(4, 72))
            prev_action = rng.choice(["view", "click", "wishlist", "compare"])

    df = pd.DataFrame(records)
    df = df.sort_values(by=["timestamp", "user_id", "product_id"]).reset_index(drop=True)
    return df


def validate_dataset(df: pd.DataFrame) -> None:
    expected_columns = [
        "user_id",
        "product_id",
        "action",
        "timestamp",
        "category",
        "price",
        "rating",
        "session_duration",
    ]

    if list(df.columns) != expected_columns:
        raise ValueError(f"Columns mismatch. Expected: {expected_columns}, got: {list(df.columns)}")

    unique_users = df["user_id"].nunique()
    if unique_users != 500:
        raise ValueError(f"Expected 500 unique users, got {unique_users}")

    if not set(df["action"].unique()).issubset(set(ACTIONS)):
        raise ValueError("Found unknown actions in dataset")

    if not set(df["category"].unique()).issubset(set(CATEGORIES)):
        raise ValueError("Found unknown categories in dataset")

    if len(df) < 4_000:
        raise ValueError(f"Too few rows generated ({len(df)}). Expected around 5000+")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate data_user500.csv for AI assignment")
    parser.add_argument("--output", default="data_user500.csv", help="Output CSV path")
    parser.add_argument("--seed", type=int, default=20260420, help="Random seed")
    args = parser.parse_args()

    df = generate_data_user500(seed=args.seed)
    validate_dataset(df)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Generated file: {output_path}")
    print(f"Rows: {len(df)}")
    print(f"Unique users: {df['user_id'].nunique()}")
    print("\nFirst 20 rows:")
    print(df.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
