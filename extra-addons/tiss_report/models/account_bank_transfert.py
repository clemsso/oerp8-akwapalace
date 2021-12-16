# -*- coding: utf-8 -*-
# Author be-cloud (Jerome Sonnet)

import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import amount_to_text_en
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import tools
import openerp.addons.decimal_precision as dp

class account_bank_transfert(models.Model):
    _name = "account.bank_transfert"
    _inherit = ['mail.thread']
    _description = "Bank Transfert"

    @api.model
    def _get_default_user_id(self):
        return self.env['res.users'].browse(self.env.uid)

    @api.depends('amount')
    @api.one
    def _amount_in_words(self):
        self.amount_to_text = amount_to_text_en.amount_to_text(nbr=self.amount, currency="FCFA")

    
    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].get('account.bank.transfert')
    
    name = fields.Char(string='Name', default=_get_default_name,
        readonly=True, states={'draft': [('readonly', False)]}, index=True,
        help="The name of the transfert.", copy=False)
    
    # number = fields.Char(related='journal_from_entry_id.name', store=True, readonly=True, copy=False)
    
    our_ref = fields.Char(string='Our Ref',required=False,
        readonly=True, states={'draft': [('readonly', False)]}, index=True)
        
    partner_id = fields.Many2one('res.partner', string='Beneficiary',
        copy=False,required=True,
        readonly=True, states={'draft': [('readonly', False)]})
        
    you_ref = fields.Char(string='You Ref',required=False,
        readonly=True, states={'draft': [('readonly', False)]}, index=True)
    
    description = fields.Char(string='Description',required=True,
        readonly=True, states={'draft': [('readonly', False)]}, index=True)
    
    transfert_request = fields.Text(string='Request',required=False,
        readonly=True, states={'draft': [('readonly', False)]}, index=True)
    
    pr_id = fields.Many2one('purchase.request','Purchase Request',required=False,
                                   track_visibility='onchange')
    purchase = fields.Boolean('For Purchase ?', help="Check if it is the case")
    user_id = fields.Many2one('res.users','User',required=False,
                                   track_visibility='onchange',
                                   default=_get_default_user_id)
    
    sent = fields.Boolean(readonly=True, default=False, copy=False,
        help="It indicates that the transfert has been sent.")
    
    trade_date = fields.Date(string='Trade Date',required=False,
        readonly=True, states={'draft': [('readonly', False)]}, index=True,
        help="The date of the transfert.", copy=False)
    
    value_date = fields.Date(string='Due Date',index=True, copy=False,
        help="Will be set to D+2 as a default")
    
    journal_id = fields.Many2one('account.journal', string='Journal', required=False) 
    
    period_id = fields.Many2one('account.period', string='Force Period',
        domain=[('state', '!=', 'done')], copy=False,
        help="Keep empty to use the period of the trade date.",
        readonly=True, states={'draft': [('readonly', False)]})
        
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('account.bank_transfert'))
    
    state = fields.Selection([
            ('draft','Draft'),
            ('open','Opened'),
            ('confirmed','Confirmed'),
            ('paid','Paid'),
            ('cancel','Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Transfert.\n"
             " * The 'Confirmed' status is used when user confirm a Transfert,a transfert number is generated. Its in open status till user executes the transfert.\n"
             " * The 'Paid' status is set automatically when the transfert is executed.\n"
             " * The 'Cancelled' status is used when user cancel a transfert.")
             
    from_account_id = fields.Many2one('res.partner.bank', string='From Bank Account', required=False,
        help='Bank Account Number from which the transfert will be done. Must be a company bank account number.',
        )
        
    to_account_id = fields.Many2one('res.partner.bank', string='To Bank Account', required=False,
        help='Bank Account Number from which the transfert will be done. Must be a company bank account number.',
        )

    amount = fields.Float(string='Amount which will be transfered.', digits=dp.get_precision('Account'), required=True,
        readonly=True, states={'draft': [('readonly', False)]}, default=0.0)

    amount_to_text = fields.Char(compute='_amount_in_words', string='Amount In Word', store=True)
        

    # journal_from_entry_id = fields.Many2one('account.move', string='Journal Entry', 
        # readonly=True, index=True, ondelete='restrict', copy=False,
        # help="Link to the automatically generated Journal Items.")

    # journal_to_entry_id = fields.Many2one('account.move', string='Journal Entry', 
        # readonly=True, index=True, ondelete='restrict', copy=False,
        # help="Link to the automatically generated Journal Items.")

    # payment_ids = fields.Many2many('account.move.line',
        # 'bank_transfert_payment_rel', 'bank_transfert_id', 'payment_id', string='Payments', compute='_compute_payments')

    note = fields.Text(string='Notes')
    
    # _sql_constraints = [
        # ('number_uniq', 'unique(number, company_id)',
            # 'Transfert Number must be unique per Company!'),
    # ]
    
    # @api.one
    # @api.depends(
        # 'journal_from_entry_id.line_id.reconcile_id.line_id',
        # 'journal_from_entry_id.line_id.reconcile_partial_id.line_partial_ids',
        # 'journal_to_entry_id.line_id.reconcile_id.line_id',
        # 'journal_to_entry_id.line_id.reconcile_partial_id.line_partial_ids',
    # )
    # def _compute_payments(self):
        # partial_lines = lines = self.env['account.move.line']
        # for line in self.journal_from_entry_id.line_id:
            # if line.account_id != self.from_account_id:
                # continue
            # if line.reconcile_id:
                # lines |= line.reconcile_id.line_id
            # elif line.reconcile_partial_id:
                # lines |= line.reconcile_partial_id.line_partial_ids
            # partial_lines += line
        # for line in self.journal_to_entry_id.line_id:
            # if line.account_id != self.to_account_id:
                # continue
            # if line.reconcile_id:
                # lines |= line.reconcile_id.line_id
            # elif line.reconcile_partial_id:
                # lines |= line.reconcile_partial_id.line_partial_ids
            # partial_lines += line
        # self.payment_ids = (lines - partial_lines).sorted()
    
    @api.multi
    def onchange_trade_date_transfert(self, trade_date):
        if not trade_date:
            trade_date = fields.Date.context_today(self)
        datetime_today = datetime.datetime.strptime(trade_date, tools.DEFAULT_SERVER_DATE_FORMAT)
        value_date = str((datetime_today + relativedelta(days=+2)).strftime(tools.DEFAULT_SERVER_DATE_FORMAT))
        return {'value': {'value_date': value_date}}
    
    @api.multi
    def action_date_assign(self):
        for tr in self:
            res = tr.onchange_trade_date_transfert(tr.trade_date)
            if res and res.get('value'):
                tr.write(res['value'])
        return True

    @api.multi
    def open(self):
        self.our_ref='GHSS/ED/'
        self.our_ref='FC/TRS'
        self.state='open'
        
    @api.multi
    def validate(self):
        print"---Validate---"
        statement_id=False
        if self.amount==0.00:
            raise Warning('Please The Amount should be greather than 0.00')
        ABSObj = self.env['account.bank.statement']
        ABSLObj = self.env['account.bank.statement.line']
        project_id = self.journal_id.project_id and self.journal_id.project_id.id or False
        abs_id = self.search([('journal_id','=',self.journal_id.id),('state','=','open')])
        #print"---abs_id---",abs_id
        if abs_id:
            statement_id=abs_id
        else:
            vals = {'journal_id':self.journal_id.id, 'user_id':self.env.uid,
                    'date':self.trade_date, 'project_id':self.journal_id.project_id.id}
            statement_id = ABSObj.create(vals)
            
        val_line = {'date':self.trade_date,'name':self.description, 'ref':self.name,
                    'partner_id':self.partner_id.id, 'amount':self.amount,
                    'bank_account_id':self.to_account_id.id,'statement_id':statement_id.id}
        absl_id = ABSLObj.create(val_line)
        print"---absl_id---",absl_id
        #statement_id.button_open()
        return self.write({'state': 'confirmed'})
    # @api.model
    # def _prepare_move(self, journal_id):
        # """Prepare the dict of values to create the move from a
           # statement line. This method may be overridden to implement custom
           # move generation (making sure to call super() to establish
           # a clean extension chain).
           # :param browse_record st_line: account.bank.statement.line record to
                  # create the move from.
           # :param char st_line_number: will be used as the name of the generated account move
           # :return: dict of value to create() the account.move
        # """
        # return {
            # 'journal_id': journal_id.id,
            # 'period_id': self.period_id.id,
            # 'company_id': self.company_id.id,
            # 'date': self.trade_date,
            # 'name': self.number or '/',
            # 'ref': self.number,
        # }
        
    # @api.multi
    # def action_move_create(self):
        # """ Creates transfert related analytics and financial move lines """
        
        # am_obj = self.env['account.move']
        # aml_obj = self.env['account.move.line']
        
        # for tr in self:
            # if not tr.from_account_id.journal_id.default_debit_account_id:
                # raise except_orm(_('Error!'), _('Please define an internal transfert account on the journal related to the origin account.'))
            # if not tr.to_account_id.journal_id.default_debit_account_id:
                # raise except_orm(_('Error!'), _('Please define an internal transfert account on the journal related to the destination account.'))
            # if not tr.from_account_id.journal_id.sequence_id:
                # raise except_orm(_('Error!'), _('Please define sequence on the journal related to the origin account.'))
            # if not tr.to_account_id.journal_id.sequence_id:
                # raise except_orm(_('Error!'), _('Please define sequence on the journal related to the destination account.'))
            # if tr.journal_from_entry_id:
                # continue
        
            # period = tr.period_id
            # if not period:
                # period = period.with_context().find(self.trade_date)[:1]
            
            # self.write({'period_id': period.id})
            
            # move_vals = self._prepare_move(tr.from_account_id.journal_id)
            # move_id = am_obj.create(move_vals)
            
            # from_line = {
                # 'journal_id': tr.from_account_id.journal_id.id,
                # 'period_id': tr.period_id.id,
                # 'name': _('change') + ': ' + (tr.name or '/'),
                # 'account_id': tr.from_account_id.journal_id.default_debit_account_id.id,
                # 'move_id': move_id.id,
                # 'partner_id': tr.company_id.id,
                # #'currency_id': tr.from_account_id.currency_id.id,
                # #'amount_currency': tr.amount,
                # 'quantity': tr.amount,
                # 'credit': tr.amount,
                # 'debit': 0,
                # 'date': tr.trade_date,
                # #'counterpart_move_line_id': mv_line.id,
            # }
            # aml_obj.create(from_line)
            
            # from_line_counterpart = {
                # 'journal_id': tr.from_account_id.journal_id.id,
                # 'period_id': tr.period_id.id,
                # 'name': _('change') + ': ' + (tr.name or '/'),
                # 'account_id': tr.from_account_id.journal_id.internal_account_id.id,
                # 'move_id': move_id.id,
                # #'amount_currency': tr.amount,
                # 'partner_id': tr.company_id.id,
                # #'currency_id': tr.from_account_id.currency_id.id,
                # 'quantity': tr.amount,
                # 'debit': tr.amount,
                # 'credit': 0,
                # 'date': tr.trade_date,
            # }
            # aml_obj.create(from_line_counterpart)
            
            # self.write({'journal_from_entry_id': move_id.id})
            
            # move_vals = self._prepare_move(tr.to_account_id.journal_id)
            # move_id = am_obj.create(move_vals)
            
            # to_line = {
                # 'journal_id': tr.to_account_id.journal_id.id,
                # 'period_id': tr.period_id.id,
                # 'name': _('change') + ': ' + (tr.name or '/'),
                # 'account_id': tr.from_account_id.journal_id.internal_account_id.id,
                # 'move_id': move_id.id,
                # 'partner_id': tr.company_id.id,
                # #'currency_id': tr.to_account_id.currency_id.id,
                # #'amount_currency': tr.amount,
                # 'quantity': tr.amount,
                # 'credit': tr.amount,
                # 'debit': 0,
                # 'date': tr.trade_date,
                # #'counterpart_move_line_id': mv_line.id,
            # }
            # aml_obj.create(to_line)
            
            # to_line_counterpart = {
                # 'journal_id': tr.to_account_id.journal_id.id,
                # 'period_id': tr.period_id.id,
                # 'name': _('change') + ': ' + (tr.name or '/'),
                # 'account_id': tr.from_account_id.journal_id.default_debit_account_id.id,
                # 'move_id': move_id.id,
                # #'amount_currency': tr.amount,
                # 'partner_id': tr.company_id.id,
                # #'currency_id': tr.to_account_id.currency_id.id,
                # 'quantity': tr.amount,
                # 'debit': tr.amount,
                # 'credit': 0,
                # 'date': tr.trade_date,
            # }
            # aml_obj.create(to_line_counterpart)
        
            # self.write({'journal_to_entry_id': move_id.id})
    
        
    # @api.multi
    # def action_cancel(self):
        # moves = self.env['account.move']
        # for tr in self:
            # if tr.journal_from_entry_id:
                # moves += tr.journal_from_entry_id
            # if tr.journal_to_entry_id:
                # moves += tr.journal_to_entry_id
            # if tr.payment_ids:
                # for move_line in tr.payment_ids:
                    # if move_line.reconcile_partial_id.line_partial_ids:
                        # raise except_orm(_('Error!'), _('You cannot cancel a transfert which is partially paid. You need to unreconcile related payment entries first.'))

        # # First, set the invoices as cancelled and detach the move ids
        # self.write({'state': 'cancel', 'journal_from_entry_id': False, 'journal_to_entry_id': False})
        # if moves:
            # # second, invalidate the move(s)
            # moves.button_cancel()
            # # delete the move this invoice was pointing to
            # # Note that the corresponding move_lines and move_reconciles
            # # will be automatically deleted too
            # moves.unlink()
        # self._log_event(-1.0, 'Cancel Transfert')
        # return True

    @api.multi
    def _log_event(self, factor=1.0, name='Open Invoice'):
        #TODO: implement messages system
        return True