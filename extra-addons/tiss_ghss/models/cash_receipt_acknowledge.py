# -*- coding: utf-8 -*-
from openerp.tools import amount_to_text_en
from openerp import api, exceptions, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError

PETTYCASH_R_STATE = [
    ('draft', 'Draft'),
    ('paid', 'Paid'),
    ('receive', 'Received')
]

class GhssCashReceipt(models.Model):
    _name = 'ghss.cash.receipt'
    _description = 'Manage Cash Receipt Acknowledgement'

    @api.depends('amount')
    @api.one
    def _amount_in_words(self):
        self.amount_to_text = amount_to_text_en.amount_to_text(nbr=self.amount, currency="FCFA")

    @api.multi
    def button_send(self):
        if self.amount>5000.0:
            raise Warning('Please Use Requesition Form')
        #Verifier si la caisse est ouverte ou pas
        ABSObj = self.env['account.bank.statement']
        filter = [('project_id','=',self.project_id.id)]
        acc_bank_statement_id = ABSObj.search(filter)
        print"---acc_bank_statement_id---",acc_bank_statement_id
        #self.state = 'send'
        return True

    @api.multi
    def button_valid(self):
        self.state = 'valid'
        return True
    
    @api.multi
    def button_approve(self):
        self.state = 'approve'
        #Ecrire dans la caisse correspondant au projet 
        
        return True

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('ghss.cash.receipt')

    # Fields
    name = fields.Char(required=True, default=_get_default_name, string="Transaction Code :")
    date = fields.Date(string="Date", default=fields.Date.context_today, readonly=False)
    project_id = fields.Many2one('hr.contract.project.template', required=True, string="Project")
    acc_bank_statement_id = fields.Many2one('account.bank.statement', string='Cash')
    amount = fields.Float(string="Amount", required=True)
    amount_to_text = fields.Char(compute='_amount_in_words', string='In Words', help="The amount in words")
    budget_id = fields.Many2one('crossovered.budget','Budget')
    budget_post_id = fields.Many2one('account.budget.post','Budget Head')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    # planned_amount = fields.Float(string="Planned Amount")
    # theoritical_amount = fields.Float(string="Theoretical Amount")
    user_id = fields.Many2one('res.users', required=True, string="Received By")
    purpose = fields.Text(string="Purpose", required=True)
    #rejet_reaseon = fields.Text(string="Reason Of Reject")
    approver_id = fields.Many2one('res.users', string="Authorized By")
    distribursed_id = fields.Many2one('res.users', string="Distribursed By")
    petty_line_id = fields.Many2one('ghss.pettycash.fund.line', string="Cash Line")
    state = fields.Selection(selection=PETTYCASH_R_STATE, default='draft')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)

    # @api.onchange('project_id')
    # def onchange_project_id(self):
        # if self.project_id:
            # budget_id = self.env['crossovered.budget'].search([('project_id','=',self.project_id.id)], limit=1)
            # self.budget_id = budget_id.id

    # @api.onchange('analytic_account_id')
    # def onchange_product_id(self):
        # if self.analytic_account_id:
            # search_vals = [('crossovered_budget_id','=',self.budget_id.id),
                           # ('general_budget_id','=',self.budget_post_id.id),
                           # ('analytic_account_id','=',self.analytic_account_id.id)]
            # line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            
            # self.planned_amount = line_id.planned_amount
            # self.theoritical_amount = line_id.theoritical_amount
