from odoo import models, fields, api
from odoo import _


class WarehouseReqExt(models.Model):
    _inherit = "warehouse.req"

    product_type_req = fields.Selection(
	   selection=[
            ('new', _('New')),
            ('repaired', _('Repaired')),
        ],
        required=True,
        default='new',
	    help=_("Products types to require"),
	)
    
