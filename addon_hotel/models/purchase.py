from odoo import models, fields, api, _
from odoo.exceptions import UserError

class Purchase(models.Model):
    _inherit = 'purchase.order'

    
    deskripsi = fields.Text(
        string='Deskripsi',
    )
    

    