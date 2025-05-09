from odoo import models, fields


class PriceList(models.Model):
    _name = "tais_plus.pricelist"
    _description = "TAIS Code Price List (header)"

    name = fields.Char(
        string="上限価格リスト名", required=True, help="pricelist_YYYY-MM-DD"
    )

    tais_code_date = fields.Date(string="適用開始日", required=True)
    filename = fields.Char(string="ファイル名")
    sheetname = fields.Char(string="シート名")

    item_ids = fields.One2many(
        comodel_name="tais_plus.pricelist.item",
        inverse_name="pricelist_id",
        string="TAISコード上限価格",
    )

    _sql_constraints = [
        (
            "unique_tais_code_date",
            "UNIQUE(tais_code_date)",
            "The tais_code_date must be unique.",
        ),
    ]

    def get_pricelist_item_view(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Price List Details",
            "view_mode": "tree,form",
            "res_model": "tais_plus.pricelist.item",
            "domain": [("pricelist_id", "=", self.id)],
            "context": {"default_pricelist_id": self.id},
        }
