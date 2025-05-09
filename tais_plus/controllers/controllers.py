# -*- coding: utf-8 -*-
# from odoo import http


# class TaisPlus(http.Controller):
#     @http.route('/tais_plus/tais_plus', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tais_plus/tais_plus/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tais_plus.listing', {
#             'root': '/tais_plus/tais_plus',
#             'objects': http.request.env['tais_plus.tais_plus'].search([]),
#         })

#     @http.route('/tais_plus/tais_plus/objects/<model("tais_plus.tais_plus"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tais_plus.object', {
#             'object': obj
#         })
