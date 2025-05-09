from pydantic import BaseModel

# Define a type alias
class TaisPriceCap(BaseModel):
    tais_code: str
    target_date: date
    target: TaisPriceCapItem
    future: TaisPriceCapItem
