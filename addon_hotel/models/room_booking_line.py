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
    ket = fields.Char(string='Keterangan', force_save='1', store=True, readonly=True)


    @api.onchange('room_id','booking_id.room_line_ids')
    def get_room_request(self):
        for line in self:
            if line == line.booking_id.room_line_ids[:1]:
                line.room_id = line.booking_id.roomsugest
                line.jumlah = line.room_id.num_person
                line.deposit = line.room_id.deposit
            else:
                line.jumlah = line.room_id.num_person
                line.deposit = line.room_id.deposit

    # @api.depends('uom_qty', 'price_unit', 'tax_ids')
    # def _compute_price_subtotal(self):
    #     """Compute the amounts of the room booking line."""
    #     for line in self:
    #         tax_results = self.env['account.tax']._compute_taxes(
    #             [line._convert_to_tax_base_line_dict()])
    #         totals = list(tax_results['totals'].values())[0]
    #         amount_untaxed = totals['amount_untaxed'] 
    #         amount_tax = totals['amount_tax']
    #         line.update({
    #             'price_subtotal': amount_untaxed - self.diskon,
    #             'price_tax': amount_tax,
    #             'price_total': amount_untaxed - self.diskon + amount_tax,
    #         })
    #         if self.env.context.get('import_file',
    #                                 False) and not self.env.user. \
    #                 user_has_groups('account.group_account_manager'):
    #             line.tax_id.invalidate_recordset(
    #                 ['invoice_repartition_line_ids'])
    
    # @api.onchange('diskon','price_subtotal','booking_id.room_line_ids')
    # def get_diskon(self):
    #    if self.diskon:
    #        self.price_subtotal = (self.price_unit * self.uom_qty) - self.diskon
    #        print(self)
    
    

class WizardExample(models.TransientModel):
    _name = 'wizard.example'
    _description = 'Wizard Example'

    def default_room(self):
        status_tersedia = self.env['room.booking.line'].browse(self.env.context.get('active_id')).room_id
        return status_tersedia

    def default_co(self):
        co = self.env['room.booking.line'].browse(self.env.context.get('active_id')).checkout_date
        return co

    # def default_duration(self):
    #     duration = self.env['room.booking.line'].browse(self.env.context.get('active_id')).uom_qty
    #     return duration
    
    room_id = fields.Many2one('hotel.room', string="Room",
                            domain=[('status', '=', 'available')],
                            help="Indicates the Room",
                            required=True, select=True, default= default_room, )

    checkout_date = fields.Datetime(string="Check Out",
                                    help="You can choose the date,"
                                         " Otherwise sets to current Date",
                                    required=True,  default= default_co,)
    uom_qty = fields.Float(string="Duration",
                        help="The quantity converted into the UoM used by "
                            "the product", readonly=True )
    
    @api.onchange("checkout_date")
    def _onchange_checkin_datee(self):
        """When you change checkin_date or checkout_date it will check
        and update the qty of hotel service line
        -----------------------------------------------------------------
        @param self: object pointer"""
        co_pertama = self.env['room.booking.line'].browse(self.env.context.get('active_id')).checkout_date
        if self.checkout_date < co_pertama:
            raise ValidationError(
                _("Checkout must be greater or equal checkin date"))
        if self.checkout_date:      
            diffdate = self.checkout_date - co_pertama
            qty = diffdate.days
            if diffdate.total_seconds() > 0:
                qty = qty + 1
            self.uom_qty = qty
    
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

        if order_line.room_id != self.room_id:

            status_tersedia = self.env['room.booking.line'].browse(order_line_id).room_id
            status_tersedia.update({
                'status' : "available"
            })
            # Update order line dengan data dari wizard
            order_line.write({
                'room_id': self.room_id.id,
                'ket': "Pindah Kamar"
            })
            order_line.room_id.update({
                'status' : "occupied"
            })
            invc = self.env['account.move'].sudo().search([('hotel_booking_id.id','=',order_line.booking_id.id),('journal_id.id','=','1')]).line_ids
            for a in invc:
                if a.display_type == 'product':
                    a.write({
                        'name': self.room_id.name,  
                    })


        if order_line.checkout_date != self.checkout_date:
            co_pertama = self.env['room.booking.line'].browse(self.env.context.get('active_id')).checkout_date
            if self.checkout_date < co_pertama:
                raise ValidationError(
                    _("Checkout must be greater or equal checkin date"))
            if self.checkout_date:      
                diffdate = self.checkout_date - co_pertama
                qty = diffdate.days
                if diffdate.total_seconds() > 0:
                    qty = qty + 1
                self.uom_qty = qty
            # Update order line dengan data dari wizard
            
            if order_line.ket:
                order_line.write({
                'checkout_date': self.checkout_date,
                'uom_qty' :self.uom_qty + self.env['room.booking.line'].browse(self.env.context.get('active_id')).uom_qty,
                'ket': order_line.ket+' & Extend'
            })
                
            elif not order_line.ket:
                order_line.write({
                    'checkout_date': self.checkout_date,
                    'ket': 'Extend',
                    'uom_qty' :self.uom_qty + self.env['room.booking.line'].browse(self.env.context.get('active_id')).uom_qty
                })

            # if not self.room_line_ids:
            #     raise ValidationError(_("Please Enter Room Details"))

        booking_list = diri._compute_amount_untaxed(True)
        if booking_list:
            account_move = self.env["account.move"].create([{
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'hotel_booking_id' : diri.id,
                'partner_id': diri.partner_id.id,
                'ref': diri.name,
            }])
            for rec in booking_list:
                account_move.invoice_line_ids.create([{
                    'name': rec['name'],
                    'quantity': self.uom_qty,
                    'price_unit': rec['price_unit'],
                    # 'tax_ids': rec['tax_ids'],
                    'move_id': account_move.id,
                    'price_subtotal': self.uom_qty * rec['price_unit'],
                    'product_type': rec['product_type'],
                }])
            diri.write({'invoice_status': "invoiced",
                        'hotel_invoice_id': account_move.id })
            diri.invoice_button_visible = True
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

           
           
    

   
    
    