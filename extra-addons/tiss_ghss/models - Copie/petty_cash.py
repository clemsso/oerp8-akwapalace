# -*- coding: utf-8 -*-

from openerp import api, exceptions, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError

PETTYCASH_STATE = [
    ('draft', 'Draft'),
    ('open', 'Open'),
    ('closed', 'Closed'),
]

class GhssPettyCash(models.Model):
    _name = 'ghss.pettycash.fund'
    _description = 'Manage Petty Cash Fund in GHSS'

    @api.multi
    def button_opened(self):
        if not self.project_id.id:
            raise Warning('This Journal does not have fund, Call for accountant')
        #Create cash register
        ABSObj = self.env['account.bank.statement']
        vals = {'journal_id':self.journal_id.id,
                'date':self.date, 'project_id':self.project_id.id,
                'user_id':self.user_id.id, 'petty_cash_fund':self.id}
        acc_bank_statement_id = ABSObj.sudo().create(vals)
        acc_bank_statement_id.button_open()
        self.state = 'open'
        return True
        
    @api.onchange('journal_id')
    def onchange_project_id(self):
        if self.journal_id.id:
            self.project_id = self.journal_id.project_id.id

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('ghss.pettycash.fund')
        
    @api.depends('line_ids.cash_in', 'line_ids.cash_out')
    def _compute_petty_cash_balance(self):
        balance=0.00
        for rec in self:
            for l in rec.line_ids:
                balance+=l.cash_in-l.cash_out
            rec.petty_cash_balance = balance

    # Fields
    name = fields.Char(required=True, default=_get_default_name)
    user_id = fields.Many2one('res.users', required=True, string="User", default=lambda self: self.env.user)
    project_id = fields.Many2one('hr.contract.project.template', string="Project", required=True)
    petty_cash_limit = fields.Float(string='Max Limit', required=True)
    petty_cash_min = fields.Float(string='Min Limit', required=True, help="To Make a need of money")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    petty_cash_balance = fields.Float(
        string='Balance',
        compute='_compute_petty_cash_balance',
    )
    journal_id = fields.Many2one('account.journal', string="Journal", required=False)
    state = fields.Selection(selection=PETTYCASH_STATE, default='draft')
    #active = fields.Boolean(default=True)
    company = fields.Many2one(
        'res.company',
        default=lambda self:
        self.env['res.company']._company_default_get('ghss.pettycash.fund'))
    line_ids = fields.One2many('ghss.pettycash.fund.line', 'petty_cash_fund', string="Details")
    inter_project_pettycash_ids = fields.One2many('ghss.pettycash.interproject.line', 'petty_cash_fund', string="Details")
    line_cash_count_ids = fields.One2many('ghss.pettycash.count.line', 'petty_cash_fund', string="Cash Count")
    cash_register_ids = fields.One2many('account.bank.statement', 'petty_cash_fund', string="Cash Registers")

    #Ouvrir l interface de la caisse
    @api.multi
    def button_cash_count(self):
        wiz = False
        #view = self.env.ref('account.view_bank_statement_form2')
        view = self.env.ref('tiss_ghss.view_cash_control_view_form')
        for abs in self.cash_register_ids:
            if abs.state=='open' and abs.lock==False:
                wiz = abs.id
        if wiz==False:
            raise Warning('No Cash Count Define, Please Contact Accountant')
        return {
            'name': _('Cash Count'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.bank.statement',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': wiz,
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'context': self.env.context,
        }

class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"
    
    @api.multi
    def button_save(self):
        return True
    
    @api.multi
    def button_lock_transaction(self):
        for t in self.line_ids:
            t.petty_line_id.write({'lock_line':True})
        self.lock=True
        continu=False
        for l in self.petty_cash_fund.line_ids:
            if l.lock_line==False:
                continu=True 
        if continu==True:
            #Create cash register
            ABSObj = self.env['account.bank.statement']
            vals = {'journal_id':self.journal_id.id,
                    'date':self.date, 'project_id':self.project_id.id,
                    'user_id':self.user_id.id, 'petty_cash_fund':self.petty_cash_fund.id}
            acc_bank_statement_id = ABSObj.create(vals)
            acc_bank_statement_id.button_open()
        return True
        
    @api.multi
    def write(self, values):
        """Override default Odoo write function and extend."""
        return super(AccountBankStatement, self).write(values)
    
    lock = fields.Boolean(string="Lock for account ?")
    
    petty_cash_fund = fields.Many2one('ghss.pettycash.fund', 'Petty Cash',
                                 required=True, delegate=True,
                                 ondelete='cascade')
                                 
    @api.multi
    def unlink(self):
        if self.lock==True:
            raise Warning('Can not delete this')
        return super(AccountBankStatement, self).unlink()

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"
    
    @api.multi
    def unlink(self):
        if self.statement_id.lock==True:
            raise Warning('Can not delete this')
        return super(AccountBankStatementLine, self).unlink()

    petty_line_id = fields.Many2one('ghss.pettycash.fund.line', string='Petty Line')

class GhssPettyCashLine(models.Model):
    _name = 'ghss.pettycash.fund.line'
    _description = 'Details of petty cash Fund'

    @api.one
    def _compute_balance(self):
        domain = [('petty_cash_fund','=',self.petty_cash_fund.id)]
        lines = self.env['ghss.pettycash.fund.line'].search(domain)
        cash_in,cash_out=0.00,0.00
        for s in lines:
            if s.cash_in:
                cash_in+=s.cash_in
            if s.cash_out:
                cash_out+=s.cash_out
            if s.id==self.id:
                s.balance = abs(cash_in-cash_out)

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('ghss.pettycash.fund.line')

    petty_cash_fund = fields.Many2one('ghss.pettycash.fund', 'Petty Cash',
                                 required=True, delegate=True,
                                 ondelete='cascade')
    
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    name = fields.Char('Communication', required=True, default=_get_default_name,)
    
    pr_id = fields.Many2one('purchase.request','Purchase Request')
    pcv_id = fields.Many2one('ghss.pettycash.voucher','Petty cash Voucher')
    pv_id = fields.Many2one('payment.voucher','Payment Voucher')
    
    cash_in = fields.Float(string='Cash In')
    cash_out = fields.Float(string='Cash Out')
    partner_id = fields.Many2one('res.partner', string='Payee')

    budget_id = fields.Many2one('crossovered.budget','Budget')
    budget_post_id = fields.Many2one('account.budget.post','Budget Head')
    analytic_account_id = fields.Many2one('account.analytic.account','Analytic Account')    
    #
    partner_name = fields.Char(string='Partner Name', help="This field is used to record the third party name when importing bank statement in electronic format, when the partner doesn't exist yet in the database (or cannot be found).")
    ref = fields.Char(string='Reference')
    note = fields.Char(string='Note')
    sequence = fields.Integer(string='Sequence', select=True, help="Gives the sequence order when displaying a list of bank statement lines.")
    balance = fields.Float(string='Balance', compute='_compute_balance')
    cash_count = fields.Boolean(string='Cash Count ?')
    cash_register = fields.Boolean(string='Cash Register ?')
    lock_line = fields.Boolean(string='Lock ?')
    voucher_number = fields.Char(string='Voucher N°')
    ackwnolegement = fields.Boolean(string="Acknowledge")
    ack_receipt = fields.Boolean(string="Receipt ?")
    #state = fields.Selection(selection=PETTYCASH_LINE_STATE, default='draft')
    # 'journal_entry_id': fields.many2one('account.move', 'Journal Entry', copy=False),
    # 'amount_currency': fields.float('Amount Currency', help="The amount expressed in an optional other currency if it is a multi-currency entry.", digits_compute=dp.get_precision('Account')),
    # 'currency_id': fields.many2one('res.currency', 'Currency', help="The optional other currency if it is a multi-currency entry."),
    @api.multi
    def print_receipt(self):
        #Pour impression::: Voir comment gerer les impressions ici
        if self.ackwnolegement==True and self.ack_receipt==False:
            ReceiptObj = self.env['ghss.cash.receipt']
            prObj = self.env['purchase.request']
            pr_id = prObj.sudo().search([('id','=',self.pr_id.id)])
            vals={'project_id':self.project_id.id, 'date':self.date, 
                  'amount':self.cash_out, 'user_id':pr_id.requested_by.id,
                  'purpose':self.note,'petty_line_id':self.id}
            receipt_id = ReceiptObj.sudo().create(vals)
            receipt_id.write({'state':'paid'})
            self.ack_receipt=True
 
    @api.multi
    def puch_to_cash(self):
        #Mise a jour du spend Plan
        if self.pr_id.id:
            if self.pr_id.sp_supplier_id.id:
                consummed_amt = self.pr_id.sp_supplier_id.consummed_amt
                self.pr_id.sp_supplier_id.write({'consummed_amt':consummed_amt+self.cash_out})
            elif self.pr_id.sp_fringe_id.id:
                consummed_amt = self.pr_id.sp_fringe_id.consummed_amt
                self.pr_id.sp_fringe_id.write({'consummed_amt':consummed_amt+self.cash_out})
            elif self.pr_id.sp_travel_id.id:
                consummed_amt = self.pr_id.sp_travel_id.consummed_amt
                self.pr_id.sp_travel_id.write({'consummed_amt':consummed_amt+self.cash_out})
            elif self.pr_id.sp_other_id.id:
                consummed_amt = self.pr_id.sp_other_id.consummed_amt
                self.pr_id.sp_other_id.write({'consummed_amt':consummed_amt+self.cash_out})
        elif self.pcv_id.id:
            if self.pcv_id.sp_supplier_id.id:
                consummed_amt = self.pcv_id.sp_supplier_id.consummed_amt
                self.pcv_id.sp_supplier_id.write({'consummed_amt':consummed_amt+self.cash_out})
            elif self.pcv_id.sp_fringe_id.id:
                consummed_amt = self.pcv_id.sp_fringe_id.consummed_amt
                self.pcv_id.sp_fringe_id.write({'consummed_amt':consummed_amt+self.cash_out})
            elif self.pcv_id.sp_travel_id.id:
                consummed_amt = self.pcv_id.sp_travel_id.consummed_amt
                self.pcv_id.sp_travel_id.write({'consummed_amt':consummed_amt+self.cash_out})
            elif self.pcv_id.sp_other_id.id:
                consummed_amt = self.pcv_id.sp_other_id.consummed_amt
                self.pcv_id.sp_other_id.write({'consummed_amt':consummed_amt+self.cash_out})
        elif self.pv_id.id:
            if self.pv_id.sp_supplier_id.id:
                consummed_amt = self.pv_id.sp_supplier_id.consummed_amt
                self.pv_id.sp_supplier_id.write({'consummed_amt':consummed_amt+self.cash_out})
            elif self.pv_id.sp_fringe_id.id:
                consummed_amt = self.pv_id.sp_fringe_id.consummed_amt
                self.pv_id.sp_fringe_id.write({'consummed_amt':consummed_amt+self.cash_out})
            elif self.pv_id.sp_travel_id.id:
                consummed_amt = self.pv_id.sp_travel_id.consummed_amt
                self.pv_id.sp_travel_id.write({'consummed_amt':consummed_amt+self.cash_out})
            elif self.pv_id.sp_other_id.id:
                consummed_amt = self.pv_id.sp_other_id.consummed_amt
                self.pv_id.sp_other_id.write({'consummed_amt':consummed_amt+self.cash_out})
              
        ABSLObj = self.env['account.bank.statement.line']
        for abs in self.petty_cash_fund.cash_register_ids:
            if abs.state=='open':
                vals={'statement_id':abs.id,'date':self.date, 
                      'amount':self.cash_in>0.0 and self.cash_in or -self.cash_out, 
                      'partner_id':self.partner_id.id,'name':self.note, 'ref':self.voucher_number,
                      'petty_line_id':self.id}
                absl_id = ABSLObj.create(vals)            
        self.cash_register=True
        return True
    
    @api.multi
    def unlink(self):
        if self.cash_register==True:
            raise Warning('Can not delete this, already send to accountant')
        return super(GhssPettyCashLine, self).unlink()

        
class GhssPettyCashCountLine(models.Model):
    _name = 'ghss.pettycash.count.line'
    _description = 'Details of petty cash Fund count'

    @api.depends('bills_ids.amount','coints_ids.amount')
    def _compute_tot_mont(self):
        for s in self:
            montant=0.0
            for line in s.bills_ids:
                montant += line.amount
            for line in s.coints_ids:
                montant += line.amount
            s.amt_balance=montant

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('ghss.pettycash.count.line')

    petty_cash_fund = fields.Many2one('ghss.pettycash.fund', 'Petty Cash',
                                 required=True, delegate=True,
                                 ondelete='cascade')
    #project_id =  fields.Many2one(string="Fund")
    purchase = fields.Boolean(string="Purchase")
    pr_id = fields.Many2one('purchase.request','Purchase Request')
    user_id = fields.Many2one('res.users', string="Custodian")
    date = fields.Date(string='Date', required=True)
    name = fields.Char('Name', required=True, default=_get_default_name,)
    
    amt_balance = fields.Float(compute='_compute_tot_mont',string='Ending Balance from Reconciliation')
    
    #Section A 
    bills_ids = fields.One2many('ghss.pettycash.count.bills', 'petty_cash_count_id', string="Cash Count")
    coints_ids = fields.One2many('ghss.pettycash.count.coints', 'petty_cash_count_id', string="Cash Count")
    # amount_bills = fields.Float(string="Bills Amount")
    
    #Section B 
    # cash_out = fields.Float(string='Cash Out')
    # partner_id = fields.Many2one('res.partner', string='Partner')
    # #bank_account_id = fields.Many2one('res.partner.bank',string='Bank Account')
    # account_id = fields.Many2one('account.account', string='Account')
    # partner_name = fields.Char(string='Partner Name', help="This field is used to record the third party name when importing bank statement in electronic format, when the partner doesn't exist yet in the database (or cannot be found).")
    # ref = fields.Char(string='Reference')
    # note = fields.Char(string='Note')
    # sequence = fields.Integer(string='Sequence', select=True, help="Gives the sequence order when displaying a list of bank statement lines.")
    # balance = fields.Float(string='Balance', compute='_compute_balance')
    # cash_count = fields.Boolean(string='Cash Count ?')

class GhssPettyCashInterprojectLine(models.Model):
    _name = 'ghss.pettycash.interproject.line'
    _description = 'Details of petty cash Fund couinter project cash form'

    @api.multi
    def button_send(self):
        self.requested_by = self.env.uid
        self.state = 'send'
        
    @api.multi
    def button_approve(self):
        if self.pc_project_provider_id.id:
            vals = {'date':self.date,'note':self.name,'cash_out':self.amount, 'petty_cash_fund':self.pc_project_provider_id.id}
            line_id = self.env['ghss.pettycash.fund.line'].create(vals)
        if self.pc_project_inneed_id.id:
            vals = {'date':self.date,'note':self.name,'cash_in':self.amount, 'petty_cash_fund':self.pc_project_inneed_id.id}
            line_id = self.env['ghss.pettycash.fund.line'].create(vals)
        self.approved_by = self.env.uid
        self.state = 'approve'
        
    #Controler que le montant est saisie
    #Controler qu'il ne s'agit pas de la meme caisse 
    #Chaque caissier ne doit voir que sa caisse et autre elements

    petty_cash_fund = fields.Many2one('ghss.pettycash.fund', 'Petty Cash',
                                 required=True, delegate=True,
                                 ondelete='cascade')
    #project_id =  fields.Many2one(string="Fund")
    name = fields.Char(string="Purpose of The Fund", required=True)
    date = fields.Date(string="Date", required=True)
    pc_project_inneed_id = fields.Many2one('ghss.pettycash.fund', string="Project in Need of Fund", required=True)
    pc_project_provider_id = fields.Many2one('ghss.pettycash.fund', string="Project provider of Fund", required=True)
    amount = fields.Float(string="Amount", required=True)
    requested_by = fields.Many2one('res.users', string="Requested By", required=False)
    approved_by = fields.Many2one('res.users', string="Approved By")
    state = fields.Selection(selection=[('draft', 'Draft'),('send', 'To be Approved'),
    ('approve', 'Approved'),('done', 'Done')],string='Status',required=True,default='draft')

class PettyCashCountBills(models.Model):

    @api.onchange('number','pieces')
    def onchange_number(self):
        val = 0.00
        if self.pieces and self.number:
            if self.pieces=='10000':
                val = 10000 * self.number
            elif self.pieces=='5000':
                val = 5000 * self.number
            elif self.pieces=='2000':
                val = 2000 * self.number
            elif self.pieces=='1000':
                val = 1000 * self.number
            elif self.pieces=='500':
                val = 500 * self.number

            self.amount=val

    _name = "ghss.pettycash.count.bills"
    _description = "Number Of Bills"
    
    pieces = fields.Selection([('10000','10 000'),('5000','5 000'),('2000','2 000'),('1000','1 000'),('500','500')], string='Bills')
    number = fields.Integer('Count')
    amount = fields.Float(string='FCFA Amount')
    
    petty_cash_count_id = fields.Many2one('ghss.pettycash.count.line', ondelete='cascade')

class PettyCashCountCoins(models.Model):

    @api.onchange('number','pieces')
    def onchange_number(self):
        val = 0.00
        if self.pieces and self.number:
            if self.pieces=='500':
                val = 500 * self.number
            elif self.pieces=='100':
                val = 100 * self.number
            elif self.pieces=='50':
                val = 50 * self.number
            elif self.pieces=='25':
                val = 25 * self.number
            elif self.pieces=='10':
                val = 10 * self.number
            elif self.pieces=='5':
                val = 5 * self.number
            self.amount=val

    _name = "ghss.pettycash.count.coints"
    _description = "Number Of Coints"
    
    pieces = fields.Selection([('500','500'),('100','100'),('50','50'),('25','25'),('10','10'),('5','5')], string='Coins')
    number = fields.Integer('Count')
    amount = fields.Float(string='FCFA Amount')
    
    petty_cash_count_id = fields.Many2one('ghss.pettycash.count.line', ondelete='cascade')
