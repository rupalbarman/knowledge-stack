import argparse
import asyncio
import os
from uuid import uuid4

import asyncpg
from dotenv import load_dotenv

from argon2 import PasswordHasher

load_dotenv()

_hasher = PasswordHasher()


DB_URL = os.getenv("DATABASE_URL")

def hash_password(password: str) -> str:
    return _hasher.hash(password)

async def create_user(email: str, password: str, project_name: str) -> None:
    global DB_URL
    print(DB_URL)
    print(email, password, project_name)
    conn = await asyncpg.connect(DB_URL)
    try:
        async with conn.transaction():
            user_id = uuid4()
            await conn.execute(
                "INSERT INTO users (id, email, hashed_password) VALUES ($1, $2, $3)",
                user_id,
                email,
                hash_password(password),
            )
            await conn.execute(
                "INSERT INTO projects (id, name, owner_id) VALUES ($1, $2, $3)",
                uuid4(),
                project_name,
                user_id,
            )
        print(f"created user {email} with project '{project_name}'")
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(prog="file-api-cli")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser(
        "create-user", help="provision a user and their project (no sign-up flow)"
    )
    create_parser.add_argument("--email", required=True)
    create_parser.add_argument("--password", required=True)
    create_parser.add_argument("--project-name", required=True)

    args = parser.parse_args()

    if args.command == "create-user":
        asyncio.run(create_user(args.email, args.password, args.project_name))


if __name__ == "__main__":
    main()
