# -*- coding: utf-8 -*-
from openerp import api, fields, models
import openerp.addons.decimal_precision as dp

class AccounBankStatement(models.Model):
    _inherit = "account.bank.statement"
    
    project_id = fields.Many2one('hr.contract.project.template', 'Project/Contract',
                        required=False, track_visibility='onchange')

class AccounBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    project_id = fields.Many2one(related='statement_id.project_id',
                        string='Project/Contract', readonly=True,
                         store=True)
    # mt_entree =  fields.Float(string='CashIn')
    # mt_sortie = fields.Float(string='CashOut')
    # verous = fields.Boolean(string='Verous')
    # veroue = fields.Boolean(string='Veroue')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
