from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import OrderedDict



class inheritWizard(models.TransientModel):

    _inherit = 'account.payment.register'

    def default_journal(self):
        status_tersedia = self.env['account.journal'].search([('type', '=','cash')])
        return status_tersedia

    journal_id = fields.Many2one(
            comodel_name='account.journal',
            compute='_compute_journal_id', store=True, readonly=False, precompute=True,
            check_company=True,
            default= default_journal,
            domain="[('id', 'in', available_journal_ids)]")


class AccountMove(models.Model):
    _inherit = 'account.move'

    hotel_booking_id = fields.Many2one('room.booking',
                                       store=True,
                                    string="Booking Reference",
                                    readonly=True, help="Choose the Booking"
                                                        "Reference",
                                                        compute='_compute_field' )
    
    # show_update_fpos = fields.Boolean(string="Show Update Fiscal Position")
    def nama(self):
        loop = self.filtered(lambda pay: pay.move_type == 'out_invoice' and pay.journal_id.id == 1)
        data_kamar =[]
        
        for a in loop:
            datanya = a.line_ids.filtered(lambda pay: pay.display_type == 'product')
            for z in datanya:
                room= z.name
                amountnya =z.credit
                testing = (room,amountnya)
                data_kamar.append(testing)
            
        result = {}
        for card, value in data_kamar:
                total = result.get(card, 0) + value
                result[card] = total 
        
        return list(result.items())

    def periode(self):

        per = []
        for a in self:
            per.append(a.date)
        return per[0]
    
    def periodee(self):

        per = []
        for a in self:
            per.append(a.date)
        return per[-1]
    
    def po(self):
        for b in self:
              c = self.env['purchase.order'].sudo().search([('name','=',b.invoice_origin)])
        return c
    # batas py untuk qweb (up)

    @api.depends('move_id', 'ref')
    def get_price_total(self):
        if not self.hotel_booking_id:
            self.hotel_booking_id = self.payment_id.room_booking_id


  
   
    