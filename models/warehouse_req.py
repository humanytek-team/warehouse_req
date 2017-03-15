from odoo import api, fields, models

# TODO Check fields required


class WarehouseReq(models.Model):
    _name = 'warehouse.req'

    name = fields.Char(index=True, string='Folio', readonly=True)  # TODO autoincrement
    warehouse = fields.Many2one(
        comodel_name='stock.warehouse',
        required=True,
    )
    purchase_required = fields.Boolean(compute='_purchase_required')
    date_request = fields.Date(
        default=fields.Date.today,
        readonly=True,
        string='Date of Request',
    )
    date_required = fields.Date()  # TODO check date_required >= date_request
    reason = fields.Selection(
        selection=[
            ('production', 'Production'),
            ('stock_cs', 'Stock CS'),
            ('loan', 'Loan'),
            ('warranty', 'Warranty'),
            ('sale', 'Sale'),
            ('reparation', 'Reparation'),
            ('replacement', 'Replacement'),
            ('internal', 'Internal Use'),
            ('integration', 'Integration'),
            ('minimal', 'Minimal Supplieres'),
        ],
        required=True,
    )
    reference_type = fields.Selection(
        selection=[
            ('support', 'Support'),
            ('kickoff', 'KickOff'),
            ('project', 'Project'),
            ('others', 'Others'),
            ('bill', 'Bill of Materials'),
        ],
    )
    reference_folio = fields.Integer()
    claimant_id = fields.Many2one(
        comodel_name='res.users',
        # default= # TODO current user
        readonly=True,
        required=True,
        string='Claimant',
    )
    state = fields.Selection(
        selection=[
            ('required', 'Required'),
            ('approved', 'Approved'),
            # TODO
        ]
    )
    shipping_type = fields.Selection(
        selection=[
            ('next', 'Next day'),
            ('other', 'Other'),
        ],
    )
    client_id = fields.Many2one(
        comodel_name="res.partner",
        domain="[('customer', '=', True)]",
        string='Client',
    )
    deliver_to = fields.Char()  # TODO field type
    deliver_address = fields.Char()  # TODO field type
    product_ids = fields.One2many(
        comodel_name='warehouse.req.product',
        inverse_name='warehouse_req_id',
        string='Products',
    )

    def _purchase_required(self):
        pass  # TODO
