# -*- coding: utf-8 -*-
from openerp.tools import amount_to_text_en
from openerp import api, fields, models
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning, ValidationError

_STATES = [
    ('draft', 'Draft'),
    ('to_approve', 'To be approved'),
    ('acc_approved', 'Accountant Approved'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected')
]

class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.model
    def _company_get(self):
        company_id = self.env['res.company']._company_default_get(self._name)
        return self.env['res.company'].browse(company_id)

    def _get_my_department(self):
        employees = self.env.user.employee_ids
        return (employees[0].department_id if employees
                else self.env['hr.department'])
                
    def _get_my_job(self):
        employees = self.env.user.employee_ids
        
        return (employees[0].job_id if employees else self.env['hr.job'])

    @api.model
    def _get_default_requested_by(self):
        return self.env['res.users'].browse(self.env.uid)

    @api.model
    def _default_currency(self):
        company_id=self._company_get()
        return self.env['res.company'].browse(company_id.id).currency_id

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('purchase.request')

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or \
            self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'),
                                 ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'),
                                     ('warehouse_id', '=', False)])
        return types[:1]

    @api.multi
    @api.depends('name', 'project_id', 'date_start', 'amount_total',
                 'requested_by', 'department_id', 'assigned_to', 'company_id',
                 'line_ids', 'picking_type_id')
    def _compute_is_editable(self):
        for rec in self:
            if rec.state in ('to_approve','acc_approved','approved', 'rejected'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    _track = {
        'state': {
            'purchase_request.mt_request_to_approve':
                lambda self, cr, uid, obj,
                ctx=None: obj.state == 'to_approve',
            'purchase_request.mt_request_approved':
                lambda self, cr, uid, obj,
                ctx=None: obj.state == 'approved',
            'purchase_request.mt_request_rejected':
                lambda self, cr, uid, obj,
                ctx=None: obj.state == 'rejected',
        },
    }
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
            self.budget_id = budget_id.id
            spendplan_id = self.env['budget.spendplan'].sudo().search([('budget_id','=',budget_id.id),('date_start','<=',self.date_start),('date_end','>=',self.date_start)], limit=1)
            self.spendplan_id = spendplan_id and spendplan_id.id or False
            
    @api.onchange('quotation_id')
    def onchange_quotation_id(self):
        if self.quotation_id:
            self.provider_id = self.quotation_id.partner_id.id

    name = fields.Char('PR No:', size=32, required=True,
                       default=_get_default_name,
                       track_visibility='onchange')
    quotation_id = fields.Many2one('purchase.order', string="Quotation")
    pj = fields.Binary(string="File attached")
    project_id = fields.Many2one('hr.contract.project.template', 'Project/Contract',
                        domain="[('state','=','open')]", required=True, track_visibility='onchange')
    date_start = fields.Date('Date', help="Date when the user initiated the "
                 "request.", default=fields.Date.context_today, track_visibility='onchange')
    spendplan_id = fields.Many2one('budget.spendplan', string="Spend Plan")
    requested_by = fields.Many2one('res.users',
                                   'Requested by',
                                   required=True,
                                   track_visibility='onchange',
                                   default=_get_default_requested_by)
    department_id = fields.Many2one('hr.department', 'Position In The Organization',
                                   default=_get_my_department, track_visibility='onchange')
    #job_id = fields.Many2one('hr.job', 'Position In The Organization', track_visibility='onchange')
    job_id = fields.Many2one('hr.job', 'Position In The Organization',
                                   default=_get_my_job, track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', 'Employee Concern',
                                   required=False,track_visibility='onchange')
    assigned_to = fields.Many2one('res.users', 'Accounting Approver',
                                  track_visibility='onchange')
    provider_id = fields.Many2one('res.partner', string='Provider', domain=[('supplier','=',True)])
    product_id = fields.Many2one('product.product', string="Product")
    company_id = fields.Many2one('res.company', 'Company',
                                 required=True,
                                 default=_company_get,
                                 track_visibility='onchange')
    line_ids = fields.One2many('purchase.request.line', 'request_id',
                               'Products to Purchase',
                               readonly=False,
                               copy=True,
                               track_visibility='onchange')
    amount_total = fields.Float(string='Total', store=True, readonly=True, compute='_amount_all')
    amount_to_text = fields.Char(compute='_amount_in_words', string='In Words', help="The amount in words")
    description = fields.Text(string="Description", required=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_currency, track_visibility='always')
    budget_id = fields.Many2one('crossovered.budget','Budget')
    checked = fields.Boolean(string='Is Checked ?')
    budget_post_id = fields.Many2one('account.budget.post',
                                          'Budget Head',
                                          track_visibility='onchange')
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account',
                                          track_visibility='onchange')
    planned_amount = fields.Float(string="Planned Amount")
    theoritical_amount = fields.Float(string="Theoretical Amount")
    petty_fund_id = fields.Many2one('ghss.pettycash.fund', string='Cash Fund') 
    
    sp_supplier_id = fields.Many2one('spendplan.supplier', string="Supplier")
    sp_fringe_id = fields.Many2one('spendplan.fringe', string="Fringe")
    sp_travel_id = fields.Many2one('spendplan.travel', string="Travel")
    sp_other_id = fields.Many2one('spendplan.other', string="Others")
    
    sp_supplier_activities_id = fields.Many2one('spendplan.supplier.activities', string="Supplier Act.")
    sp_fringe_activities_id = fields.Many2one('spendplan.fringe.activities', string="Fringe Act.")
    sp_travel_activities_id = fields.Many2one('spendplan.travel.activities', string="Travel Act.")
    sp_other_activities_id = fields.Many2one('spendplan.other.activities', string="Others Act.")
    
    no_po = fields.Boolean(string="Without PO ?", help="Check This Box if the current Requisition is without Purchase Order")
    ed_approved = fields.Boolean(string="ED : ")
    ded_approved = fields.Boolean(string="DED : ")
    fo_approved = fields.Boolean(string="FO :")
    acc_reject_reason = fields.Char(string="Reason of Reject")
    acc_reject = fields.Boolean(string="Acc Reject ?")
    dfi_reject_reason = fields.Char(string="Reason of Reject")
    propagate = fields.Boolean(string="Propagate : ", help="Check the box, if you want to propagate it on lines", default=True)
    state = fields.Selection(selection=_STATES,
                             string='Status',
                             track_visibility='onchange',
                             required=True,
                             default='draft')
    is_editable = fields.Boolean(string="Is editable",
                                 compute="_compute_is_editable",
                                 readonly=True)

    picking_type_id = fields.Many2one('stock.picking.type',
                                      'Picking Type', required=True,
                                      default=_default_picking_type)

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({
            'state': 'draft',
            'name': self.env['ir.sequence'].get('purchase.request'),
        })
        return super(PurchaseRequest, self).copy(default)

    @api.model
    def create(self, vals):
        if vals.get('assigned_to'):
            assigned_to = self.env['res.users'].browse(vals.get(
                'assigned_to'))
            vals['message_follower_ids'] = [(4, assigned_to.partner_id.id)]
        return super(PurchaseRequest, self).create(vals)

    @api.multi
    def write(self, vals):
        self.ensure_one()
        if vals.get('assigned_to'):
            assigned_to = self.env['res.users'].browse(
                vals.get('assigned_to'))
            vals['message_follower_ids'] = [(4, assigned_to.partner_id.id)]
        res = super(PurchaseRequest, self).write(vals)
        return res

    @api.multi
    def button_draft(self):
        self.state = 'draft'
        return True

    @api.multi
    def button_to_approve(self):
        if not self.quotation_id.id and self.amount_total>=150000.0 and self.no_po==False:
            raise Warning('Quotation must be define!')
        if not self.budget_id:
            budget_id = self.env['crossovered.budget'].search([('state','=','draft'),('project_id','=',self.project_id.id)], limit=1)
            self.budget_id = budget_id.id
        SpendPlandObj = self.env['budget.spendplan']
        filter = [('budget_id','=',self.budget_id.id)]
        spend_plan_id = SpendPlandObj.sudo().search(filter)
        if not spend_plan_id:
            raise Warning('Spend Plan must be define by the financial Officer')
        self.spendplan_id = spend_plan_id.id
        self.state = 'to_approve'
        return True
    
    @api.multi
    def button_acc_rejected(self):
        if not self.acc_reject_reason:
            raise Warning('Please Give the reason')
        self.state='draft'
        self.acc_reject=True
        return True    

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
            print"---others_id---",others_id
            self.planned_amount = others_id[0].total_price*rate
        else:
            raise ValidationError('Please Ckeck the product correctly')        
        self.checked=True
        return True
    
    @api.multi
    def button_acc_approved(self):
        if not self.budget_id.id:
            raise Warning('Please Define Budget')
        if not self.spendplan_id.id:
            raise Warning('Please Define Spend Plan')
        if not self.budget_post_id.id:
            raise Warning('Please Define Activity')
        if not self.product_id.id:
            raise Warning('Please Product')           
        #
        # if not self.checked:
            # self.button_check()
        if self.planned_amount<self.amount_total:
            raise Warning('You can not validate this Operation, Planned amount is lowest')
        if not self.assigned_to:
            self.assigned_to = self.env.user
        if self.quotation_id:
            for pl in self.quotation_id.order_line:
                pl.write({'account_analytic_id':self.analytic_account_id.id})
            self.quotation_id.wkf_confirm_order()
        if self.propagate:
            for l in self.line_ids:
                l.write({'budget_post_id':self.budget_post_id.id,
                         'budget_id':self.budget_id.id,
                         'analytic_account_id':self.analytic_account_id.id})
        for l in self.line_ids:
            if not l.budget_post_id.id:
                raise Warning('Please Insert Budget in line')
            elif not l.analytic_account_id.id:
                raise Warning('Please Insert Analytic in line')
        self.state = 'acc_approved'
        return True

    @api.multi
    def button_ed_approved(self):
        self.state = 'approved'
        self.ed_approved = True
        return True
        
    @api.multi
    def button_ded_approved(self):
        if self.amount_total>=1000000.0:
            vals = {'description':'description', 'partner_id':self.provider_id.id,
                    'purchase':True, 'pr_id':self.id, 'amount':self.amount_total}
            bank_transfert_id = self.env['account.bank_transfert'].create(vals)
        self.state = 'approved'
        self.ded_approved = True
        return True
        
    @api.multi
    def button_fo_approved(self):
        if self.amount_total>=1000000.0:
            raise Warning('You can not approved this amount')

        self.fo_approved = True
        if self.amount_total>=150000.0:
            vals = {'description':'description', 'partner_id':self.requested_by.partner_id.id,
                    'purchase':True, 'pr_id':self.id, 'amount':self.amount_total}
            bank_transfert_id = self.env['account.bank_transfert'].create(vals)
        elif self.amount_total>=5999 and self.amount_total<150000.0:
            ABSObj = self.env['ghss.pettycash.fund']
            filter = [('project_id','=',self.project_id.id)]
            petty_fund_id = ABSObj.sudo().search(filter)
            if not petty_fund_id.id:
                raise Warning('Please There is no Petty Cash Open For this Project, Ask Cashier to open It')
            self.petty_fund_id=petty_fund_id.id
            vals={'petty_cash_fund':self.petty_fund_id.id, 'purchase':True,
                  'cash_out':self.amount_total, 'partner_id':self.requested_by.partner_id.id,
                  'note':self.description, 'budget_id':self.budget_id.id,
                  'budget_post_id':self.budget_post_id.id, 'pr_id':self.id,
                  'analytic_account_id': self.analytic_account_id.id, 'ackwnolegement':True}
            self.env['ghss.pettycash.fund.line'].create(vals)
        self.state = 'approved'        
        return True

    @api.multi
    def button_rejected(self):
        self.state = 'rejected'
        return True

    @api.depends('amount_total')
    @api.one
    def _amount_in_words(self):
        self.amount_to_text = amount_to_text_en.amount_to_text(nbr=self.amount_total, currency="FCFA")


    @api.depends('line_ids.price_subtotal')
    def _amount_all(self):
        for order in self:
            amount_untaxed = 0.0
            amount_to_text = False
            for line in order.line_ids:
                amount_untaxed += line.price_subtotal
            #amount_to_text = amount_to_text_en.amount_to_text(nbr=amount_untaxed, currency="FCFA")
            order.update({
                'amount_total': amount_untaxed,
                #'amount_to_text':amount_to_text
            })
            
    @api.onchange('analytic_account_id')
    def onchange_analytic_account_id(self):
        if self.analytic_account_id:
            search_vals = [('crossovered_budget_id','=',self.budget_id.id),
                           ('general_budget_id','=',self.budget_post_id.id),
                           ('analytic_account_id','=',self.analytic_account_id.id)]
            line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            
            self.planned_amount = line_id.planned_amount
            self.theoritical_amount = line_id.practical_amount
            
    # @api.onchange('product_id')
    # def onchange_product_id(self):
        # if self.product_id:
            # search_vals = [('crossovered_budget_id','=',self.budget_id.id),
                           # ('general_budget_id','=',self.budget_post_id.id),
                           # ('analytic_account_id','=',self.analytic_account_id.id)]
            # line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            
            # self.planned_amount = line_id.planned_amount
            # self.theoritical_amount = line_id.practical_amount
            
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

