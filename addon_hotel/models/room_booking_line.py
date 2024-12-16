from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


from odoo.tools.safe_eval import pytz

class RoomBookingLineee(models.Model):
    _inherit = 'room.booking.line'

    room_id = fields.Many2one('hotel.room', string="Room",
                            domain=[('status', '=', 'available')],
                            help="Indicates the Room",
                            required=True,  tracking=1,)
    jumlah = fields.Integer(string='Dewasa',store=True,)
    jumlahanak = fields.Integer(string='Anak',store=True,)
    deposit = fields.Float(string='Deposit',required=True,store=True,)
    diskon = fields.Float(string='Diskon', tracking=True, force_save='1',readonly=True, store=True,)
    ket = fields.Char(string='Keterangan', force_save='1', store=True, readonly=True)
    
    price_unit = fields.Float(string='Rent',
                              digits='Product Price',
                              help="The rent price of the selected room.", readonly=True)
    checkin_date = fields.Datetime(string="Check In",
                                   help="You can choose the date,"
                                        " Otherwise sets to current Date",
                                   required=True, default=fields.Datetime.now())
    checkout_date = fields.Datetime(string="Check Out",
                                    help="You can choose the date,"
                                         " Otherwise sets to current Date", default=fields.Datetime.now() + timedelta(
                                        hours=23, minutes=59, seconds=49))
    uom_qty = fields.Float(string="Duratioon",
                        help="The quantity converted into the UoM used by"
                            "the product", readonly=False)
    #  checkin_date = fields.Datetime(string="Check In",
    #                                help="Date of Checkin",tracking=True,
    #                                default=fields.Datetime.now())
    # checkout_date = fields.Datetime(string="Check Out",
    #                                 help="Date of Checkout", tracking=True,
    #                                 default=fields.Datetime.now() + timedelta(
    #                                     hours=23, minutes=59, seconds=59))

    

    @api.onchange("checkin_date", "checkout_date")
    def _onchange_checkin_date(self):
        """When you change checkin_date or checkout_date it will check
        and update the qty of hotel service line
        -----------------------------------------------------------------
        @param self: object pointer"""
        if self.checkout_date < self.checkin_date:
            raise ValidationError(
                _("Checkout must be greater or equal checkin date"))
        if self.checkin_date and self.checkout_date:
            diffdate = self.checkout_date - self.checkin_date
            hari_ci = fields.Datetime.context_timestamp(self, self.checkin_date).day
            hari_co = fields.Datetime.context_timestamp(self, self.checkout_date).day
            qty = diffdate.days
            if diffdate.total_seconds() > 0:
                qty = qty + 1
                if hari_ci == hari_co  and fields.Datetime.context_timestamp(self, self.checkout_date).hour >= 12:
                    qty = qty + 1
            

            if diffdate.days > 1:
                qty = qty - 1 
               

            # if qty == 0:
            #     qty = qty + 1
            # elif qty > 0:
            #     qty = diffdate.days
            self.uom_qty = qty

    # @api.onchange("checkin_date", "checkout_date")
    # def _onchange_checkin_date(self):
    #     """When you change checkin_date or checkout_date it will check
    #     and update the qty of hotel service line
    #     -----------------------------------------------------------------
    #     @param self: object pointer"""
    #     if self.checkout_date < self.checkin_date:
    #         raise ValidationError(
    #             _("Checkout must be greater or equal checkin date"))
    #     if self.checkin_date and self.checkout_date:
    #         diffdate = self.checkout_date - self.checkin_date
    #         qty = diffdate.days
    #         if diffdate.total_seconds() > 0:
    #             qty = qty + 1
    #         # self.uom_qty = qty

    

    @api.onchange('room_id','booking_id.room_line_ids')
    def get_room_request(self):
        for line in self:
            if line == line.booking_id.room_line_ids[:1]:
                line.room_id = line.booking_id.roomsugest
                line.jumlah = line.room_id.num_person
                line.deposit = line.room_id.deposit
                # line.price_unit = line.room_id.list_price
            else:
                line.jumlah = line.room_id.num_person
                line.deposit = line.room_id.deposit
                # line.price_unit = line.room_id.list_price
    
    @api.depends('uom_qty', 'price_unit', 'tax_ids')
    # @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_price_subtotal(self):
        """Compute the amounts of the room booking line."""
        # for line in self:
        #     tax_results = self.env['account.tax']._compute_taxes([
        #         line._convert_to_tax_base_line_dict()
        #     ])
        #     # totals = list(tax_results['totals'].values())[0]
        #     totals = list(tax_results['tax_lines_to_add'])[0]
        #     amount_untaxed = totals['base_amount']
        #     amount_tax = totals['tax_amount']

        #     line.update({
        #         'price_subtotal': amount_untaxed,
        #         'price_tax': amount_tax,
        #         'price_total': amount_untaxed + amount_tax,
        #     })



        for line in self:
            tax_results = self.env['account.tax']._compute_taxes(
                [line._convert_to_tax_base_line_dict()])
            
            if not list(tax_results['tax_lines_to_add']):
                totals = list(tax_results['totals'].values())[0]
                amount_untaxed = totals['amount_untaxed']
                amount_tax = totals['amount_tax']
                line.update({
                    'price_subtotal': amount_untaxed,
                    'price_tax': amount_tax,
                    'price_total': amount_untaxed + amount_tax,
                })
            else:
                totals = list(tax_results['tax_lines_to_add'])[0]
                amount_untaxed = totals['base_amount']
                amount_tax = totals['tax_amount']
                line.update({
                    'price_subtotal': amount_untaxed,
                    'price_tax': amount_tax,
                    'price_total': amount_untaxed + amount_tax,
                })
            if self.env.context.get('import_file',
                                    False) and not self.env.user. \
                    user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_recordset(
                    ['invoice_repartition_line_ids'])
                
    @api.onchange('booking_id.room_line_ids','price_unit','tax_ids')
    def _onchange_price_unit(self):
        for lines in self:
            if lines.price_unit != lines.room_id.list_price or lines.tax_ids.name != lines.room_id.taxes_ids.name:
                lines.update({
                'price_unit': lines.room_id.list_price,
                'tax_ids': lines.room_id.taxes_ids._origin
                })
                return {
                'warning': {
                    'title': "Tidak dapat diubah",
                    'message': "Silahkan hubungi manager anda untuk ubah data!",
                },
            }
            if lines.booking_id.state != 'draft':
                 return {
                'warning': {
                    'title': "Tidak dapat diubah",
                    'message': "Silahkan hubungi manager anda untuk ubah data!",
                },
            }
           
    # def admininvsible(self):
    #     admininv = self.env['res.partner'].browse(self._uid).admin
    #     return admininv
    

    @api.onchange('checkin_date', 'checkout_date', 'room_id')
    def onchange_checkin_date(self):
        records = self.env['room.booking'].search(
            [('state', 'in', ['reserved', 'check_in'])])
        for rec in records:
            for a in rec.room_line_ids:
                rec_room_id = a.room_id
                rec_checkin_date = a.checkin_date
                rec_checkout_date = a.checkout_date

                if rec_room_id and rec_checkin_date and rec_checkout_date:
                    # Check for conflicts with existing room lines
                    for line in self:
                        if line.id != rec.id and line.room_id == rec_room_id:
                            # Check if the dates overlap
                            if (rec_checkin_date >= line.checkin_date >= rec_checkout_date or
                                    rec_checkin_date >= line.checkout_date >= rec_checkout_date):
                                raise ValidationError(
                                    _("Sorry, You cannot create a reservation for "
                                    "this date since it overlaps with another "
                                    "reservation..!!"))
                            if rec_checkout_date <= line.checkout_date and rec_checkin_date >= line.checkin_date:
                                raise ValidationError(
                                    "Sorry You cannot create a reservation for this"
                                    "date due to an existing reservation between "
                                    "this date")
        if self.checkin_date == False:
           self.write({'checkin_date': fields.Datetime.now()})
        if self.checkout_date == False:
           self.write({'checkout_date': fields.Datetime.now() + timedelta(hours=22, minutes=59, seconds=59)})
        print(self)
   
    
    

