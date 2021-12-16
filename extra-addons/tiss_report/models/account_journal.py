# -*- coding: utf-8 -*-
from openerp import api, fields, models
import openerp.addons.decimal_precision as dp


class AccountJournal(models.Model):
    _inherit = "account.journal"

    amt_min = fields.Float(string="Min")
    amt_max = fields.Float(string="Max")
    project_id = fields.Many2one('hr.contract.project.template', 'Project/Contract',
                        required=False, track_visibility='onchange')

    # @api.multi
    # @api.constrains('type')
    # def _check_ou(self):
        # for journal in self:
            # if journal.type in ('bank', 'cash') \
                    # and journal.company_id.ou_is_self_balanced \
                    # and not journal.operating_unit_id:
                # raise UserError(_('Configuration error!\nThe operating unit '
                                  # 'must be indicated in bank journals, '
                                  # 'if it has been defined as self-balanced '
                                  # 'at company level.'))
