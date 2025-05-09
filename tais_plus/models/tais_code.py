import base64
import requests
from odoo import models, fields, api


class TaisCode(models.Model):
    _name = "tais_plus.taiscode"
    _description = "TAIS Code"

    _sql_constraints = [
        ("tais_code", "UNIQUE(tais_code)", "The tais_code must be unique!")
    ]

    name = fields.Char(string="商品名", required=True)

    tais_code = fields.Char(
        string="TAISコード",
        required=True,
        help="TAISコードは、企業コード(5桁)と福祉用具コード(6桁)で構成されます。",
    )

    ccta95_id = fields.Many2one(
        "tais_plus.ccta95",
        string="分類項目",
        required=False,
        help="福祉用具は、分類コード(CCTA95)で分類されています。",
    )

    product_model = fields.Char(string="型番")

    manufacturer = fields.Char(string="製造メーカー")

    rental_service = fields.Selection(
        selection=[
            ("R00", "--:（非貸与）"),
            ("R01", "01: 車いす"),
            ("R02", "02: 車いす付属品"),
            ("R03", "03: 特殊寝台"),
            ("R04", "04: 特殊寝台付属品"),
            ("R05", "05: 床ずれ防止用具"),
            ("R06", "06: 体位変換器"),
            ("R07", "07: 手すり"),
            ("R08", "08: スロープ"),
            ("R09", "09: 歩行器"),
            ("R10", "10: 歩行補助つえ"),
            ("R11", "11: 認知症老人徘徊感知機器"),
            ("R12", "12: 移動用リフト"),
            ("R13", "13: 自動排泄処理装置"),
        ],
        string="レンタルサービス種目",
        required=True,
        help="福祉用具レンタルサービス種目を選択してください。",
    )
    sales_service = fields.Selection(
        selection=[
            ("S00", "--:（非購入）"),
            ("S01", "01: 腰掛便座"),
            ("S02", "02: 自動排泄処理装置の交換可能部品"),
            ("S03", "03: 排泄予測支援機器"),
            ("S04", "04: 入浴補助用具"),
            ("S05", "05: 簡易浴槽"),
            ("S06", "06: 移動用リフトのつり具の部分"),
            ("S07", "07: スロープ"),
            ("S08", "08: 歩行器"),
            ("S09", "09: 歩行補助つえ"),
        ],
        string="販売サービス種目",
        required=True,
        help="福祉用具販売サービス種目を選択してください。",
    )
    image_url = fields.Char(
        string="画像リンク", help="商品に関連する画像のURLを入力してください。"
    )
    tais_url = fields.Char(
        string="TAIS URL", help="TAISコードに関連するURLを入力してください。"
    )
    image = fields.Binary(string="Image", compute="_compute_image_url")

    product_summary = fields.Text(string="製品概要")

    is_discontinued = fields.Boolean(string="生産終了", default=False)

    @api.depends("image_url")
    def _compute_image_url(self):
        """function to load image from URL"""
        image = False
        if self.image_url:
            # 画像の処理ロジック
            image = base64.b64encode(requests.get(self.image_url).content)
        self.image = image

    def name_get(self):
        """
        オーバーライドして参照時に "[TAISコード] 商品名称" の形式を表示
        """
        result = []
        for record in self:
            display_name = f"[{record.tais_code}] {record.name}"
            result.append((record.id, display_name))
        return result
