from odoo import models
from datetime import date

from ..models.price_list_item import PriceListItem
from ..schemas.tais_price_cap import TaisPriceCap
from ..schemas.tais_price_cap_item import TaisPriceCapItem


class PriceListService(models.AbstractModel):
    _name = "tais_plus.pricelist.service"
    _description = "TAIS Code Price List Service"

    def get_tais_price_cap(
        self,
        tais_code: str,
        target_date: date,
    ) -> TaisPriceCap:

        # Fetch target and previous records
        target = self._get_tais_price_cap_target(tais_code, target_date)

        # Determine target or minimum
        future = self._get_tais_price_cap_target_or_future(target, tais_code, target_date)

        data = TaisPriceCap(
            tais_code=tais_code,
            target_date=target_date,
            target=target,
            future=future,
        )
        return data

    def _get_tais_price_cap_target_or_future(
        self, target: TaisPriceCapItem, tais_code: str, target_date: date
    ):
        priceListItem: PriceListItem = self.env["tais_plus.pricelist.item"]
        record = priceListItem.search(
            [("tais_code", "=", tais_code), ("tais_code_date", ">", target_date)],
            order="maximum_price asc",
            limit=1,
        )
        if record:
            future = TaisPriceCapItem(
                name=record.pricelist_id.name,
                date=record.tais_code_date,
                maximum=record.maximum_price,
                currency=record.currency_id.name,
            )
            if target and target["maximum"] <= future["maximum"]:
                return target
            return future
        return target

    def _get_tais_price_cap_target(
        self,
        tais_code: str,
        target_date: date,
    ):
        priceListItem: PriceListItem = self.env["tais_plus.pricelist.item"]
        record = priceListItem.search(
            [("tais_code", "=", tais_code), ("tais_code_date", "<=", target_date)],
            order="tais_code_date desc",
            limit=1,
        )
        target = None
        if record:
            target = TaisPriceCapItem(
                name=record.pricelist_id.name,
                date=record.tais_code_date,
                maximum=record.maximum_price,
                currency=record.currency_id.name,
            )
        return target
