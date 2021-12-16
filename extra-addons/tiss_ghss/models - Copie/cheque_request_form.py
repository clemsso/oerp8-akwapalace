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
        self.state = 'valide'
        self.prepared_by_id = self.env.uid
        
    @api.multi
    def button_approved(self):
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
    company = fields.Many2one(
        'res.company',
        default=lambda self:
        self.env['res.company']._company_default_get('cheque.request.form'))
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

    request_cheque_id = fields.Many2one(comodel_name="cheque.request.form",
        ondelete='cascade', required=True
    )
    project_id = fields.Many2one(comodel_name="hr.contract.project.template", string="Project")
    bank_id = fields.Many2one(comodel_name="res.partner.bank", string="Bank")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    name = fields.Char(string="Goods/Services requested")
    amount = fields.Float(string="Amount")

