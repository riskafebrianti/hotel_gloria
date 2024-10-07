from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import pytz

class RoomBookingline(models.Model):
    _inherit = 'room.booking.line'

    
    jumlah = fields.Integer(string='Dewasa',store=True,)
    jumlahanak = fields.Integer(string='Anak',store=True,)
    deposit = fields.Float(string='Deposit',required=True,store=True,)
    diskon = fields.Float(string='Diskon', tracking=True, force_save='1', store=True,)


    @api.onchange('room_id','booking_id.room_line_ids')
    def get_room_request(self):
        for line in self:
            if line == line.booking_id.room_line_ids[:1]:
                line.room_id = line.booking_id.roomsugest
                line.jumlah = line.room_id.num_person
            else:
                line.jumlah = line.room_id.num_person

    @api.depends('uom_qty', 'price_unit', 'tax_ids')
    def _compute_price_subtotal(self):
        """Compute the amounts of the room booking line."""
        for line in self:
            tax_results = self.env['account.tax']._compute_taxes(
                [line._convert_to_tax_base_line_dict()])
            totals = list(tax_results['totals'].values())[0]
            amount_untaxed = totals['amount_untaxed'] 
            amount_tax = totals['amount_tax']
            line.update({
                'price_subtotal': amount_untaxed - self.diskon,
                'price_tax': amount_tax,
                'price_total': amount_untaxed - self.diskon + amount_tax,
            })
            if self.env.context.get('import_file',
                                    False) and not self.env.user. \
                    user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_recordset(
                    ['invoice_repartition_line_ids'])
    
    @api.onchange('diskon','price_subtotal','booking_id.room_line_ids')
    def get_diskon(self):
       if self.diskon:
           self.price_subtotal = (self.price_unit * self.uom_qty) - self.diskon
           print(self)
           
           
    

   
    
    