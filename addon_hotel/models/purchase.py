from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Purchase(models.Model):
    _inherit = 'purchase.order'

    
    deskripsi = fields.Text(
        string='Deskripsi',
    )
    
    @api.onchange('order_line')
    def get_name(self):
        isiqty = []
        for a in self.order_line:
            qty = int(a.product_qty)
            uom = a.product_uom.name
            name = a.name
            subtotal = '{0:,.0f}'.format(a.price_subtotal)
            isiqty.append(f"Pembelian {qty} {uom} {name} @Rp.{subtotal} ")
            self.deskripsi = ', '.join(map(str, isiqty))+ ", ".join([f"({vendor.partner_id.name})" for vendor in a.order_id])
            # subtotal = int(a.price_subtotal)
            # vendor = a.order_id.partner_id.name
            # combined_names = ', '.join(map(str, isiqty))
            # combined_names =  isiqty
    

    