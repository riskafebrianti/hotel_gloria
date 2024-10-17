from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    room_booking_id = fields.Many2one('room.booking',
                                       store=True,
                                    string="Booking Reference",
                                    readonly=True, help="Choose the Booking"
                                                        "Reference")
    
    def _create_paired_internal_transfer_payment(self):
        ''' When an internal transfer is posted, a paired payment is created
        with opposite payment_type and swapped journal_id & destination_journal_id.
        Both payments liquidity transfer lines are then reconciled.
        '''
        for payment in self:

            paired_payment = payment.copy({
                'journal_id': payment.destination_journal_id.id,
                'destination_journal_id': payment.journal_id.id,
                'payment_type': payment.payment_type == 'outbound' and 'inbound' or 'outbound',
                'move_id': None,
                'ref': payment.ref,
                'hotel_booking_id': payment.room_booking_id,
                'paired_internal_transfer_payment_id': payment.id,
                'date': payment.date,
            })
            paired_payment.move_id._post(soft=False)
            payment.paired_internal_transfer_payment_id = paired_payment
            body = _("This payment has been created from:") + payment._get_html_link()
            paired_payment.message_post(body=body)
            body = _("A second payment has been created:") + paired_payment._get_html_link()
            payment.message_post(body=body)

            lines = (payment.move_id.line_ids + paired_payment.move_id.line_ids).filtered(
                lambda l: l.account_id == payment.destination_account_id and not l.reconciled)
            lines.reconcile()
        
    def action_post(self):
        ''' draft -> posted '''
        # Do not allow to post if the account is required but not trusted
        for payment in self:
            if payment.require_partner_bank_account and not payment.partner_bank_id.allow_out_payment:
                raise UserError(_('To record payments with %s, the recipient bank account must be manually validated. You should go on the partner bank account in order to validate it.', self.payment_method_line_id.name))

        self.move_id._post(soft=False)
        
        if self.room_booking_id:
            self.move_id.hotel_booking_id = self.room_booking_id

        self.filtered(
            lambda pay: pay.is_internal_transfer and not pay.paired_internal_transfer_payment_id
        )._create_paired_internal_transfer_payment()

    
    def periode(self):
        print(self)
        per = []
        for a in self:
            per.append(a.date_order)
        return per[0]

    
