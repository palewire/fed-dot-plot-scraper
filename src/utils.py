"""Utility functions."""
from __future__ import annotations

import re
from datetime import datetime

import pandas as pd
import requests


def parse_date(url) -> datetime:
    """Parse the date from a source URL."""
    s = re.split(r"fomcprojtabl", url)[1]
    s = s.replace(".htm", "")
    return pd.to_datetime(s[-8:])


def get_url(url) -> str:
    """Get the provided URL."""
    r = requests.get(url)
    assert r.ok
    return r.text


def safestr(ele) -> str | None:
    """Return a stripped string or None."""
    return ele.strip() or None
