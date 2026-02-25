import os
import struct
from urllib.parse import quote_plus

import pandas as pd
from azure.identity import DefaultAzureCredential
from sqlalchemy import create_engine

_SQL_SCOPE = "https://database.windows.net/.default"
_ACCESS_TOKEN_ATTRIBUTE = 1256  # SQL_COPT_SS_ACCESS_TOKEN


def _get_access_token() -> str:
    credential = DefaultAzureCredential()
    token = credential.get_token(_SQL_SCOPE)
    return token.token


def _build_engine():
    endpoint = os.environ.get("FABRIC_SQL_ENDPOINT")
    database = os.environ.get("FABRIC_DATABASE_NAME")

    if not endpoint:
        raise ValueError("FABRIC_SQL_ENDPOINT environment variable is not set")
    if not database:
        raise ValueError("FABRIC_DATABASE_NAME environment variable is not set")

    server = endpoint.replace("tcp:", "")

    access_token = _get_access_token()
    token_bytes = access_token.encode("utf-16-le")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)

    odbc_str = (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server={server};"
        f"Database={database};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    quoted = quote_plus(odbc_str)
    engine = create_engine(
        f"mssql+pyodbc:///?odbc_connect={quoted}",
        connect_args={"attrs_before": {_ACCESS_TOKEN_ATTRIBUTE: token_struct}},
    )

    return engine


def query_to_dataframe(sql: str) -> pd.DataFrame:
    engine = _build_engine()
    with engine.connect() as connection:
        df = pd.read_sql(sql, connection)
    engine.dispose()
    return df
