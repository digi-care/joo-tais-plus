from odoo import models, fields
import openpyxl
import base64
from datetime import datetime
from io import BytesIO


class PriceListImport(models.TransientModel):
    _name = "tais_plus.pricelist.import"
    _description = "Import Price List"

    file = fields.Binary(string="File", required=True)
    filename = fields.Char(string="Filename")

    def import_pricelist(self):

        # Validate filename format
        if not self.filename.lower().startswith("pricelist"):
            raise ValueError("Filename must start with 'pricelist'.")
        if not self.filename.lower().endswith(".xlsx"):
            raise ValueError("Filename must have an extension of .xlsx.")
        header_filename = self.filename

        # Extract date from the filename
        try:
            if "_" in self.filename:
                # Format: pricelist_YYYY-MM-DD_○○.xlsx
                date_str = self.filename.split("_")[1]  # Extract 'YYYY-MM-DD'
                header_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                # Validate the sheet by searching for the header row
                expected_headers = [
                    "商品コード",
                    "法人名",
                    "商品名",
                    "型番",
                    "全国平均貸与価格（円）",
                    "貸与価格の上限（円）",
                ]
            else:
                # Format: pricelistYYYYMM.xlsx
                date_str = self.filename[9:15]  # Extract 'YYYYMM'
                header_date = datetime.strptime(date_str, "%Y%m").replace(day=1).date()
                # Validate the sheet by searching for the header row
                expected_headers = [
                    "コード",
                    "法人名",
                    "商品名",
                    "型番",
                    "全国平均貸与価格（円）",
                    "貸与価格の上限（円）",
                ]
        except (IndexError, ValueError):
            raise ValueError(
                "Filename must include a valid date in 'YYYY-MM-DD' or 'YYYYMM' format "
                "(e.g., 'pricelist_2025-04-01_remarks.xlsx' or 'pricelist202504.xlsx')."
            )

        # Create header name
        header_name = f"上限一覧 {header_date.strftime('%Y-%m-%d')}"

        # Decode the file content
        file_content = base64.b64decode(self.file)
        # Load the workbook (XLSX only)
        workbook = openpyxl.load_workbook(BytesIO(file_content))

        header_sheetname = ", ".join([sheet.title for sheet in workbook.worksheets])

        num_columns = len(expected_headers)  # Determine the number of columns

        # Process all sheets in the workbook
        temp_data = []
        for sheet in workbook.worksheets:
            header_row = None
            for row_idx in range(1, 7):  # Search within the first 6 rows
                actual_headers = [
                    sheet.cell(row=row_idx, column=col).value
                    for col in range(1, num_columns + 1)
                ]
                if actual_headers == expected_headers:
                    header_row = row_idx
                    break

            if header_row is None:
                raise ValueError(
                    f"Valid headers not found in sheet '{self.filename}!{sheet.title}'. Expected: {expected_headers}"
                )

            # Load data starting from the row after the header
            for row in sheet.iter_rows(
                min_row=header_row + 1,
                max_row=sheet.max_row,
                min_col=1,
                max_col=num_columns,
            ):
                if row[0].value is None:  # Exit loop if tais_code is None
                    break
                temp_data.append(
                    {
                        "tais_code": row[0].value,  # 商品コード
                        "manufacturer": row[1].value,  # 法人名
                        "product_name": row[2].value,  # 商品名
                        "model_number": row[3].value,  # 型番
                        "average_price": row[4].value,  # 全国平均貸与価格（円）
                        "maximum_price": row[5].value,  # 貸与価格の上限（円）
                    }
                )

        # model for price_list and price_list_item
        price_list = self.env["tais_plus.pricelist"].sudo()
        price_list_item = self.env["tais_plus.pricelist.item"].sudo()

        # Determine or create the price_list record
        header_rec = price_list.search(
            [("tais_code_date", "=", header_date)], limit=1
        )
        if not header_rec:
            header_rec = price_list.create(
                {
                    "name": header_name,
                    "tais_code_date": header_date,
                    "filename": header_filename,
                    "sheetname": header_sheetname,
                }
            )
        else:
            # Update existing header
            header_rec.name = header_name
            header_rec.filename = header_filename
            header_rec.sheetname = header_sheetname
            # Delete existing price_list_item records
            header_rec.item_ids.unlink()

        # Perform intermediate processing and add records to price_list_item
        date_str = header_date.strftime("%Y-%m-%d")
        for item in temp_data:
            price_list_item.create(
                {
                    "name": item["tais_code"] + ":" + date_str,
                    "tais_code": item["tais_code"],
                    "manufacturer": item["manufacturer"],
                    "product_name": item["product_name"],
                    "model_number": item["model_number"],
                    "average_price": item["average_price"],
                    "maximum_price": item["maximum_price"],
                    "pricelist_id": header_rec.id,
                }
            )

        # Open the form view of the created/updated header record
        return {
            "type": "ir.actions.act_window",
            "res_model": "tais_plus.pricelist",
            "view_mode": "form",
            "res_id": header_rec.id,
            "target": "current",
        }
