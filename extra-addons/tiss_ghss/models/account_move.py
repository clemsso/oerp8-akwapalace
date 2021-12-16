# -*- coding: utf-8 -*-
from openerp import api, fields, models
import openerp.addons.decimal_precision as dp


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    project_id = fields.Many2one('hr.contract.project.template', 'Project/Contract')

class AccountMove(models.Model):
    _inherit = "account.move"

    project_id = fields.Many2one('hr.contract.project.template', 'Project/Contract')