class PurchaseRequestLine(models.Model):
    _name = "purchase.request.line"
    _description = "Purchase Request Line"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    @api.depends('product_id', 'name', 'price', 'price_subtotal', 'product_uom_id', 'product_qty',
                 'budget_post_id','project_id','analytic_account_id', 'date_required', 
                 'specifications')
    def _compute_is_editable(self):
        for rec in self:
            if rec.request_id.state in ('to_approve','acc_approved','approved', 'rejected'):
                rec.is_editable = False
            else:
                rec.is_editable = True

    @api.depends('product_qty', 'price')
    def _compute_amount(self):
        for line in self:
            line.update({
                'price_subtotal': line.product_qty*line.price,
            })

    @api.multi
    def _compute_supplier_id(self):
        for rec in self:
            if rec.product_id:
                for product_supplier in rec.product_id.seller_ids:
                    rec.supplier_id = product_supplier.name

    product_id = fields.Many2one(
        'product.product', 'Product',
        domain=[('purchase_ok', '=', True)],
        track_visibility='onchange')
    name = fields.Char('Goods/Services Requested', size=256, required=True,
                       track_visibility='onchange')
    product_uom_id = fields.Many2one('product.uom', 'Product Unit of Measure',
                                     track_visibility='onchange')
    product_qty = fields.Float('Quantity', track_visibility='onchange',
                               digits_compute=dp.get_precision(
                                   'Product Unit of Measure'))
    price = fields.Float('Estimated Unit Cost', required=True, track_visibility='onchange')
    price_subtotal = fields.Float(compute='_compute_amount', string='Total Estimated Unit Cost', store=True, track_visibility='onchange')
    request_id = fields.Many2one('purchase.request',
                                 'Purchase Request',
                                 ondelete='cascade', readonly=True)
    company_id = fields.Many2one('res.company',
                                 related='request_id.company_id',
                                 string='Company',
                                 store=True, readonly=True)
    budget_post_id = fields.Many2one('account.budget.post',
                                          'Budget Head',
                                          track_visibility='onchange')
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          'Analytic Account',
                                          track_visibility='onchange')
    budget_id = fields.Many2one('crossovered.budget','Budget')
    
    requested_by = fields.Many2one('res.users',
                                   related='request_id.requested_by',
                                   string='Requested by',
                                   store=True, readonly=True)
    assigned_to = fields.Many2one('res.users',
                                  related='request_id.assigned_to',
                                  string='Assigned to',
                                  store=True, readonly=True)
    date_start = fields.Date(related='request_id.date_start',
                             string='Request Date', readonly=True,
                             store=True)
    project_id = fields.Many2one(related='request_id.project_id',
                        string='Project/Contract', readonly=True,
                         store=True)
    date_required = fields.Date(string='Request Date', required=True,
                                track_visibility='onchange',
                                default=fields.Date.context_today)
    is_editable = fields.Boolean(string='Is editable',
                                 compute="_compute_is_editable",
                                 readonly=True)
    specifications = fields.Text(string='Specifications')
    request_state = fields.Selection(string='Request state',
                                     readonly=True,
                                     related='request_id.state',
                                     selection=_STATES,
                                     store=True)
    supplier_line_ids = fields.One2many('res.partner.line', 'request_line_id',
                               'Potential Vendors',track_visibility='onchange')
    supplier_id = fields.Many2one('res.partner',
                                  string='Preferred supplier',
                                  compute="_compute_supplier_id")
    department_id = fields.Many2one(
        comodel_name='hr.department',
        related='request_id.department_id',
        store=True,
        string='Department', readonly=True)

    procurement_id = fields.Many2one('procurement.order',
                                     'Procurement Order',
                                     readonly=True)

    @api.onchange('product_id', 'product_uom_id')
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = '[%s] %s' % (name, self.product_id.code)
            if self.product_id.description_purchase:
                name += '\n' + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.product_qty = 1
            self.name = name
            
    @api.multi
    def unlink(self):
        if self.is_editable==False:
            raise Warning('You can not delete on this state') 
        return super(PurchaseRequestLine, self).unlink()   

class ResPartnerLine(models.Model):
    _name = "res.partner.line"
    _description = "Potential Vendors"
    
    request_line_id = fields.Many2one('purchase.request.line',
                                 'Line Purchase Request',
                                 ondelete='cascade')
    number = fields.Integer(string="Number")
    supplier_id = fields.Many2one('res.partner', string='supplier')