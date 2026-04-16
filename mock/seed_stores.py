"""Seed 20 mock stores into the database and export credentials to CSV."""

import csv
import os
import sys

# Resolve backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import app.db.base  # noqa: F401 — register all models before any query
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.store import Store

OUTPUT_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(OUTPUT_DIR, "stores.csv")

STORES = [
    {
        "name": "TechNova Electronics",
        "description": "Premium consumer electronics and cutting-edge gadgets.",
    },
    {
        "name": "Urban Thread",
        "description": "Streetwear and contemporary fashion for young adults.",
    },
    {
        "name": "GreenLeaf Organics",
        "description": "Certified organic food, snacks, and health supplements.",
    },
    {
        "name": "PetPal Paradise",
        "description": "Everything your furry friends need — food, toys, and accessories.",
    },
    {
        "name": "HomeNest Decor",
        "description": "Stylish furniture and home decoration for modern living.",
    },
    {
        "name": "FitZone Gear",
        "description": "Sports equipment, activewear, and fitness accessories.",
    },
    {
        "name": "BookHaven",
        "description": "Wide selection of books, e-readers, and stationery.",
    },
    {
        "name": "GlowUp Beauty",
        "description": "Skincare, cosmetics, and beauty tools from top brands.",
    },
    {
        "name": "TinyTots Kids",
        "description": "Toys, clothing, and essentials for babies and children.",
    },
    {
        "name": "AutoDrive Parts",
        "description": "Car parts, accessories, and maintenance supplies.",
    },
    {
        "name": "FreshBite Kitchen",
        "description": "Kitchen appliances, cookware, and gourmet ingredients.",
    },
    {
        "name": "Wanderlust Travel",
        "description": "Luggage, travel gear, and outdoor adventure equipment.",
    },
    {
        "name": "PixelCraft Studio",
        "description": "Art supplies, digital drawing tablets, and creative tools.",
    },
    {
        "name": "SoundWave Audio",
        "description": "Headphones, speakers, and professional audio equipment.",
    },
    {
        "name": "GardenGrove",
        "description": "Plants, gardening tools, seeds, and outdoor furniture.",
    },
    {
        "name": "SmartHome Hub",
        "description": "IoT devices, smart lighting, and home automation systems.",
    },
    {
        "name": "VintageVault",
        "description": "Retro clothing, antiques, and collectible items.",
    },
    {
        "name": "EcoWear Fashion",
        "description": "Sustainable and eco-friendly clothing and accessories.",
    },
    {
        "name": "GamersEdge",
        "description": "Video games, consoles, and gaming peripherals.",
    },
    {
        "name": "WellnessFirst",
        "description": "Vitamins, supplements, and wellness products for healthy living.",
    },
]

TOTAL_STORES = len(STORES)


def build_slug(name: str) -> str:
    """Convert store name to a URL-friendly slug."""
    return name.lower().replace(" ", "-").replace("'", "")


def build_store_list() -> list[dict]:
    """Build the full list of store dicts with generated fields."""
    stores = []
    for i, s in enumerate(STORES, start=1):
        slug = build_slug(s["name"])
        stores.append({
            "name": s["name"],
            "slug": slug,
            "email": f"{slug}@mockstore.com",
            "password": f"Store{i:03d}!pass",
            "description": s["description"],
            "avatar_url": f"https://ui-avatars.com/api/?name={slug}&background=random&size=150",
        })
    return stores


def main():
    stores = build_store_list()
    db = SessionLocal()
    created = 0
    skipped = 0

    try:
        for s in stores:
            existing = db.query(Store).filter(Store.email == s["email"]).first()
            if existing:
                print(f"  SKIP (email exists): {s['email']}")
                skipped += 1
                continue

            store = Store(
                name=s["name"],
                slug=s["slug"],
                email=s["email"],
                password_hash=hash_password(s["password"]),
                avatar_url=s["avatar_url"],
                description=s["description"],
            )
            db.add(store)
            db.commit()
            db.refresh(store)
            created += 1
            if created % 5 == 0:
                print(f"  Created {created} stores...")
    finally:
        db.close()

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["name", "slug", "email", "password", "description"],
        )
        writer.writeheader()
        for s in stores:
            writer.writerow({
                "name": s["name"],
                "slug": s["slug"],
                "email": s["email"],
                "password": s["password"],
                "description": s["description"],
            })

    print(f"\nDone! Created: {created}, Skipped: {skipped}")
    print(f"Credentials saved to: {CSV_PATH}")


if __name__ == "__main__":
    main()
