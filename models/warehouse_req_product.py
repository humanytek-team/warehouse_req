from odoo import api, fields, models, _


class WarehouseReqProduct(models.Model):
    _name = 'warehouse.req.product'

    sequence = fields.Integer()
    warehouse_req_id = fields.Many2one(
        comodel_name='warehouse.req',
        index=True,
        ondelete='cascade',
        required=True,
        string=_('Requirement'),
    )
    name = fields.Char(
        related='product_id.name',
        string=_('Description'),
    )
    product_id = fields.Many2one(
        comodel_name='product.template',
        domain="[('purchase_ok', '=', True)]",
        required=True,
        string=_('Product'),
    )
    specs = fields.Char()
    on_hand = fields.Float(
        default=lambda self: self.product_id.virtual_available,
        readonly=True,
        store=False,
    )
    requested_qty = fields.Integer(
        required=True,
        string=_('Requested Qty'),
    )
    ordered_qty = fields.Integer(
        readonly=True,
        string=_('Ordered Qty'),
    )
    supplied_qty = fields.Integer(
        readonly=True,
        string=_('Supplied Qty'),
    )
    suggested_supplier = fields.Many2one(
        comodel_name='res.partner',
        domain="[('supplier', '=', True)]",
    )
