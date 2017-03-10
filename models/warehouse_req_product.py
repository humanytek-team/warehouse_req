from odoo import api, fields, models


class WarehouseReqProduct(models.Model):
    _name = 'warehouse.req.product'

    product_id = fields.Many2one(
        comodel_name="product.template",  # TODO template vs product
        domain="[('purchase_ok', '=', True)]",
        required=True,
    )
    # description  # TODO need?
    specs = fields.Text()
    # on_hand  # TODO need?
    requested_qty = fields.Integer()
    auothorized_qty = fields.Integer()  # readonly if no authorized
    ordered_qty = fields.Integer(readonly=True)
    supplied_qty = fields.Integer(readonly=True)
    # inventory_notes  # TODO ??
    suggested_supplier = fields.Many2one(
        comodel_name="res.partner",
        domain="[('supplier', '=', True)]",
    )
