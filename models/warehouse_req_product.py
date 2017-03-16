from odoo import api, fields, models


class WarehouseReqProduct(models.Model):
    _name = 'warehouse.req.product'

    warehouse_req_id = fields.Many2one(
        comodel_name="warehouse.req",
    )
    product_id = fields.Many2one(
        comodel_name="product.template",  # TODO template vs product
        domain="[('purchase_ok', '=', True)]",
        required=True,
    )
    # description  # TODO need?
    specs = fields.Text()
    # on_hand  # TODO need?
    requested_qty = fields.Integer(required=True)
    auothorized_qty = fields.Integer()  # readonly if no authorized
    ordered_qty = fields.Integer(readonly=True)
    supplied_qty = fields.Integer(readonly=True)
    suggested_supplier = fields.Many2one(
        comodel_name="res.partner",
        domain="[('supplier', '=', True)]",
    )
