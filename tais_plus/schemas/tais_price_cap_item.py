from datetime import date
from typing import TypedDict

# Define a type alias
class TaisPriceCapItem(TypedDict):
    name: str
    date: date
    maximum: float
    currency: str
