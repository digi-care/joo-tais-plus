import requests
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class TaisCodeImport(models.TransientModel):
    _name = "tais_plus.taiscode.import"
    _description = "Import TAIS Codes"

    tais_codes = fields.Text(
        string="TAIS Codes", required=True, help="Enter TAIS codes, one per line."
    )

    @api.model
    def fetch_tais_data(self, tais_code):
        """Fetch TAIS data from the API and update the record."""
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        port = self.env["ir.config_parameter"].sudo().get_param("web.base.port", "8069")
        api_url = f"{base_url}:{port}/tais_plus/api/tais/{tais_code}"
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                raise ValueError(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            raise ValueError(f"Failed to fetch TAIS data: {str(e)}")

    def import_tais_codes(self):
        """Import TAIS codes from the entered text."""
        if not self.tais_codes:
            raise ValueError("No TAIS codes provided.")

        tais_code_list = [
            code.strip() for code in self.tais_codes.splitlines() if code.strip()
        ]
        TaisCode = self.env["tais_plus.taiscode"].sudo()
        for tais_code in tais_code_list:
            try:
                # Fetch data from the API
                data = self.fetch_tais_data(tais_code)

                # ccta95_id
                ccta95 = self.env["tais_plus.ccta95"].search(
                    [("ccta95_code", "=", data.get("ccta95_code", ""))], limit=1
                )
                if ccta95:
                    data["ccta95_id"] = ccta95.id

                # rental_service
                data["rental_service"] = "R" + data.get("rental_service_code")
                # sales_service
                data["sales_service"] = "S" + data.get("sales_service_code")

                # Upsert
                existing_record = TaisCode.search([("tais_code", "=", tais_code)], limit=1)
                if existing_record:
                    new_data = {
                        "name": data.get("product_name"),
                        "tais_code": tais_code,
                        "ccta95_id": data.get("ccta95_id"),
                        "product_model": data.get("product_model"),
                        "manufacturer": data.get("manufacturer"),
                        "rental_service": data.get("rental_service"),
                        "sales_service": data.get("sales_service"),
                        "image_url": data.get("image_url"),
                        "product_summary": data.get("product_summary"),
                        "is_discontinued": data.get("is_discontinued"),
                        "tais_url": data.get("tais_url"),
                    }
                    existing_record.write(
                        {
                            key: value
                            for key, value in new_data.items()
                            if value is not None
                        }
                    )
                else:
                    new_data = {
                        "name": data.get("product_name"),
                        "tais_code": tais_code,
                        "ccta95_id": data.get("ccta95_id"),
                        "product_model": data.get("product_model"),
                        "manufacturer": data.get("manufacturer"),
                        "rental_service": data.get("rental_service"),
                        "sales_service": data.get("sales_service"),
                        "image_url": data.get("image_url"),
                        "product_summary": data.get("product_summary"),
                        "is_discontinued": data.get("is_discontinued"),
                        "tais_url": data.get("tais_url"),
                    }
                    TaisCode.create(
                        {
                            key: value
                            for key, value in new_data.items()
                            if value is not None
                        }
                    )
            except Exception as e:
                _logger.error(f"Error importing TAIS code {tais_code}: {e}")
