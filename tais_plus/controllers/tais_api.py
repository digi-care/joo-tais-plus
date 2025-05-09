from typing import Tuple, TypedDict, Union

from pytz import utc
from odoo import http
from odoo.http import request
import json
from datetime import datetime, date
from ..models.tais_code_service import TaisCodeService
from ..models.price_list_service import PriceListService


def date_serializer(obj):
    """Custom serializer for date objects."""
    if isinstance(obj, date):
        return obj.isoformat()
    return obj  # Return the object as-is if it's not serializable


class TaisAPI(http.Controller):

    class ErrorResponse(TypedDict):
        error: str
        details: str

    def _validate_tais_code(
        self, tais_code: str
    ) -> Tuple[bool, Union[list[str], ErrorResponse]]:
        if not tais_code:
            return False, TaisAPI.ErrorResponse(
                error="TAIS code is required.",
                details="The format '01234-012345' is required.",
            )
        parts = tais_code.split("-")
        if len(parts) != 2:
            return False, TaisAPI.ErrorResponse(
                error="The TAIS code format is invalid.",
                details="The format '01234-012345' is required.",
            )
        return True, parts

    @http.route(
        "/tais_plus/api/tais/<string:tais_code>",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def get_tais(self, tais_code, **kwargs):
        # Validate the TAIS code parameter
        is_valid, validation_result = self._validate_tais_code(tais_code)
        if not is_valid:
            return request.make_response(
                json.dumps(validation_result),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        # Fetch data from TAIS
        taisCodeService: TaisCodeService = request.env[
            "tais_plus.taiscode.service"
        ].sudo()
        tais_url = taisCodeService.generate_tais_url(
            validation_result[0], validation_result[1]
        )
        try:
            taisProduct = taisCodeService.get_tais_product(tais_url)
        except Exception as e:
            return request.make_response(
                json.dumps(
                    TaisAPI.ErrorResponse(
                        error="An error occurred while processing the TAIS data.",
                        details=tais_url,
                    )
                ),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        # Validate the extracted TAIS code
        if taisProduct.get("tais_code") != tais_code:
            return request.make_response(
                json.dumps(
                    TaisAPI.ErrorResponse(
                        error="The TAIS code is not recognized.",
                        details=tais_url,
                    )
                ),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        return request.make_response(
            json.dumps(taisProduct),
            headers=[("Content-Type", "application/json")],
        )

    @http.route(
        "/tais_plus/api/pricecap/<string:tais_code>/<string:target_date>",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def get_price(self, tais_code, target_date, **kwargs):
        # Validate the TAIS code and target date parameters
        is_valid, validation_result = self._validate_tais_code(tais_code)
        if not is_valid:
            return request.make_response(
                json.dumps(validation_result),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        try:
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            return request.make_response(
                json.dumps(
                    TaisAPI.ErrorResponse(
                        error="Invalid date format.",
                        details="Expected yyyy-mm-dd.",
                    )
                ),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        # env
        priceListService: PriceListService = request.env[
            "tais_plus.pricelist.service"
        ].sudo()
        taisPriceCap = priceListService.get_tais_price_cap(tais_code, target_date)
        return request.make_response(
            json.dumps(taisPriceCap, default=date_serializer),
            headers=[("Content-Type", "application/json")],
        )

    @http.route(
        "/tais_plus/api/aid_product/<string:aid_product_code>/<string:target_datetime>",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def get_aid_product(self, aid_product_code, target_datetime, **kwargs):

        # Replace "+" with "/" in aid_product_code
        aid_product_code = aid_product_code.replace("+", "/")

        try:
            # target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            target_date = datetime.fromisoformat(target_datetime).date()
            target_datetime = datetime.fromisoformat(target_datetime).astimezone(utc)

        except ValueError:
            return request.make_response(
                json.dumps(
                    {
                        "error": "Invalid date format. Expected ISO8601, yyyy-mm-ddThh:mm:ssZ."
                    }
                ),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        # default_code (Internal Reference)
        product_product = request.env["product.product"].sudo()
        product = product_product.search(
            [("default_code", "=", aid_product_code)], limit=1
        )

        if not product:
            return request.make_response(
                json.dumps({"error": "Product not found"}),
                headers=[("Content-Type", "application/json")],
                status=404,
            )

        # TAIS price cap
        priceListService: PriceListService = request.env[
            "tais_plus.pricelist.service"
        ].sudo()
        taisPriceCap = priceListService.get_tais_price_cap(
            product.tais_code, target_date
        )

        # Product Price
        product_pricelist_item = request.env["product.pricelist.item"].sudo()
        query = (
            "SELECT id FROM product_pricelist_item"
            + " WHERE active AND min_quantity = 1 AND compute_price = 'fixed'"
            + "   AND (product_tmpl_id = %s or product_tmpl_id is null)"
            + "   AND (product_id = %s or product_id is null)"
            + "   AND (date_start <= %s or date_start is null)"
            + "   AND (date_end >= %s or date_end is null)"
            + " ORDER BY date_start desc nulls last, date_end asc nulls last, product_id asc nulls last, product_tmpl_id asc nulls last"
        )
        params = (
            product.product_tmpl_id.id,  # product_tmpl_id
            product.id,  # product_id
            target_datetime,  # date_start
            target_datetime,  # date_end
        )
        product_pricelist_item.env.cr.execute(query, params)
        pricelist_item = product_pricelist_item.env.cr.fetchone()
        if pricelist_item:
            pricelist_item = product_pricelist_item.browse(pricelist_item[0])
            sales_price = pricelist_item.fixed_price
            sales_currency = pricelist_item.currency_id.name
            sales_date_start = pricelist_item.date_start
        else:
            sales_price = None
            sales_currency = None
            sales_date_start = None

        # Purchase price
        product_supplierinfo = request.env["product.supplierinfo"].sudo()
        query = (
            "SELECT id FROM product_supplierinfo"
            + " WHERE min_qty = 1"
            + "   AND (product_tmpl_id = %s or product_tmpl_id is null)"
            + "   AND (product_id = %s or product_id is null)"
            + "   AND (date_start <= %s or date_start is null)"
            + "   AND (date_end >= %s or date_end is null)"
            + " ORDER BY date_start desc nulls last, date_end asc nulls last, product_id asc nulls last, product_tmpl_id asc nulls last"
        )
        params = (
            product.product_tmpl_id.id,  # product_tmpl_id
            product.id,  # product_id
            target_date,  # date_start
            target_date,  # date_end
        )
        product_supplierinfo.env.cr.execute(query, params)
        supplierinfo = product_supplierinfo.env.cr.fetchone()
        if supplierinfo:
            supplierinfo = product_supplierinfo.browse(supplierinfo[0])
            purchase_price = supplierinfo.price
            purchase_currency = supplierinfo.currency_id.name
            purchase_date_start = supplierinfo.date_start
        else:
            purchase_price = None
            purchase_currency = None
            purchase_date_start = None

        return request.make_response(
            json.dumps(
                {
                    "product_code": (
                        product.default_code if product.default_code else None
                    ),
                    "product_name": product.name if product.name else None,
                    "pricecap": taisPriceCap,
                    "sales": {
                        "price": sales_price,
                        "currency": sales_currency,
                        "date_start": (
                            sales_date_start.isoformat() if sales_date_start else None
                        ),
                        "target_datetime": target_datetime.isoformat(),
                    },
                    "purchase": {
                        "price": purchase_price,
                        "currency": purchase_currency,
                        "date_start": (
                            purchase_date_start.isoformat()
                            if purchase_date_start
                            else None
                        ),
                        "target_date": target_date.isoformat(),
                    },
                }, default=date_serializer
            ),
            headers=[("Content-Type", "application/json")],
            status=200,
        )
