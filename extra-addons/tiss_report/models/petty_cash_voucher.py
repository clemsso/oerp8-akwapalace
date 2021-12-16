# -*- coding: utf-8 -*-
from openerp.tools import amount_to_text_en
from openerp import api, exceptions, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError

PETTYCASH_V_STATE = [
    ('draft', 'Draft'),
    ('send', 'send'),
    ('valid', 'Validate'),
    ('approve', 'Approved'),
    ('paid', 'Paid'),
    ('receive', 'Received'),
    ('cancel', 'Cancelled'),
    ('reject', 'Rejected'),
]

_type = [
    ('1100','Personnel'),
    ('1200','Fringe'),
    ('2100','Travel'),
    ('2500', 'Consultancy'),
    ('2600', 'Supplies'),
    ('3100', 'Equipment'),
    ('4100', 'Others'),
    ('5100', 'Indirect Cost'),
]

class GhssPettycashVoucher(models.Model):
    _name = 'ghss.pettycash.voucher'
    _description = 'Manage Petty Cash Voucher'
    _order = "date desc"

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('ghss.pettycash.voucher') or '/'
        return super(GhssPettycashVoucher, self).create(vals)

    @api.depends('amount')
    @api.one
    def _amount_in_words(self):
        self.amount_to_text = amount_to_text_en.amount_to_text(nbr=self.amount, currency="FCFA")

    @api.multi
    def button_send(self):
        if self.amount>5000.0:
            raise Warning('Please Use Requesition Form')
        #Verifier si la caisse est ouverte ou pas
        ABSObj = self.env['ghss.pettycash.fund']
        filter = [('project_id','=',self.project_id.id),('project_id','=',self.project_id.id)]
        petty_fund_id = ABSObj.sudo().search(filter)
        #
        SpendPlandObj = self.env['budget.spendplan']
        filter = [('budget_id','=',petty_fund_id.id)]
        spend_plan_id = SpendPlandObj.sudo().search(filter)
        if not petty_fund_id.id:
            raise Warning('Please There is no Petty Cash Open For this Project, Ask Cashier to open It')
        self.petty_fund_id=petty_fund_id.id
        self.spendplan_id=spend_plan_id.id
        self.state = 'send'
        return True
        
    @api.multi
    def acc_button_reject(self):
        if not self.rejet_reaseon:
            raise Warning('Please Insert the reason!')
        self.state='draft'
        return True

    @api.multi
    def button_check(self):
        #check if field are charge spend_plan_id
        if not self.spendplan_id.id :
            raise ValidationError('Please Spend Plan is not load')
        # if not self.product_id.id :
            # raise ValidationError('Please Product is not load') 
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
        crossovered_budget_detail_id=False
        if supplier_id:
            crossovered_budget_detail_id = supplier_id[0].id
            suppliers_id = self.env['spendplan.supplier'].search([('crossovered_budget_detail_id','=',crossovered_budget_detail_id)])
            planned_amount = suppliers_id and (suppliers_id[0].amount_subtotal*rate-suppliers_id[0].consummed_amt) or 0.00
            self.planned_amount = planned_amount
            self.sp_supplier_id = suppliers_id and suppliers_id[0].id or False
        elif fringe_id:
            crossovered_budget_detail_id = fringe_id[0].id
            fringes_id = self.env['spendplan.fringe'].search([('crossovered_budget_detail_id','=',crossovered_budget_detail_id)])
            planned_amount = fringes_id and (fringes_id[0].annual_pay*rate-fringes_id[0].consummed_amt) or 0.00
            self.planned_amount = planned_amount
            self.sp_fringe_id = fringes_id and fringes_id[0].id or False
        elif travel_id:
            crossovered_budget_detail_id = travel_id[0].id
            travels_id = self.env['spendplan.travel'].search([('crossovered_budget_detail_id','=',crossovered_budget_detail_id)])
            planned_amount = travels_id and (travels_id[0].total_price*rate-travels_id[0].consummed_amt) or 0.00
            self.planned_amount = planned_amount
            self.sp_travel_id = travels_id and travels_id[0].id or False
        elif other_id:
            crossovered_budget_detail_id = other_id[0].id
            others_id = self.env['spendplan.other'].search([('crossovered_budget_detail_id','=',crossovered_budget_detail_id)])
            planned_amount = others_id and (others_id[0].total_price*rate-others_id[0].consummed_amt) or 0.00
            self.planned_amount = planned_amount
            self.sp_other_id = others_id and others_id[0].id or False
        # else:
            # raise ValidationError('Please Ckeck the product correctly')        
        return True

    @api.multi
    def button_valid(self):
        if not self.checked:
            self.button_check()   
        self.state = 'valid'
        return True
    
    @api.multi
    def button_approve(self):
        self.state = 'approve'
        partner_id=False
        vals={'petty_cash_fund':self.petty_fund_id.id,
              'cash_out':self.amount, 'partner_id':partner_id,
              'note':self.purpose, 'budget_id':self.budget_id.id,
              'budget_post_id':self.budget_post_id.id,
              'analytic_account_id': self.analytic_account_id.id,
              'pcv_id':self.id}
        self.env['ghss.pettycash.fund.line'].create(vals)
        return True

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('ghss.pettycash.voucher')
        
    @api.model
    def _get_default_user_id(self):
        return self.env['res.users'].browse(self.env.uid)

    # Fields
    #name = fields.Char(required=True, default=_get_default_name, string="Transaction Code :")
    name = fields.Char(required=True, default='New', string="Transaction Code :")
    date = fields.Date(string="Date", default=fields.Date.context_today, readonly=True, states={'draft': [('readonly', False)]})
    project_id = fields.Many2one('hr.contract.project.template', required=True, string="Project",
    readonly=True, domain="[('state','=','open')]", states={'draft': [('readonly', False)]})
    #acc_bank_statement_id = fields.Many2one('account.bank.statement', string='Cash')
    checked = fields.Boolean(string='Is Checked ?')
    pj = fields.Binary(string="File attached")
    employee_id = fields.Many2one('hr.employee', 'Employee Concern',
                                   required=False,track_visibility='onchange')
    petty_fund_id = fields.Many2one('ghss.pettycash.fund', string='Cash Fund')
    amount = fields.Float(string="Amount", required=True, readonly=True, states={'draft': [('readonly', False)]})
    amount_to_text = fields.Char(compute='_amount_in_words', string='In Words', help="The amount in words")
    
    spendplan_id = fields.Many2one('budget.spendplan', string="Spend Plan")
    product_id = fields.Many2one('product.product', string="Product")
    budget_id = fields.Many2one('crossovered.budget','Budget')
    budget_post_id = fields.Many2one('account.budget.post','Activity')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')
    planned_amount = fields.Float(string="Planned Amount")
    theoritical_amount = fields.Float(string="Theoretical Amount")

    user_id = fields.Many2one('res.users', required=True, default=_get_default_user_id, string="Peyee", readonly=False)
    purpose = fields.Text(string="Purpose", required=True, readonly=True, states={'draft': [('readonly', False)]})
    rejet_reaseon = fields.Char(string="Reject For Accountant")
    dfi_rejet_reaseon = fields.Char(string="Reject For Finance")
    approver_id = fields.Many2one('res.users', string="Approved By", readonly=True, states={'open': [('readonly', False)]})
    distribursed_id = fields.Many2one('res.users', string="Distribursed By", readonly=True, states={'valid': [('readonly', False)]})
    state = fields.Selection(selection=PETTYCASH_V_STATE, default='draft')
    
    sp_supplier_id = fields.Many2one('spendplan.supplier', string="Supplier")
    sp_fringe_id = fields.Many2one('spendplan.fringe', string="Fringe")
    sp_travel_id = fields.Many2one('spendplan.travel', string="Travel")
    sp_other_id = fields.Many2one('spendplan.other', string="Others")
    
    sp_supplier_activities_id = fields.Many2one('spendplan.supplier.activities', string="Supplier Act.")
    sp_fringe_activities_id = fields.Many2one('spendplan.fringe.activities', string="Fringe Act.")
    sp_travel_activities_id = fields.Many2one('spendplan.travel.activities', string="Travel Act.")
    sp_other_activities_id = fields.Many2one('spendplan.other.activities', string="Others Act.")
    find_selection = fields.Selection(_type, string="Budget Head")
    company = fields.Many2one(
        'res.company',
        default=lambda self:
        self.env['res.company']._company_default_get('ghss.pettycash.voucher'))

    @api.onchange('project_id')
    def onchange_project_id(self):
        if self.project_id:
            budget_id = self.env['crossovered.budget'].search([('state','=','draft'),('project_id','=',self.project_id.id)], limit=1)
            self.budget_id = budget_id.id
            spendplan_id = self.env['budget.spendplan'].sudo().search([('budget_id','=',budget_id.id),('date_start','<=',self.date),('date_end','>=',self.date)], limit=1)
            self.spendplan_id = spendplan_id and spendplan_id.id or False

    @api.onchange('budget_post_id')
    def onchange_budget_post_id(self):
        if self.budget_post_id:
            search_vals = [('crossovered_budget_id','=',self.budget_id.id),
                           ('general_budget_id','=',self.budget_post_id.id)]
            line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            #
            self.analytic_account_id = line_id and line_id[0].analytic_account_id.id or False
    
    # @api.onchange('sp_other_id')
    # def onchange_sp_other_id(self):
        # if self.sp_other_id:
            # total_price=self.sp_other_id.total_price
            # currency_amount=self.spendplan_id.currency_amount
            # self.planned_amount = total_price*currency_amount
    
    # @api.onchange('sp_travel_id')
    # def onchange_sp_travel_id(self):
        # if self.sp_travel_id:
            # total_price=self.sp_travel_id.total_price
            # currency_amount=self.spendplan_id.currency_amount
            # self.planned_amount = total_price*currency_amount
    
    # @api.onchange('sp_fringe_id')        
    # def onchange_sp_fringe_id(self):
        # if self.sp_fringe_id:
            # total_price=self.sp_fringe_id.annual_pay
            # currency_amount=self.spendplan_id.currency_amount
            # self.planned_amount = total_price*currency_amount
            
    # def onchange_sp_supplier_id(self):
        # if self.sp_supplier_id:
            # total_price=self.sp_supplier_id.total_price
            # currency_amount=self.spendplan_id.currency_amount
            # self.planned_amount = total_price*currency_amount
            
    @api.onchange('sp_other_id')
    def onchange_sp_other_id(self):
        if self.sp_other_id:
            total_price=self.sp_other_id.total_price
            currency_amount=self.spendplan_id.budget_id.currency_amount
            self.planned_amount = total_price*currency_amount
            self.product_id = self.sp_other_id.product_id and self.sp_other_id.product_id.id or False
    
    @api.onchange('sp_travel_id')
    def onchange_sp_travel_id(self):
        if self.sp_travel_id:
            total_price=self.sp_travel_id.total_price
            currency_amount=self.spendplan_id.budget_id.currency_amount
            self.planned_amount = total_price*currency_amount
            self.product_id = self.sp_travel_id.product_id and self.sp_travel_id.product_id.id or False
    
    @api.onchange('sp_fringe_id')        
    def onchange_sp_fringe_id(self):
        if self.sp_fringe_id:
            total_price=self.sp_fringe_id.annual_pay
            currency_amount=self.spendplan_id.budget_id.currency_amount
            self.planned_amount = total_price*currency_amount
            self.product_id = self.sp_fringe_id.product_id and self.sp_fringe_id.product_id.id or False
            
    def onchange_sp_supplier_id(self):
        if self.sp_supplier_id:
            total_price=self.sp_supplier_id.total_price
            currency_amount=self.spendplan_id.budget_id.currency_amount
            self.planned_amount = total_price*currency_amount
            self.product_id = self.sp_supplier_id.product_id and self.sp_supplier_id.product_id.id or False
