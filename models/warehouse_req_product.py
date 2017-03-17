from odoo import api, fields, models


class WarehouseReqProduct(models.Model):
    _name = 'warehouse.req.product'

    sequence = fields.Integer()
    warehouse_req_id = fields.Many2one(
        comodel_name="warehouse.req",
        index=True,
        ondelete="cascade",
        required=True,
        string="Requirement",
    )
    name = fields.Char(related='product_id.name')
    product_id = fields.Many2one(
        comodel_name="product.template",  # TODO template vs product
        domain="[('purchase_ok', '=', True)]",
        required=True,
    )
    specs = fields.Char()
    on_hand = fields.Float(
        default=lambda self: self.product_id.virtual_available,
        readonly=True,
        store=False,
    )
    requested_qty = fields.Integer(required=True)
    auothorized_qty = fields.Integer()  # readonly if no authorized
    ordered_qty = fields.Integer(readonly=True)
    supplied_qty = fields.Integer(readonly=True)
    suggested_supplier = fields.Many2one(
        comodel_name="res.partner",
        domain="[('supplier', '=', True)]",
    )
