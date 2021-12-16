# -*- coding: utf-8 -*-
from openerp.tools import amount_to_text_en
from openerp import models, fields, api
from openerp.exceptions import Warning, ValidationError

_STATES = [
    ('draft', 'Draft'),
    ('prepare', 'Prepared'),
    ('valide', 'Validated'),
    ('authorize', 'Authorized'),
    ('done', 'Done')
]

class PaymentVoucher(models.Model):
    _name = "payment.voucher"
    _description = "Payment Voucher"
    _order = "date desc"

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('payment.voucher')
        
    @api.model
    def _get_default_requested_by_id(self):
        return self.env['res.users'].browse(self.env.uid)
        
    @api.multi
    def button_prepare(self):
        self.state = 'prepare'
        
    @api.multi
    def button_validate(self):
        self.validate_by_id = self.env.uid
        self.state = 'valide'
        
    @api.multi
    def button_authorize(self):
        #Mettre dans la caisse ou le bank transfert
        if not self.employee_id.user_id.id:
            raise Warning('Please fill the related user for this employee')
        if self.bank:
            description = 'Not Define'
            for l in self.line_ids:
                description = l.name
            vals = {'description':description, 'partner_id':self.employee_id.user_id.partner_id.id,
                    'purchase':False, 'pr_id':False, 'amount':self.amount_total}
            bank_transfert_id = self.env['account.bank_transfert'].create(vals)
        # else: Mttre la caisse ici
        else:
            raise Warning('Please fill the cashier')
        self.state = 'authorize'
        self.authorize_by_id = self.env.uid
        
    @api.depends('amount_total')
    @api.one
    def _amount_in_words(self):
        self.amount_to_text = amount_to_text_en.amount_to_text(nbr=self.amount_total, currency="FCFA")

    @api.depends('line_ids.amount')
    def _compute_amount_total(self):
        balance=0.00
        for rec in self:
            for l in rec.line_ids:
                balance+=l.amount
            rec.amount_total = balance
            
    @api.multi
    def button_check(self):
        #check if field are charge spend_plan_id
        if not self.spendplan_id.id :
            raise ValidationError('Please Spend Plan is not load')
        if not self.product_id.id :
            raise ValidationError('Please Product is not load') 
        if not self.budget_post_id.id :
            raise ValidationError('Please Activity is not load') 
        #Verify if the demand is normal view the spend plan 
        search_vals = [('product_id','=',self.product_id.id),('general_budget_id','=',self.budget_post_id.id),
                       ('analytic_account_id','=',self.analytic_account_id.id)]
        supplier_id = self.env['crossovered.budget.detail'].search(search_vals, limit=1)
        fringe_id = self.env['crossovered.budget.fringe'].search(search_vals, limit=1)
        travel_id = self.env['crossovered.budget.travel'].search(search_vals, limit=1)
        other_id = self.env['crossovered.budget.other'].search(search_vals, limit=1)
        #
        rate = self.spendplan_id.currency_amount
        print"---rate---",rate
        crossovered_budget_detail_id=False
        if supplier_id:
            crossovered_budget_detail_id = supplier_id[0].id
            suppliers_id = self.env['spendplan.supplier'].search([('crossovered_budget_detail_id','=',crossovered_budget_detail_id)])
            self.planned_amount = suppliers_id[0].amount_subtotal*rate
        elif fringe_id:
            crossovered_budget_detail_id = fringe_id[0].id
            fringes_id = self.env['spendplan.fringe'].search([('crossovered_budget_detail_id','=',crossovered_budget_detail_id)])
            self.planned_amount = fringes_id[0].annual_pay*rate
        elif travel_id:
            crossovered_budget_detail_id = travel_id[0].id
            travels_id = self.env['spendplan.travel'].search([('crossovered_budget_detail_id','=',crossovered_budget_detail_id)])
            self.planned_amount = travels_id[0].total_price*rate
        elif other_id:
            crossovered_budget_detail_id = other_id[0].id
            others_id = self.env['spendplan.other'].search([('crossovered_budget_detail_id','=',crossovered_budget_detail_id)])
            self.planned_amount = others_id[0].total_price*rate
        else:
            raise ValidationError('Please Ckeck the product correctly')        
        self.checked=True
        return True            
        
    name = fields.Char('No:', size=32, required=True,
                       default=_get_default_name,
                       track_visibility='onchange')
                       
    requested_by_id = fields.Many2one('res.users',string="Prepared By:", required=True, default=_get_default_requested_by_id)
    validate_by_id = fields.Many2one('res.users',string="Validated By:")
    authorize_by_id = fields.Many2one('res.users',string="Athorized By:")
    employee_id = fields.Many2one('hr.employee', string="Payee",required=True,)
    project_id = fields.Many2one(comodel_name="hr.contract.project.template", required=True, string="Project", domain="[('state','=','open')]")
    budget_post_id = fields.Many2one('account.budget.post',
                                          'Budget Head',
                                          track_visibility='onchange')
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account',
                                          track_visibility='onchange')
    budget_id = fields.Many2one('crossovered.budget','Budget',required=True,)
    spendplan_id = fields.Many2one('budget.spendplan', string="Spend Plan")
    pj = fields.Binary(string="File attached")
    planned_amount = fields.Float(string="Planned Amount")
    product_id = fields.Many2one('product.product', string="Product")
    
    exchange_rate = fields.Float(string="Exchange Rate", required=True,)
    amount_to_text = fields.Char(compute='_amount_in_words', string='Amount In Words', help="The amount in words")
    currency_id = fields.Many2one('account.currency', string="Currency")
    
    cash = fields.Boolean(string="Cash", help="Check if it is paid by Cahier")
    bank = fields.Boolean(string="Bank", help="Check if it is paid by Bank")
    date = fields.Date(string="Date",required=True,)
    amount_total = fields.Float(string="Total", compute=_compute_amount_total)
    
    cheque_number = fields.Char(string="Cheque N°")
    company = fields.Many2one(
        'res.company',
        default=lambda self:
        self.env['res.company']._company_default_get('cheque.request.form'))
    line_ids = fields.One2many('payment.voucher.line', 'payment_voucher_id', string="Details Of Payment Voucher")
    
    sp_supplier_id = fields.Many2one('spendplan.supplier', string="Supplier")
    sp_fringe_id = fields.Many2one('spendplan.fringe', string="Fringe")
    sp_travel_id = fields.Many2one('spendplan.travel', string="Travel")
    sp_other_id = fields.Many2one('spendplan.other', string="Others")
       
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             track_visibility='onchange',
                             required=True,
                             default='draft')
    
    @api.onchange('budget_post_id')
    def onchange_budget_post_id(self):
        if self.budget_post_id:
            search_vals = [('crossovered_budget_id','=',self.budget_id.id),
                           ('general_budget_id','=',self.budget_post_id.id)]
            line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            #
            self.analytic_account_id = line_id and line_id[0].analytic_account_id.id or False    
    
    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            budget_id = self.env['crossovered.budget'].search([('state','=','draft'),('project_id','=',self.project_id.id)], limit=1)
            self.budget_id = budget_id and budget_id.id or False
            spendplan_id = self.env['budget.spendplan'].sudo().search([('budget_id','=',budget_id.id),('date_start','<=',self.date),('date_end','>=',self.date)], limit=1)
            self.spendplan_id = spendplan_id and spendplan_id.id or False
            self.exchange_rate = spendplan_id and spendplan_id.currency_amount or 0.00
    
    @api.onchange('analytic_account_id')
    def onchange_product_id(self):
        if self.analytic_account_id:
            search_vals = [('crossovered_budget_id','=',self.budget_id.id),
                           ('general_budget_id','=',self.budget_post_id.id),
                           ('analytic_account_id','=',self.analytic_account_id.id)]
            line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            
            self.planned_amount = line_id.planned_amount
            self.theoritical_amount = line_id.practical_amount   

    @api.onchange('sp_other_id')
    def onchange_sp_other_id(self):
        if self.sp_other_id:
            total_price=self.sp_other_id.total_price
            currency_amount=self.spendplan_id.currency_amount
            self.planned_amount = total_price*currency_amount
    
    @api.onchange('sp_travel_id')
    def onchange_sp_travel_id(self):
        if self.sp_travel_id:
            total_price=self.sp_travel_id.total_price
            currency_amount=self.spendplan_id.currency_amount
            self.planned_amount = total_price*currency_amount
    
    @api.onchange('sp_fringe_id')        
    def onchange_sp_fringe_id(self):
        if self.sp_fringe_id:
            total_price=self.sp_fringe_id.annual_pay
            currency_amount=self.spendplan_id.currency_amount
            self.planned_amount = total_price*currency_amount
            
    def onchange_sp_supplier_id(self):
        if self.sp_supplier_id:
            total_price=self.sp_supplier_id.total_price
            currency_amount=self.spendplan_id.currency_amount
            self.planned_amount = total_price*currency_amount            

