from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.exceptions import UserError
class room(models.Model):
    _inherit = 'hotel.room'

    kanbancolor = fields.Integer('Color Index', compute="set_kanban_color")
    room_type = fields.Selection([
                                ('twin', 'Deluxe Twin'),
                                ('single', 'Deluxe Single'),
                                ('grand_deluxe', 'Grand Deluxe non Balkon'),
                                ('grand_deluxe_balkon', 'Grand Deluxe Balkon')],
                                # ('single', 'Single'),
                                # ('double', 'Double'),
                                # ('dormitory', 'Dormitory')
                                
                                required=True, string="Room Type",
                                help="Automatically selects the Room Type",
                                tracking=True,
                                default="twin")
    
    mentenance_id = fields.Char(string='Status Kerusakan', 
                                # compute='_maintenance',
                                )
    
    status_kerusakan = fields.Char(
        string='status_kerusakan',
        store=True,
        compute='_maintenance',
    )
    
    deposit = fields.Float(
        string='Deposit',
         store=True,
          required=True, 
    )

    list_price = fields.Float(string='Rent', digits='Product Price',
                            help="The rent of the room.", store=True,required=True, )
    
    draft = fields.Boolean(
                            string="Ada di draft",
                            store=True,
                            readonly=True
                            )
    
    mentenance_ids = fields.One2many('maintenance.request', 'room_maintenance_ids', string='field_name')
    booking_line_id = fields.One2many('room.booking.line', 'room_id', string='field_namee')
  
    terbooking = fields.Char(string='Jumlah Terpesan', compute='_terbooking',store=True,)
    ket = fields.Char(string='Keterangan booking', compute='get_price_total',)
    maintenance = fields.Char(string='Maintenance',tracking=True, store=True, readonly=True)

    # @api.depends('quantity', 'price')
    def get_price_total(self):
        for diri in self:
            data = self.env['room.booking'].sudo().search([('room_line_ids.room_id','=', diri.id),('state','in',['reserved','check_in'])])
            if data :
                for oc in data.room_line_ids:
                    if oc.checkout_date < datetime.today():
                        diri.ket = 'Over CheckOut'      
                    else:
                        diri.ket ='Terisi'          
            if not data:
                diri.ket = ''
            if diri.status == 'available':
                diri.ket = '-'    
    # @api.depends('booking_line_id')
    # def draft(self):
    #     print(self)
    
        # cari = self.env['room.booking'].sudo().search([('room_line_ids.room_id','=', self.id),('state','in',['reserved','check_in'])]).id
        # cari_draft = self.env['room.booking'].sudo().search([('room_line_ids.room_id','=', self.id),('state','==','draft')]).id

        # if cari:
        #     self.draft = 'False'
        # if cari_draft:
        #     self.draft = 'True'
    

    # @api.onchange('terbooking','name','list_price')
    def create(self, vals):
        # if vals.terbooking:
        if not vals['list_price'] or not vals['deposit']:
            
            raise UserError(_( "Isi Harga kamar dan deposit"))
        else:
            return super(room, self).create(vals)
            

        
    

    @api.depends('booking_line_id','booking_line_id.booking_id.state','terbooking')
    def _terbooking(self):
            
        for order in self:
            date_begin = datetime.now().replace(datetime.now().year, datetime.now().month, day=1).strftime('%Y-%m-%d') if datetime.now().month != 1 else (12, datetime.now().year-1)
            jumpes = self.env['room.booking.line'].sudo().search([('room_id','=', order.id),('booking_id.state', 'not in', ['draft', 'cancel']),('checkin_date','>',date_begin), ('checkin_date','<',datetime.now())])
            order.terbooking = len(jumpes)
            print(order)
    
    # @api.depends('booking_line_id.booking_id')
    # def _terket(self):
    #     self.write({"status": "occupied"})
    #     # for room in self.room_line_ids:
    #     #     room.room_id.write({
    #     #         'status': 'occupied',
    #     #         'is_room_avail': True
    #     #     })
    #     # # for order in self:
    #     #     jumpess = self.env['room.booking.line'].sudo().search([('room_id','=', order.id),('booking_id.state','=', 'draft')])
    #     #     # jumpesss = jumpess.booking_id[-1]
    #     #     if jumpess:
    #     #         self.keterangan = 'True'
    #     #     if not jumpess:
    #     #         self.keterangan = 'False'
            
            
          
            # print(order)
        
    
    @api.depends('mentenance_ids','status_kerusakan')
    def _maintenance(self):

        for tea in self:
            search = self.env['maintenance.request'].sudo().search([('room_maintenance_ids','=', tea.id),('state','!=','done'),('kerusakan_berat','=', True)])
            if search:
                tea.status_kerusakan = 'Berat'
    
   
  
    
    

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
       cari = self.env['room.booking'].sudo().search([('room_line_ids.room_id','=', self.id),('state','in',['reserved','check_in'])]).id
       cari_draft = self.env['room.booking'].sudo().search([('room_line_ids.room_id','=', self.id),('state','in',['draft'])]).id
       if cari:
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
       if cari_draft:
           return{
                #    'name' : self.display_name,
                'type' : 'ir.actions.act_window',
                'view_id' : self.env.ref('hotel_management_odoo.room_booking_view_form').id,
                'res_model' :'room.booking',
                'res_id' :cari_draft,
                'view_mode':'form',
                'target' : 'current',
                #    'domain': [('room_line_ids.room_id', '=', self.id)],
                #    'domain' : [('room_line_ids.room_id', '=', self.id)],
            }
    
    def action_show_maintenance(self):
        print(self)
        # cari = self.env['room.booking'].sudo().search([('room_line_ids.room_id','=', self.id),('state','in',['reserved','check_in'])])[-1].id
        #   """Method for Returning invoice View"""
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Room Maintenance',
            'view_mode': 'tree,form',
            'view_type': 'tree,form',
            'res_model': 'maintenance.request',
            'domain': [('room_maintenance_ids.id','=', self.id),('state','!=','done')],
            'context': "{'create': False}"
        }
    
    # @api.depends('status')
    # def _cari(self):
    #     for b in self:
    #         cari = self.env['room.booking'].sudo().search([('state','in',['draft']),('room_line_ids.room_id','=', b.id)])
    #         if not cari:
    #             self.ket = "-"
    #         else:
    #             for a in cari:
    #                 self.ket = a.id
        

    

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
        if self.room_type:
            self.num_person = 4

        if self.room_type == "twin":
            self.deposit = '141000'
            self.list_price = '359000'

        elif self.room_type == "single":
            self.deposit = '141000'
            self.list_price = '359000'

        elif self.room_type == "grand_deluxe_balkon":
            self.deposit = '171000'
            self.list_price = '429000'

        elif self.room_type == "grand_deluxe":
             self.deposit = '101000'
             self.list_price = '399000'
        # else:
        #     self.num_person = 4

    #  ('twin', 'Deluxe Twin')
    #                             ('single', 'Deluxe Single'),
    #                             ('grand_deluxe', 'Grand Deluxe non Balkon'),
    #                             ('grand_deluxe_balkon', 'Grand Deluxe Balkon')

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
    

    
    