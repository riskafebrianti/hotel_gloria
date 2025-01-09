from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class Maintenance(models.Model):
    _inherit = 'maintenance.request'

    kerusakan_berat = fields.Boolean(string='Kerusakan Berat', 
                                     help="Centang jika jenis maintenance berat maka FO tidak akan bisa membuat reservasi atas kamar ini")
    catatan = fields.Char(string='Note')


    def action_assign_team(self):
        """Button action for changing the state to team_leader_approve"""
        if self.team_id:
            self.state = 'team_leader_approve'
            self.room_maintenance_ids.maintenance= 'Request Maintenance'
        else:
            raise ValidationError(
                _("Please assign a Team"))
        
    def action_assign_user(self):
        """Button action for changing the state to pending"""
        # if self.assigned_user_id:
        self.state = 'pending'
        

        # else:
        #     raise ValidationError(
        #         _("Please assign a User"))

    def action_start(self):
        """Button action for changing the state to ongoing"""
        self.state = 'ongoing'
        self.room_maintenance_ids.maintenance= 'Ongoing Maintenance'

    def action_support(self):
        """Button action for changing the state to support"""
        if self.support_reason:
            self.state = 'support'
            self.room_maintenance_ids.maintenance= 'Need Support Maintenance'
        else:
            raise ValidationError(_('Please enter the reason'))
        
    def action_cancel(self):
        """Button action for changing the state to cancel"""
        self.state = 'cancel'
        self.room_maintenance_ids.maintenance = None

    def action_complete(self):
        """Button action for changing the state to verify"""
        if self.remarks:
            self.state = 'verify'
            self.room_maintenance_ids.maintenance= 'Verify Maintenance'
        else:
            raise ValidationError(_('Please Add remark'))

    def action_assign_support(self):
        """Button action for changing the state to ongoing"""
        if self.support_team_ids:
            self.state = 'ongoing'
        else:
            raise ValidationError(_('Please choose support'))

    def action_verify(self):
        """Button action for changing the state to done"""
        self.state = 'done'
        self.room_maintenance_ids.maintenance= 'Done Maintenance'
        if self.vehicle_maintenance_id:
            self.vehicle_maintenance_id.status = 'available'