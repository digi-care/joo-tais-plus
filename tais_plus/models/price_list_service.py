from odoo import models
from datetime import date
from typing import Optional, TypedDict

from ..models.price_list_item import PriceListItem


class PriceListService(models.AbstractModel):
    _name = "tais_plus.pricelist.service"
    _description = "TAIS Code Price List Service"

    # Define a type alias
    class TaisPrice(TypedDict):
        name: str
        date: date
        maximum: float
        currency: str

    # Define a type alias
    class TaisInfo(TypedDict):
        tais_code: str
        target_date: date
        target: any
        future: any

    def get_tais_info(
        self,
        tais_code: str,
        target_date: date,
    ) -> TaisInfo:

        # Fetch target and previous records
        target = self.get_tais_price_target(tais_code, target_date)

        # Determine target or minimum
        future = self.get_tais_price_target_or_future(target, tais_code, target_date)

        data = PriceListService.TaisInfo(
            tais_code=tais_code,
            target_date=target_date,
            target=target,
            future=future,
        )
        return data

    def get_tais_price_target_or_future(
        self, target: Optional[TaisPrice], tais_code: str, target_date: date
    ) -> Optional[TaisPrice]:
        priceListItem: PriceListItem = self.env["tais_plus.pricelist.item"]
        record = priceListItem.search(
            [("tais_code", "=", tais_code), ("tais_code_date", ">", target_date)],
            order="maximum_price asc",
            limit=1,
        )
        if record:
            future = PriceListService.TaisPrice(
                name=record.pricelist_id.name,
                date=record.tais_code_date,
                maximum=record.maximum_price,
                currency=record.currency_id.name,
            )
            if target and target["maximum"] <= future["maximum"]:
                return target
            return future
        return target

    def get_tais_price_target(
        self,
        tais_code: str,
        target_date: date,
    ) -> Optional[TaisPrice]:
        priceListItem: PriceListItem = self.env["tais_plus.pricelist.item"]
        record = priceListItem.search(
            [("tais_code", "=", tais_code), ("tais_code_date", "<=", target_date)],
            order="tais_code_date desc",
            limit=1,
        )
        target: Optional[PriceListService.TaisPrice] = None
        if record:
            target = PriceListService.TaisPrice(
                name=record.pricelist_id.name,
                date=record.tais_code_date,
                maximum=record.maximum_price,
                currency=record.currency_id.name,
            )
        return target
