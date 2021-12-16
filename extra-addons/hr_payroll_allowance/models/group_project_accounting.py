# -*- encoding: utf-8 -*-

from datetime import timedelta, date, datetime
from calendar import monthrange
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning, ValidationError
from openerp.tools import amount_to_text_en
from openerp import workflow
from xlwt import Workbook, Formula, easyxf
import base64
import locale
import StringIO
    
class HR_Payroll_History(models.Model):
	
	_inherit = 'hr.contract.project.history'

	date_account = fields.Date('Date Account', readonly=True, help="Keep empty to use the period of the validation(Payslip) date.")
	journal_id = fields.Many2one('account.journal', 'Salary Journal', readonly=True, required=True,
        default=lambda self: self.env['account.journal'].search([('type', '=', 'general')], limit=1))
	move_id = fields.Many2one('account.move', 'Accounting Entry', readonly=True, copy=False)
	computation_history_id = fields.One2many('hr.contract.project.history.computation', 'history_id', string='Computation')

	@api.multi
	def payroll_computation(self):
		if self.move_id.id:
			raise Warning("You can not generate account move twice for this Project History")
		rule_ids = self.env['hr.salary.rule'].search([])
		for rule in rule_ids:
		    #Basic Salary
			if rule.code=='BASIC':
			    val_basic_salary = {'history_id':self.id, 'name':'Basic Salary', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':self.total_basic}
			    basic=self.env['hr.contract.project.history.computation'].create(val_basic_salary)
			
			for allowance in self.allowance_ids:
				amount = 0
				for payslip in self.payslip_batch_id.slip_ids:
					if payslip.contract_id in self.contract_ids:
						perc=100.00
						date_start = self.payslip_batch_id.date_start
						date_end = self.payslip_batch_id.date_end
						contract_job_ids = self.get_contract_jobs(payslip.contract_id, date_start, date_end)
						for contract in contract_job_ids:
						    contract=self.env['hr.contract.job'].search([('id','=',contract)])
						    if self.project_id.id == contract.project_id.id:
						        if len(contract_job_ids)>1:
						            perc = contract.percentage
                        #
						for line in payslip.line_ids:
							if line.salary_rule_id.id == allowance.allowance_id.rule_id.id:
								amount += line.total*perc/100.00
				#Duty Post
				if rule.code=='DPOST' and rule.id==allowance.allowance_id.rule_id.id:
					val = {'history_id':self.id, 'name':'Duty Post', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					basic=self.env['hr.contract.project.history.computation'].create(val)
				#Representation
				elif rule.code=='REPRESENT' and rule.id==allowance.allowance_id.rule_id.id:
					val = {'history_id':self.id, 'name':'Representation', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					basic=self.env['hr.contract.project.history.computation'].create(val)
				#Housing
				elif rule.code=='HOUSE' and rule.id==allowance.allowance_id.rule_id.id:
					val = {'history_id':self.id, 'name':'Housing', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					basic=self.env['hr.contract.project.history.computation'].create(val)
				#Water and Electricity
				elif rule.code=='WATELEC' and rule.id==allowance.allowance_id.rule_id.id:
					val = {'history_id':self.id, 'name':'Water and Electricity', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					basic=self.env['hr.contract.project.history.computation'].create(val)
				#Car Allowance
				elif rule.code=='CAR' and rule.id==allowance.allowance_id.rule_id.id:
					val = {'history_id':self.id, 'name':'Car', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					basic=self.env['hr.contract.project.history.computation'].create(val)
				#Risk Allowance
				elif rule.code=='RISK' and rule.id==allowance.allowance_id.rule_id.id:
					val = {'history_id':self.id, 'name':'Risk Allowance', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					basic=self.env['hr.contract.project.history.computation'].create(val)
				#CFC Employer
				elif rule.code=='CFC' and rule.id==allowance.allowance_id.rule_id.id:
					val = {'history_id':self.id, 'name':'CFC Employer', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					basic=self.env['hr.contract.project.history.computation'].create(val)
				#FNE Employer
				elif rule.code=='FNE' and rule.id==allowance.allowance_id.rule_id.id:
					val = {'history_id':self.id, 'name':'FNE Employer', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					basic=self.env['hr.contract.project.history.computation'].create(val)
				# #Retirement Pension Employee
				# if rule.code=='DPOST' and rule.id==allowance.allowance_id.rule_id.id:
					# val = {'history_id':self.id, 'name':'Duty Post', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					# basic=self.env['hr.contract.project.history.computation'].create(val)
				# #Representation
				# elif rule.code=='REPRESENT' and rule.id==allowance.allowance_id.rule_id.id:
					# val = {'history_id':self.id, 'name':'Representation', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					# basic=self.env['hr.contract.project.history.computation'].create(val)
				# #Housing
				# elif rule.code=='HOUSE' and rule.id==allowance.allowance_id.rule_id.id:
					# val = {'history_id':self.id, 'name':'Housing', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					# basic=self.env['hr.contract.project.history.computation'].create(val)
				# #Water and Electricity
				# elif rule.code=='WATELEC' and rule.id==allowance.allowance_id.rule_id.id:
					# val = {'history_id':self.id, 'name':'Water and Electricity', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					# basic=self.env['hr.contract.project.history.computation'].create(val)
				# #Car Allowance
				# elif rule.code=='CAR' and rule.id==allowance.allowance_id.rule_id.id:
					# val = {'history_id':self.id, 'name':'Car', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					# basic=self.env['hr.contract.project.history.computation'].create(val)
				# #Risk Allowance
				# elif rule.code=='RISK' and rule.id==allowance.allowance_id.rule_id.id:
					# val = {'history_id':self.id, 'name':'Risk Allowance', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					# basic=self.env['hr.contract.project.history.computation'].create(val)
				# #CFC Employer
				# elif rule.code=='CFC' and rule.id==allowance.allowance_id.rule_id.id:
					# val = {'history_id':self.id, 'name':'CFC Employer', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					# basic=self.env['hr.contract.project.history.computation'].create(val)
				# #FNE Employer
				# elif rule.code=='FNE' and rule.id==allowance.allowance_id.rule_id.id:
					# val = {'history_id':self.id, 'name':'FNE Employer', 'rule_id':rule.id, 'rule_code':rule.code,'account_debit':rule.account_debit, 'account_credit':rule.account_credit,'amount':amount}
					# basic=self.env['hr.contract.project.history.computation'].create(val)
		# if self.payslip_batch_id and self.payslip_batch_id.slip_ids:
			# # allowances = []
			# # payslip_with_bank_account_ids = []
			# # allowance_obj = self.env['hr.contract.project.history.allowance']
			# # for allowance in self.allowance_set_ids:
				# # allowance_id = allowance_obj.search([('allowance_id','=',allowance.id),('history_id','=',self.id)])
				# # if not allowance_id:
					# # allowance_id = allowance_obj.create({'allowance_id':allowance.id,'total_amount':0,'history_id':self.id})
				# # allowances.append(allowance_id[0].id)
			# # self.allowance_ids = [(6,0,allowances)]
			
			# date_start = self.payslip_batch_id.date_start
			# date_end = self.payslip_batch_id.date_end
			
			# for slip in self.payslip_batch_id.slip_ids:	
				# if slip.contract_id in self.contract_ids:
					# perc=100
					# gross_salary=0.00
					# net = slip.net
					# contract_job_ids = self.get_contract_jobs(slip.contract_id, date_start, date_end)
					# for contract in contract_job_ids:
						# contract=self.env['hr.contract.job'].search([('id','=',contract)])
						# if self.project_id.id == contract.project_id.id:
							# if len(contract_job_ids)>1:
								# perc = contract.percentage
								# net = slip.net * perc/100.0
					# #
					# # self.total_gross += slip.gross_salary*perc/100.0
					# # self.total_taxable += slip.taxable_salary*perc/100.0
					# # self.total_pit += slip.pit*perc/100.0
					# # self.total_act += slip.act*perc/100.0
					# # self.total_ctax += slip.ctax*perc/100.0
					# # self.total_cfce += slip.cfce*perc/100.0
					# # self.total_cfcp += slip.cfcp*perc/100.0
					# # self.total_fne += slip.fne*perc/100.0
					# # self.total_crtv += slip.crtv*perc/100.0
					# net_salary += net
					# # self.total_basic += slip.basic*perc/100.0
					# # self.total_cnpse += slip.cnpse*perc/100.0
					# # self.total_cnpsp += slip.cnpsp*perc/100.0
					# # self.total_ipa += slip.ipa*perc/100.0
					# # self.total_fcon += slip.fcon*perc/100.0
					# # self.total_other_deductions += slip.extra_deduction*perc/100.0
					# # payslip_with_bank_account_ids.append(slip.id)
					# #Comptabiliser le salaire NET
					# if net_salary > 0:
					    # i					
		# # self.total_taxes = self.total_pit + self.total_act + self.total_ctax + self.total_crtv
		# # self.total_taxes += self.total_cfce + self.total_cfcp + self.total_fne 
		# # self.total_taxes_employees_basic = self.total_pit + self.total_act + self.total_ctax + self.total_cfce
		# # self.total_taxes_employees_basic += self.total_cnpse + self.total_crtv
		# # self.total_taxes_employees = self.total_pit + self.total_act + self.total_ctax + self.total_cfce
		# # self.total_taxes_employees += self.total_cnpse + self.total_crtv + self.total_other_deductions
		# # self.total_taxes_employer = self.total_cfcp + self.total_fne + self.total_fcon
		# # self.total_taxes_employer += self.total_cnpsp + self.total_ipa
		# # self.total_taxes_deductions = self.total_taxes_employees + self.total_taxes_employer
		
		# # self.payslip_with_bank_account_ids = self.env['hr.payslip'].search([('id','in',payslip_with_bank_account_ids)]).filtered(lambda r: len(r.employee_id.bank_account_ids) > 0).sorted(key=lambda r: r.employee_id.bank_account_ids[0].bank_id.id)
	
		# # bank_ids = []
		# # for payslip in self.payslip_with_bank_account_ids:
			# # if payslip.employee_id.bank_account_ids:
				# # my_id = payslip.employee_id.bank_account_ids[0].bank_id.id
				# # if not my_id in bank_ids:
					# # bank_ids.append(payslip.employee_id.bank_account_ids[0].bank_id.id)
				
		# # self.bank_ids = self.env['hr.bank'].search([('id','in',bank_ids)])
		# # self.nb_bank = len(self.bank_ids)
		return True

class HR_Payroll_History_computation(models.Model):
	
	_name = 'hr.contract.project.history.computation'
	_description = 'For Salary History Computation'
	
	name = fields.Char(string='Name')
	rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule')
	rule_code = fields.Char(string='Code of Rule')
	account_debit = fields.Many2one('account.account', 'Debit Account')
	account_credit = fields.Many2one('account.account', 'Credit Account')
	amount = fields.Float(string='Amount')
	
	history_id = fields.Many2one('hr.contract.project.history',string="Project History")
	
	