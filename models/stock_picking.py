from odoo import api, exceptions, fields, models, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        for pick in self:
            warehouse_req_id = self.env['warehouse.req'].search([('name', '=', pick.origin)], limit=1)
            if warehouse_req_id:
                for line in warehouse_req_id.product_ids:
                    if line.stock_picking_id.id == pick.id:
                        account_analytic_id = line.account_analytic_id
                        stock_move_ids = [stock_move.id for stock_move in pick.move_lines]
                        account_move_lines = pick.env['account.move.line'].search([('stock_move_id', 'in', stock_move_ids)])
                        for account_move_line in account_move_lines:
                            if account_move_line.debit > 0 and account_move_line.credit == 0:
                                account_move_line.analytic_account_id = account_analytic_id
        return res
