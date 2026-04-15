"""Seed 100 mock users into the database and export credentials to CSV."""

import csv
import os
import random
import sys

# Resolve backend imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import app.db.base  # noqa: F401 — register all models before any query
from app.crud.user import create_user, get_user_by_email, get_user_by_username
from app.db.session import SessionLocal
from app.schemas.user import RegisterRequest

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen", "Charles",
    "Lisa", "Daniel", "Nancy", "Matthew", "Betty", "Anthony", "Margaret",
    "Mark", "Sandra", "Donald", "Ashley", "Steven", "Emily", "Paul", "Donna",
    "Andrew", "Michelle", "Joshua", "Carol", "Kenneth", "Amanda", "Kevin",
    "Dorothy", "Brian", "Melissa", "George", "Deborah", "Timothy", "Stephanie",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts",
]

OUTPUT_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(OUTPUT_DIR, "users.csv")
TOTAL_USERS = 100


def generate_users():
    """Generate a list of user dicts with unique email/username."""
    used_usernames: set[str] = set()
    users = []

    for i in range(1, TOTAL_USERS + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        fullname = f"{first} {last}"

        base_username = f"{first.lower()}.{last.lower()}"
        username = base_username
        counter = 1
        while username in used_usernames:
            username = f"{base_username}{counter}"
            counter += 1
        used_usernames.add(username)

        email = f"{username}@mockmail.com"
        password = f"User{i:03d}!pass"
        avatar = f"https://i.pravatar.cc/150?u={email}"

        users.append({
            "email": email,
            "username": username,
            "password": password,
            "fullname": fullname,
            "avatar": avatar,
        })

    return users


def main():
    users = generate_users()
    db = SessionLocal()
    created = 0
    skipped = 0

    try:
        for u in users:
            if get_user_by_email(db, u["email"]):
                print(f"  SKIP (email exists): {u['email']}")
                skipped += 1
                continue
            if get_user_by_username(db, u["username"]):
                print(f"  SKIP (username exists): {u['username']}")
                skipped += 1
                continue

            create_user(db, RegisterRequest(
                email=u["email"],
                username=u["username"],
                password=u["password"],
                fullname=u["fullname"],
                avatar=u["avatar"],
            ))
            created += 1
            if created % 10 == 0:
                print(f"  Created {created} users...")
    finally:
        db.close()

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "username", "password", "fullname"])
        writer.writeheader()
        for u in users:
            writer.writerow({
                "email": u["email"],
                "username": u["username"],
                "password": u["password"],
                "fullname": u["fullname"],
            })

    print(f"\nDone! Created: {created}, Skipped: {skipped}")
    print(f"Credentials saved to: {CSV_PATH}")


if __name__ == "__main__":
    main()
