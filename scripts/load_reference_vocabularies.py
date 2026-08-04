"""Load version-controlled ECI vocabularies into MariaDB.

Usage:
  pip install pymysql pyyaml
  python scripts/load_reference_vocabularies.py

Required environment variables: MARIADB_HOST, MARIADB_DATABASE,
MARIADB_USER, and MARIADB_PASSWORD. MARIADB_PORT defaults to 3306.
"""

from __future__ import annotations

import os
from pathlib import Path

import pymysql
import yaml

ROOT = Path(__file__).resolve().parents[1]
VOCAB_DIR = ROOT / "knowledge" / "vocabularies"
FILES = {
    "theme": "themes.yaml",
    "capability": "capabilities.yaml",
    "community": "communities.yaml",
    "source_type": "source_types.yaml",
}


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    connection = pymysql.connect(
        host=os.getenv("MARIADB_HOST", "127.0.0.1"),
        port=int(os.getenv("MARIADB_PORT", "3306")),
        user=required("MARIADB_USER"),
        password=required("MARIADB_PASSWORD"),
        database=required("MARIADB_DATABASE"),
        charset="utf8mb4",
        autocommit=False,
    )
    loaded = 0
    try:
        with connection.cursor() as cursor:
            for vocabulary_type, filename in FILES.items():
                document = yaml.safe_load((VOCAB_DIR / filename).read_text(encoding="utf-8"))
                version = str(document.get("version", 1))
                for sort_order, item in enumerate(document.get("items", []), start=1):
                    cursor.execute(
                        """
                        INSERT INTO reference_vocabularies (
                            vocabulary_type, item_code, item_name, description,
                            active, sort_order, vocabulary_version
                        ) VALUES (%s, %s, %s, %s, TRUE, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            item_name = VALUES(item_name),
                            description = VALUES(description),
                            active = TRUE,
                            sort_order = VALUES(sort_order),
                            vocabulary_version = VALUES(vocabulary_version)
                        """,
                        (
                            vocabulary_type,
                            item["code"],
                            item["name"],
                            item.get("description"),
                            sort_order,
                            version,
                        ),
                    )
                    loaded += 1
        connection.commit()
        print(f"Loaded {loaded} reference vocabulary items.")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
