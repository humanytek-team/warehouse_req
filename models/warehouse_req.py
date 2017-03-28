from odoo import api, exceptions, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError


class WarehouseReq(models.Model):
    _name = 'warehouse.req'

    name = fields.Char(
        copy=False,
        default=lambda self: _('New'),
        index=True,
        string=_('Folio'),
        readonly=True,
        required=True,
    )
    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        required=True,
        string=_('Warehouse'),
    )
    purchase_required = fields.Boolean(
        compute='_purchase_required',
        store=False,
    )
    date_requested = fields.Date(
        default=fields.Date.today,
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
    reference_folio = fields.Integer(
        string=_('Reference'),
    )
    claimant_id = fields.Many2one(
        comodel_name='res.users',
        default=lambda self: self.env.uid,
        readonly=True,
        required=True,
        string=_('Claimant'),
    )
    state = fields.Selection(
        selection=[
            ('draft', _('Draft')),
            ('required', _('Required')),
            ('approved', _('Approved')),
            ('done', _('Done')),
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
        store=False,
        string=_('# Items'),
    )
    supplied_products_qty = fields.Float(  # TODO use the stock_picking_id status instead
        compute='_supplied_products_qty',
        store=False,
    )
    purchase_order_id = fields.Many2one(
        comodel_name='purchase.order',
        readonly=True,
        string='Purchase order',
    )
    stock_picking_id = fields.Many2one(
        comodel_name='stock.picking',
        readonly=True,
        string='Stock picking',
    )

    @api.depends('product_ids')
    def _purchase_required(self):
        for r in self:
            for p in r.product_ids:
                if p.on_hand < p.requested_qty:
                    r.purchase_required = True
                    break
            else:
                r.purchase_required = False

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
        if len(self.product_ids) > 0:
            self.state = 'required'
        else:
            raise exceptions.ValidationError(_('Product lines needed'))

    @api.multi
    def action_approve(self):
        if self.env.uid != SUPERUSER_ID and self.env.uid == self.claimant_id.id:
            raise exceptions.ValidationError(_('You can not approve your own requirements'))

        picking_type_id = self.env['stock.picking.type'].browse(9)  # FIXME magic numbers?
        stock_picking_dict = {
            'location_id': self.warehouse_id.id,
            'location_dest_id': self.env['stock.warehouse']._get_partner_locations()[1].id,  # FIXME magic numbers?
            'min_date': self.date_required,
            'origin': self.name,
            'partner_id': self.product_ids[0].product_id.seller_ids[0].name.id,  # FIXME magic numbers?
            'picking_type_id': picking_type_id.id,
        }
        self.stock_picking_id = self.env['stock.picking'].create(stock_picking_dict)
        for p in self.product_ids:
            stock_move_dict = {
                'location_id': self.warehouse_id.id,
                'location_dest_id': self.env['stock.warehouse']._get_partner_locations()[1].id,  # FIXME magic numbers?
                'name': p.product_id.name,
                'origin': self.name,
                'picking_id': self.stock_picking_id.id,
                'price_unit': p.product_id.list_price,
                'product_id': p.product_id.id,
                'product_uom': p.product_id.uom_po_id.id or p.product_id.uom_id.id,
                'product_uom_qty': p.requested_qty,
            }
            self.env['stock.move'].create(stock_move_dict)

        if self.purchase_required:
            purchase_order_dict = {
                'date_planned': self.date_required,
                'name': 'New',
                'partner_id': self.product_ids[0].product_id.seller_ids[0].name.id,  # FIXME magic numbers?
                'origin': self.name,
            }
            self.purchase_order_id = self.env['purchase.order'].create(purchase_order_dict)

            for p in self.product_ids:
                if self.purchase_required:
                    if p.on_hand < p.requested_qty:
                        p.ordered_qty = p.requested_qty - p.on_hand
                        purchase_order_line_dict = {
                            'date_planned': self.date_required,
                            'name': p.product_id.name,
                            'order_id': self.purchase_order_id.id,
                            'price_unit': p.product_id.list_price,
                            'product_id': p.product_id.id,
                            'product_qty': p.ordered_qty,
                            'product_uom': p.product_id.uom_po_id.id or p.product_id.uom_id.id,
                        }
                        self.env['purchase.order.line'].create(purchase_order_line_dict)
        self.state = 'approved'

    @api.multi
    def action_done(self):
        self.state = 'done'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('warehouse.req')
        return super(WarehouseReq, self).create(vals)
