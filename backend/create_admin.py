
import getpass

from sqlalchemy import select

from backend.auth_service import hash_password
from backend.database import SessionLocal
from backend.models import Administrator


def main():
    print("\n=== MachineDoctor Administrator Setup ===")

    username = input(
        "Administrator username: "
    ).strip()

    if not username or len(username) > 100:
        raise ValueError(
            "Username must contain 1 to 100 characters."
        )

    password = getpass.getpass(
        "Administrator password: "
    )

    confirmation = getpass.getpass(
        "Confirm password: "
    )

    if password != confirmation:
        raise ValueError(
            "Passwords do not match."
        )

    if len(password) < 12:
        raise ValueError(
            "Administrator password must contain at least 12 characters."
        )

    with SessionLocal() as db:
        existing = db.scalar(
            select(Administrator).where(
                Administrator.username == username
            )
        )

        if existing is not None:
            raise ValueError(
                "Administrator username already exists."
            )

        # Bootstrap only the first administrator.
        # This is not a general-purpose account creation API.
        if db.scalar(select(Administrator.id).limit(1)) is not None:
            raise ValueError(
                "An administrator already exists. "
                "Additional accounts require an authorized workflow."
            )

        administrator = Administrator(
            username=username,
            password_hash=hash_password(password),
            is_active=True,
        )

        db.add(administrator)
        db.commit()

        print("\nAdministrator created successfully.")
        print("Username:", username)
        print("Administrator ID:", administrator.id)


if __name__ == "__main__":
    main()
