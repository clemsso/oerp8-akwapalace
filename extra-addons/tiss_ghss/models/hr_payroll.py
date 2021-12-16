#-*- coding:utf-8 -*-

from openerp.tools import amount_to_text_en
from openerp import api, fields, models
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning, ValidationError

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    project_id = fields.Many2one('hr.contract.project.template', 'Project/Contract',
                        domain="[('state','=','open')]")
    budget_id = fields.Many2one('crossovered.budget','Budget')
    spendplan_id = fields.Many2one('budget.spendplan', string="Spend Plan")
    
    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            budget_id = self.env['crossovered.budget'].search([('state','=','draft'),('project_id','=',self.project_id.id)], limit=1)
            self.budget_id = budget_id.id
            spendplan_id = self.env['budget.spendplan'].sudo().search([('budget_id','=',budget_id.id),('date_start','<=',self.date_start),('date_end','>=',self.date_end)], limit=1)
            self.spendplan_id = spendplan_id and spendplan_id.id or False