class WizardExample(models.TransientModel):
    _name = 'wizard.example'
    _description = 'Wizard Example'

    def default_room(self):
        status_tersedia = self.env['room.booking.line'].browse(self.env.context.get('active_id')).room_id
        return status_tersedia

    def default_co(self):
        co = self.env['room.booking.line'].browse(self.env.context.get('active_id')).checkout_date
        return co

    def default_duration(self):
        duration = self.env['room.booking.line'].browse(self.env.context.get('active_id')).uom_qty
        return duration
    
    def default_total(self):
        price = self.env['room.booking.line'].browse(self.env.context.get('active_id')).price_subtotal
        return price
    
    # struk_ids = fields.One2many(
    #     comodel_name='toko.struk',
    #     inverse_name='pegawai_id',
    #     string='Riwayat Jual',
    #     )

    room_id = fields.Many2one('hotel.room', string="Room",
                            domain=[('status', '=', 'available')],  
                            help="Indicates the Room",
                            required=True, default=default_room, select=True, tracking=1)

    checkout_date = fields.Datetime(string="Check Out",
                                    help="You can choose the date,"
                                         " Otherwise sets to current Date",
                                    required=True,  default= default_co,)
    uom_qty = fields.Float(string="Duration",
                        help="The quantity converted into the UoM used by "
                            "the product", readonly=True, compute='_compute_default' )
    price_total = fields.Float(string="Total",
                            compute='_compute_price_subtotal',
                            # default= default_total,
                            store=True)
    
    # @api.multi
    # def action_save_log_note(self):
    #     # Implement the logic to save the log note, such as adding it to a related record's chatter
    #     related_record = self.env['room.booking'].browse(self._context.get('active_id'))
    #     if related_record:
    #         related_record.message_post(body=self.room_id)  
   
            

    @api.depends('room_id','checkout_date')
    def _compute_default(self):
        order_line_id = self.env.context.get('active_id')
        order_line = self.env['room.booking.line'].browse(order_line_id)
        if order_line.checkout_date != self.checkout_date or order_line.room_id != self.room_id:
            diffdate = self.checkout_date - order_line.checkin_date
            qty = diffdate.days
            if diffdate.total_seconds() > 0:
                qty = qty + 1
            self.uom_qty = qty
            # self.room_id = self.room_id
            self.price_total = self.room_id.list_price * self.uom_qty
        else:
            self.uom_qty = order_line.uom_qty
            # self.room_id = order_line.room_id
            self.price_total = order_line.room_id.list_price * order_line.uom_qty


    @api.depends('checkout_date','room_id','uom_qty')
    def _compute_price_subtotal(self):
        """Compute the amounts of the room booking line."""
        print(self)
        diri = self.env['room.booking.line'].browse(self.env.context.get('active_id'))

        self.price_total = self.room_id.list_price * self.uom_qty
    
    def _compute_amount_untaxed(self, flag=False):
        """Compute the total amounts of the Sale Order"""
        order_line_id = self.env.context.get('active_id')
        order_line = self.env['room.booking.line'].browse(order_line_id)
        diri = self.env['room.booking.line'].browse(self.env.context.get('active_id')).booking_id
        amount_untaxed_room = 0.0
        amount_untaxed_food = 0.0
        amount_untaxed_fleet = 0.0
        amount_untaxed_event = 0.0
        amount_untaxed_service = 0.0
        amount_taxed_room = 0.0
        amount_taxed_food = 0.0
        amount_taxed_fleet = 0.0
        amount_taxed_event = 0.0
        amount_taxed_service = 0.0
        amount_total_room = 0.0
        amount_total_food = 0.0
        amount_total_fleet = 0.0
        amount_total_event = 0.0
        amount_total_service = 0.0
        room_lines = order_line
        
        booking_list = []
        account_move_line = self.env['account.move.line'].search_read(
            domain=[('ref', '=', diri.name),
                    ('display_type', '!=', 'payment_term')],
            fields=['name', 'quantity', 'price_unit', 'product_type'], )
        for rec in account_move_line:
            del rec['id']
        if room_lines:
            amount_untaxed_room += sum(room_lines.mapped('price_subtotal'))
            amount_taxed_room += sum(room_lines.mapped('price_tax'))
            amount_total_room += sum(room_lines.mapped('price_total'))
            for room in room_lines:
                booking_dict = {'name': room.room_id.name,
                                'tax_ids': room.tax_ids,
                                'quantity': self.uom_qty,
                                'diskon': room.diskon,
                                'price_unit': room.price_unit,
                                'product_type': 'room'}
                if booking_dict not in account_move_line:
                    if not account_move_line:
                        booking_list.append(booking_dict)
                    else:
                        for rec in account_move_line:
                            if rec['product_type'] == 'room':
                                if booking_dict['name'] == rec['name'] and \
                                        booking_dict['price_unit'] == rec[
                                    'price_unit'] and booking_dict['quantity']\
                                        != rec['quantity']:
                                    booking_list.append(
                                        {'name': room.room_id.name,
                                         "quantity": booking_dict[
                                                         'quantity'] - rec[
                                                         'quantity'],
                                         "price_unit": room.price_unit,
                                         "product_type": 'room'})
                                else:
                                    booking_list.append(booking_dict)
                    if flag:
                        room.booking_line_visible = True
        
        for rec in diri:
            rec.amount_untaxed = amount_untaxed_food + amount_untaxed_room + \
                                 amount_untaxed_fleet + \
                                 amount_untaxed_event + amount_untaxed_service
            rec.amount_untaxed_food = amount_untaxed_food
            rec.amount_untaxed_room = amount_untaxed_room
            rec.amount_untaxed_fleet = amount_untaxed_fleet
            rec.amount_untaxed_event = amount_untaxed_event
            rec.amount_untaxed_service = amount_untaxed_service
            rec.amount_tax = (amount_taxed_food + amount_taxed_room
                              + amount_taxed_fleet
                              + amount_taxed_event + amount_taxed_service)
            rec.amount_taxed_food = amount_taxed_food
            rec.amount_taxed_room = amount_taxed_room
            rec.amount_taxed_fleet = amount_taxed_fleet
            rec.amount_taxed_event = amount_taxed_event
            rec.amount_taxed_service = amount_taxed_service
            rec.amount_total = (amount_total_food + amount_total_room
                                + amount_total_fleet + amount_total_event
                                + amount_total_service)
            rec.amount_total_food = amount_total_food
            rec.amount_total_room = amount_total_room
            rec.amount_total_fleet = amount_total_fleet
            rec.amount_total_event = amount_total_event
            rec.amount_total_service = amount_total_service
        return booking_list
    
    def action_confirm(self):   
        order_line_id = self.env.context.get('active_id')
        order_line = self.env['room.booking.line'].browse(order_line_id)
        diri = self.env['room.booking.line'].browse(self.env.context.get('active_id')).booking_id
        msg= f"Dari Kamar: {order_line.room_id.name} Pindah Ke Kamar:  {self.room_id.name}"
        order_line.booking_id.message_post(body=msg)

        accmove =  self.env['account.move'].sudo().search([('hotel_booking_id.id','=',order_line.booking_id.id),('journal_id.id','=','1'),('state','=','posted')])
                    # context = dict(self._context or {})
        if accmove:
            # for loop in accmove:
            #     if loop.display_type == 'product':
            accmove[0].line_ids.remove_move_reconcile()
            accmove.update({
                'state' : 'cancel'
            })
            if order_line.room_id != self.room_id:
                    status_tersedia = self.env['room.booking.line'].browse(order_line_id).room_id
                    diri.invoice_button_visible = True

                    status_tersedia.update({
                        'status' : "available"
                    })
                    # Update order line dengan data dari wizard
                    if order_line.ket =='Extend':
                        order_line.update({
                            'room_id': self.room_id.id,
                            'ket': order_line.ket+" & Pindah Kamar"
                        })
                        

                    elif order_line.ket == 'Pindah Kamar':
                        order_line.update({
                            'room_id': self.room_id.id,
                            'ket': "Pindah Kamar"
                        })
                        
                    elif not order_line.ket:
                        order_line.update({
                            'room_id': self.room_id.id,
                            'ket': "Pindah Kamar"
                        })
                        
                    else:
                        order_line.update({
                            'room_id': self.room_id.id,
                            # 'ket': "Pindah Kamar"
                        })
                    
                    order_line.room_id.update({
                        'status' : "occupied"
                    })

                    # invc = self.env['account.move'].sudo().search([('hotel_booking_id.id','=',order_line.booking_id.id),('journal_id.id','=','1')])
                    # if not invc:
                    #     order_line.update({
                    #         'room_id': self.room_id.id,
                    #     })
                       
                    # else:
                    #     invcc = invc[-1].line_ids
                    #     for a in invcc:
                    #         if a.display_type == 'product':
                    #             a.update({
                    #                 'name': self.room_id.name,  
                    #             })
        
        if not accmove:
            if order_line.room_id != self.room_id:

                    status_tersedia = self.env['room.booking.line'].browse(order_line_id).room_id
                    status_tersedia.update({
                        'status' : "available"
                    })
                    # Update order line dengan data dari wizard
                    if order_line.ket =='Extend':
                        order_line.update({
                            'room_id': self.room_id.id,
                            'ket': order_line.ket+" & Pindah Kamar"
                        })
                        

                    elif order_line.ket == 'Pindah Kamar':
                        order_line.update({
                            'room_id': self.room_id.id,
                            'ket': "Pindah Kamar"
                        })
                        
                    elif not order_line.ket:
                        order_line.update({
                            'room_id': self.room_id.id,
                            'ket': "Pindah Kamar"
                        })
                        
                    else:
                        order_line.update({
                            'room_id': self.room_id.id,
                            # 'ket': "Pindah Kamar"
                        })
                    
                    order_line.room_id.update({
                        'status' : "occupied"
                    })
                    invc = self.env['account.move'].sudo().search([('hotel_booking_id.id','=',order_line.booking_id.id),('journal_id.id','=','1')])
                    if not invc:
                        order_line.update({
                            'room_id': self.room_id.id,
                            # 'ket': "Pindah Kamar"
                        })
                        #  raise ValidationError(_('Lakukan invoice di Kamar sebelumnya.'))
                    else:
                        invcc = invc[-1].line_ids
                        for a in invcc:
                            if a.display_type == 'product':
                                a.update({
                                    'name': self.room_id.name,  
                                })
        
        if order_line.checkout_date != self.checkout_date and order_line.price_subtotal > self.price_total:
        
            if order_line.ket =='Pindah Kamar':
                order_line.write({
                'checkout_date': self.checkout_date,
                'uom_qty' :self.uom_qty,
                'ket': order_line.ket+' & Extend'
            })
            
            elif order_line.ket =='Extend': 
                order_line.update({
                'checkout_date': self.checkout_date,
                'uom_qty' :self.uom_qty,
                'ket': 'Extend'
            })
            elif not order_line.ket:
                order_line.update({
                    'checkout_date': self.checkout_date,
                    'ket': 'Extend',
                    'uom_qty' :self.uom_qty
                })
            else:
                order_line.update({
                    'checkout_date': self.checkout_date,
                    # 'ket': 'Extend',
                    'uom_qty' :self.uom_qty
                })
                
         
        if order_line.price_subtotal != self.price_total:

            booking_list = diri._compute_amount_untaxed(True)
            if booking_list:
                account_move = self.env["account.move"].create([{
                    'move_type': 'out_invoice',
                    'invoice_date': fields.Date.today(),
                    'hotel_booking_id' : diri.id,
                    'partner_id': diri.partner_id.id,
                    'ref': diri.name,
                }])
                for rec in order_line:
                   account_move.line_ids.create([{
                        'name': rec['room_id'].name,
                        'quantity': self.uom_qty,
                        'price_unit': rec['room_id'].list_price,
                        # 'tax_ids': rec['tax_ids'],
                        'product_uom_id' : rec['uom_id'].id,
                        'move_id': account_move.id,
                        'price_subtotal': self.uom_qty * self.price_total,
                        'product_type': 'room',
                    }])
                diri.update({'invoice_status': "invoiced",
                            'hotel_invoice_id':  account_move.id })
                diri.invoice_button_visible = True

            

                if order_line.room_id != self.room_id:

                    status_tersedia = self.env['room.booking.line'].browse(order_line_id).room_id
                    status_tersedia.update({
                        'status' : "available"
                    })
                
                    # context = dict(self._context or {})
                    # if context.get('active_ids', False):
                    #     self.env['account.move.line'].browse(context.get('active_ids')).remove_move_reconcile()
                    # return {'type': 'ir.actions.act_window_close'}


                   
                        

                    # Update order line dengan data dari wizard
                    if order_line.ket =='Extend':
                        order_line.write({
                            'room_id': self.room_id.id,
                            'ket': order_line.ket+" & Pindah Kamar"
                        })
                        
                    elif order_line.ket == 'Pindah Kamar':
                        order_line.update({
                            'room_id': self.room_id.id,
                            'ket': "Pindah Kamar"
                        })
                        
                    elif not order_line.ket:
                        order_line.write({
                            'room_id': self.room_id.id,
                            'ket': "Pindah Kamar"
                        })
                        
                    else:
                        order_line.write({
                            'room_id': self.room_id.id,
                            # 'ket': "Pindah Kamar"
                        })
                        
                    
                    order_line.room_id.update({
                        'status' : "occupied"
                    })
                    invc = self.env['account.move'].sudo().search([('hotel_booking_id.id','=',order_line.booking_id.id),('journal_id.id','=','1')])[-1].line_ids
                    for a in invc:
                        if a.display_type == 'product':
                            a.write({
                                'name': self.room_id.name,  
                            })
                   
            # return {'type': 'ir.actions.act_window_close'}
                
                if order_line.checkout_date != self.checkout_date:
                    
                    if order_line.ket =='Pindah Kamar':
                        order_line.write({
                        'checkout_date': self.checkout_date,
                        'uom_qty' :self.uom_qty,
                        'ket': order_line.ket+' & Extend'
                    })
                    
                    elif order_line.ket =='Extend': 
                        order_line.update({
                        'checkout_date': self.checkout_date,
                        'uom_qty' :self.uom_qty ,
                        'ket': 'Extend'
                    })
                    elif not order_line.ket:
                        order_line.update({
                            'checkout_date': self.checkout_date,
                            'ket': 'Extend',
                            'uom_qty' :self.uom_qty 
                        })
                    else:
                        order_line.update({
                            'checkout_date': self.checkout_date,
                            # 'ket': 'Extend',
                            'uom_qty' :self.uom_qty 
                        })
            

            
    

            return {
                    'type': 'ir.actions.act_window',
                    'name': 'Invoices',
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'account.move',
                    'view_id': self.env.ref('account.view_move_form').id,
                    'res_id': account_move.id,
                    'context': "{'create': False}"
                    }
        
        

        print(self)

    
           
    

   
    
    