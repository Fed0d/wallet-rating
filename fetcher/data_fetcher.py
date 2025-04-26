import time
from datetime import datetime

import pandas as pd
import requests


def date_to_timestamp(date_str: str) -> int:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return int(time.mktime(dt.timetuple()))


def fetch_transactions(
    address: str, api_key: str, end_date: str, tx_type: str = "normal"
) -> list:
    base_url = "https://api.arbiscan.io/api"
    action = "txlist" if tx_type == "normal" else "txlistinternal"
    cutoff_ts = date_to_timestamp(end_date)
    params = {
        "module": "account",
        "action": action,
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 10000,
        "sort": "asc",
        "apikey": api_key,
    }
    result = []
    while True:
        resp = requests.get(base_url, params=params)
        data = resp.json()
        if data.get("status") != "1":
            break
        batch = data.get("result", [])
        for tx in batch:
            if int(tx["timeStamp"]) <= cutoff_ts:
                result.append(tx)
            else:
                return result
        if len(batch) < params["offset"]:
            break
        params["page"] += 1
    return result


def fetch_token_transfers(address: str, api_key: str, end_date: str) -> list:
    base_url = "https://api.arbiscan.io/api"
    cutoff_ts = date_to_timestamp(end_date)
    params = {
        "module": "account",
        "action": "tokentx",
        "address": address,
        "startblock": 0,
        "endblock": 99999999,
        "page": 1,
        "offset": 10000,
        "sort": "asc",
        "apikey": api_key,
    }
    result = []
    while True:
        resp = requests.get(base_url, params=params)
        data = resp.json()
        if data.get("status") != "1":
            break
        batch = data.get("result", [])
        for tx in batch:
            if int(tx["timeStamp"]) <= cutoff_ts:
                result.append(tx)
            else:
                return result
        if len(batch) < params["offset"]:
            break
        params["page"] += 1
    return result


def collect_all_to_dataframe(
    addresses: list, api_key: str, end_date: str
) -> pd.DataFrame:
    rows = []
    for addr in addresses:
        for tx_type in ("normal", "internal"):
            for tx in fetch_transactions(addr, api_key, end_date, tx_type):
                rec = tx.copy()
                rec["tx_type"] = tx_type
                rec["address"] = addr
                rows.append(rec)
        for tx in fetch_token_transfers(addr, api_key, end_date):
            rec = tx.copy()
            rec["tx_type"] = "erc20"
            rec["address"] = addr
            rows.append(rec)
    import pandas as pd  # ensure pandas imported for return type

    return pd.DataFrame(rows)
