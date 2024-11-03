from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import pytz
from odoo.exceptions import UserError
from collections import OrderedDict
import numpy as np

class RoomBookingTree(models.Model):
    _inherit = 'room.booking'

    ktp = fields.Char(string='ktp', related='partner_id.ktp', )
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help="Customers of hotel",
                                 required=True, index=True, tracking=1,
                                 domain="[('type', '!=', 'private'),"
                                        " ('company_id', 'in', "
                                        "(False, company_id))]"
                                        )
    pricelist_id = fields.Many2one(comodel_name='product.pricelist',
                                string="Pricelist",
                                compute='_compute_pricelist_id',
                                store=True, readonly=False,
                                tracking=1,
                                help="If you change the pricelist,"
                                    " only newly added lines"
                                    " will be affected.")
    roomsugest = fields.Many2one("hotel.room",
                                 string='RoomSugest',
                                 store=True,)
    deposit_in = fields.Boolean(string='deposit_in', )
    deposit_out = fields.Boolean(string='deposit_out', )
    deposit_sisa = fields.Float(string='Deposit',store=True, compute='depoSisa',)
    
    state_paymnt = fields.Char(
        string='state_paymnt',store=True,  
    )
    piutang = fields.Char(
        string='state_paymnt',store=True,  
    )
    
    depo_count = fields.Integer(string='depo_count', compute='_compute_depo_count'
    )
    pricelist_id = fields.Many2one(comodel_name='product.pricelist',
                                string="Pricelist",
                                compute='_compute_pricelist_id',
                                store=True, readonly=False,
                                required=False,
                                tracking=1,
                                help="If you change the pricelist,"
                                    " only newly added lines"
                                    " will be affected.")

    
    payment_ids = fields.One2many(
        string='payment',
        comodel_name='account.payment',
        inverse_name='room_booking_id',
    )
    
    
    maintenance_request_sent = fields.Boolean(default=False,
                                            string="Maintenance Request sent "
                                                    "or Not",
                                                    tracking=True,
                                                    # compute='get_price',
                                            help="sets to True if the "
                                                "maintenance request send "
                                                "once" )
    def default_CO(self):
        tes = fields.Datetime.now().replace(hour=4, minute= 00) + timedelta(days=1)
        
        return tes
    
    
    checkout_date = fields.Datetime(string="Check Out",
                                help="Date of Checkout",
                                default=default_CO)
    
    def _compute_depo_count(self):
        """Compute the invoice count"""
        for record in self:
            record.depo_count = self.env['account.payment'].search_count(
                [('room_booking_id','=', self.id)])
    
    def total_semua(self):
        total = sum(self.room_line_ids.mapped('price_total'))
        total1 = sum(self.room_line_ids.booking_id.mapped('deposit_sisa'))
        jumlah = total+total1

        return jumlah

    def periode(self):

        per = []
        for a in self:
            per.append(a.date_order)
        return per[0]
    
    def periodee(self):

        per = []
        for a in self:
            per.append(a.date_order)
        return per[-1]
#   def paid(self):
#         for a in self:
#             b = a.env['account.move'].sudo().search([('hotel_booking_id','=',a.id),('move_type','=','out_invoice'),('journal_id.name','!=','CHARGE')]).payment_state
#             return b
        
