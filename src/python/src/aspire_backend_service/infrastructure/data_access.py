import logging
import math
import os
import time

from .fabric_sql import query_to_dataframe

logger = logging.getLogger(__name__)


def get_customer_information():
    sql = os.getenv("CUSTOMER_INFORMATION_QUERY")
    if not sql:
        raise ValueError("CUSTOMER_INFORMATION_QUERY is not configured")

    start_time = time.perf_counter()
    df = query_to_dataframe(sql)
    duration_ms = (time.perf_counter() - start_time) * 1000

    record_count = len(df)

    records = df.to_dict(orient="records")

    def _sanitize_for_json(obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        if isinstance(obj, dict):
            return {k: _sanitize_for_json(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_sanitize_for_json(v) for v in obj]
        return obj

    sanitized_records = _sanitize_for_json(records)

    logger.info(
        "Customer information query executed",
        extra={
            "record_count": record_count,
            "duration_ms": round(duration_ms, 2),
        },
    )

    if record_count > 1000:
        logger.warning(
            "Customer information query returned high record count",
            extra={"record_count": record_count},
        )

    return sanitized_records
