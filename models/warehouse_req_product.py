from odoo import api, fields, models, _


class WarehouseReqProduct(models.Model):
    _name = 'warehouse.req.product'

    sequence = fields.Integer()
    warehouse_req_id = fields.Many2one(
        comodel_name='warehouse.req',
        index=True,
        required=True,
        string=_('Requirement'),
    )
    name = fields.Char(
        readonly=True,
        related='product_id.name',
        store=False,
        string=_('Description'),
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        required=True,
        string=_('Product'),
    )
    specs = fields.Char()
    on_hand = fields.Float(
        compute="_on_hand",
        readonly=True,
        store=False,
    )
    requested_qty = fields.Float(
        required=True,
        string=_('Requested Qty'),
    )
    ordered_qty = fields.Float(
        string=_('Ordered Qty'),
    )
    supplied_qty = fields.Float(
        compute='_supplied_qty',
        readonly=True,
        store=False,
        string=_('Supplied Qty'),
    )
    suggested_supplier = fields.Many2one(
        comodel_name='res.partner',
        domain="[('supplier', '=', True)]",
    )
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        readonly=True,
        string='Purchase order',
    )
    src_location_id = fields.Many2one(
        comodel_name='stock.location',
        string=_('Src location'),
    )
    stock_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        readonly=True,
        string=_('Stock picking'),
    )
    state = fields.Selection(
        related='warehouse_req_id.state',
        store=False,
    )
    picked = fields.Boolean(
        related='warehouse_req_id.picked',
        store=False,
    )

    @api.depends('product_id')
    def _on_hand(self):
        for r in self:
            r.on_hand = r.product_id.qty_available

    @api.depends('stock_picking_id')
    def _supplied_qty(self):
        for r in self:
            operations = r.stock_picking_id.pack_operation_product_ids
            r.supplied_qty = sum(operation.qty_done for operation in operations if operation.product_id == r.product_id)
