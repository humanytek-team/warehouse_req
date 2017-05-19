# -*- coding: utf-8 -*-
from odoo import api, exceptions, fields, models, _, SUPERUSER_ID

approver_string = u"Requerimientos de almacén / Autorizador / "
claimant_string = u"Requerimientos de almacén / Solicitante / "


class WarehouseReq(models.Model):
    _name = 'warehouse.req'
    _inherit = 'mail.thread'

    name = fields.Char(
        copy=False,
        default=lambda self: _('New'),
        index=True,
        string=_('Folio'),
        readonly=True,
        required=True,
    )
    dest_location_id = fields.Many2one(
        comodel_name='stock.location',
        string=_('Location Dest'),
    )
    date_requested = fields.Date(
        default=fields.Date.context_today,
        readonly=True,
        string=_('Date of Request'),
    )
    date_required = fields.Date(
        required=True,
    )
    reason = fields.Selection(
        selection=[
            ('production', _('Production')),
            ('stock_cs', _('Stock CS')),
            ('loan', _('Loan')),
            ('warranty', _('Warranty')),
            ('sale', _('Sale')),
            ('reparation', _('Reparation')),
            ('replacement', _('Replacement')),
            ('internal', _('Internal Use')),
            ('integration', _('Integration')),
            ('minimal', _('Minimal Suppliers')),
        ],
        required=True,
    )
    reference_type = fields.Selection(
        selection=[
            ('support', _('Support')),
            ('kickoff', _('KickOff')),
            ('project', _('Project')),
            ('others', _('Others')),
            ('bill', _('Bill of Materials')),
        ],
    )
    reference_folio = fields.Char(
        string=_('Reference'),
    )
    claimant_id = fields.Many2one(
        comodel_name='res.users',
        default=lambda self: self.env.uid,
        readonly=True,
        required=True,
        string=_('Claimant'),
    )
    approver_id = fields.Many2one(
        comodel_name='res.users',
        readonly=True,
        string=_('Approver'),
    )
    state = fields.Selection(
        selection=[
            ('draft', _('Draft')),
            ('required', _('Required')),
            ('approved', _('Approved')),
            ('partial_supplied', _('Partial Supplied')),
            ('done', _('Done')),
            ('cancel', _('Cancelled')),
        ],
        default='draft',
    )
    shipping_type = fields.Selection(
        selection=[
            ('next', _('Next day')),
            ('other', _('Other')),
        ],
    )
    client_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('customer', '=', True)]",
        string=_('Client'),
    )
    deliver_to = fields.Char()
    deliver_address = fields.Char()
    product_ids = fields.One2many(
        comodel_name='warehouse.req.product',
        inverse_name='warehouse_req_id',
        string=_('Products'),
    )
    requested_products_qty = fields.Float(
        compute='_requested_products_qty',
        string=_('# Items'),
    )
    supplied_products_qty = fields.Float(
        compute='_supplied_products_qty',
    )
    ordered = fields.Boolean(
        default=False
    )
    picked = fields.Boolean(
        default=False
    )
    picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type',
        string=_('Picking type'),
    )

    @api.multi
    def check_areas(self):
        approver_areas = {group.name[len(approver_string):] for group in self.env.user.groups_id if group.name[:len(approver_string)] == approver_string}
        claimant_areas = {group.name[len(claimant_string):] for group in self.env['res.users'].browse(self.claimant_id.id).groups_id if group.name[:len(claimant_string)] == claimant_string}
        if len(claimant_areas & approver_areas):
            self.action_approve()
        else:
            raise exceptions.ValidationError(_('Only can approve requirements from your areas'))

    @api.depends('product_ids')
    def _requested_products_qty(self):
        for r in self:
            r.requested_products_qty = sum(p.requested_qty for p in r.product_ids)

    @api.depends('product_ids')
    def _supplied_products_qty(self):
        for r in self:
            r.supplied_products_qty = sum(p.supplied_qty for p in r.product_ids)

    @api.constrains('date_required')
    def _check_date_required_ge_date_requested(self):
        for r in self:
            if r.date_required and r.date_required < r.date_requested:
                raise exceptions.ValidationError(_('The date of requirement cannot be lower than the date of requestment'))

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_require(self):
        self.state = 'required'

    @api.constrains('product_ids')
    def _check_product_ids_len_ne_0(self):
        for r in self:
            if len(r.product_ids) == 0:
                raise exceptions.ValidationError(_('Product lines needed'))

    @api.multi
    def action_approve(self):
        if self.env.uid != SUPERUSER_ID and self.env.uid == self.claimant_id.id:
            raise exceptions.ValidationError(_('You can not approve your own requirements'))
        self.approver_id = lambda self: self.env.uid
        self.state = 'approved'

    @api.multi
    def action_check_state(self):
        if self.state == 'approved' or self.state == 'partial_supplied':
            for product in self.product_ids:
                while True:
                    temp = product.stock_picking_id
                    product.stock_picking_id = self.env['stock.picking'].search([('backorder_id', '=', product.stock_picking_id.id)]) or product.stock_picking_id
                    if temp == product.stock_picking_id:
                        break
            if self.supplied_products_qty > 0:
                if self.supplied_products_qty < self.requested_products_qty:
                    self.action_partial_supply()
                else:
                    self.action_done()

    @api.multi
    def action_partial_supply(self):
        self.state = 'partial_supplied'

    @api.multi
    def action_done(self):
        for p in self.product_ids:
            if not p.stock_picking_id:
                raise exceptions.ValidationError(_('The product {} has no SP').format(p.product_id.name))
            elif p.stock_picking_id.state != 'done':
                raise exceptions.ValidationError(_('The SP {} is not done').format(p.stock_picking_id.name))
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

    @api.multi
    def generate_purchase_orders(self):
        suppliers = {}
        for p in self.product_ids:
            if p.product_id.seller_ids and p.product_id.seller_ids[0]:
                suppliers[p.product_id.seller_ids[0].name.id] = ''
            else:
                raise exceptions.ValidationError(_('The product {} has no supplier').format(p.product_id.name))
            if p.ordered_qty < 0:
                raise exceptions.ValidationError(_('The product {} has invalid ordered qty').format(p.product_id.name))
            if p.on_hand + p.ordered_qty < p.requested_qty:
                raise exceptions.ValidationError(_('The product {} has no enough stock').format(p.product_id.name))
        for k, v in suppliers.iteritems():
            purchase_order_dict = {
                'date_planned': self.date_required,
                'name': 'New',
                'partner_id': k,
                'origin': self.name,
            }
            suppliers[k] = self.env['purchase.order'].create(purchase_order_dict)
        for p in self.product_ids:
            if p.ordered_qty == 0:
                continue
            p.purchase_order_id = suppliers[p.product_id.seller_ids[0].name.id].id
            purchase_order_line_dict = {
                'date_planned': self.date_required,
                'account_analytic_id': p.account_analytic_id and p.account_analytic_id.id or False,
                'name': p.product_id.name,
                'order_id': suppliers[p.product_id.seller_ids[0].name.id].id,
                'price_unit': p.product_id.seller_ids[0].price,
                'product_id': p.product_id.id,
                'product_qty': p.ordered_qty,
                'product_uom': p.product_id.uom_po_id.id or p.product_id.uom_id.id,
            }
            purchase_order_line = self.env['purchase.order.line'].create(purchase_order_line_dict)
            purchase_order_line.taxes_id = p.product_id.supplier_taxes_id
            p.purchase_order_id.fiscal_position_id = p.product_id.seller_ids[0].name.property_account_position_id.id
            p.purchase_order_id.currency_id = p.product_id.seller_ids[0].name.property_purchase_currency_id
        self.ordered = True

    @api.multi
    def generate_stock_picks(self):
        for p in self.product_ids:
            if not (p.product_id.seller_ids and p.product_id.seller_ids[0]):
                raise exceptions.ValidationError(_('The product {} has no supplier').format(p.product_id.name))
        for p in self.product_ids:
            stock_picking_dict = {
                'location_id': p.src_location_id.id,
                'location_dest_id': self.dest_location_id.id,
                'min_date': self.date_required,
                'origin': self.name,
                'partner_id': p.product_id.seller_ids[0].name.id,
                'picking_type_id': self.picking_type_id.id,
            }
            p.stock_picking_id = self.env['stock.picking'].create(stock_picking_dict)
            stock_move_dict = {
                'location_id': p.src_location_id.id,
                'location_dest_id': self.dest_location_id.id,
                'name': p.product_id.name,
                'origin': self.name,
                'picking_id': p.stock_picking_id.id,
                'price_unit': p.product_id.list_price,
                'product_id': p.product_id.id,
                'product_uom': p.product_id.uom_po_id.id or p.product_id.uom_id.id,
                'product_uom_qty': p.requested_qty,
            }
            self.env['stock.move'].create(stock_move_dict)
        self.picked = True

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('warehouse.req')
        return super(WarehouseReq, self).create(vals)
