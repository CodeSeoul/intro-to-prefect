#!/usr/bin/env python3

import httpx
import psycopg2
from prefect import flow, get_run_logger, task


@task
def get_petstore_inventory(
    base_url: str = "petstore.swagger.io",
    path: str = "/v2/store/inventory",
    secure: bool = True,
):
    logger = get_run_logger()

    if path[0] != "/":
        path = f"/{path}"
    if secure:
        url = f"https://{base_url}{path}"
    else:
        url = f"http://{base_url}{path}"

    response = httpx.get(url)
    try:
        response.raise_for_status()
    except Exception as e:
        logger.exception("Getting Pet Store API data failed")
        raise e
    inventory_stats = response.json()
    return inventory_stats


def clean_stats(inventory_stats: dict):
    return {
        "sold": inventory_stats.get("sold", 0) + inventory_stats.get("Sold", 0),
        "pending": inventory_stats.get("pending", 0)
        + inventory_stats.get("Pending", 0),
        "available": inventory_stats.get("available", 0)
        + inventory_stats.get("Available", 0),
        "unavailable": inventory_stats.get("unavailable", 0)
        + inventory_stats.get("Unavailable", 0),
    }


def insert_results(
    inventory_stats: dict,
    db_user,
    db_password,
    db_name,
    db_host,
):
    with psycopg2.connect(
        user=db_user, password=db_password, dbname=db_name, host=db_host
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
insert into inventory_history (
                           fetch_timestamp,
                           sold,
                           pending,
                           available,
                           unavailable
) values (now(), %(sold)s, %(pending)s, %(available)s, %(unavailable)s)
                           """,
                inventory_stats,
            )


@flow
def collect_repo_info(
    base_url: str = "petstore.swagger.io",
    path: str = "/v2/store/inventory",
    secure: bool = True,
    db_user: str = "root",
    db_password: str = "root",
    db_name: str = "petstore",
    db_host: str = "localhost",
):
    inventory_stats = get_petstore_inventory(base_url, path, secure)
    inventory_stats = clean_stats(inventory_stats)
    insert_results(
        inventory_stats,
        db_user,
        db_password,
        db_name,
        db_host,
    )


def main():
    collect_repo_info.serve(name="prefect-docker-guide")


if __name__ == "__main__":
    main()
