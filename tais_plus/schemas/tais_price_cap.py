from datetime import date
from typing import TypedDict
from .tais_price_cap_item import TaisPriceCapItem


# Define a type alias
class TaisPriceCap(TypedDict):
    tais_code: str
    target_date: date
    target: TaisPriceCapItem
    future: TaisPriceCapItem