#     def amount(self):
#         residual = []
#         for z in self:
#             c = self.env['account.move'].sudo().search([('hotel_booking_id','=',z.id),('move_type','=','out_invoice'),('journal_id.name','!=','CHARGE')]).amount_residual
#             residual.append(c)
#             # a = np.array.residual.tolist()
#         return residual
  
        
        
    
    @api.depends('hotel_invoice_id.payment_state','hotel_invoice_id.amount_residual')
    def paymnt(self):
    
        a = self.env['account.move'].sudo().search([('hotel_booking_id','=',self.id),('move_type','=','out_invoice'),('journal_id.name','!=','CHARGE')])
    #     for a in self:
        self.state_paymnt = a.payment_state
        self.piutang = a.amount_residual
        print(self)
        
    
    @api.depends('payment_ids.payment_type')
    def depoSisa(self):
        print(self)
        for depo in self:
            depomasuk = depo.env['account.payment'].sudo().search([('room_booking_id','=',self.id),('payment_type','=','inbound')])
            depokeluar = depo.env['account.payment'].sudo().search([('room_booking_id','=',self.id),('payment_type','=','outbound')])
            self.deposit_sisa = depomasuk.amount - depokeluar.amount
    

    def action_deposit_in(self):
       self.ensure_one()
       print(self)
       if not self.room_line_ids.deposit:
           raise ValidationError(
                _("Masukkan Nilai Deposit"))
       
       self.deposit_in = True
       return{
           'type' : 'ir.actions.act_window',
           'view_id' : self.env.ref('account.view_account_payment_form').id,
           'res_model' :'account.payment',
           'view_mode':'form',
           
           'context' : {
                        'default_partner_id': self.partner_id.id,
                        'default_journal_id': self.env['account.journal'].sudo().search([('code','=', 'CSH1')]).id,
                        'default_amount': sum(self.room_line_ids.mapped('deposit')),
                        'default_room_booking_id' : self.id,
                        'default_ref': 'Deposit Booking: '+ str(self.name)
                        }
       }
    def action_checkout(self):
        """Button action_heck_out function"""
        self.write({"state": "check_out"})
        for room in self.room_line_ids:
            room.room_id.write({
                'status': 'available',
                'is_room_avail': True
            })
            room.write({'checkout_date': datetime.today()})
        self.deposit_out = True
        # print(self)
        return{
           'type' : 'ir.actions.act_window',
           'view_id' : self.env.ref('account.view_account_payment_form').id,
           'res_model' :'account.payment',
           'view_mode':'form',
           'context' : {
                        'default_partner_id': self.partner_id.id,
                        'default_journal_id': self.env['account.journal'].sudo().search([('code','=', 'CSH1')]).id,
                        'default_payment_type': 'outbound',
                        'default_amount': sum(self.room_line_ids.mapped('deposit')),
                         'default_room_booking_id' : self.id,
                        'default_ref': 'Deposit Booking Out: '+ str(self.name),
                         'create': False
                        },
       }
    def action_deposit_out(self):
       
       self.deposit_out = True
       print(self)
       return{
           'type' : 'ir.actions.act_window',
           'view_id' : self.env.ref('account.view_account_payment_form').id,
           'res_model' :'account.payment',
           'view_mode':'form',
           'context' : {
                        'default_partner_id': self.partner_id.id,
                        'default_journal_id': self.env['account.journal'].sudo().search([('code','=', 'CSH1')]).id,
                        'default_payment_type': 'outbound',
                        'default_amount': sum(self.room_line_ids.mapped('deposit')),
                         'default_room_booking_id' : self.id,
                        'default_ref': 'Deposit Booking Out: '+ str(self.name),
                         'create': False
                        },
       }
    def action_charge(self):
        self.ensure_one()
       
        print(self)
        """Method for creating invoice"""
        journal = self.env['account.journal'].sudo().search([('name','=','CHARGE')]).id
        if not self.room_line_ids:
            raise ValidationError(_("Please Enter Room Details"))
        booking_list = self._compute_amount_untaxed(True)
        if booking_list:
            account_move = self.env["account.move"].create([{
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'hotel_booking_id' : self.id,
                'partner_id': self.partner_id.id,
                'ref': self.name,
                'journal_id': journal,
            }])
           
            self.write({'invoice_status': "invoiced"})
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoices',
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': self.env.ref('account.view_move_form').id,
                'res_id': account_move.id,
                
            }



    def _compute_amount_untaxed(self, flag=False):
        """Compute the total amounts of the Sale Order"""
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
        room_lines = self.room_line_ids
        food_lines = self.food_order_line_ids
        service_lines = self.service_line_ids
        fleet_lines = self.vehicle_line_ids
        event_lines = self.event_line_ids
        booking_list = []
        for loop in self:

            account_move_line = self.env['account.move.line'].search_read(
                domain=[('ref', '=', loop.name),
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
                                'quantity': room.uom_qty,
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
        if food_lines:
            for food in food_lines:
                booking_list.append(self.create_list(food))
            amount_untaxed_food += sum(food_lines.mapped('price_subtotal'))
            amount_taxed_food += sum(food_lines.mapped('price_tax'))
            amount_total_food += sum(food_lines.mapped('price_total'))
        if service_lines:
            for service in service_lines:
                booking_list.append(self.create_list(service))
            amount_untaxed_service += sum(
                service_lines.mapped('price_subtotal'))
            amount_taxed_service += sum(service_lines.mapped('price_tax'))
            amount_total_service += sum(service_lines.mapped('price_total'))
        if fleet_lines:
            for fleet in fleet_lines:
                booking_list.append(self.create_list(fleet))
            amount_untaxed_fleet += sum(fleet_lines.mapped('price_subtotal'))
            amount_taxed_fleet += sum(fleet_lines.mapped('price_tax'))
            amount_total_fleet += sum(fleet_lines.mapped('price_total'))
        if event_lines:
            for event in event_lines:
                booking_list.append(self.create_list(event))
            amount_untaxed_event += sum(event_lines.mapped('price_subtotal'))
            amount_taxed_event += sum(event_lines.mapped('price_tax'))
            amount_total_event += sum(event_lines.mapped('price_total'))
        for rec in self:
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
    
    def action_invoice(self):

        """Method for creating invoice"""
        if not self.room_line_ids:
            raise ValidationError(_("Please Enter Room Details"))
        booking_list = self._compute_amount_untaxed(True)
        if booking_list:
            account_move = self.env["account.move"].create([{
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'hotel_booking_id' : self.id,
                'partner_id': self.partner_id.id,
                'ref': self.name,
            }])
            for rec in booking_list:
                account_move.invoice_line_ids.create([{
                    'name': rec['name'],
                    'quantity': rec['quantity'],
                    'price_unit': rec['price_unit'],
                    'tax_ids': rec['tax_ids'],
                    'move_id': account_move.id,
                    'price_subtotal': rec['quantity'] * rec['price_unit'],
                    'product_type': rec['product_type'],
                }])
            self.write({'invoice_status': "invoiced",
                        'hotel_invoice_id': account_move.id })
            self.invoice_button_visible = True
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

    def action_view_depo(self):
        """Method for Returning invoice View"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Deposit',
            'view_mode': 'tree,form',
            'view_type': 'tree,form',
            'res_model': 'account.payment',
            'domain': [('room_booking_id','=', self.id)],
            'context': "{'create': False}"
        }
    
    def action_done(self):
        """Button action_confirm function"""
        for rec in self.env['account.move'].search(
                [('ref', '=', self.name)]):
            # if rec.payment_state != 'not_paid':
            if rec.state == 'posted' and rec.payment_state !='not_paid':
                self.write({"state": "done"})
                self.is_checkin = False
                if self.room_line_ids:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'type': 'success',
                            'message': "Booking Checked Out Successfully!",
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                    }
            if rec.state == 'draft' and rec.payment_state !='paid':
                self.write({"state": "done"})
                self.is_checkin = False
                if self.room_line_ids:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'type': 'success',
                            'message': "Booking Checked Out Successfully!",
                            'next': {'type': 'ir.actions.act_window_close'},
                        }
                    }
            raise ValidationError(_('Your Invoice is Due for Payment.'))
        self.write({"state": "done"})
