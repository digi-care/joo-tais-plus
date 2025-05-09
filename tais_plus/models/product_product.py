
from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    tais_code = fields.Char(string='TAISコード')
