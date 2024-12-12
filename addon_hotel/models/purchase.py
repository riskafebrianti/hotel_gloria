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
    
    
    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')

        partner_invoice = self.env['res.partner'].browse(self.partner_id.address_get(['invoice'])['invoice'])
        partner_bank_id = self.partner_id.commercial_partner_id.bank_ids.filtered_domain(['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])[:1]

        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
            'deskripsi': self.deskripsi,
            'currency_id': self.currency_id.id,
            'partner_id': partner_invoice.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(partner_invoice)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': partner_bank_id.id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
        }
        return invoice_vals
    

    