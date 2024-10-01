# -*- coding: utf-8 -*-
# from odoo import http


# class AddonHotel(http.Controller):
#     @http.route('/addon_hotel/addon_hotel', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/addon_hotel/addon_hotel/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('addon_hotel.listing', {
#             'root': '/addon_hotel/addon_hotel',
#             'objects': http.request.env['addon_hotel.addon_hotel'].search([]),
#         })

#     @http.route('/addon_hotel/addon_hotel/objects/<model("addon_hotel.addon_hotel"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('addon_hotel.object', {
#             'object': obj
#         })
