from pydantic import BaseModel

# Define a type alias
class TaisPriceCapItem(BaseModel):
    name: str
    date: date
    maximum: float
    currency: str
