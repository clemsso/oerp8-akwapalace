# -*- coding: utf-8 -*-
from openerp import api, fields, models
import openerp.addons.decimal_precision as dp

class AccounBankStatement(models.Model):
    _inherit = "account.bank.statement"
    
    project_id = fields.Many2one('hr.contract.project.template', 'Project/Contract', track_visibility='onchange')
    bank_acc_id = fields.Many2one('res.partner.bank', 'Acc. Bank Number', track_visibility='onchange')
	
    @api.model
    def create(self,vals):
    	res = super(AccounBankStatement,self).create(vals)
    	print"---project_id---",self.project_id
    		# my_vals = {'name':vals['name']}
    		# self.rule_id.write(my_vals)
    	return res

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
