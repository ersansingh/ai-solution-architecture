"""Read the raw-data layout (raw-data/<source>/ingest_date=YYYY-MM-DD/*.csv) from a local path."""
from __future__ import annotations

import glob
import os
from typing import Dict, Optional

import pandas as pd

from churn import config


def latest_partition(source_dir: str) -> Optional[str]:
    partitions = sorted(glob.glob(os.path.join(source_dir, "ingest_date=*")))
    return partitions[-1] if partitions else None


def load_raw(raw_root: str, include_label: bool = True) -> Dict[str, pd.DataFrame]:
    """Load the newest ingest_date partition of every source under raw_root."""
    frames = {}
    for source in config.features()["sources"]:
        if source == "churn" and not include_label:
            continue
        partition = latest_partition(os.path.join(raw_root, source))
        if partition is None:
            if source == "churn":
                continue
            raise FileNotFoundError(f"no partitions for source '{source}' under {raw_root}")
        files = sorted(glob.glob(os.path.join(partition, "*.csv")))
        frames[source] = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    return frames