class PaymentVoucherLine(models.Model):
    _name = "payment.voucher.line"
    _description = "Payment Voucher Line"
            
    @api.depends('number_of_day','rate')
    def _compute_values(self):
        e_rate=self.payment_voucher_id.exchange_rate
        self.amount = e_rate*self.number_of_day*self.rate
 
    payment_voucher_id = fields.Many2one(comodel_name="payment.voucher",
        ondelete='cascade', required=True
    )
    #project_id = fields.Many2one(comodel_name="hr.contract.project.template", string="Project")
    #bank_id = fields.Many2one(comodel_name="res.partner.bank", string="Bank")
    
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    name = fields.Char(string="Purpose", required=True)
    account_id = fields.Many2one('account.account', string="ACC Code")
    number_of_day = fields.Integer(string="Number Of Days", required=True)
    rate = fields.Float(string="Rate $", required=True)
    amount = fields.Float(string="Amount CFA", compute=_compute_values)
    line_ids = fields.One2many('payment.voucher.line.details', 'payment_voucher_line_id', string="Line Details Of Payment Voucher")    

    # @api.multi
    # def write(self, vals):
        # amount = 0.00
        # for details in self.line_ids:
            # amount += details.values
        # print"---amount---",amount
        # print"---self.amount---",self.amount
        # if (amount > self.amount):
            # raise Warning('The details amount values is greater')
        # return super(PaymentVoucherLine, self).write(vals)

class PaymentVoucherLineDetails(models.Model):
    _name = "payment.voucher.line.details"
    _description = "Payment Voucher Line Details"
    
    @api.model
    def create(self, vals):
        parent_amount = self.env['payment.voucher.line'].search([('id','=',vals.get('payment_voucher_line_id'))])[0].amount
        vals['values'] = parent_amount * vals.get('percentage')/100.0
        details = super(PaymentVoucherLineDetails, self).create(vals)
        return details
    
    # @api.multi
    # def write(self, vals):
        # vals['values'] = self.parent_amount * vals.get('percentage')/100.0
        # return super(PaymentVoucherLineDetails, self).write(vals)
    
    payment_voucher_line_id = fields.Many2one('payment.voucher.line',
        ondelete='cascade', required=True)
    parent_amount = fields.Float(related='payment_voucher_line_id.amount',string="Amount Parent", store=True, readonly=True)
    description = fields.Char(string="Description")
    percentage = fields.Float(string="Percentage x%")
    values = fields.Float(string="Amount")
    
    @api.onchange(
        "percentage",
    )
    def onchange_percentage(self):
        if self.percentage:
            self.values = self.parent_amount * self.percentage/100.0
