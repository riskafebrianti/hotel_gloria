from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    company_type = fields.Selection(string='Company Type',
        selection=[('person', 'Individual'), ('company', 'Company')],
        compute='_compute_company_type', inverse='_write_company_type', default='person')
    ktp = fields.Char(string='No KTP',store=True,)
    sim = fields.Char(string='No SIM',store=True,)
    # admin = fields.Boolean(string='Admin')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        partners = self.search(['|', '|', ('name', operator, name), ('sim', operator, name), ('ktp', operator, name)])   # here you need to pass the args as per your requirement.
        return partners.name_get()

class HotelAmenity(models.Model):
    _inherit = 'hotel.amenity'

    icon = fields.Image(string="Iconas", 
                        help="Image of the amenity")


    

    