from odoo import models
from datetime import date
from typing import TypedDict


class ProductService(models.AbstractModel):
    _name = "tais_plus.product.service"
    _description = "Product Service"

