from odoo import models, fields, api, _
from odoo.exceptions import UserError
from collections import OrderedDict

class AccountMove(models.Model):
    _inherit = 'account.move'

    hotel_booking_id = fields.Many2one('room.booking',
                                       store=True,
                                    string="Booking Reference",
                                    readonly=True, help="Choose the Booking"
                                                        "Reference",
                                                        compute='_compute_field' )
    
        
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
    
    # batas py untuk qweb (up)

    @api.depends('move_id', 'ref')
    def get_price_total(self):
        if not self.hotel_booking_id:
            self.hotel_booking_id = self.payment_id.room_booking_id


  
   
    