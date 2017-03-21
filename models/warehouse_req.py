from odoo import api, exceptions, fields, models, _

# TODO Check fields required


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
    purchase_required = fields.Boolean(compute='_purchase_required')
    date_requested = fields.Date(
        default=fields.Date.today,
        readonly=True,
        string=_('Date of Request'),
    )
    date_required = fields.Date()
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
            ('minimal', _('Minimal Supplieres')),
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
            # TODO verify status
        ]
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
    supplied_products_qty = field.Float(
        compute='_supplied_products_qty',
        store=False,
    )

    def _purchase_required(self):
        pass  # TODO

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

    @api.multi
    def action_approve(self):
        self.state = 'approved'

    @api.multi
    def action_done(self):
        self.state = 'self'

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('warehouse.req')
        return super(WarehouseReq, self).create(vals)
