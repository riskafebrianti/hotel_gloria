from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    hotel_booking_id = fields.Many2one('room.booking',
                                       store=True,
                                    string="Booking Reference",
                                    readonly=True, help="Choose the Booking"
                                                        "Reference",
                                                        compute='_compute_field' )
    
        
    
    # @api.depends('depends')
    # def _compute_field(self):
    #      if self.payment_id:
    #         self.update({
    #             'hotel_booking_id': self.payment_id.hotel_booking_id,
    #         })
    #         print()
        # if self.payment_id:
        #     self.hotel_booking_id = self.payment_id.hotel_booking_id
            # for record in self:
            #     record.field = something
    
    # @api.onchange('ref')
    # def _compute_field(self):
    #     if not self.hotel_booking_id:
    #         self.hotel_booking_id = self.payment_id.room_booking_id
    @api.depends('move_id', 'ref')
    def get_price_total(self):
        if not self.hotel_booking_id:
            self.hotel_booking_id = self.payment_id.room_booking_id
    
    
    
    
    