from odoo import models, fields, api, _
from odoo.exceptions import UserError

class eminitas(models.Model):
    _inherit = 'hotel.amenity'

    
    icon = fields.Image(string="Icon", required=False,
                        help="Image of the amenity")

    
    

    