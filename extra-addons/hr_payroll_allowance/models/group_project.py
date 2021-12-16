# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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

MONTHS = [
	'January',
	'February',
	'March',
	'April',
	'May',
	'June',
	'July',
	'August',
	'Spetember',
	'October',
	'November',
	'December',
]

class HR_Projet_Account(models.Model):

	_name = 'hr.project.bank.account'
	
	name = fields.Char(string="Account Number",required=True)
	bank_id = fields.Many2one('hr.bank',string="Bank",required=True)
	project_ids = fields.Many2many('hr.contract.project.template','hr_project_bank_account_rel','project_id','bank_account_id',readonly=True)

class HR_Employee(models.Model):

	_inherit = 'hr.employee'
	
	group_id = fields.Many2one('hr.employee.group',string="Group")

class HR_Payroll_Group1(models.Model):

	_name = 'hr.employee.group'
	
	name = fields.Char(string="Name",required=True)
	employee_ids = fields.One2many('hr.employee','group_id',string="Employees")
	nb_emp = fields.Integer(string="Number of Employees",compute='_nb_employees')
	
	def _nb_employees(self):
		self.nb_emp = 0
		
		if self.employee_ids:
			self.nb_emp = len(self.employee_ids)

class HR_Payroll_Project_Template(models.Model):

	_name = 'hr.contract.project.template'
	
	name = fields.Char("Name",required=True)
	code = fields.Char("Code",size=4, required=False)
	date_start = fields.Date(string="Start End", required=False)
	date_end = fields.Date(string="End Date", required=False)
	contract_ids = fields.One2many('hr.contract','project_template_id',string="Contracts")
	nb_contract = fields.Integer(string="Number of Contracts",compute='_nb_contracts')
	state = fields.Selection([('open','Open'),('close','Close')],string="Status",default='open')
	bank_account_ids = fields.Many2many('hr.project.bank.account','hr_project_bank_account_rel','bank_account_id','project_id')
	employee_one_id = fields.Many2one('hr.employee',string="Approval 1")
	employee_two_id = fields.Many2one('hr.employee',string="Approval 2")
	employee_three_id = fields.Many2one('hr.employee',string="Approval 3")
	
	@api.one
	@api.depends('contract_ids')
	def _nb_contracts(self):
		self.nb_contract = 0
		
		if self.contract_ids:
			self.nb_contract = len(self.contract_ids)
			
	@api.multi
	def unlink(self):
		history_obj = self.env['hr.contract.project.history']
		history_id = history_obj.search([('project_id','=',self.id)])
		
		if len(history_id) == 0:
			super(HR_Payroll_Project_Template).unlink()
		else:
			raise Warning("Sorry ! We caanot delete this project cause there are some Payroll history related to it !")
			
	@api.one
	def close(self):
		if self.contract_ids:
			for contract in self.contract_ids:
				self.contract_ids = [(3,contract.id)]
		self.write({'state':'close'})
		
	@api.one
	def reopen(self):
		self.write({'state':'open'})

class HR_Payroll_Project_Allowance_History(models.Model):
	_name = 'hr.contract.project.history.allowance'
	
	allowance_id = fields.Many2one('hr.payroll.allowance.set',readonly=True)
	total_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'),readonly=True)
	history_id = fields.Many2one('hr.contract.project.history',string="History")

class HR_Payroll_History_Gross(models.Model):
	_name = 'hr.contract.project.history.gros'
    
	contract_id = fields.Many2one('hr.contract',string='Contract')
	amt_gross = fields.Float(string='Gross Amount')
	
	history_id = fields.Many2one('hr.contract.project.history',string="Project History")
    
class HR_Payroll_History_Basic(models.Model):
	_name = 'hr.contract.project.history.basic'
    
	contract_id = fields.Many2one('hr.contract',string='Contract')
	amt_basic = fields.Float(string='Basic Amount')
	
	history_id = fields.Many2one('hr.contract.project.history',string="Project History")
	
class HR_Payroll_History_All(models.Model):
	_name = 'hr.contract.project.history.all'
    
	contract_id = fields.Many2one('hr.contract',string='Contract')
	allowance_id = fields.Many2one('hr.payroll.allowance.set',string='Allowance')
	amt_global = fields.Float(string='Amount Global')
	percentage = fields.Float(string='Percentage')
	amt = fields.Float(string='Amount')
	
	history_id = fields.Many2one('hr.contract.project.history',string="Project History")
    
