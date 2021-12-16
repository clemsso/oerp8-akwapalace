# -*- coding: utf-8 -*-
from openerp import models, fields, api
from datetime import datetime
_STATES = [
    ('draft', 'Draft'),
    ('valide', 'Prepared'),
    ('review', 'Reviewed'),
    ('approve', 'Approved'),
]
_months=[('1','January'),('2','February'),('3','March'),('4','April'),('5','May'),('6','June'),
		 ('7','July'),('8','August'),('9','September'),('10','October'),('11','November'),('12','December')]
class BankReconciliation(models.Model):
    _name = "bank.reconciliation"
    _description = "Bank Reconciliation"

    # @api.model
    # def _get_default_name(self):
        
        # return self.env['ir.sequence'].get('cheque.request.form')
        
    @api.model
    def _get_default_requested_by_id(self):
        return self.env['res.users'].browse(self.env.uid)
        
    # @api.multi
    # def button_to_prepared(self):
        # self.state = 'send'
        
    # @api.multi
    # def button_prepared(self):
		# BSTObj = self.env['account.bank.statement']
		# for line in self.line_ids:
			# abs_id = BSTObj.search([('journal_id','=',line.bank_id.journal_id.id),('period_id','=',self.period_id.id),
			# ('project_id','!=',line.project_id.id),('bank_acc_id','=',line.bank_id.id),('state','!=','confirm')])
			# if not abs_id:
				# # raise Warning('No Cash Count Define, Please Contact Accountant')
				# abs_id = BSTObj.create({'journal_id':line.bank_id.journal_id.id, 'date':self.date,
				# 'period':self.period_id.id, 'project_id':line.project_id.id, 'bank_acc_id':line.bank_id.id})
			# line.write({'abs_id':abs_id.id})
			# # line.write({'':})
		# self.state = 'valide'
		# self.prepared_by_id = self.env.uid
        
    # @api.multi
    # def button_approved(self):
		# for line in self.line_ids:
			# line_id = self.env['account.bank.statement.line'].create({'date':line.abs_id.date, 'name':line.name, 'ref':self.name, 'amount':-line.amount, 'statement_id':line.abs_id.id})
		# self.state = 'approve'
		# self.approved_by_id = self.env.uid

    @api.onchange('vte_prepa_id')
    def _onchange_vte_prepa_id(self):
        if self.vte_prepa_id:
            exist = self.search([('ou_id','=',self.ou_id.id),('quart_id','=',self.vte_prepa_id.quart_id.id),('date','=',self.date)])
            if exist:
                raise ValidationError("Attention vous ne pouvez ouvrir deux fois le meme quart pour cette journee!")
            #
            self.quart_id = self.vte_prepa_id.quart_id.id
       
    name = fields.Char('No:', size=32, required=True, track_visibility='onchange')
    prepared_by_id = fields.Many2one('res.users',string="Prepared By:", default=_get_default_requested_by_id)
    year = fields.Selection([(num, str(num)) for num in range(2020, (datetime.now().year)+1 )], 'Year', required=True, track_visibility='onchange')
    months = fields.Selection(_months,string="Month")
    reviewed_by_id = fields.Many2one('res.users',string="Reviewed By:")
    approved_by_id = fields.Many2one('res.users',string="Approved By:")
    @api.onchange('date')
    def _onchange_date(self):
        if self.date:
            datee = datetime.datetime.strptime(self.date, "%Y-%m-%d")
            print"---datee.month---",datee.month
            # if exist:
                # raise ValidationError("Attention vous ne pouvez ouvrir deux fois le meme quart pour cette journee!")
            #
            # self.quart_id = self.vte_prepa_id.quart_id.id
    date = fields.Date(string="Date", required=True,)
    period_id = fields.Many2one('account.period', string="Period")
    pj = fields.Binary(string="File attached", help="Statement of Bank")
    bank_id = fields.Many2one(comodel_name="res.partner.bank", string="Bank Number")
    abs_id = fields.Many2one('account.bank.statement',string="Related Bank Statement")
	
    company_id = fields.Many2one('res.company', string='Societe', default=lambda self: self.env.user.company_id, readonly=True, track_visibility='onchange')
    reconcile_acc_bank_ids = fields.One2many('bank.reconciliation.bank', 'reconciliation_id', string="Reconciliation Bank")
    reconcile_acc_company_ids = fields.One2many('bank.reconciliation.company', 'reconciliation_id', string="Reconciliation Company")
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             track_visibility='onchange',
                             required=True,
                             default='draft')
                             

class BankReconciliationBank(models.Model):
    _name = "bank.reconciliation.bank"
    _description = "Company Account In Bank Details"

    reconciliation_id = fields.Many2one(comodel_name="bank.reconciliation",
        ondelete='cascade', required=True
    )
    date = fields.Date(string="Date")
    name = fields.Char(string="Description")
    debit = fields.Float(string="Debit")
    credit = fields.Float(string="Credit")	
    balance = fields.Float(string="Closing Balance")
	
class BankReconciliationCompany(models.Model):
    _name = "bank.reconciliation.company"
    _description = "Bank Account In Company Details"

    reconciliation_id = fields.Many2one(comodel_name="bank.reconciliation",
        ondelete='cascade', required=True
    )
    date = fields.Date(string="Date")
    name = fields.Char(string="Description")
    debit = fields.Float(string="Debit")
    credit = fields.Float(string="Credit")	
    balance = fields.Float(string="Closing Balance")