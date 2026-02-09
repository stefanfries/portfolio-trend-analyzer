from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel
from pydantic_extra_types.currency_code import Currency

type Interval = Literal["5min", "15min", "30min", "hour", "day", "week", "month"]


class HistoryRecord(BaseModel):
    datetime: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class HistoryData(BaseModel):
    wkn: str
    name: str
    id_notation: str
    trading_venue: str
    currency: Currency
    start: datetime
    end: datetime
    interval: Interval
    data: List[HistoryRecord]