class HR_Payroll_History(models.Model):
	
	_name = 'hr.contract.project.history'
	
	name = fields.Char("Name", required=True)
	amt_basic_history_id = fields.One2many('hr.contract.project.history.basic', 'history_id', string='Gross')
	amt_gross_history_id = fields.One2many('hr.contract.project.history.gros', 'history_id', string='Gross')
	amt_all_history_id = fields.One2many('hr.contract.project.history.all', 'history_id', string='Allowances')
	project_id = fields.Many2one('hr.contract.project.template',string="Project")
	payslip_batch_id = fields.Many2one('hr.payslip.run',string="Month")
	contract_ids = fields.Many2many('hr.contract','hr_contract_project_history_rel','my_hr_contract_project_history_id','my_hr_contract_id',string="Contracts")
	nb_contract = fields.Integer(string="Number of Contracts",compute='_nb_contracts')
	company_id = fields.Many2one('res.company',string="Company",compute='_get_payslips')
	payslip_ids = fields.Many2many('hr.payslip',string="Payslips",compute='_get_payslips')
	month = fields.Char(string="Month of payslip",compute='_get_month')
	nb_pages = fields.Integer(string="Number of pages",compute='_get_pages')
	total_gross = fields.Float(string="Gross",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxable = fields.Float(string="Taxable",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_pit = fields.Float(string="PIT",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_ctax = fields.Float(string="Communal Tax",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_act = fields.Float(string="ACT",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_cfce = fields.Float(string="CFC Employee",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_cfcp = fields.Float(string="CFC Employer",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_cnpse = fields.Float(string="CNPS Employee",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_cnpsp = fields.Float(string="CNPS Employer",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_fne = fields.Float(string="FNE",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_crtv = fields.Float(string="CRTV",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_ipa = fields.Float(string="IPA",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_fcon = fields.Float(string="Familly Contribution",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxes = fields.Float(string="Total Deduction",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxes_employees = fields.Float(string="Total Deduction - Employees",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxes_employees_basic = fields.Float(string="Total Deduction - Employees Basic",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxes_employer = fields.Float(string="Total Deduction - Employer",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_net = fields.Float(string="Total Net",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_net_text = fields.Char(string="Amount in Text", compute='_convert_net_to_text', readonly=True)
	total_basic = fields.Float(string="Total Basic",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_other_deductions = fields.Float(string="Total Other Deductions",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxes_deductions = fields.Float(string="Total Tax Deductions",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	wire_transfert_name = fields.Char("Wire Transfert File Name",compute='_update_transfert')
	monthly_wire_transfert = fields.Binary(string="Monthly Wire Transfert",compute='_update_transfert')
	dipe_pit_project_name = fields.Char("Dipe PIT File Name",compute='_update_dipe_pit_project')
	dipe_pit_project_file = fields.Binary(string="Dipe PIT Project File",compute='_update_dipe_pit_project')
	patroll_component_project_name = fields.Char("Payroll Component File Name",compute='_update_payroll_component_project')
	payroll_component_project_file = fields.Binary(string="Payroll Component Project File",compute='_update_payroll_component_project')
	patroll_taxes_name = fields.Char("Payroll Taxe Name",compute='_update_payroll_taxes')
	payroll_taxes_file = fields.Binary(string="Payroll Taxe File",compute='_update_payroll_taxes')
	payslip_with_bank_account_ids = fields.Many2many('hr.payslip',compute='_get_amount',readonly=True)
	bank_ids = fields.Many2many('hr.bank',compute='_get_amount')
	nb_bank = fields.Integer(string="Bank number",compute='_get_amount')
	allowance_set_ids = fields.Many2many('hr.payroll.allowance.set',compute='_get_allowance_set')
	nb_allowances = fields.Integer(string="Allowances Set Number",compute='_get_allowance_set')
	allowance_ids = fields.Many2many('hr.contract.project.history.allowance',string="Allowances",compute='_get_amount')
	previous_project_history_id = fields.Many2one('hr.contract.project.history',string="Previous Month Wizard",compute='_get_previous_project_history')
	nb_payslips = fields.Integer(string="Number of Payslips",compute='_get_nb_payslips',readonly=True)
	
	our_ref = fields.Char(string="Our Ref")
	your_ref = fields.Char(string="Your Ref")
	
	account_number = fields.Char(string="Account Number")
	bank_address = fields.Text(string="Bank Address")
	
	the_current_date = fields.Date(string="Date")
	extra_text = fields.Text(string="Extra Text")
	
	approval_right_id = fields.Many2one('hr.employee',string="Approval Right")
	approval_left_id = fields.Many2one('hr.employee',string="Approval Left")

	@api.one
	def get_gross(self):
		print"---len(self.payslip_ids)---",len(self.payslip_ids)
		for a in self.allowance_ids:
			if a.allowance_id.code=='CAR':
			    a.allowance_id.write({'name':'Water Allowance'})
			elif a.allowance_id.code=='WATELEC':
			    a.allowance_id.write({'name':'Electricity Allowance'})
		for payslip in self.payslip_ids:
			mt_d_distribuer=0.00
			for line in payslip.line_ids:
				if line.salary_rule_id.id==42:
					mt_d_distribuer = line.total
					print"---payslip---",payslip.name
					print"---mt_d_distribuer---",mt_d_distribuer
					line.unlink()
			for line in payslip.line_ids:
				if line.salary_rule_id.id==1:
					mt=line.amount+mt_d_distribuer
					# print"---DPOST mt---",mt
					line.write({'amount':mt})   
				# elif line.salary_rule_id.code=='HOUSE':
					# mt=line.total+mt_d_distribuer/4.0
					# line.amount=mt
				# elif line.salary_rule_id.code=='WATELEC':
					# mt=line.total+mt_d_distribuer/4.0
					# line.amount=mt                    
				# elif line.salary_rule_id.code=='CAR':
					# mt=line.total+mt_d_distribuer/4.0
					# line.amount=mt                    
		for a in self.allowance_ids:
			if a.allowance_id.id==3:
				print"Trouve"
				a.unlink()
		return True
        
	@api.one
	@api.depends('total_net')
	def _convert_net_to_text(self):
		if self.total_net:
			temp = amount_to_text_en.amount_to_text(self.total_net, 'en','Francs CFA')
			self.total_net_text = temp[:temp.find("CFA") + 3]
		else:
			self.total_net_text = ''
	
	@api.one
	@api.depends('contract_ids')
	def _nb_contracts(self):
		self.nb_contract = 0
		
		if self.contract_ids:
			self.nb_contract = len(self.contract_ids)

	@api.one
	@api.depends('payslip_batch_id')
	def _get_nb_payslips(self):
		if self.payslip_batch_id:
			self.nb_payslips = len(self.payslip_batch_id.slip_ids)
		else:
			self.nb_payslips = 0
	
	@api.one
	def _get_allowance_set(self):
		self.allowance_set_ids = self.env['hr.payroll.allowance.set'].search([]).sorted(key=lambda r: r.sequence)
		self.nb_allowances = len(self.allowance_set_ids)
	
	@api.model
	def get_contract_jobs(self, contract, date_from, date_to):
		# a contract job is valid if it ends between the given dates
		clause_1 = ['&', ('end_date', '<=', date_to), ('end_date', '>=', date_from)]
		# OR if it starts between the given dates
		clause_2 = ['&', ('start_date', '<=', date_to), ('start_date', '>=', date_from)]
        # OR if it starts before the date_from and finish after the end_date (or never finish)
		clause_3 = ['&', ('start_date', '<=', date_from), '|', ('end_date', '=', False), ('end_date', '>=', date_to)]
		clause_final = [('contract_id', '=', contract.id), '|', '|'] + clause_1 + clause_2 + clause_3
		return self.env['hr.contract.job'].search(clause_final).ids
	
	@api.one
	@api.depends('payslip_batch_id')
	def _get_amount(self):
		self.total_gross = 0
		self.total_taxable = 0
		self.total_pit = 0
		self.total_act = 0
		self.total_ctax = 0
		self.total_cfce = 0
		self.total_cfcp = 0
		self.total_fne = 0
		self.total_crtv = 0
		self.total_cnpse = 0
		self.total_cnpsp = 0
		self.total_ipa = 0
		self.total_fcon = 0
		self.total_net = 0
		self.total_basic = 0
		self.total_other_deductions = 0
		
		if self.payslip_batch_id and self.payslip_batch_id.slip_ids:
			allowances = []
			payslip_with_bank_account_ids = []
			
			allowance_obj = self.env['hr.contract.project.history.allowance']
			for allowance in self.allowance_set_ids:
				allowance_id = allowance_obj.search([('allowance_id','=',allowance.id),('history_id','=',self.id)])
				
				if not allowance_id:
					allowance_id = allowance_obj.create({'allowance_id':allowance.id,'total_amount':0,'history_id':self.id})
					
				allowances.append(allowance_id[0].id)
#				self.allowance_ids = [(4,[allowance_id.id])]
			
			self.allowance_ids = [(6,0,allowances)]
			
			#raise Warning("Value of allowances IDS : %s" % (allowance_ids))
			date_start = self.payslip_batch_id.date_start
			date_end = self.payslip_batch_id.date_end
			for slip in self.payslip_batch_id.slip_ids:	
				if slip.contract_id in self.contract_ids:
					#
					perc=100
					gross_salary=0.00
					net = slip.net
					contract_job_ids = self.get_contract_jobs(slip.contract_id, date_start, date_end)
					for contract in contract_job_ids:
						contract=self.env['hr.contract.job'].search([('id','=',contract)])
						# if len(contract)>1:
						print"---contract---",contract
						if self.project_id.id == contract.project_id.id:
							if len(contract_job_ids)>1:
								perc = contract.percentage
								net = slip.net * perc/100.0
							#gross_salary = contract.wage
					#
					self.total_gross += slip.gross_salary*perc/100.0
					#self.total_gross += gross_salary
					self.total_taxable += slip.taxable_salary*perc/100.0
					self.total_pit += slip.pit*perc/100.0
					self.total_act += slip.act*perc/100.0
					self.total_ctax += slip.ctax*perc/100.0
					self.total_cfce += slip.cfce*perc/100.0
					self.total_cfcp += slip.cfcp*perc/100.0
					self.total_fne += slip.fne*perc/100.0
					self.total_crtv += slip.crtv*perc/100.0
					self.total_net += net #slip.net*perc/100.0
					self.total_basic += slip.basic*perc/100.0
					self.total_cnpse += slip.cnpse*perc/100.0
					self.total_cnpsp += slip.cnpsp*perc/100.0
					self.total_ipa += slip.ipa*perc/100.0
					self.total_fcon += slip.fcon*perc/100.0
					self.total_other_deductions += slip.extra_deduction*perc/100.0

					payslip_with_bank_account_ids.append(slip.id)
				
	
		self.total_taxes = self.total_pit + self.total_act + self.total_ctax + self.total_crtv
		self.total_taxes += self.total_cfce + self.total_cfcp + self.total_fne 
		self.total_taxes_employees_basic = self.total_pit + self.total_act + self.total_ctax + self.total_cfce
		self.total_taxes_employees_basic += self.total_cnpse + self.total_crtv
		self.total_taxes_employees = self.total_pit + self.total_act + self.total_ctax + self.total_cfce
		self.total_taxes_employees += self.total_cnpse + self.total_crtv + self.total_other_deductions
		self.total_taxes_employer = self.total_cfcp + self.total_fne + self.total_fcon
		self.total_taxes_employer += self.total_cnpsp + self.total_ipa
		self.total_taxes_deductions = self.total_taxes_employees + self.total_taxes_employer
		
		self.payslip_with_bank_account_ids = self.env['hr.payslip'].search([('id','in',payslip_with_bank_account_ids)]).filtered(lambda r: len(r.employee_id.bank_account_ids) > 0).sorted(key=lambda r: r.employee_id.bank_account_ids[0].bank_id.id)
	
		bank_ids = []
		for payslip in self.payslip_with_bank_account_ids:
			if payslip.employee_id.bank_account_ids:
				my_id = payslip.employee_id.bank_account_ids[0].bank_id.id
				if not my_id in bank_ids:
					bank_ids.append(payslip.employee_id.bank_account_ids[0].bank_id.id)
				
		self.bank_ids = self.env['hr.bank'].search([('id','in',bank_ids)])
		self.nb_bank = len(self.bank_ids)

	@api.one
	@api.depends('project_id','payslip_batch_id')
	def _get_previous_project_history(self):
		history_id = None
		
		if self.project_id and self.payslip_batch_id:
			history_obj = self.env['hr.contract.project.history']
			
			if self.payslip_batch_id.previous_payslip_run_id:
				history_id = history_obj.search([('project_id','=',self.project_id.id),('payslip_batch_id','=',self.payslip_batch_id.previous_payslip_run_id.id)])
				
		self.previous_project_history_id = history_id
		
	@api.one
	@api.depends('project_id','payslip_batch_id')
	def _get_payslips(self):
		if self.project_id and self.payslip_batch_id and self.payslip_batch_id.slip_ids:
			temp = []
#			temp = self.payroll_batch_id.slip_ids.search([()])
			for payslip in self.payslip_batch_id.slip_ids:
				if payslip.contract_id in self.contract_ids:
					temp.append(payslip.id)
					
			self.payslip_ids = self.payslip_batch_id.slip_ids.filtered(lambda r: r.id in temp)
			#self.payslip_ids = self.payroll_batch_id.slip_ids.filtered(lambda r: r.contract_id.project_id and  (for proj_id in r.contract_id.project_id: if proj_id.id == self.project_id: ))
			if self.payslip_ids:
				self.company_id = self.payslip_ids[0].employee_id.company_id
		else:
			self.payslip_ids = None
			self.company_id = None
	
	@api.one
	@api.depends('payslip_batch_id')
	def _get_pages(self):
		if self.payslip_batch_id.slip_ids:
			self.nb_pages = (len(self.payslip_ids) / 16 ) + 1
		else:
			self.nb_pages = 0
	
	@api.one
	@api.depends('payslip_batch_id')
	def _get_month(self):
		if self.payslip_batch_id:
			the_date = datetime.strptime(self.payslip_batch_id.date_end,'%Y-%m-%d')
			the_month = the_date.month
			the_year = the_date.year
			self.month = "%s %s" % (MONTHS[the_month - 1],the_year)
		else:
			self.month = ""

	@api.multi
	def get_transfert_pdf(self):
		if self.payslip_batch_id and self.project_id:
#			raise Warning('Number of Payslips: %s' % self.payslip_ids)
			if self.payslip_with_bank_account_ids:
				return self.env['report'].get_action(self,'hr_payroll_allowance.wire_transfert_project_history_template')
			elif self.payslip_ids:
				raise Warning('Sorry, there are some employees that does not get Bank Account Information\n Please fix it and reprint !')
			else:
				raise Warning('Sorry, there is no payslip for this Project during this month !')
		else:
			raise Warning('Please select a Payslip Month')
	
	@api.multi
	def letter_transfert_pdf(self):
		#raise Warning('This is the letter for wire transfer')
		if self.payslip_with_bank_account_ids:
			if not self.our_ref:
				raise Warning('Please, fill the \'Our Reference\' first !')
			if not self.your_ref:
				raise Warning('Please, fill the \'Your Reference\' first !')
			if not self.account_number:
				raise Warning('Please, fill the Bank Account Reference first !')
			if not self.bank_address:
				raise Warning('Please, fill the Bank Address first !')
			if not self.the_current_date:
				raise Warning('Please, fill the Date !')
			if not self.extra_text:
				raise Warning('Please, Enter the sentence that indicates the \'object of the expenses\', the \'office\' and the \'period\' !')
			if not self.approval_left_id:
				raise Warning('Who is the approval on left of the document ?')
			if not self.approval_right_id:
				raise Warning('Who is the approval on the right of the document ?')
			return self.env['report'].get_action(self,'hr_payroll_allowance.wire_transfert_project_history_letter_template')
		elif self.payslip_ids:
			raise Warning('Sorry, there are some employees that does not get Bank Account Information\n Please fix it and reprint !')
		else:
			raise Warning('Sorry, there is no payslip for this Project during this month !')
	
	@api.multi
	def get_transfert_xls(self):
		#raise Warning("Ready to print")
		return {
			'type':'ir.actions.act_url',
			'url':'/web/binary/download_document?model=hr.contract.project.history&field=monthly_wire_transfert&id=%s&filename=monthly_transfert_%s_%s.xls'%(self.id,self.project_id.name,self.month),
			'target':'self',
			}
		
	@api.multi
	def get_dipe_pit_xls(self):
		#raise Warning("Ready to print")
		return {
			'type':'ir.actions.act_url',
			'url':'/web/binary/download_document?model=hr.contract.project.history&field=dipe_pit_project_file&id=%s&filename=dipe_pit_%s_%s.xls'%(self.id,self.project_id.name,self.month),
			'target':'self',
		}
		
	@api.multi
	def print_dipe(self):
		#raise Warning("Ready to print")
		if self.payslip_ids:
			#raise Warning("Payslips : %s " % self.payslip_ids)
			return self.env['report'].get_action(self,'hr_payroll_allowance.dipe_project_pit_history_template')
		else:
			raise Warning('Sorry there is no Payslip for this project during this Month')
	
	@api.multi
	def get_payroll_components_xls(self):
		#raise Warning("Ready to print")
		return {
			'type':'ir.actions.act_url',
			'url':'/web/binary/download_document?model=hr.contract.project.history&field=payroll_component_project_file&id=%s&filename=payroll_componenets_%s_%s.xls'%(self.id,self.project_id.name,self.month),
			'target':'self',
		}
	
	@api.multi
	def print_employee_taxes_xls(self):
#		raise Warning("Ready to print")
		return {
			'type':'ir.actions.act_url',
			'url':'/web/binary/download_document?model=hr.contract.project.history&field=payroll_taxes_file&id=%s&filename=payroll_taxes_%s_%s.xls'%(self.id,self.project_id.name,self.month),
			'target':'self',
		}
	
	@api.multi
	def print_allowances(self):
		#raise Warning("Ready to print")
		if self.payslip_ids:
			return self.env['report'].get_action(self,'hr_payroll_allowance.allowances_project_history_template')
		else:
			raise Warning('Sorry, there is no payslip for this project during this Month')
			
	@api.multi
	def print_compare_payroll(self):
		#raise Warning("Ready to print")
		#raise Warning("Information: %s" % self.previous_project_history_id)
		if self.payslip_ids:
			return self.env['report'].get_action(self,'hr_payroll_allowance.project_compare_history_template')
		else:
			raise Warning('Sorry, there is no payslip for this project during this Month')

	@api.multi
	def print_employee_taxes(self):
#		raise Warning("Ready to print")
		if self.payslip_ids:
			return self.env['report'].get_action(self,'hr_payroll_allowance.employee_taxes_project_history_template')
		else:
			raise Warning('Sorry, there is no payslip for this project during this Month')

	@api.one
	@api.depends('payslip_batch_id','month')
	def _update_payroll_taxes(self):
		content = ""
		wb = Workbook()
		sheet = wb.add_sheet('GHSS Payroll Taxes')
		
		# SN column
		sheet.col(0).width = 256 * 8
		
		# Name Column
		sheet.col(1).width = 256 * 40
		
		# Gross Salary Column
		sheet.col(2).width = 256 * 12
		
		# Non Taxable Element
		sheet.col(3).width = 256 * 10 # Represent Allowance
		sheet.col(4).width = 256 * 10 # Risk Allowance
		sheet.col(5).width = 256 * 12 # Total
		
		# Taxable Salary
		sheet.col(6).width = 256 * 12

		# Taxes Paid
		sheet.col(7).width = 256 * 10 # PIT
		sheet.col(8).width = 256 * 10 # CAC
		sheet.col(9).width = 256 * 10 # CCFs
		sheet.col(10).width = 256 * 10 # CCFp
		sheet.col(11).width = 256 * 10 # CRTV
		sheet.col(12).width = 256 * 10 # LDT
		sheet.col(13).width = 256 * 10 # FNE
		sheet.col(14).width = 256 * 12 # Total
		
		style_total_title = easyxf('font: bold on; align: horiz center; align: wrap on; border: left thin, right thin, top thin, bottom thin')
		style_total_amount = easyxf('font: bold on;')
		style_amount = easyxf()
		style_total_amount.num_format_str = '#,##0'
		style_amount.num_format_str = '#,##0'
		
		xls_file = StringIO.StringIO()
		
		line_number = 1
		
		title = "Taxes of %s - %s" % (self.project_id.name,self.month)
		sheet.write_merge(line_number,line_number,0,14,title,style_total_title)
		
		line_number = 3
		
		sheet.write_merge(line_number,line_number+1,0,0,"SN",style_total_title)
		sheet.write_merge(line_number,line_number+1,1,1,"NAME",style_total_title)
		
		sheet.write_merge(line_number,line_number+1,2,2,"GROSS SALARY",style_total_title)
		
		sheet.write_merge(line_number,line_number,3,5,"ELEMENT OF NON TAXABLE SALARY",style_total_title)
		sheet.write_merge(line_number+1,line_number+1,3,3,"REP ALL",style_total_title)
		sheet.write_merge(line_number+1,line_number+1,4,4,"RISK ALL",style_total_title)
		sheet.write_merge(line_number+1,line_number+1,5,5,"TOTAL",style_total_title)
		
		sheet.write_merge(line_number,line_number+1,6,6,"TAXABLE SALARY",style_total_title)
		
		sheet.write_merge(line_number,line_number,7,14,"TOTAL PAID",style_total_title)
		sheet.write_merge(line_number+1,line_number+1,7,7,"PIT",style_total_title)
		sheet.write_merge(line_number+1,line_number+1,8,8,"CAC",style_total_title)
		sheet.write_merge(line_number+1,line_number+1,9,9,"CCFs",style_total_title)
		sheet.write_merge(line_number+1,line_number+1,10,10,"CCFp",style_total_title)
		sheet.write_merge(line_number+1,line_number+1,11,11,"CRTV",style_total_title)
		sheet.write_merge(line_number+1,line_number+1,12,12,"LDT",style_total_title)
		sheet.write_merge(line_number+1,line_number+1,13,13,"FNE",style_total_title)
		sheet.write_merge(line_number+1,line_number+1,14,14,"TOTAL",style_total_title)

		line_number += 1
		date_start = self.payslip_batch_id.date_start
		date_end = self.payslip_batch_id.date_end
		if self.payslip_ids:
			for payslip in self.payslip_ids:
				#
				perc=100
				contract_job_ids = self.get_contract_jobs(payslip.contract_id, date_start, date_end)
				for contract in contract_job_ids:
					contract = self.env['hr.contract.job'].search([('id','=',contract)])
					if self.project_id.id == contract.project_id.id:
						if len(contract_job_ids)>1:
							perc = contract.percentage
						#gross_salary = contract.wage 
				#
				
				line_number += 1
				sheet.write(line_number,0,payslip.employee_id.matricule)
				sheet.write(line_number,1,payslip.employee_id.real_name)
				sheet.write(line_number,2,payslip.gross_salary*perc/100.0,style_total_amount)
				#sheet.write(line_number,2,gross_salary,style_total_amount)
				sheet.write(line_number,3,payslip.represent*perc/100.0,style_amount)
				sheet.write(line_number,4,payslip.risk*perc/100.0,style_amount)
#				allowances = '=D%s+E%s' % (line_number+1,line_number+1)
				allowances = int(payslip.represent*perc/100.0) + int(payslip.risk*perc/100.0)
				sheet.write(line_number,5,allowances,style_total_amount)
				
				sheet.write(line_number,6,payslip.taxable_salary*perc/100.0,style_total_amount)
				
				sheet.write(line_number,7,payslip.pit*perc/100.0,style_amount)
				sheet.write(line_number,8,payslip.act*perc/100.0,style_amount)
				sheet.write(line_number,9,payslip.cfce*perc/100.0,style_amount)
				sheet.write(line_number,10,payslip.cfcp*perc/100.0,style_amount)
				sheet.write(line_number,11,payslip.crtv*perc/100.0,style_amount)
				sheet.write(line_number,12,payslip.ctax*perc/100.0,style_amount)
				sheet.write(line_number,13,payslip.fne*perc/100.0,style_amount)
				taxes = int(payslip.pit*perc/100.0) + int(payslip.act*perc/100.0) + int(payslip.cfce*perc/100.0)
				taxes += int(payslip.cfcp*perc/100.0) + int(payslip.crtv*perc/100.0) + int(payslip.ctax*perc/100.0)
				taxes += int(payslip.fne*perc/100.0)
				sheet.write(line_number,14,taxes,style_total_amount)

		wb.save(xls_file)
		xls_content = xls_file.getvalue()
		xls_file.close()
#		raise Warning("Value of Payroll Date %s" % (the_date))
		self.payroll_taxes_file = base64.b64encode(xls_content)
		self.patroll_taxes_name = "Taxes_%s.xls" % (self.project_id.name)

	@api.one
	@api.depends('payslip_batch_id','month')
	def _update_transfert(self):
		content = ""
		wb = Workbook()
		sheet = wb.add_sheet('GHSS Account Transfer')
		sheet.col(0).width = 256 * 50
		sheet.col(1).width = 256 * 60
		sheet.col(2).width = 256 * 25
		sheet.col(3).width = 256 * 12
		
		style_total_title = easyxf('font: bold on; align: horiz center;')
		style_total_amount = easyxf('font: bold on;')
		style_amount = easyxf()
		style_total_amount.num_format_str = '#,##0'
		style_amount.num_format_str = '#,##0'
		
		line_number = 0
		xls_file = StringIO.StringIO()
				
		if self.payslip_batch_id and self.payslip_batch_id.slip_ids:
			sheet.write(line_number,0,"Bank")
			sheet.write(line_number,1,"Name")
			sheet.write(line_number,2,"Account Number")
			sheet.write(line_number,3,"Net Payment")
			line_number += 2
			
			current_bank = 0
			
			ecobank_name = []
			ecobank_employee = []
			ecobank_account = []
			ecobank_net = []
			
			other_name = []
			other_employee = []
			other_account = []
			other_net = []
			
			total_ecobank = 0
			total_other = 0
			total_net_payment = 0
			date_start = self.payslip_batch_id.date_start
			date_end = self.payslip_batch_id.date_end
			for payslip in self.payslip_with_bank_account_ids:
				
				if current_bank == 0 and payslip.employee_id.bank_account_ids:
					current_bank = payslip.employee_id.bank_account_ids[0].bank_id.id

				if payslip.employee_id.bank_account_ids and current_bank != payslip.employee_id.bank_account_ids[0].bank_id.id:
					current_bank = payslip.employee_id.bank_account_ids[0].bank_id.id
					
					line_number += 1
					sheet.write_merge(line_number,line_number,0,2,"TOTAL",style_total_title)
					sheet.write(line_number,3,total_net_payment,style_total_amount)
					line_number += 2
					total_net_payment = 0
					
				if payslip.employee_id.bank_account_ids and current_bank == payslip.employee_id.bank_account_ids[0].bank_id.id:
					#
					perc=0
					net = payslip.net
					contract_job_ids = self.get_contract_jobs(payslip.contract_id, date_start, date_end)
					for contract in contract_job_ids:
						contract=self.env['hr.contract.job'].search([('id','=',contract)])
						if self.project_id.id == contract.project_id.id:
							if len(contract_job_ids)>1:
								perc = contract.percentage
								net = payslip.net * perc/100.0

					bank_name = payslip.employee_id.bank_account_ids[0].bank_id.name
					employee_name = payslip.employee_id.real_name
					bank_account_number = payslip.employee_id.bank_account_ids[0].name
					#net_payment = payslip.net * perc/100.0
					net_payment = net
					
					sheet.write(line_number,0,bank_name)
					sheet.write(line_number,1,employee_name)
					sheet.write(line_number,2,bank_account_number)
					sheet.write(line_number,3,net_payment,style_amount)
					total_net_payment += net_payment
					
					line_number += 1
			
			if current_bank != 0:
				line_number += 1
				sheet.write_merge(line_number,line_number,0,2,"TOTAL",style_total_title)
				sheet.write(line_number,3,total_net_payment,style_total_amount)
		
		wb.save(xls_file)
		xls_content = xls_file.getvalue()
		xls_file.close()
#		raise Warning("Value of Payroll Date %s" % (the_date))
		self.monthly_wire_transfert = base64.b64encode(xls_content)
		self.wire_transfert_name = "monthly_transfert_%s.xls" % (self.project_id.name)

	@api.one
	@api.depends('payslip_batch_id','month')
	def _update_dipe_pit_project(self):
		content = ""
		wb = Workbook()
		sheet = wb.add_sheet('GHSS DIPE PIT')
		sheet.col(0).width = 256 * 50
		sheet.col(1).width = 256 * 5
		sheet.col(2).width = 256 * 15
		sheet.col(3).width = 256 * 15
		sheet.col(4).width = 256 * 15
		sheet.col(5).width = 256 * 15
		sheet.col(6).width = 256 * 15
		sheet.col(7).width = 256 * 15
		sheet.col(8).width = 256 * 15
		sheet.col(9).width = 256 * 15
		sheet.col(10).width = 256 * 15
		
		style_total_title = easyxf('font: bold on; align: horiz center; align: vert center;')
		style_total_amount = easyxf('font: bold on;')
		style_amount = easyxf()
		style_total_amount.num_format_str = '#,##0'
		style_amount.num_format_str = '#,##0'
		
		line_number = 0
		xls_file = StringIO.StringIO()

		sheet.write_merge(line_number,line_number+1,0,10,"PIT - %s (%s)"  % (self.project_id.name,self.month),style_total_title)
		
		line_number += 3
		
		if self.payslip_batch_id and self.payslip_batch_id.slip_ids:
			sheet.write_merge(line_number,line_number+1,0,0,"Name",style_total_title)
			sheet.write_merge(line_number,line_number+1,1,1,"Days",style_total_title)
			sheet.write_merge(line_number,line_number+1,2,2,"Gross",style_total_title)
			sheet.write_merge(line_number,line_number+1,3,3,"Taxable",style_total_title)
			sheet.write_merge(line_number,line_number+1,4,4,"PIT",style_total_title)
			sheet.write_merge(line_number,line_number+1,5,5,"CAC",style_total_title)
			sheet.write_merge(line_number,line_number,6,7,"Credit Foncier",style_total_title)
			sheet.write_merge(line_number+1,line_number+1,6,6,"Employee",style_total_title)
			sheet.write_merge(line_number+1,line_number+1,7,7,"Employer",style_total_title)
			sheet.write_merge(line_number,line_number+1,8,8,"CRTV",style_total_title)
			sheet.write_merge(line_number,line_number+1,9,9,"Communal Tax",style_total_title)
			sheet.write_merge(line_number,line_number+1,10,10,"FNE",style_total_title)
			
			line_number += 2
			date_start = self.payslip_batch_id.date_start
			date_end = self.payslip_batch_id.date_end
			for payslip in self.payslip_batch_id.slip_ids:
				if payslip.contract_id in self.contract_ids:
					#
					perc=100
					gross_salary = payslip.gross_salary
					contract_job_ids = self.get_contract_jobs(payslip.contract_id, date_start, date_end)
					for contract in contract_job_ids:
						contract = self.env['hr.contract.job'].search([('id','=',contract)])
						if self.project_id.id == contract.project_id.id:
							if len(contract_job_ids)>1:
								perc = contract.percentage
							gross_salary = contract.wage 
                    #
					sheet.write(line_number,0,payslip.employee_id.real_name)
					sheet.write(line_number,1,payslip.worked_days,style_amount)
					#sheet.write(line_number,2,payslip.gross_salary,style_amount)
					sheet.write(line_number,2,gross_salary,style_amount)
					sheet.write(line_number,3,payslip.taxable_salary*perc/100.0,style_amount)
					sheet.write(line_number,4,payslip.pit*perc/100.0,style_amount)
					sheet.write(line_number,5,payslip.act*perc/100.0,style_amount)
					sheet.write(line_number,6,payslip.cfce*perc/100.0,style_amount)
					sheet.write(line_number,7,payslip.cfcp*perc/100.0,style_amount)
					sheet.write(line_number,8,payslip.crtv*perc/100.0,style_amount)
					sheet.write(line_number,9,payslip.ctax*perc/100.0,style_amount)
					sheet.write(line_number,10,payslip.fne*perc/100.0,style_amount)
					
					line_number += 1

			sheet.write_merge(line_number,line_number,0,1,"TOTAL",style_total_title)
			sheet.write(line_number,2,self.total_gross,style_total_amount)
			sheet.write(line_number,3,self.total_taxable,style_total_amount)
			sheet.write(line_number,4,self.total_pit,style_total_amount)
			sheet.write(line_number,5,self.total_act,style_total_amount)
			sheet.write(line_number,6,self.total_cfce,style_total_amount)
			sheet.write(line_number,7,self.total_cfcp,style_total_amount)
			sheet.write(line_number,8,self.total_crtv,style_total_amount)
			sheet.write(line_number,9,self.total_ctax,style_total_amount)
			sheet.write(line_number,10,self.total_fne,style_total_amount)
		
		wb.save(xls_file)
		xls_content = xls_file.getvalue()
		xls_file.close()
#		raise Warning("Value of Payroll Date %s" % (the_date))
		self.dipe_pit_project_file = base64.b64encode(xls_content)
		self.dipe_pit_project_name = "dipe_pit_%s.xls" % (self.project_id.name)

	@api.one
	@api.depends('payslip_batch_id','month')
	def _update_payroll_component_project(self):
		content = ""
		wb = Workbook()
		sheet = wb.add_sheet('GHSS PAYROLL COMPONENENTS')
		sheet.col(0).width = 256 * 50
		sheet.col(1).width = 256 * 50
		
		style_total_title = easyxf('font: bold on; align: horiz center; align: vert center;')
		style_total_amount = easyxf('font: bold on;')
		style_amount = easyxf()
		style_total_amount.num_format_str = '#,##0'
		style_amount.num_format_str = '#,##0'
		
		line_number = 0
		xls_file = StringIO.StringIO()

		sheet.write_merge(line_number,line_number+1,0,2,"PAYROLL COMPONENETS - %s (%s)"  % (self.project_id.name,self.month),style_total_title)
		
		line_number += 3
		
		if self.payslip_batch_id.slip_ids:
			sheet.write_merge(line_number,line_number+1,0,1,"SUMMARY",style_total_title)
			
			line_number += 2
			sheet.write(line_number,0,"Designation",style_total_title)
			sheet.write(line_number,1,"Amount",style_total_title)
			
			line_number += 1
			
			sheet.write(line_number,0,"BASIC")
			sheet.write(line_number,1,self.total_basic,style_amount)
			
			line_number += 2
			
			sheet.write_merge(line_number,line_number,0,1,"ALLOWANCES",style_total_title)
			date_start = self.payslip_batch_id.date_start
			date_end = self.payslip_batch_id.date_end
			for allowance in self.allowance_ids:
				amount = 0
				for payslip in self.payslip_batch_id.slip_ids:
					if payslip.contract_id in self.contract_ids:
						#
						perc=100.00
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
				line_number += 1
				sheet.write(line_number,0,allowance.allowance_id.name)
				sheet.write(line_number,1,amount,style_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Gross Salary",style_total_title)
			sheet.write(line_number,1,self.total_gross,style_total_amount)
					
			line_number += 2
			
			sheet.write(line_number,0,"Taxable Salary",style_total_title)
			sheet.write(line_number,1,self.total_taxable,style_total_amount)
			
			line_number += 2
			
			sheet.write_merge(line_number,line_number,0,1,"Employee Deductions",style_total_title)
			
			line_number += 1
			
			sheet.write(line_number,0,"PIT")
			sheet.write(line_number,1,self.total_pit,style_amount)
		
			line_number += 1
			
			sheet.write(line_number,0,"ACT")
			sheet.write(line_number,1,self.total_act,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Land Bank Rate")
			sheet.write(line_number,1,self.total_cfce,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"CRTV")
			sheet.write(line_number,1,self.total_crtv,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Communal Tax")
			sheet.write(line_number,1,self.total_ctax,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Old age pension (CNPS) - Employee")
			sheet.write(line_number,1,self.total_cnpse,style_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Total Employee Tax Deductions",style_total_title)
			sheet.write(line_number,1,self.total_taxes_employees_basic,style_total_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Other Deductions")
			sheet.write(line_number,1,self.total_other_deductions,style_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Total Employee Deductions",style_total_title)
			sheet.write(line_number,1,self.total_taxes_employees,style_total_amount)
			
			line_number += 2
			
			sheet.write_merge(line_number,line_number,0,1,"Employer Deductions",style_total_title)
			
			line_number += 1
			
			sheet.write(line_number,0,"CFC")
			sheet.write(line_number,1,self.total_cfcp,style_amount)
		
			line_number += 1
			
			sheet.write(line_number,0,"FNE")
			sheet.write(line_number,1,self.total_fne,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Family Contribution")
			sheet.write(line_number,1,self.total_fcon,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Old age pension (CNPS) - Employer")
			sheet.write(line_number,1,self.total_cnpsp,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Industrial and Profesional Accident")
			sheet.write(line_number,1,self.total_ipa,style_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Total Employer Tax Deductions",style_total_title)
			sheet.write(line_number,1,self.total_taxes_employer,style_total_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Net Payment",style_total_title)
			sheet.write(line_number,1,self.total_net,style_total_amount)
			
		
		wb.save(xls_file)
		xls_content = xls_file.getvalue()
		xls_file.close()
#		raise Warning("Value of Payroll Date %s" % (the_date))
		self.payroll_component_project_file = base64.b64encode(xls_content)
		self.patroll_component_project_name = "payroll_componenets_%s.xls" % (self.project_id.name)
	
class HR_Payslip_Batch_run(models.Model):

	_inherit = 'hr.payslip.run'
	
	@api.one
	def generate_dipe(self):
		super(HR_Payslip_Batch_run,self).generate_dipe()
		payslip_run_id = self.id
		history_obj = self.env['hr.contract.project.history']
		project_obj = self.env['hr.contract.project.template']
		
		project_ids = project_obj.search([])
		
		if self.slip_ids:
			for payslip in self.slip_ids:
				for contract in payslip.contract_id.contract_job_ids:
					project_history_id = history_obj.search([('project_id','=',contract.project_id.id),('payslip_batch_id','=',self.id)])
					if not project_history_id:
						name = "%s - %s" % (contract.project_id.name,self.name)
						project_id = contract.project_id.id
						project_history_id = history_obj.create({'name': name, 'project_id': project_id, 'payslip_batch_id':payslip_run_id})
					project_history_id.contract_ids = [(4, payslip.contract_id.id)]
		
        #raise Warning("Number of Project: %s" % len(project_ids))
		
	@api.one
	def cancel_dipe(self):
		project_history_ids = self.env['hr.contract.project.history'].search([('payslip_batch_id','=',self.id)])
		
		if project_history_ids:
			project_history_ids.unlink()
			
		super(HR_Payslip_Batch_run,self).cancel_dipe()

		
class HR_Contract(models.Model):

	_inherit = 'hr.contract'
	
	project_id = fields.Many2many('hr.contract.project','hr_contract_project_rel',string="Project")
	project_template_id = fields.Many2one('hr.contract.project.template',string="Project")
	project_history_ids = fields.Many2many('hr.contract.project.history','my_hr_contract_id','my_hr_contract_project_history_id',string="Project")

class HR_Payroll_Group(models.Model):

	_name = 'hr.contract.project'
	
	name = fields.Char(string="Name",required=True)
#	contract_ids = fields.One2many('hr.contract','project_id',string="Contracts")
	contract_ids = fields.Many2many('hr.contract','hr_contract_project_rel',string="Contracts")
	nb_contract = fields.Integer(string="Number of Contracts",compute='_nb_contracts')
	
	@api.one
	@api.depends('contract_ids')
	def _nb_contracts(self):
		self.nb_contract = 0
		
		if self.contract_ids:
			self.nb_contract = len(self.contract_ids)
			
	@api.multi
	def print_dipe_pit(self):
		wizard_form = self.env.ref('hr_payroll_allowance.hr_payroll_project_pit_wizard_view',False)
		view_id = self.env['hr.payroll.project.pit.wizard']
		vals = {
			'project_id'	: self.id,
			}
		new_info = view_id.create(vals)
		return {
			'name'		:	_('Project'),
			'type'		:	'ir.actions.act_window',
			'res_model'	:	'hr.payroll.project.pit.wizard',
			'res_id'	:	new_info.id,
			'view_id'	:	wizard_form.id,
			'view_type'	:	'form',
			'view_mode'	:	'form',
			'target'	:	'new'
			}

class HR_Payroll_Project_Allowance(models.TransientModel):
	_name = 'hr.payroll.project.pit.wizard.allowance'
	
	allowance_id = fields.Many2one('hr.payroll.allowance.set',readonly=True)
	total_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'),readonly=True)
	wizard_id = fields.Many2one('hr.payroll.project.pit.wizard',string="Wiazrd")
			
class HR_Payroll_Project_Wizard(models.TransientModel):
	_name = 'hr.payroll.project.pit.wizard'
	
	project_id = fields.Many2one('hr.contract.project',string="Project")
	payroll_batch_id = fields.Many2one('hr.payslip.run',string="Month")
	payslip_ids = fields.Many2many('hr.payslip',compute='_get_payslips',readonly=True)
	company_id = fields.Many2one('res.company',string="Company",compute='_get_payslips',readonly=True)
	month = fields.Char(string="Month of payslip",compute='_get_month')
	nb_pages = fields.Integer(string="Number of pages",compute='_get_pages')
	total_gross = fields.Float(string="Gross",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxable = fields.Float(string="Taxable",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_pit = fields.Float(string="PIT",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_ctax = fields.Float(string="Communal Tax",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_act = fields.Float(string="ACT",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_cfce = fields.Float(string="CFC Employee",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_cfcp = fields.Float(string="CFC Employer",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_cnpse = fields.Float(string="CNPS Employee",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_cnpsp = fields.Float(string="CNPS Employer",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_fne = fields.Float(string="FNE",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_crtv = fields.Float(string="CRTV",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_ipa = fields.Float(string="IPA",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_fcon = fields.Float(string="Familly Contribution",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxes = fields.Float(string="Total Deduction",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxes_employees = fields.Float(string="Total Deduction - Employees",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxes_employees_basic = fields.Float(string="Total Deduction - Employees Basic",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxes_employer = fields.Float(string="Total Deduction - Employer",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_net = fields.Float(string="Total Net",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_basic = fields.Float(string="Total Basic",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_other_deductions = fields.Float(string="Total Other Deductions",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	total_taxes_deductions = fields.Float(string="Total Tax Deductions",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	wire_transfert_name = fields.Char("Wire Transfert File Name",compute='_update_transfert')
	monthly_wire_transfert = fields.Binary(string="Monthly Wire Transfert",compute='_update_transfert')
	dipe_pit_project_name = fields.Char("Dipe PIT File Name",compute='_update_dipe_pit_project')
	dipe_pit_project_file = fields.Binary(string="Dipe PIT Project File",compute='_update_dipe_pit_project')
	patroll_component_project_name = fields.Char("Payroll Component File Name",compute='_update_payroll_component_project')
	payroll_component_project_file = fields.Binary(string="Payroll Component Project File",compute='_update_payroll_component_project')
	payslip_with_bank_account_ids = fields.Many2many('hr.payslip',compute='_get_amount',readonly=True)
	bank_ids = fields.Many2many('hr.bank',compute='_get_amount')
	nb_bank = fields.Integer(string="Bank number",compute='_get_amount')
	allowance_set_ids = fields.Many2many('hr.payroll.allowance.set',compute='_get_allowance_set')
	nb_allowances = fields.Integer(string="Allowances Set Number",compute='_get_allowance_set')
	allowance_ids = fields.Many2many('hr.payroll.project.pit.wizard.allowance',string="Allowances",compute='_get_amount')
	previous_payroll_project_wizard_id = fields.Many2one('hr.payroll.project.pit.wizard',string="Previous Month Wizard",compute='_get_previous_wizard')
	nb_payslips = fields.Integer(string="Number of Payslips",compute='_get_nb_payslips',readonly=True)
	
	@api.one
	@api.depends('payslip_ids')
	def _get_nb_payslips(self):
		self.nb_payslips = len(self.payslip_ids)
	
	@api.one
	def _get_allowance_set(self):
		self.allowance_set_ids = self.env['hr.payroll.allowance.set'].search([]).sorted(key=lambda r: r.sequence)
		self.nb_allowances = len(self.allowance_set_ids)
	
	@api.model
	def get_contract_jobs(self, contract, date_from, date_to):
        # a contract job is valid if it ends between the given dates
		clause_1 = ['&', ('end_date', '<=', date_to), ('end_date', '>=', date_from)]
        # OR if it starts between the given dates
		clause_2 = ['&', ('start_date', '<=', date_to), ('start_date', '>=', date_from)]
        # OR if it starts before the date_from and finish after the end_date (or never finish)
		clause_3 = ['&', ('start_date', '<=', date_from), '|', ('end_date', '=', False), ('end_date', '>=', date_to)]
		clause_final = [('contract_id', '=', contract.id), '|', '|'] + clause_1 + clause_2 + clause_3
		return self.env['hr.contract.job'].search(clause_final).ids
    
	@api.one
	@api.depends('payslip_ids')
	def _get_amount(self):
		self.total_gross = 0
		self.total_taxable = 0
		self.total_pit = 0
		self.total_act = 0
		self.total_ctax = 0
		self.total_cfce = 0
		self.total_cfcp = 0
		self.total_fne = 0
		self.total_crtv = 0
		self.total_cnpse = 0
		self.total_cnpsp = 0
		self.total_ipa = 0
		self.total_fcon = 0
		self.total_net = 0
		self.total_basic = 0
		self.total_other_deductions = 0
		
		if self.payslip_ids:
			allowances = []
			allowance_obj = self.env['hr.payroll.project.pit.wizard.allowance']
			for allowance in self.allowance_set_ids:
				allowance_id = allowance_obj.create({'allowance_id':allowance.id,'total_amount':0,'wizard_id':self.id})
				allowances.append(allowance_id.id)
#				self.allowance_ids = [(4,[allowance_id.id])]
			
			self.allowance_ids = [(6,0,allowances)]
			
			#raise Warning("Value of allowances IDS : %s" % (allowance_ids))
			
			for slip in self.payslip_ids:
				perc=0
				if slip.contract_id in self.contract_ids:
					#
					for contract in slip.contract_id.contract_job_ids:
						if self.project_id.id == contract.project_id.id:
							perc = contract.percentage
					#
				#
				self.total_gross += slip.gross_salary * perc/100.0
				self.total_taxable += slip.taxable_salary * perc/100.0
				self.total_pit += slip.pit * perc/100.0
				self.total_act += slip.act * perc/100.0
				self.total_ctax += slip.ctax * perc/100.0
				self.total_cfce += slip.cfce * perc/100.0
				self.total_cfcp += slip.cfcp * perc/100.0
				self.total_fne += slip.fne * perc/100.0
				self.total_crtv += slip.crtv * perc/100.0
				self.total_net += slip.net * perc/100.0
				self.total_basic += slip.basic * perc/100.0
				self.total_cnpse += slip.cnpse * perc/100.0
				self.total_cnpsp += slip.cnpsp * perc/100.0
				self.total_ipa += slip.ipa * perc/100.0
				self.total_fcon += slip.fcon * perc/100.0
				self.total_other_deductions += slip.extra_deduction * perc/100.0
				
	
		self.total_taxes = self.total_pit + self.total_act + self.total_ctax + self.total_crtv
		self.total_taxes += self.total_cfce + self.total_cfcp + self.total_fne 
		self.total_taxes_employees_basic = self.total_pit + self.total_act + self.total_ctax + self.total_cfce
		self.total_taxes_employees_basic += self.total_cnpse + self.total_crtv
		self.total_taxes_employees = self.total_pit + self.total_act + self.total_ctax + self.total_cfce
		self.total_taxes_employees += self.total_cnpse + self.total_crtv + self.total_other_deductions
		self.total_taxes_employer = self.total_cfcp + self.total_fne + self.total_fcon
		self.total_taxes_employer += self.total_cnpsp + self.total_ipa
		self.total_taxes_deductions = self.total_taxes_employees + self.total_taxes_employer
		self.payslip_with_bank_account_ids = self.payslip_ids.filtered(lambda r: len(r.employee_id.bank_account_ids) > 0).sorted(key=lambda r: r.employee_id.bank_account_ids[0].bank_id.id)
	
		bank_ids = []
		for payslip in self.payslip_with_bank_account_ids:
			my_id = payslip.employee_id.bank_account_ids[0].bank_id.id
			if not my_id in bank_ids:
				bank_ids.append(payslip.employee_id.bank_account_ids[0].bank_id.id)
				
		self.bank_ids = self.env['hr.bank'].search([('id','in',bank_ids)])
		self.nb_bank = len(self.bank_ids)
	
	@api.one
	@api.depends('project_id','payroll_batch_id')
	def _get_previous_wizard(self):
		if self.project_id and self.payroll_batch_id:
			wizard_obj = self.env['hr.payroll.project.pit.wizard']
			values = {'project_id':self.project_id.id,'payroll_batch_id':self.payroll_batch_id.previous_payslip_run_id.id,'level':2}
			res = wizard_obj.create(values)
			self.previous_payroll_project_wizard_id = res
		else:
			self.previous_payroll_project_wizard_id = None
	
	@api.one
	@api.depends('project_id','payroll_batch_id')
	def _get_payslips(self):
		if self.project_id and self.payroll_batch_id and self.payroll_batch_id.slip_ids:
			temp = []
#			temp = self.payroll_batch_id.slip_ids.search([()])
			for payslip in self.payroll_batch_id.slip_ids:
				if payslip.contract_id and payslip.contract_id.project_id and (self.project_id in payslip.contract_id.project_id):
					temp.append(payslip.id)
			self.payslip_ids = self.payroll_batch_id.slip_ids.filtered(lambda r: r.id in temp)
			#self.payslip_ids = self.payroll_batch_id.slip_ids.filtered(lambda r: r.contract_id.project_id and  (for proj_id in r.contract_id.project_id: if proj_id.id == self.project_id: ))
			if self.payslip_ids:
				self.company_id = self.payslip_ids[0].employee_id.company_id.id	
		else:
			self.payslip_ids = None
			self.company_id = None

	@api.one
	@api.depends('payslip_ids')
	def _get_pages(self):
		if self.payslip_ids:
			self.nb_pages = (len(self.payslip_ids) / 16 ) + 1
		else:
			self.nb_pages = 0
	
	@api.multi
	def print_dipe(self):
		if self.payroll_batch_id:
#			raise Warning("Payslips : %s " % self.payslip_ids)
			return self.env['report'].get_action(self,'hr_payroll_allowance.dipe_project_pit_template')
		else:
			raise Warning('Please select a Payslip Month')

	@api.multi
	def print_allowances(self):
		if self.payroll_batch_id:
			return self.env['report'].get_action(self,'hr_payroll_allowance.allowances_project_template')
		else:
			raise Warning('Please select a Payslip Month')
	
	@api.multi
	def print_compare_payroll(self):
		if self.payroll_batch_id:
			return self.env['report'].get_action(self,'hr_payroll_allowance.project_compare_template')
		else:
			raise Warning('Please select a Payslip Month')
	
	@api.multi
	def get_transfert_pdf(self):
		if self.payroll_batch_id:
			return self.env['report'].get_action(self,'hr_payroll_allowance.wire_transfert_project_template')
		else:
			raise Warning('Please select a Payslip Month')
			
	@api.multi
	def get_transfert_xls(self):
		return {
			'type':'ir.actions.act_url',
			'url':'/web/binary/download_document?model=hr.payroll.project.pit.wizard&field=monthly_wire_transfert&id=%s&filename=monthly_transfert_%s_%s.xls'%(self.id,self.project_id.name,self.month),
			'target':'self',
		}
		
	@api.multi
	def get_dipe_pit_xls(self):
		return {
			'type':'ir.actions.act_url',
			'url':'/web/binary/download_document?model=hr.payroll.project.pit.wizard&field=dipe_pit_project_file&id=%s&filename=dipe_pit_%s_%s.xls'%(self.id,self.project_id.name,self.month),
			'target':'self',
		}
	
	@api.multi
	def get_payroll_components_xls(self):
		return {
			'type':'ir.actions.act_url',
			'url':'/web/binary/download_document?model=hr.payroll.project.pit.wizard&field=payroll_component_project_file&id=%s&filename=payroll_componenets_%s_%s.xls'%(self.id,self.project_id.name,self.month),
			'target':'self',
		}
	
	@api.one
	@api.depends('payroll_batch_id')
	def _get_month(self):
		if self.payroll_batch_id:
			the_date = datetime.strptime(self.payroll_batch_id.date_end,'%Y-%m-%d')
			the_month = the_date.month
			the_year = the_date.year
			self.month = "%s %s" % (MONTHS[the_month - 1],the_year)
		else:
			self.month = ""

	@api.one
	@api.depends('payslip_ids','month')
	def _update_transfert(self):
		content = ""
		wb = Workbook()
		sheet = wb.add_sheet('GHSS Account Transfer')
		sheet.col(0).width = 256 * 50
		sheet.col(1).width = 256 * 60
		sheet.col(2).width = 256 * 25
		sheet.col(3).width = 256 * 12
		
		style_total_title = easyxf('font: bold on; align: horiz center;')
		style_total_amount = easyxf('font: bold on;')
		style_amount = easyxf()
		style_total_amount.num_format_str = '#,##0'
		style_amount.num_format_str = '#,##0'
		
		line_number = 0
		xls_file = StringIO.StringIO()
				
		if self.payslip_ids:
			sheet.write(line_number,0,"Bank")
			sheet.write(line_number,1,"Name")
			sheet.write(line_number,2,"Account Number")
			sheet.write(line_number,3,"Net Payment")
			line_number += 2
			
			current_bank = 0
			
			ecobank_name = []
			ecobank_employee = []
			ecobank_account = []
			ecobank_net = []
			
			other_name = []
			other_employee = []
			other_account = []
			other_net = []
			
			total_ecobank = 0
			total_other = 0
			total_net_payment = 0
			
			for payslip in self.payslip_with_bank_account_ids:
				
				if current_bank == 0 and payslip.employee_id.bank_account_ids:
					current_bank = payslip.employee_id.bank_account_ids[0].bank_id.id

				if payslip.employee_id.bank_account_ids and current_bank != payslip.employee_id.bank_account_ids[0].bank_id.id:
					current_bank = payslip.employee_id.bank_account_ids[0].bank_id.id
					
					line_number += 1
					sheet.write_merge(line_number,line_number,0,2,"TOTAL",style_total_title)
					sheet.write(line_number,3,total_net_payment,style_total_amount)
					line_number += 2
					total_net_payment = 0
					
				if payslip.employee_id.bank_account_ids and current_bank == payslip.employee_id.bank_account_ids[0].bank_id.id:
					bank_name = payslip.employee_id.bank_account_ids[0].bank_id.name
					employee_name = payslip.employee_id.real_name
					bank_account_number = payslip.employee_id.bank_account_ids[0].name
					net_payment = payslip.net
					
					sheet.write(line_number,0,bank_name)
					sheet.write(line_number,1,employee_name)
					sheet.write(line_number,2,bank_account_number)
					sheet.write(line_number,3,net_payment,style_amount)
					total_net_payment += net_payment
					
					line_number += 1
			
			if current_bank != 0:
				line_number += 1
				sheet.write_merge(line_number,line_number,0,2,"TOTAL",style_total_title)
				sheet.write(line_number,3,total_net_payment,style_total_amount)
		
		wb.save(xls_file)
		xls_content = xls_file.getvalue()
		xls_file.close()
#		raise Warning("Value of Payroll Date %s" % (the_date))
		self.monthly_wire_transfert = base64.b64encode(xls_content)
		self.wire_transfert_name = "monthly_transfert_%s.xls" % (self.project_id.name)

	@api.one
	@api.depends('payslip_ids','month')
	def _update_dipe_pit_project(self):
		content = ""
		wb = Workbook()
		sheet = wb.add_sheet('GHSS DIPE PIT')
		sheet.col(0).width = 256 * 50
		sheet.col(1).width = 256 * 5
		sheet.col(2).width = 256 * 15
		sheet.col(3).width = 256 * 15
		sheet.col(4).width = 256 * 15
		sheet.col(5).width = 256 * 15
		sheet.col(6).width = 256 * 15
		sheet.col(7).width = 256 * 15
		sheet.col(8).width = 256 * 15
		sheet.col(9).width = 256 * 15
		sheet.col(10).width = 256 * 15
		
		style_total_title = easyxf('font: bold on; align: horiz center; align: vert center;')
		style_total_amount = easyxf('font: bold on;')
		style_amount = easyxf()
		style_total_amount.num_format_str = '#,##0'
		style_amount.num_format_str = '#,##0'
		
		line_number = 0
		xls_file = StringIO.StringIO()

		sheet.write_merge(line_number,line_number+1,0,10,"PIT - %s (%s)"  % (self.project_id.name,self.month),style_total_title)
		
		line_number += 3
		
		if self.payslip_ids:
			sheet.write_merge(line_number,line_number+1,0,0,"Name",style_total_title)
			sheet.write_merge(line_number,line_number+1,1,1,"Days",style_total_title)
			sheet.write_merge(line_number,line_number+1,2,2,"Gross",style_total_title)
			sheet.write_merge(line_number,line_number+1,3,3,"Taxable",style_total_title)
			sheet.write_merge(line_number,line_number+1,4,4,"PIT",style_total_title)
			sheet.write_merge(line_number,line_number+1,5,5,"CAC",style_total_title)
			sheet.write_merge(line_number,line_number,6,7,"Credit Foncier",style_total_title)
			sheet.write_merge(line_number+1,line_number+1,6,6,"Employee",style_total_title)
			sheet.write_merge(line_number+1,line_number+1,7,7,"Employer",style_total_title)
			sheet.write_merge(line_number,line_number+1,8,8,"CRTV",style_total_title)
			sheet.write_merge(line_number,line_number+1,9,9,"Communal Tax",style_total_title)
			sheet.write_merge(line_number,line_number+1,10,10,"FNE",style_total_title)
			
			line_number += 2
			
			for payslip in self.payslip_ids:
				sheet.write(line_number,0,payslip.employee_id.real_name)
				sheet.write(line_number,1,payslip.worked_days,style_amount)
				sheet.write(line_number,2,payslip.gross_salary,style_amount)
				sheet.write(line_number,3,payslip.taxable_salary,style_amount)
				sheet.write(line_number,4,payslip.pit,style_amount)
				sheet.write(line_number,5,payslip.act,style_amount)
				sheet.write(line_number,6,payslip.cfce,style_amount)
				sheet.write(line_number,7,payslip.cfcp,style_amount)
				sheet.write(line_number,8,payslip.crtv,style_amount)
				sheet.write(line_number,9,payslip.ctax,style_amount)
				sheet.write(line_number,10,payslip.fne,style_amount)
					
				line_number += 1

			sheet.write_merge(line_number,line_number,0,1,"TOTAL",style_total_title)
			sheet.write(line_number,2,self.total_gross,style_total_amount)
			sheet.write(line_number,3,self.total_taxable,style_total_amount)
			sheet.write(line_number,4,self.total_pit,style_total_amount)
			sheet.write(line_number,5,self.total_act,style_total_amount)
			sheet.write(line_number,6,self.total_cfce,style_total_amount)
			sheet.write(line_number,7,self.total_cfcp,style_total_amount)
			sheet.write(line_number,8,self.total_crtv,style_total_amount)
			sheet.write(line_number,9,self.total_ctax,style_total_amount)
			sheet.write(line_number,10,self.total_fne,style_total_amount)
		
		wb.save(xls_file)
		xls_content = xls_file.getvalue()
		xls_file.close()
#		raise Warning("Value of Payroll Date %s" % (the_date))
		self.dipe_pit_project_file = base64.b64encode(xls_content)
		self.dipe_pit_project_name = "dipe_pit_%s.xls" % (self.project_id.name)

	@api.one
	@api.depends('payslip_ids','month')
	def _update_payroll_component_project(self):
		content = ""
		wb = Workbook()
		sheet = wb.add_sheet('GHSS PAYROLL COMPONENENTS')
		sheet.col(0).width = 256 * 50
		sheet.col(1).width = 256 * 50
		
		style_total_title = easyxf('font: bold on; align: horiz center; align: vert center;')
		style_total_amount = easyxf('font: bold on;')
		style_amount = easyxf()
		style_total_amount.num_format_str = '#,##0'
		style_amount.num_format_str = '#,##0'
		
		line_number = 0
		xls_file = StringIO.StringIO()

		sheet.write_merge(line_number,line_number+1,0,2,"PAYROLL COMPONENETS - %s (%s)"  % (self.project_id.name,self.month),style_total_title)
		
		line_number += 3
		
		if self.payslip_ids:
			sheet.write_merge(line_number,line_number+1,0,1,"SUMMARY",style_total_title)
			
			line_number += 2
			sheet.write(line_number,0,"Designation",style_total_title)
			sheet.write(line_number,1,"Amount",style_total_title)
			
			line_number += 1
			
			sheet.write(line_number,0,"BASIC")
			sheet.write(line_number,1,self.total_basic,style_amount)
					
			line_number += 2
			
			sheet.write_merge(line_number,line_number,0,1,"ALLOWANCES",style_total_title)
			
			for allowance in self.allowance_ids:
				amount = 0
				for payslip in self.payslip_ids:
					for line in payslip.line_ids:
						if line.salary_rule_id.id == allowance.allowance_id.rule_id.id:
							amount += line.total

				line_number += 1
				sheet.write(line_number,0,allowance.allowance_id.name)
				sheet.write(line_number,1,amount,style_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Gross Salary",style_total_title)
			sheet.write(line_number,1,self.total_gross,style_total_amount)
					
			line_number += 2
			
			sheet.write(line_number,0,"Taxable Salary",style_total_title)
			sheet.write(line_number,1,self.total_taxable,style_total_amount)
			
			line_number += 2
			
			sheet.write_merge(line_number,line_number,0,1,"Employee Deductions",style_total_title)
			
			line_number += 1
			
			sheet.write(line_number,0,"PIT")
			sheet.write(line_number,1,self.total_pit,style_amount)
		
			line_number += 1
			
			sheet.write(line_number,0,"ACT")
			sheet.write(line_number,1,self.total_act,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Land Bank Rate")
			sheet.write(line_number,1,self.total_cfce,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"CRTV")
			sheet.write(line_number,1,self.total_crtv,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Communal Tax")
			sheet.write(line_number,1,self.total_ctax,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Old age pension (CNPS) - Employee")
			sheet.write(line_number,1,self.total_cnpse,style_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Total Employee Tax Deductions",style_total_title)
			sheet.write(line_number,1,self.total_taxes_employees_basic,style_total_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Other Deductions")
			sheet.write(line_number,1,self.total_other_deductions,style_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Total Employee Deductions",style_total_title)
			sheet.write(line_number,1,self.total_taxes_employees,style_total_amount)
			
			line_number += 2
			
			sheet.write_merge(line_number,line_number,0,1,"Employer Deductions",style_total_title)
			
			line_number += 1
			
			sheet.write(line_number,0,"CFC")
			sheet.write(line_number,1,self.total_cfcp,style_amount)
		
			line_number += 1
			
			sheet.write(line_number,0,"FNE")
			sheet.write(line_number,1,self.total_fne,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Family Contribution")
			sheet.write(line_number,1,self.total_fcon,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Old age pension (CNPS) - Employer")
			sheet.write(line_number,1,self.total_cnpsp,style_amount)
			
			line_number += 1
			
			sheet.write(line_number,0,"Industrial and Profesional Accident")
			sheet.write(line_number,1,self.total_ipa,style_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Total Employer Tax Deductions",style_total_title)
			sheet.write(line_number,1,self.total_taxes_employer,style_total_amount)
			
			line_number += 2
			
			sheet.write(line_number,0,"Net Payment",style_total_title)
			sheet.write(line_number,1,self.total_net,style_total_amount)
			
		
		wb.save(xls_file)
		xls_content = xls_file.getvalue()
		xls_file.close()
#		raise Warning("Value of Payroll Date %s" % (the_date))
		self.payroll_component_project_file = base64.b64encode(xls_content)
		self.patroll_component_project_name = "payroll_componenets_%s.xls" % (self.project_id.name)