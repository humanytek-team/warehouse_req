from odoo import api, exceptions, fields, models, _


class WarehouseReqProduct(models.Model):
    _name = 'warehouse.req.product'

    sequence = fields.Integer()
    warehouse_req_id = fields.Many2one(
        comodel_name='warehouse.req',
        index=True,
        required=True,
        string=_('Requirement'),
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        required=True,
        string=_('Product'),
    )
    specs = fields.Char()
    on_hand = fields.Float(
        compute='_on_hand',
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
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        required=True,
        string=_('Account analytic'),
    )

    @api.depends('product_id')
    def _on_hand(self):
        for r in self:
            r.on_hand = r.product_id.qty_available

    @api.depends('stock_picking_id')
    def _supplied_qty(self):
        for r in self:
            stock_picking_id = r.stock_picking_id
            operations = stock_picking_id.pack_operation_product_ids
            supplied_qty = sum(operation.qty_done for operation in operations if operation.product_id == r.product_id)
            while True:
                stock_picking_id = stock_picking_id.backorder_id
                if not stock_picking_id:
                    break
                operations = stock_picking_id.pack_operation_product_ids
                supplied_qty = supplied_qty + sum(operation.qty_done for operation in operations if operation.product_id == r.product_id)
            r.supplied_qty = supplied_qty

    @api.constrains('requested_qty')
    def _check_requested_qty_gt_0(self):
            for r in self:
                if r.requested_qty <= 0:
                    raise exceptions.ValidationError(_('The product {} has invalid ordered qty').format(r.product_id.name))
