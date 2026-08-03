import os
from typing import Any

import requests


API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "http://localhost:8000",
)


def get(
    path: str,
    params: dict[str, Any] | None = None,
) -> Any:
    response = requests.get(
        f"{API_BASE_URL}{path}",
        params=params,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def patch(
    path: str,
    payload: dict[str, Any],
) -> Any:
    response = requests.patch(
        f"{API_BASE_URL}{path}",
        json=payload,
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def post(
    path: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    response = requests.post(
        f"{API_BASE_URL}{path}",
        json=payload or {},
        timeout=30,
    )

    response.raise_for_status()
    return response.json()
