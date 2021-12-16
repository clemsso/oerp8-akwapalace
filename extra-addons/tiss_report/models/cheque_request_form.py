# -*- coding: utf-8 -*-
from openerp import models, fields, api
_STATES = [
    ('draft', 'Draft'),
    ('send', 'To be Prepared'),
    ('valide', 'Prepared'),
    ('approve', 'Approved'),
    ('done', 'Done')
]

class ChequeRequestForm(models.Model):
    _name = "cheque.request.form"
    _description = "Cheque Request Form"

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('cheque.request.form')
        
    @api.model
    def _get_default_requested_by_id(self):
        return self.env['res.users'].browse(self.env.uid)
        
    @api.multi
    def button_to_prepared(self):
        self.state = 'send'
        
    @api.multi
    def button_prepared(self):
		BSTObj = self.env['account.bank.statement']
		for line in self.line_ids:
			abs_id = BSTObj.search([('journal_id','=',line.bank_id.journal_id.id),('period_id','=',self.period_id.id),
			('project_id','!=',line.project_id.id),('bank_acc_id','=',line.bank_id.id),('state','!=','confirm')])
			if not abs_id:
				# raise Warning('No Cash Count Define, Please Contact Accountant')
				abs_id = BSTObj.create({'journal_id':line.bank_id.journal_id.id, 'date':self.date,
				'period':self.period_id.id, 'project_id':line.project_id.id, 'bank_acc_id':line.bank_id.id})
			line.write({'abs_id':abs_id.id})
			# line.write({'':})
		self.state = 'valide'
		self.prepared_by_id = self.env.uid
        
    @api.multi
    def button_approved(self):
		for line in self.line_ids:
			line_id = self.env['account.bank.statement.line'].create({'date':line.abs_id.date, 'name':line.name, 'ref':self.name, 'amount':-line.amount, 'statement_id':line.abs_id.id})
		self.state = 'approve'
		self.approved_by_id = self.env.uid
        
    name = fields.Char('No:', size=32, required=True,
                       default=_get_default_name,
                       track_visibility='onchange')
    requested_by_id = fields.Many2one('res.users',string="Requested By:", default=_get_default_requested_by_id)
    requested_by_position_id = fields.Many2one('hr.job',string="Position:")
    prepared_by_id = fields.Many2one('res.users',string="Prepared By:")
    prepared_by_position_id = fields.Many2one('hr.job',string="Position:")
    approved_by_id = fields.Many2one('res.users',string="Approved By:")
    approved_by_position_id = fields.Many2one('hr.job',string="Position:")
    date = fields.Date(string="Date",required=True,)
    pj = fields.Binary(string="File attached")
    type_cheque = fields.Selection([('pc','Petty Cash'),('sup','Supplier')],string="Petty Cash/Supplier")
    journal_id = fields.Many2one('account.journal',string="Related Journal")
    period_id = fields.Many2one('account.period', string="Period")
    company = fields.Many2one(
        'res.company',
        default=lambda self:
        self.env['res.company']._company_default_get('cheque.request.form'))
		
    @api.onchange('date')
    def onchange_date(self):
		res = {}
		period_pool = self.env['account.period']
		pids = period_pool.find(dt=self.date)
		if pids:
		    res.update({'period_id': pids[0]})
		return {'value':res}

    line_ids = fields.One2many('cheque.request.form.line', 'request_cheque_id', string="Details")
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             track_visibility='onchange',
                             required=True,
                             default='draft')
                             

class ChequeRequestFormLine(models.Model):
    _name = "cheque.request.form.line"
    _description = "Cheque Request Form Line"

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id.id:
            self.name = self.product_id.description_purchase

    # @api.model
    # def _get_default_partner_id(self):
        # return self.company.partner_id

    request_cheque_id = fields.Many2one(comodel_name="cheque.request.form",
        ondelete='cascade', required=True
    )
    project_id = fields.Many2one(comodel_name="hr.contract.project.template", string="Project")
    bank_id = fields.Many2one(comodel_name="res.partner.bank", string="Bank")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    name = fields.Char(string="Goods/Services requested")
    amount = fields.Float(string="Amount")
    partner_id = fields.Many2one('res.partner', string="Partner", default=1 )
    abs_id = fields.Many2one('account.bank.statement', string="Account Bank Statement")
    company = fields.Many2one(
        'res.company',
        default=lambda self:
        self.env['res.company']._company_default_get('cheque.request.form.line'))