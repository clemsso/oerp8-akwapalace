# -*- coding:utf-8 -*-

from openerp import models, fields, api, exceptions, _


class hr_contract_job(models.Model):
    """
    An instance of a job position for an employee's contract.

    This model may look trivial for now, but the purpose is that other modules
    add fields to it, e.g. a salary class or a wage scale. These are fields
    that depend on both the contract and the job position.
    """
    _name = 'hr.contract.job'
    _description = 'Relational object between contract and job'

    name = fields.Char(string='Job', related='job_id.name', index=True)
    job_id = fields.Many2one('hr.job',
                             string='Job',
                             required=True,
                             ondelete='cascade')
    wage = fields.Float(string='Wage')
    percentage = fields.Float(string='Working Percentage', help="This is related about time working in project")
    project_id = fields.Many2one('hr.contract.project.template', 
                                  string='Project',
                                  required=True)
    contract_id = fields.Many2one('hr.contract',
                                  string='Contract',
                                  required=True,
                                  ondelete='cascade')
    is_main_job = fields.Boolean(string='Main Job Position')
    start_date = fields.Date(string='Date Start', required=True)
    end_date = fields.Date(string='Date End', required=True)
    
    @api.one
    def confirm(self):
        ProContractObj=self.env['project.contract']
        for contract in self.project_id.new_contract_ids:
            if contract.employee_id.id==self.contract_id.employee_id.id:
                contract.write({'percentage':self.percentage})
            # else:
                # print"---confirm---"
                # line_id = ProContractObj.create({'project_template_id':self.project_id.id,
                                                 # 'percentage':self.percentage,
                                                 # 'employee_id':self.contract_id.employee_id.id,
                                                 # 'contract_id':self.contract_id.id})
    
