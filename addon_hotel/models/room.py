from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError

class room(models.Model):
    _inherit = 'hotel.room'

    kanbancolor = fields.Integer('Color Index', compute="set_kanban_color")
    room_type = fields.Selection([('single', 'Single'),
                                ('double', 'Double'),
                                ('twin', 'Room Twin'),
                                ('grand_deluxe', 'Grand Deluxe'),
                                ('single_deluxe', 'Single Deluxe'),
                                ('dormitory', 'Dormitory')],
                                required=True, string="Room Type",
                                help="Automatically selects the Room Type",
                                tracking=True,
                                default="twin")
    
    mentenance_id = fields.Many2one(
        string='mentenance',
        comodel_name='maintenance.request',
        
    )
    
    
    maintenance = fields.Char(string='Maintenance',tracking=True, store=True, readonly=True)

    @api.depends('status')
    def set_kanban_color(self):
        for record in self:
            if record.status == 'available':
                record.kanban_color = 10  # Green
            elif record.status == 'occupied':
                record.kanban_color = 3  # Yellow
            else:
                record.kanban_color = 2  # Red

    def addroom(self):
       self.ensure_one()
       cari = self.env['room.booking'].sudo().search([('room_line_ids.room_id','=', self.id),('state','in',['reserved','check_in'])])[-1].id
       return{
        #    'name' : self.display_name,
           'type' : 'ir.actions.act_window',
           'view_id' : self.env.ref('hotel_management_odoo.room_booking_view_form').id,
           'res_model' :'room.booking',
           'res_id' :cari,
           'view_mode':'form',
           'target' : 'current',
        #    'domain': [('room_line_ids.room_id', '=', self.id)],
        #    'domain' : [('room_line_ids.room_id', '=', self.id)],
       }
        

    def room(self):
       self.ensure_one()
    #    ctx = {'partner_id':'tes'}
       return{
        #    'name' : self.display_name,
           'type' : 'ir.actions.act_window',
           'view_id' : self.env.ref('hotel_management_odoo.room_booking_view_form').id,
           'res_model' :'room.booking',
           'view_mode':'form',
           'context' : {'default_roomsugest': self.id}
           
           
       }

    @api.onchange("room_type")
    def _onchange_room_type(self):
        """
        Based on selected room type, number of person will be updated.
        ----------------------------------------
        @param self: object pointer
        """
        if self.room_type == "single":
            self.num_person = 1
        elif self.room_type == "double":
            self.num_person = 2
        elif self.room_type == "grand_deluxe":
            self.num_person = 2
        elif self.room_type == "single_deluxe":
            self.num_person =  1
        elif self.room_type == "room_twin":
            self.num_person = 2
        else:
            self.num_person = 4

    
    # def action_open_order_line(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Order Lines',
    #         'view_mode': 'tree,form',
    #         'res_model': 'room.booking.line',
    #         # 'domain': [('order_id', '=', self.id)],
    #         'context': {
    #             'default_room_id': self.id,  # Default order_id in sale.order.line
    #              # Default product_id
    #         }
    #     }
    

    
    