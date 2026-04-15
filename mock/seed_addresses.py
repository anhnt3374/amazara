"""Seed 1–3 mock addresses per user into the database and export to CSV."""

import csv
import os
import random
import sys

# Resolve backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import app.db.base  # noqa: F401 — register all models before any query
from app.crud.address import create_address, get_addresses_by_user
from app.crud.user import get_user_by_email
from app.db.session import SessionLocal
from app.schemas.address import AddressCreate

OUTPUT_DIR = os.path.dirname(__file__)
USERS_CSV = os.path.join(OUTPUT_DIR, "users.csv")
ADDRESSES_CSV = os.path.join(OUTPUT_DIR, "addresses.csv")

STREETS = [
    "Main St", "Oak Ave", "Elm St", "Maple Dr", "Cedar Ln",
    "Pine Rd", "Birch Blvd", "Walnut St", "Willow Way", "Cherry Ct",
    "Park Ave", "Lake Dr", "River Rd", "Hill St", "Sunset Blvd",
    "Broadway", "Spring St", "Forest Ave", "Garden Ln", "Valley Rd",
]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "San Antonio", "Dallas", "San Jose", "Austin", "Denver",
    "Seattle", "Boston", "Portland", "Miami", "Atlanta",
]

STATES = [
    "NY", "CA", "IL", "TX", "AZ", "CO", "WA", "MA", "OR", "FL", "GA",
]

LABEL_PREFIXES = ["Home", "Office", "Apartment", "Parents' House"]


def random_phone() -> str:
    """Generate a random US-style phone number."""
    return f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"


def random_place() -> str:
    """Generate a random street address."""
    number = random.randint(1, 9999)
    street = random.choice(STREETS)
    city = random.choice(CITIES)
    state = random.choice(STATES)
    zipcode = random.randint(10000, 99999)
    return f"{number} {street}, {city}, {state} {zipcode}"


def load_user_emails() -> list[str]:
    """Read emails from users.csv."""
    with open(USERS_CSV, newline="") as f:
        reader = csv.DictReader(f)
        return [row["email"] for row in reader]


def main():
    emails = load_user_emails()
    print(f"Loaded {len(emails)} users from {USERS_CSV}")

    db = SessionLocal()
    created = 0
    skipped_users = 0
    all_addresses: list[dict] = []

    try:
        for email in emails:
            user = get_user_by_email(db, email)
            if not user:
                print(f"  SKIP (user not found): {email}")
                skipped_users += 1
                continue

            existing = get_addresses_by_user(db, user.id)
            if existing:
                print(f"  SKIP (already has addresses): {email}")
                skipped_users += 1
                continue

            count = random.randint(1, 3)
            for _ in range(count):
                phone = random_phone()
                place = random_place()
                client_name = user.fullname

                address = create_address(db, user_id=user.id, data=AddressCreate(
                    place=place,
                    phone=phone,
                    client_name=client_name,
                ))
                all_addresses.append({
                    "email": email,
                    "address_id": address.id,
                    "place": address.place,
                    "phone": address.phone,
                    "client_name": address.client_name,
                })
                created += 1

            if created % 50 == 0 and created > 0:
                print(f"  Created {created} addresses...")
    finally:
        db.close()

    with open(ADDRESSES_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "address_id", "place", "phone", "client_name"])
        writer.writeheader()
        for a in all_addresses:
            writer.writerow(a)

    print(f"\nDone! Created: {created}, Skipped users: {skipped_users}")
    print(f"Addresses saved to: {ADDRESSES_CSV}")


if __name__ == "__main__":
    main()
