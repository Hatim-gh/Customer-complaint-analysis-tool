import os
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import Column, DateTime, MetaData, Table, Text, create_engine, delete, func, select
from sqlalchemy.engine import Engine


LIVE_DATA_FILE = Path("data/live_complaints.csv")
LIVE_DB_FILE = Path("data/live_complaints.db")
LIVE_DATA_TABLE_NAME = "live_complaints"
LIVE_DATA_COLUMNS = [
    "Complaint",
    "Sentiment",
    "Category",
    "Summary",
    "Reason",
    "RecordedAt",
]


live_metadata = MetaData()
live_complaints_table = Table(
    LIVE_DATA_TABLE_NAME,
    live_metadata,
    Column("Complaint", Text, nullable=False),
    Column("Sentiment", Text, nullable=False),
    Column("Category", Text, nullable=False),
    Column("Summary", Text, nullable=False),
    Column("Reason", Text, nullable=False),
    Column("RecordedAt", DateTime, nullable=False),
)


def _default_sqlite_url() -> str:
    LIVE_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{LIVE_DB_FILE.resolve().as_posix()}"


def _resolve_database_url() -> str:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        return _default_sqlite_url()

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)

    return database_url


@st.cache_resource(show_spinner=False)
def get_live_store_engine() -> Engine:
    database_url = _resolve_database_url()
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, future=True, connect_args=connect_args)


def _normalize_recorded_at(value: object) -> object:
    timestamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(timestamp):
        timestamp = pd.Timestamp.now()
    return timestamp.to_pydatetime()


def init_live_data_store() -> None:
    live_metadata.create_all(get_live_store_engine())


def _legacy_csv_has_rows() -> bool:
    return LIVE_DATA_FILE.exists() and LIVE_DATA_FILE.stat().st_size > 0


def migrate_live_csv_if_needed() -> None:
    init_live_data_store()
    if not _legacy_csv_has_rows():
        return

    engine = get_live_store_engine()
    with engine.connect() as connection:
        existing_rows = connection.execute(
            select(func.count()).select_from(live_complaints_table)
        ).scalar_one()

    if existing_rows:
        return

    legacy_data = pd.read_csv(LIVE_DATA_FILE)
    if legacy_data.empty:
        return

    for column in LIVE_DATA_COLUMNS:
        if column not in legacy_data.columns:
            legacy_data[column] = ""

    records = legacy_data[LIVE_DATA_COLUMNS].to_dict("records")
    for record in records:
        record["RecordedAt"] = _normalize_recorded_at(record["RecordedAt"])

    with engine.begin() as connection:
        connection.execute(live_complaints_table.insert(), records)


def load_live_data() -> pd.DataFrame:
    migrate_live_csv_if_needed()

    query = select(live_complaints_table).order_by(live_complaints_table.c.RecordedAt.asc())
    with get_live_store_engine().connect() as connection:
        live_data = pd.read_sql_query(query, connection)

    if live_data.empty:
        return pd.DataFrame(columns=LIVE_DATA_COLUMNS)

    for column in LIVE_DATA_COLUMNS:
        if column not in live_data.columns:
            live_data[column] = ""

    return live_data[LIVE_DATA_COLUMNS]


def append_live_record(record: dict[str, str]) -> None:
    init_live_data_store()

    payload = {column: record.get(column, "") for column in LIVE_DATA_COLUMNS}
    payload["RecordedAt"] = _normalize_recorded_at(payload["RecordedAt"])

    with get_live_store_engine().begin() as connection:
        connection.execute(live_complaints_table.insert().values(**payload))


def clear_live_data() -> None:
    init_live_data_store()
    with get_live_store_engine().begin() as connection:
        connection.execute(delete(live_complaints_table))
