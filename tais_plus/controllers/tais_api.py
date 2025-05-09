from typing import Tuple, TypedDict, Union
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
