import pandas as pd


def extract_sybil_features(df: pd.DataFrame, cutoff_date: str) -> dict:
    df = df.copy()
    num_cols = [
        "blockNumber",
        "nonce",
        "transactionIndex",
        "value",
        "gas",
        "gasPrice",
        "cumulativeGasUsed",
        "gasUsed",
        "confirmations",
        "isError",
    ]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
    df["timeStamp"] = pd.to_datetime(df["timeStamp"].astype(int), unit="s")
    cutoff_ts = pd.to_datetime(cutoff_date)
    df = df[df["timeStamp"] <= cutoff_ts]
    if df.empty:
        return {}
    addr = df["address"].iloc[0].lower()
    features = {}
    tx_count = len(df)
    days_active = df["timeStamp"].dt.date.nunique()
    features.update(
        {
            "tx_count": tx_count,
            "active_days": days_active,
            "lifetime_days": (
                (df["timeStamp"].max() - df["timeStamp"].min()).days
                if tx_count > 1
                else 0
            ),
        }
    )
    df["time_diff"] = df["timeStamp"].diff().dt.total_seconds()
    features.update(
        {
            "mean_tx_interval": df["time_diff"].mean(),
            "fast_tx_ratio": (df["time_diff"] < 1).mean(),
        }
    )
    v_eth = df["value"].astype(float) / 1e18
    features.update(
        {
            "total_value_eth": v_eth.sum(),
            "zero_value_tx_ratio": (v_eth == 0).mean(),
        }
    )
    out_v = v_eth[df["from"].str.lower() == addr]
    in_v = v_eth[df["to"].str.lower() == addr]
    features["net_value_eth"] = in_v.sum() - out_v.sum()
    return features


def process_dataframe(df: pd.DataFrame, cutoff_date: str) -> pd.DataFrame:
    """
    Group by address and compute features with given cutoff_date.
    """
    feats = []
    for addr, sub in df.groupby("address"):
        feats_dict = extract_sybil_features(sub, cutoff_date)
        if feats_dict:
            feats_dict["address"] = addr
            feats.append(feats_dict)
    return pd.DataFrame(feats)
