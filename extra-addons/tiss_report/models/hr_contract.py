# -*- coding:utf-8 -*-

from openerp import models, fields, api, exceptions, _

class hr_contract(models.Model):
    _inherit = 'hr.contract'

    @api.one
    @api.depends('contract_job_ids')
    def _get_main_job_position(self):
        """
        Get the main job position from the field contract_job_ids which
        contains one and only one record with field is_main_job == True
        """
        main_job = self.contract_job_ids.filtered('is_main_job') or False
        if main_job:
            main_job = main_job[0].job_id.id
        self.job_id = main_job

    contract_job_ids = fields.One2many('hr.contract.job',
                                       'contract_id',
                                       string='Jobs')

    # Modify the job_id field so that it points to the main job
    job_id = fields.Many2one(
        'hr.job',
        string="Job Title",
        compute="_get_main_job_position",
        store=True)
        
    state = fields.Selection(
        [('draft', 'Draft'),('done', 'Done')],
        string='Status',
        index=True,
        default='draft',
        track_visibility='onchange',
        copy=False)
        
    wage_visible = fields.Float(string='Wage', compute="_compute_wages", store=True)
    wage = fields.Float('Basic', digits=(16,2), required=True, compute="_compute_basic", store=True)
    
    @api.model
    def get_contract_jobs(self, contract, date_from, date_to):
        # a contract job is valid if it ends between the given dates
        clause_1 = ['&', ('end_date', '<=', date_to), ('end_date', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('start_date', '<=', date_to), ('start_date', '>=', date_from)]
        # OR if it starts before the date_from and finish after the end_date (or never finish)
        clause_3 = ['&', ('start_date', '<=', date_from), '|', ('end_date', '=', False), ('end_date', '>=', date_to)]
        clause_final = [('contract_id', '=', contract.id), '|', '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract.job'].search(clause_final).ids
        
    @api.depends('contract_job_ids.wage')
    def _compute_wages(self):
        for s in self:
            montant=0.0
            # contract_job_ids = self.get_contract_jobs(self.id, date_start, date_end)
            for line in s.contract_job_ids:
                if not line.is_passed:
            	    montant += line.wage
            s.update({
                'wage_visible':montant,
            })
            
    @api.depends('contract_job_ids.wage', 'contract_job_ids.percentage')
    def _compute_basic(self):
        for s in self:
            montant,perc=0.0,0.0
            # contract_job_ids = self.get_contract_jobs(self.id, date_start, date_end)
            for line in s.contract_job_ids:
                if not line.is_passed:
					montant += line.wage
					perc+=line.percentage
            s.update({
                'wage':montant*perc/100.0,
            })
            
    @api.multi
    @api.constrains('contract_job_ids')
    def _check_one_main_job(self):
        for contract in self:
            # if the contract has no job assigned, a main job
            # is not required. Otherwise, one main job assigned is
            # required.
            if contract.contract_job_ids:
                main_jobs = contract.contract_job_ids.filtered('is_main_job')
                if len(main_jobs) != 1:
                    raise exceptions.Warning(
                        _("You must assign one and only one job position "
                          "as main job position."))
                          
    @api.multi
    def done(self):
        ProContractObj=self.env['project.contract']
        self.state = 'done'
        for cj in self.contract_job_ids:
            line_id = ProContractObj.create({'project_template_id':cj.project_id.id,
                                            'percentage':cj.percentage,
                                            'employee_id':cj.contract_id.employee_id.id,
                                            'contract_id':cj.contract_id.id})
        return True