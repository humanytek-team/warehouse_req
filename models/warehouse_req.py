from odoo import api, fields, models

# TODO Check fields required


class WarehouseReq(models.Model):
    _name = 'warehouse.req'

    folio = fields.Integer(required=True)
    warehouse = fields.Many2one(
        comodel_name="stock.warehouse",
        # ondelete=  # TODO
        # default=  # TODO
    )
    purchase_required = fields.Boolean(compute='_purchase_required')
    date_request = fields.Date(
        string="Dato fo Request",
        default=fields.Date.today,
        readonly=True,
    )
    date_required = fields.Date()  # TODO check date_required >= date_request
    reason = fields.Selection(
        selection=[
            # TODO
        ],
    )
    reference_type = fields.Selection(
        selection=[
            # TODO
        ],
    )
    reference_folio = fields.Integer()
    claimant_id = fields.Many2one(
        comodel_name="res.users",
        # default= # TODO current user
        # ondelete=  # TODO
        readonly=True,
        required=True,
    )
    state = fields.Selection(
        selection=[
            # TODO
        ]
    )
    shipping_type = fields.Selection(
        selection=[
            # TODO
        ],
    )
    client_id = fields.Many2one(
        string="Client",
        comodel_name="res.partner",
        domain="[('customer', '=', True)]",
        # ondelete=  # TODO
    )
    # deliver_to = fields.  # TODO field type
    # deliver_address = fields.  # TODO field type
    products_ids = fields.Many2many(
        string="Field name",
        comodel_name="warehouse.req.product",
    )

    def _purchase_required(self):
        pass  # TODO
