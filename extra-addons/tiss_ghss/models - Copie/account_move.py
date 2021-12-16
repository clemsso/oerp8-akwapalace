# -*- coding: utf-8 -*-
from openerp import api, fields, models
import openerp.addons.decimal_precision as dp


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    project_id = fields.Many2one('hr.contract.project.template', 'Project/Contract')

    # @api.model
    # def create(self, vals):
        # if vals.get('move_id', False):
            # move = self.env['account.move'].browse(vals['move_id'])
            # if move.project_id:
                # vals['project_id'] = move.project_id.id
        # _super = super(AccountMoveLine, self)
        # return _super.create(vals)

    # @api.multi
    # @api.constrains('project_id', 'company_id')
    # def _check_company_operating_unit(self):
        # for rec in self:
            # if (rec.company_id and rec.project_id and rec.company_id !=
                    # rec.project_id.company_id):
                # raise UserError(_('Configuration error!\nThe Company in the'
                                  # ' Move Line and in the Operating Unit must '
                                  # 'be the same.'))

    # @api.multi
    # @api.constrains('project_id', 'move_id')
    # def _check_move_project_id(self):
        # for rec in self:
            # if (rec.move_id and rec.move_id.project_id and
                # rec.project_id and rec.move_id.project_id !=
                    # rec.project_id):
                # raise UserError(_('Configuration error!\nThe Operating Unit in'
                                  # ' the Move Line and in the Move must be the'
                                  # ' same.'))


class AccountMove(models.Model):
    _inherit = "account.move"

    project_id = fields.Many2one('hr.contract.project.template', 'Project/Contract')

    # @api.multi
    # def _prepare_inter_project_balancing_move_line(self, move, ou_id,
                                              # ou_balances):
        # if not move.company_id.inter_project_clearing_account_id:
            # raise UserError(_('Error!\nYou need to define an inter-project\
                # unit clearing account in the company settings'))

        # res = {
            # 'name': 'Project-Balancing',
            # 'move_id': move.id,
            # 'journal_id': move.journal_id.id,
            # 'date': move.date,
            # 'project_id': project_id,
            # 'account_id': move.company_id.inter_project_clearing_account_id.id
        # }

        # if project_balances[project_id] < 0.0:
            # res['debit'] = abs(project_balances[project_id])

        # else:
            # res['credit'] = project_balances[project_id]
        # return res

    # @api.multi
    # def _check_project_balance(self, move):
        # # Look for the balance of each OU
        # project_id = {}
        # for line in move.line_ids:
            # if line.project_id.id not in project_id:
                # project_id[line.project_id.id] = 0.0
            # project_id[line.project_id.id] += (line.debit - line.credit)
        # return project_balance

    # @api.multi
    # def post(self):
        # ml_obj = self.env['account.move.line']
        # for move in self:
            # if not move.company_id.project_is_self_balanced:
                # continue

            # # If all move lines point to the same operating unit, there's no
            # # need to create a balancing move line
            # project_list_ids = [line.project_id and
                           # line.project_id.id for line in
                           # move.line_ids if line.project_id]
            # if len(ou_list_ids) <= 1:
                # continue

            # # Create balancing entries for un-balanced OU's.
            # project_balances = self._check_project_balance(move)
            # amls = []
            # for project_id in project_balances.keys():
                # # If the OU is already balanced, then do not continue
                # if move.company_id.currency_id.is_zero(project_balances[project_id]):
                    # continue
                # # Create a balancing move line in the operating unit
                # # clearing account
                # line_data = self._prepare_inter_project_balancing_move_line(
                    # move, project_id, ou_balances)
                # if line_data:
                    # amls.append(ml_obj.with_context(wip=True).
                                # create(line_data))
            # if amls:
                # move.with_context(wip=False).\
                    # write({'line_ids': [(4, aml.id) for aml in amls]})

        # return super(AccountMove, self).post()

    # def assert_balanced(self):
        # if self.env.context.get('wip'):
            # return True
        # return super(AccountMove, self).assert_balanced()

    # @api.multi
    # @api.constrains('line_ids')
    # def _check_project_id(self):
        # for move in self:
            # if not move.company_id.project_is_self_balanced:
                # continue
            # for line in move.line_ids:
                # if not line.project_id:
                    # raise UserError(_('Configuration error!\nThe operating\
                    # unit must be completed for each line if the operating\
                    # unit has been defined as self-balanced at company level.'))
