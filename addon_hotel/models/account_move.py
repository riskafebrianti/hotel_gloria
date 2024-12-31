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
    deskripsi = fields.Text(
        string='Deskripsi',
    )
    
    @api.onchange('invoice_line_ids')
    def get_name(self):
        isiqty = []
        for a in self.invoice_line_ids:
            qty = int(a.quantity)
            uom = a.product_id.product_tmpl_id.uom_id.name
            name = a.name
            subtotal = '{0:,.0f}'.format(a.price_subtotal)
            isiqty.append(f"Pembelian {qty} {uom} {name} @Rp.{subtotal} ")
            self.deskripsi = ', '.join(map(str, isiqty))+ ", ".join([f"({vendor.partner_id.name})" for vendor in a.move_id])
            # subtotal = int(a.price_subtotal)
            # vendor = a.order_id.partner_id.name
            # combined_names = ', '.join(map(str, isiqty))
            # combined_names =  isiqty
    
    
    def action_post(self):
        moves_with_payments = self.filtered('payment_id')
        other_moves = self - moves_with_payments
        if moves_with_payments:
            moves_with_payments.payment_id.action_post()
        if other_moves:
            other_moves._post(soft=False)
            if self.journal_id.name == 'CHARGE':
                for record_line in self.line_ids:
                    if record_line.product_id.product_tmpl_id.type=='product':
                        tes = self.env['stock.scrap'].sudo().create({
                        'product_id':record_line.product_id.id,
                        'origin': record_line.move_id.name,
                        'scrap_qty':record_line.quantity
                        })
                        print(self)
                        return tes.action_validate()
        return False
    
    def _now(self):
        return fields.Datetime.context_timestamp(self, fields.datetime.now()).strftime('%d %B %Y %H-%M-%S')
    
    def nama(self):
        loop = self.filtered(lambda pay: pay.move_type == 'out_invoice' and pay.state == 'posted' and pay.payment_state == 'paid')
        data_kamar = {}
        
        for a in loop:
            datanya = a.line_ids.filtered(lambda pay: pay.display_type == 'product')
            for z in datanya:
                if z.name in data_kamar:
                    data_kamar[z.name][0] = data_kamar[z.name][0] + z.price_subtotal
                    data_kamar[z.name][1] = data_kamar[z.name][1] + z.price_total
                else:
                    room= z.name
                    amountnya =z.price_subtotal
                    amount =z.price_total
                    # testing = (room,amountnya,amount)
                    data_kamar[room]=[amountnya,amount]
        hasil = sorted(list(data_kamar.items()))
        # print(data_kamar)
        
        return hasil
            
        # result = {}
        # for card, value, vol in data_kamar:
        #     if card in result:
        #         result[card]['total_value'] += result.get('total_value', value)
        #         result[card]['amount'] += result.get('amount', vol)
        #     else:
        #         total = result.get(card, 0) + value
        #         total1 = result.get(card, 0) + vol
        #     # total1 = result.get(card, 0) + vol
        #     # totall =list(total)vol
        #     # result[card] = total
        #     print(self)
        #     result[card] = {
        #         "total_value": total,
        #         "amount":  total1
        #     }
        #     result[card]['total_value'] += result.get('total_value', value)
        #     result[card]['amount'] += result.get('amount', vol)
        #     print(self)
        # # hasil = list(data_kamar.items())
        
        # # return hasil

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



    
   
    class moveLine(models.Model):
        _inherit = 'account.move.line'

        @api.onchange('product_id')
        def ganti(self):
            if self.move_id.journal_id.name == 'CHARGE':
                data = self.env['room.booking'].search([('name', '=', self.move_id.ref)]).room_line_ids.room_id.name
                for record in self:
                    if record.product_id:
                        record.name = "Kamar "+ data + " "+record.product_id.name
           
        
                
            
   
    