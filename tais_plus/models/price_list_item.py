from odoo import models, fields


class PriceListItem(models.Model):
    _name = "tais_plus.pricelist.item"
    _description = "TAIS Code Price List (detail)"

    name = fields.Char(
        string="TAISコード:適用開始日",
        required=True,
        help="<TAISコード> + ':' + <yyyy-mm-dd>",
    )

    tais_code = fields.Char(string="TAISコード", required=True, help="商品コード")
    product_name = fields.Char(string="商品名称")
    manufacturer = fields.Char(string="製造メーカー", help="法人名")
    model_number = fields.Char(string="型番")
    average_price = fields.Monetary(
        string="全国平均貸与価格", currency_field="currency_id"
    )
    maximum_price = fields.Monetary(
        string="貸与価格の上限", currency_field="currency_id", required=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.ref("base.JPY"),  # Default to Japanese Yen
        required=True,
    )

    pricelist_id = fields.Many2one(
        comodel_name="tais_plus.pricelist",
        string="上限価格リスト名",
        required=True,
        ondelete="cascade",
        help="The header this detail belongs to",
    )

    tais_code_date = fields.Date(
        string="適用開始日",
        related="pricelist_id.tais_code_date",
        store=True,
        readonly=True,
        help="Effective start date inherited from the associated Price List Header",
    )

    _sql_constraints = [
        ("unique_name", "UNIQUE(name)", "The name must be unique."),
        (
            "unique_tais_code_date_combination",
            "UNIQUE(tais_code, tais_code_date)",
            "The combination of TAIS Code and Effective Date must be unique.",
        ),
    ]
