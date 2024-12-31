from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import pytz
from odoo.exceptions import UserError
from collections import OrderedDict


class RoomBookingTree(models.Model):
    _inherit = 'room.booking'

    ktp = fields.Char(string='KTP', related='partner_id.ktp',)
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
                                 string='Room',
                                 store=True,)
    
    deposit_in = fields.Boolean(string='deposit_in', default=False, compute='_compute_invsb')
    deposit_out = fields.Boolean(string='deposit_out', compute='_compute_invsb', default=False)
    charge = fields.Boolean(string='charge', compute='_compute_invsb', default=False)
    deposit_sisa = fields.Float(string='Deposit',store=True, compute='depoSisa',)
    datepymnt = fields.Date(string='pyshift1', search = '_search_paymnt1', store=False,)
    datepymnt_2 = fields.Date(string='pyshift2', search = '_search_paymnt2', store=False,)
    datepymnt_3 = fields.Date(string='pyshift3', search = '_search_paymnt3', store=False,)
    datesrc = fields.Date(string='shift1', search = '_search_is_expired1', store=False,)
    shift_2 = fields.Date(string='shift2', search = '_search_is_expired2', store=False,)
    shift_3 = fields.Date(string='shift3', search = '_search_is_expired3', store=False,)
    checkin_date = fields.Datetime(string="Check In",
                                   help="Date of Checkin",tracking=True,
                                   default=fields.Datetime.now())
    checkout_date = fields.Datetime(string="Check Out",
                                    help="Date of Checkout", tracking=True,
                                    default=fields.Datetime.now() + timedelta(
                                        hours=23, minutes=59, seconds=59))
    kamar = fields.Char(string='Room', related='room_line_ids.room_id.name')
    status_pembayaran = fields.Char(string='Status Bayar', compute='byr_state')
    chargeee = fields.Char(string='Status Charge',  compute='_chrg_state')

    
    
    # state_paymnt = fields.Char(
    #     string='bayar',store=True, compute='paymnt',
    # )
    # piutang = fields.Char(
    #     string='piutang',store=True,  compute='paymnt',
    # )
  
    
    depo_count = fields.Integer(string='depo_count', compute='_compute_depo_count'
    )
    chrg_count = fields.Integer(string='depo_count', compute='_compute_chrg_count'
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
    
    # @api.depends('chrg_count')
    # def chrg_state(self):
    #     if self.chrg_count:
    #         self.charge = 'CHARGE'

    # def _chrg_state(self):
    #     """Compute the invoice count"""
    #     for record in self:
    #         record.chrg_count = self.env['account.move'].search_count(
    #             [('hotel_booking_id','=', record.id),('journal_id.code','=','CHRG')])

    # @api.depends('chrg_count','chargeee','hotel_invoice_id','state','roomsugest')
    def _chrg_state(self):
        """Compute the invoice count"""
        # if self.chrg_count:
        for dataa in self:
            data_accmovee = self.env['account.move'].sudo().search([('ref','=', dataa.name),('journal_id.name','=', 'CHARGE'),('state','=','posted')])
            # for g in dataa:
            if dataa.chrg_count >= 0:
                if data_accmovee:
                    dataa.chargeee = 'CHARGE'
                else:
                    dataa.chargeee = False
            if dataa.chrg_count == 0:
                dataa.chargeee = False

    # api.depends('chrg_count','chargeee','hotel_invoice_id','state','roomsugest')
    def byr_state(self):
        """Compute the invoice count"""
        for dataa in self:
            # for g in dataa:
            data_accmove = self.env['account.move'].sudo().search([('ref','=', dataa.name),('journal_id.name','!=', 'CHARGE'),('state','=','posted')])
            if len(data_accmove) == 1:
                dataa.status_pembayaran = data_accmove.payment_state
            elif len(data_accmove) > 1:
                # data_accmove.filtered(lambda state: state.state == 'posted')
                dataa.status_pembayaran = data_accmove[-1].payment_state
            else:
                dataa.status_pembayaran = 'Tidak Ada Transaksi'
              
   
    
    @api.onchange('room_line_ids')
    def get_price(self):
        # if self.room_line_ids.checkin_date == False:
        #     self.room_line_ids.checkin_date = self.checkin_date
        
        # if self.room_line_ids.checkout_date == False:
        #     self.room_line_ids.checkout_date = self.checkout_date

        if self.room_line_ids.checkin_date != self.checkin_date:
           self.write({'checkin_date': self.room_line_ids.checkin_date})

        if self.room_line_ids.checkout_date != self.checkout_date:
            self.write({'checkout_date': self.room_line_ids.checkout_date})

    def _compute_invsb(self):
        for record in self:
            data_in = self.env['account.payment'].search(
                [('room_booking_id','=', record.id),('move_id.journal_id.code','!=','CHRG')])
            charge = self.env['account.payment'].search(
                [('room_booking_id','=', record.id),('move_id.journal_id.code','=','CHRG')])
            
            if charge:
                record.charge = True
            if not charge:
                record.charge = False
            for semua_data in data_in:
                if data_in :
                    if semua_data.payment_type == 'inbound':
                        record.deposit_in = True    
                    if semua_data.payment_type == 'outbound':
                        record.deposit_out = True    
                    if not semua_data.payment_type == 'outbound':
                        record.deposit_out = False
                    if not semua_data.payment_type == 'inbound':
                        record.deposit_in= False

            if not data_in:
                record.deposit_in = False
                record.deposit_out = False
            
                print(self)
    

    def _now(self):
        return fields.Datetime.context_timestamp(self, fields.datetime.now()).strftime('%d %B %Y %H-%M-%S')
    
    
    def _name_cust(self):
        for data in self:
            tes = data.partner_id.name
            if len(tes) > 23:
                record = data.partner_id.name[:23] + ' ...'
            if len(tes) <= 23:
                record = data.partner_id.name

        return record
    
    # filter payment shift 1
    def _search_paymnt1(self, operator, value):
        # today = fields.Datetime.context_timestamp(self, datetime.now())
        tes = fields.datetime.now()
        hasil = fields.Datetime.context_timestamp(self, tes)
        shift1_awal =  hasil.replace(hour=7, minute=0, second=0)
        shift1_akhir =  hasil.replace(hour=15, minute=0, second=0)
        
        data = self.env['account.payment'].search([])
        record = []
        for data_waktu in data:
            # date_order = 
            tgl_timestamp = fields.Datetime.context_timestamp(self,  data_waktu.create_date)
            if tgl_timestamp >= shift1_awal and tgl_timestamp <= shift1_akhir:
                array_1 = self.env['room.booking'].sudo().search([('hotel_invoice_id.name','=', data_waktu.ref)])
                for data in array_1:
                    array = record.append(data.id)
        records = self.env['room.booking'].browse(record)
       
        # records = self.env['room.booking'].search([(tgl_timestamp, '>=', todayy)])

        return [('id', 'in', records.ids)]
    

    # filter payment shift 2
    def _search_paymnt2(self, operator, value):
        # today = fields.Datetime.context_timestamp(self, datetime.now())
        tes = fields.datetime.now()
        hasil = fields.Datetime.context_timestamp(self, tes)
        shift1_awal =  hasil.replace(hour=15, minute=0, second=0)
        shift1_akhir =  hasil.replace(hour=23, minute=0, second=0)
        
        data = self.env['account.payment'].search([])
        record = []
        for data_waktu in data:
            # date_order = 
            tgl_timestamp = fields.Datetime.context_timestamp(self,  data_waktu.create_date)
            if tgl_timestamp >= shift1_awal and tgl_timestamp <= shift1_akhir:
                array_1 = self.env['room.booking'].sudo().search([('hotel_invoice_id.name','=', data_waktu.ref)])
                for data in array_1:
                    array = record.append(data.id)
        records = self.env['room.booking'].browse(record)
        # records = self.env['room.booking'].search([(tgl_timestamp, '>=', todayy)])

        return [('id', 'in', records.ids)]
    

    # filter payment shift 3
    def _search_paymnt3(self, operator, value):
        # today = fields.Datetime.context_timestamp(self, datetime.now())
        tes = fields.datetime.now()
        hasil = fields.Datetime.context_timestamp(self, tes)
        shift1_awal =  hasil.replace(hour=23, minute=0, second=0)
        shift1_akhir =  hasil.replace(hour=7, minute=0, second=0)
        
        data = self.env['account.payment'].search([])
        record = []
        for data_waktu in data:
            # date_order = 
            tgl_timestamp = fields.Datetime.context_timestamp(self,  data_waktu.create_date)
            if tgl_timestamp >= shift1_awal and tgl_timestamp <= shift1_akhir:
                array_1 = self.env['room.booking'].sudo().search([('hotel_invoice_id.name','=', data_waktu.ref)])
                for data in array_1:
                    array = record.append(data.id)
        records = self.env['room.booking'].browse(record)
        # records = self.env['room.booking'].search([(tgl_timestamp, '>=', todayy)])

        return [('id', 'in', records.ids)]
    
    # filter shift 1
    def _search_is_expired1(self, operator, value):
        # today = fields.Datetime.context_timestamp(self, datetime.now())
        tes = fields.datetime.now()
        hasil = fields.Datetime.context_timestamp(self, tes)
        shift1_awal =  hasil.replace(hour=7, minute=0, second=0)
        shift1_akhir =  hasil.replace(hour=15, minute=0, second=0)
        
        data = self.env['room.booking'].search([])
        record = []
        for data_waktu in data:
            # date_order = 
            tgl_timestamp = fields.Datetime.context_timestamp(self,  data_waktu.date_order)
            if tgl_timestamp >= shift1_awal and tgl_timestamp <= shift1_akhir:
                array = record.append(data_waktu.id)
        records = self.env['room.booking'].browse(record)
        # records = self.env['room.booking'].search([(tgl_timestamp, '>=', todayy)])

        return [('id', 'in', records.ids)]
    

    # filter shift 2
    def _search_is_expired2 (self, operator, value):
        # today = fields.Datetime.context_timestamp(self, datetime.now())
        tes = fields.datetime.now()
        hasil = fields.Datetime.context_timestamp(self, tes)
        shift1_awal =  hasil.replace(hour=15, minute=0, second=0)
        shift1_akhir =  hasil.replace(hour=23, minute=0, second=0)
        
        data = self.env['room.booking'].search([])
        record = []
        for data_waktu in data:

            tgl_timestamp = fields.Datetime.context_timestamp(self,  data_waktu.date_order)
            if tgl_timestamp >= shift1_awal and tgl_timestamp <= shift1_akhir:
                array = record.append(data_waktu.id)
        records_shift2 = self.env['room.booking'].browse(record)
        # records = self.env['room.booking'].search([(tgl_timestamp, '>=', todayy)])

        return [('id', 'in', records_shift2.ids)]
    
    # filter shift 3
    def _search_is_expired3(self, operator, value):
        # today = fields.Datetime.context_timestamp(self, datetime.now())
        tes = fields.datetime.now()
        hasil = fields.Datetime.context_timestamp(self, tes)
        shift1_awal =  hasil.replace(hour=23, minute=0, second=0)
        shift1_akhir =  hasil.replace(hour=7, minute=0, second=0)
        
        data = self.env['room.booking'].search([])
        record = []
        for data_waktu in data:

            tgl_timestamp = fields.Datetime.context_timestamp(self,  data_waktu.date_order)
            if tgl_timestamp >= shift1_awal and tgl_timestamp <= shift1_akhir:
                array = record.append(data_waktu.id)
        records = self.env['room.booking'].browse(record)
        # records = self.env['room.booking'].search([(tgl_timestamp, '>=', todayy)])

        return [('id', 'in', records.ids)]
    

    def create(self, vals):
        if vals['room_line_ids'] and vals['state'] == 'draft':
            # self.room_line_ids.room_id.write({'draft':True,})
            valsaa = vals['room_line_ids'][0][2]['room_id']
            updatee = self.env['hotel.room'].sudo().search([('id','=', valsaa)])
            updatee.write({'draft' : True})
            return super(RoomBookingTree, self).create(vals)


    # @api.depends('quantity', 'price')
    # def hallo(self):
    #     default=fields.Date.today()
    #     return default
    
    # @api.model
    # def action_filter_by_custom_date(self):
    #     action = self.env.ref('room_booking.room_booking_search').read()[0]
    #     action['context'] = {
    #         'custom_date': fields.Date.today()
    #     }
    #     return action
    
    
    # def get_price_total(self):
    #     tes = datetime.today().replace(hour=7, minute=0, second=0)
    #     return tes
    

    
    def _compute_depo_count(self):
        """Compute the invoice count"""
        for record in self:
            record.depo_count = self.env['account.payment'].search_count(
                [('room_booking_id','=', record.id),('move_id.journal_id.code','!=','CHRG')])
            
    def _compute_chrg_count(self):
        """Compute the invoice count"""
        for record in self:
            record.chrg_count = self.env['account.move'].search_count(
                [('hotel_booking_id','=', record.id),('journal_id.code','=','CHRG')])

    def _compute_invoice_count(self):
        """Compute the invoice count"""
        for record in self:
            record.invoice_count = self.env['account.move'].search_count(
                [('ref', '=', self.name),('journal_id.code','!=','CHRG')])

    
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
    
    # def paid(self):
    #         for a in self:
    #             b = a.env['account.move'].sudo().search([('hotel_booking_id','=',a.id),('move_type','=','out_invoice'),('journal_id.name','!=','CHARGE')]).payment_state
    #             return b
        
    def amount(self):
    
        for z in self:
            c = self.env['account.move'].sudo().search([
                ('ref','=',z.name),
                ('move_type','=','out_invoice'),
                ('payment_state','=','not_paid'),
                ('state','=','posted'),
                ('journal_id.name','!=','CHARGE')])
            if len(c) >=1:
                hasil = sum(line.amount_residual for line in c)
            if not c:
                hasil = 0
        
        return hasil
    
    # def paymnt(self):

    #     for b in self:
    #         a = self.env['account.move'].sudo().search([('hotel_booking_id','=',b.id),('move_type','=','out_invoice'),('journal_id.name','!=','CHARGE')])
    #         for pay in a:
    #             d = self.env['account.move'].sudo().search([('ref','=', pay.name)])
    #             if len(d) >= 1:
    #                 b = sum(line.amount_total for line in d)
    #             if not d: 
    #                 b =  0
    #         return d
#  def _search_is_expired1(self, operator, value):
#         # today = fields.Datetime.context_timestamp(self, datetime.now())
#         tes = fields.datetime.now()
#         hasil = fields.Datetime.context_timestamp(self, tes)
#         shift1_awal =  hasil.replace(hour=7, minute=0, second=0)
#         shift1_akhir =  hasil.replace(hour=15, minute=0, second=0)
        
#         data = self.env['room.booking'].search([])
#         record = []
#         for data_waktu in data:
#             # date_order = 
#             tgl_timestamp = fields.Datetime.context_timestamp(self,  data_waktu.date_order)
#             if tgl_timestamp >= shift1_awal and tgl_timestamp <= shift1_akhir:
#                 array = record.append(data_waktu.id)
#         records = self.env['room.booking'].browse(record)
#         # records = self.env['room.booking'].search([(tgl_timestamp, '>=', todayy)])

#         return [('id', 'in', records.ids)]



        
    def paymnt(self):
        # hasil = fields.datetime.now()
        for b in self:
            a = self.env['account.move'].sudo().search([
                ('ref','=',b.name),
                ('move_type','=','out_invoice'),
                ('state','=','posted'),
                ('journal_id.name','!=','CHARGE'),
                ('payment_state','=','paid'),
                # ('hotel_booking_id.date_order','=', hasil)
                ])
            hasil = b.hotel_invoice_id.date
            if a:
                for pay in a:
                    data = self.env['account.move'].sudo().search([('ref','=', pay.name)])

                if pay.hotel_booking_id.date_order.strftime('%d/%m/%y') != hasil.strftime('%d/%m/%y'):
                    d = 0  # Set d ke 0 jika tanggal order berbeda dengan hasil
                if pay.hotel_booking_id.date_order.strftime('%d/%m/%y') == hasil.strftime('%d/%m/%y'):
                    # Jika tanggal sama, ambil total amount dari transaksi terkait
                    if len(data) >= 1:
                        d = data[-1].amount_total  # Ambil total amount dari elemen terakhir
                    else:
                        d = data.amount_total

            if not a:
                d = 0
            return d
        
    def paymnttotal(self):
        # tgl = fields.datetime.now()
        for b in self:
            a = self.env['account.move'].sudo().search([
               ('ref','=',b.name),
                ('move_type','=','out_invoice'),
                ('journal_id.name','!=','CHARGE'),
                ('payment_state','=','paid')
                ])
            tgl = b.hotel_invoice_id.date
            if a:
                for pay in a:
                    data = self.env['account.move'].sudo().search([('ref','=', pay.name)])

                if pay.hotel_booking_id.date_order.strftime('%d/%m/%y') != tgl.strftime('%d/%m/%y'):
                    hasil = 0  # Set d ke 0 jika tanggal order berbeda dengan hasil
                if pay.hotel_booking_id.date_order.strftime('%d/%m/%y') == tgl.strftime('%d/%m/%y'):
                    # Jika tanggal sama, ambil total amount dari transaksi terkait
                    if len(data) >= 1:
                        hasil= sum(data.mapped('amount_total'))  # Ambil total amount dari elemen terakhir
                    else:
                        hasil= sum(data.mapped('amount_total'))

                    # hasil= sum(data.mapped('amount_total'))
            if not a:
                hasil= 0
                   
                print(self)
            return hasil
        
        # payment pelunasan qwqeb

    def paymntlns(self):
        # hasil = fields.datetime.now()
        for b in self:
            a = self.env['account.move'].sudo().search([
                ('ref','=',b.name),
                ('move_type','=','out_invoice'),
                ('state','=','posted'),
                ('journal_id.name','!=','CHARGE'),
                ('payment_state','=','paid'),
                # ('hotel_booking_id.date_order','=', hasil)
                ])
            hasil = b.hotel_invoice_id.date
            if a:
                for pay in a:
                    data = self.env['account.move'].sudo().search([('ref','=', pay.name)])

                if pay.hotel_booking_id.date_order.strftime('%d/%m/%y') == hasil.strftime('%d/%m/%y'):
                    d = 0  # Set d ke 0 jika tanggal order berbeda dengan hasil
                if pay.hotel_booking_id.date_order.strftime('%d/%m/%y') != hasil.strftime('%d/%m/%y'):
                    # Jika tanggal sama, ambil total amount dari transaksi terkait
                    if len(data) >= 1:
                        d = data[-1].amount_total  # Ambil total amount dari elemen terakhir
                    else:
                        d = data.amount_total

            if not a:
                d = 0
            return d
        
    def paymnttotallns(self):
        # tgl = fields.datetime.now()
        for b in self:
            a = self.env['account.move'].sudo().search([
               ('ref','=',b.name),
                ('move_type','=','out_invoice'),
                ('journal_id.name','!=','CHARGE'),
                ('payment_state','=','paid')
                ])
            tgl = b.hotel_invoice_id.date
            if a:
                for pay in a:
                    data = self.env['account.move'].sudo().search([('ref','=', pay.name)])

                if pay.hotel_booking_id.date_order.strftime('%d/%m/%y') == tgl.strftime('%d/%m/%y'):
                    hasil = 0  # Set d ke 0 jika tanggal order berbeda dengan hasil
                if pay.hotel_booking_id.date_order.strftime('%d/%m/%y') != tgl.strftime('%d/%m/%y'):
                    # Jika tanggal sama, ambil total amount dari transaksi terkait
                    if len(data) >= 1:
                        hasil= sum(data.mapped('amount_total'))  # Ambil total amount dari elemen terakhir
                    else:
                        hasil= sum(data.mapped('amount_total'))

                    # hasil= sum(data.mapped('amount_total'))
            if not a:
                hasil= 0
                   
                print(self)
            return hasil
                
        

  
        
    
    @api.depends('payment_ids.payment_type')
    def depoSisa(self):
        print(self)
        for depo in self:
            depomasuk = depo.env['account.payment'].sudo().search([('room_booking_id','=',self.id),('payment_type','=','inbound')])
            depokeluar = depo.env['account.payment'].sudo().search([('room_booking_id','=',self.id),('payment_type','=','outbound')])
            self.deposit_sisa = depomasuk.amount - depokeluar.amount
    

    def action_deposit_in(self):
        for k in self.room_line_ids:
            if not k.deposit:
                raise ValidationError(
                _("Masukkan Nilai Deposit"))
        
        return{
            'type' : 'ir.actions.act_window',
            'view_id' : self.env.ref('account.view_account_payment_form').id,
            'res_model' :'account.payment',
            'view_mode':'form',
            
            'context' : {
                            'default_partner_id': self.partner_id.id,
                            'default_journal_id': self.env['account.journal'].sudo().search([('code','=', 'CSH1')]).id,
                            'default_amount': sum(k.mapped('deposit')),
                            'default_room_booking_id' : self.id,
                            'default_ref': 'Deposit Booking: '+ str(self.name)
                            }
        }
        # self.deposit_in = True
    
    def action_check_in_ubah(self):
        if self.state == 'check_out':
            self.update({'state': "check_in",
                            })
            for data in self.room_line_ids.room_id:
                data.update({'status': "occupied",
                            })

        
       
    def action_maintenance_request(self):
        """
        Function that handles the maintenance request
        """
        room_list = []
        for rec in self.room_line_ids.room_id.ids:
            room_list.append(rec)
        if room_list:
            room_id = self.env['hotel.room'].search([
                ('id', 'in', room_list)])
            self.env['maintenance.request'].sudo().create({
                'date': fields.Date.today(),
                'state': 'draft',
                'type': 'room',
                'room_maintenance_ids': room_id.ids,
            })
            
            room_id.maintenance = 'Request Maintenance'
            self.maintenance_request_sent = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': "Maintenance Request Sent Successfully",
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        raise ValidationError(_("Please Enter Room Details"))
    
    def action_checkout(self):
        """Button action_heck_out function"""
        self.write({"state": "check_out"})
        for room in self.room_line_ids:
            room.room_id.write({
                'status': 'available',
                'is_room_avail': True
            })
            room.write({'checkout_date': datetime.today()})
        # self.deposit_out = True
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
       
    #    self.deposit_out = True
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
    def action_view_invoices(self):
        """Method for Returning invoice View"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'tree,form',
            'view_type': 'tree,form',
            'res_model': 'account.move',
            'domain': [('ref', '=', self.name),('journal_id.code','!=','CHRG')],
            'context': "{'create': False}"
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
            # for rec in booking_list:
            #     account_move.invoice_line_ids.create([{
            #         'name': rec['name'],
            #         'price_unit': rec['price_unit'],
            #         'tax_ids': rec['tax_ids'],
            #         'move_id': account_move.id,
            #         'price_subtotal': rec['quantity'] * rec['price_unit'],
            #         'product_type': rec['product_type'],
            #     }])
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
        account_move_line = self.env['account.move.line'].search_read(
            domain=[('ref', '=', self.name),
                    ('display_type', '!=', 'payment_term'),
                    ('journal_id.name', '!=', 'CHARGE')],
            fields=['name', 'quantity', 'price_unit', 'product_type'], )
        for rec in account_move_line:
            del rec['id']
        if room_lines:
            amount_untaxed_room += sum(room_lines.mapped('price_subtotal'))
            amount_taxed_room += sum(room_lines.mapped('price_tax'))
            amount_total_room += sum(room_lines.mapped('price_total'))
            for room in room_lines:
                booking_dict = {'name': room.room_id.name,
                                'quantity': room.uom_qty,
                                'price_unit': room.price_unit,
                                "tax_ids": room.tax_ids,
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
                                         "tax_ids": room.tax_ids,
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
                    'name': 'Kamar '+rec['name'],
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
            'domain': [('room_booking_id','=', self.id),('move_id.journal_id.code','!=','CHRG')],
            'context': "{'create': False}"
        }
    
    def action_view_chrg(self):
        """Method for Returning invoice View"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Charge',
            'view_mode': 'tree,form',
            'view_type': 'tree,form',
            'res_model': 'account.move',
            'domain': [('hotel_booking_id','=', self.id),('journal_id.code','=','CHRG')],
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
            raise ValidationError(_('Invoice Belum terbayar.'))
        self.write({"state": "done"})

    def action_checkin(self):
        """
        @param self: object pointer
        """
        if not self.room_line_ids:
            raise ValidationError(_("Please Enter Room Details"))
        else:
            for room in self.room_line_ids:
                room.room_id.write({
                    'status': 'occupied',
                     'draft': False
                })
                room.room_id.is_room_avail = False
            self.write({"state": "check_in"})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': "Booking Checked In Successfully!",
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
    def action_reserve(self):
        """Button Reserve Function"""
        if self.state == 'reserved':
            message = _("Room Already Reserved.")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': message,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        if self.room_line_ids:
            for room in self.room_line_ids:
                room.room_id.write({
                    'status': 'reserved',
                     'draft': False
                })
                room.room_id.is_room_avail = False
            self.write({"state": "reserved"})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': "Rooms reserved Successfully!",
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        raise ValidationError(_("Please Enter Room Details"))

    def report_charge(self):
        # loop = self.filtered(lambda pay: pay.move_type == 'out_invoice')
        list_charge = []
        for ini in self:

            print(self)
            data = self.env['account.move.line'].search([('move_id.hotel_booking_id', '=', ini.id),('move_id.journal_id.name','=','CHARGE')]).filtered(lambda pay: pay.product_id and pay.move_id.state =='posted')
            # data = self.env['account.move'].search([('hotel_booking_id', '=', ini.id),('journal_id.name','=','CHARGE')])
            for dataa in data:

            # data = self.env['account.move'].search([('hotel_booking_id', '=', ini.id),('journal_id.name','=','CHARGE')]).line_ids
                list_charge.append(dataa)
            print(self)
        return list(list_charge)