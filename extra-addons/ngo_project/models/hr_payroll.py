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
from openerp.osv import fields as field, osv
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning, ValidationError
from openerp import workflow
import logging

class HR_Payroll(models.Model):

	_inherit = 'hr.payslip'
	
#	@api.model
#	def _get_default_days(self):
#		nb_days = 30
#		if self.date_from:
#			the_date = datetime.strptime(self.date_from,'%Y-%m-%d')
#			nb_days = monthrange(the_date.year,the_date.month)[1]
		
#		return nb_days
	
	worked_days = fields.Integer(string="Worked days",default=30)
	extra_deduction = fields.Float(string="Other Deductions",digits_compute=dp.get_precision('Payroll'),default=0.0)
	gross_salary = fields.Float(string="Gross",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	except_salary = fields.Float(string="Exceptional",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	taxable_salary = fields.Float(string="Taxable",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	cotisable_salary = fields.Float(string="Cotisable",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	cotisable_ref_salary = fields.Float(string="Cotisable",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	pit = fields.Float(string="PIT",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	ctax = fields.Float(string="Communal Tax",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	act = fields.Float(string="ACT",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	cfce = fields.Float(string="CFC Employee",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	cfcp = fields.Float(string="CFC Employer",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	cnpse = fields.Float(string="CNPS Employee",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	cnpsp = fields.Float(string="CNPS Employer",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	other_deductions = fields.Float(string="Other Deductions",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	ipa = fields.Float(string="I.P. Accident",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	fcon = fields.Float(string="Family Contribution",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	fne = fields.Float(string="FNE",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	crtv = fields.Float(string="CRTV",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	net = fields.Float(string="Net Payment",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	basic = fields.Float(string="Basic",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	employee_deduction = fields.Float(string="Employee Deductions",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	employer_deduction = fields.Float(string="Employer Deductions",compute='_get_amount',readonly=True,digits_compute=dp.get_precision('Payroll'))
	
	@api.one
	def _get_amount(self):
		gross = self.line_ids.search([('code','=','GROSS'),('slip_id','=',self.id)])
		taxable = self.line_ids.search([('code','=','TSAL'),('slip_id','=',self.id)])
		cotisable = self.line_ids.search([('code','=','CSAL'),('slip_id','=',self.id)])
		cotisable_ref = self.line_ids.search([('code','=','CSAL'),('slip_id','=',self.id)])
		pit = self.line_ids.search([('code','=','PIT'),('slip_id','=',self.id)])
		act = self.line_ids.search([('code','=','ACT'),('slip_id','=',self.id)])
		ctax = self.line_ids.search([('code','=','CTAX'),('slip_id','=',self.id)])
		cfce = self.line_ids.search([('code','=','LBR'),('slip_id','=',self.id)])
		cfcp = self.line_ids.search([('code','=','CFC'),('slip_id','=',self.id)])
		cnpse = self.line_ids.search([('code','=','CNPSE'),('slip_id','=',self.id)])
		cnpsp = self.line_ids.search([('code','=','CNPSP'),('slip_id','=',self.id)])
		ipa = self.line_ids.search([('code','=','IPA'),('slip_id','=',self.id)])
		fcon = self.line_ids.search([('code','=','FCON'),('slip_id','=',self.id)])
		fne = self.line_ids.search([('code','=','FNE'),('slip_id','=',self.id)])
		crtv = self.line_ids.search([('code','=','CRTV'),('slip_id','=',self.id)])
		net = self.line_ids.search([('code','=','NET'),('slip_id','=',self.id)])
		basic = self.line_ids.search([('code','=','BASIC'),('slip_id','=',self.id)])
		employee_deduction = self.line_ids.search([('code','=','ALLEMPDED'),('slip_id','=',self.id)])
		employer_deduction = self.line_ids.search([('code','=','TEMPYDED'),('slip_id','=',self.id)])
		
		if gross:
			self.gross_salary = gross[0].total
		else:
			self.gross_salary = 0

		self.except_salary = 0
		
		if taxable:
			self.taxable_salary = taxable[0].total
		else:
			self.taxable_salary = 0
	
		if cotisable:
			self.cotisable_salary = cotisable[0].total
		else:
			self.cotisable_salary = 0
		
		if cotisable_ref:
			if cotisable[0].total > 750000:
				self.cotisable_ref_salary = 750000
			else:
				self.cotisable_ref_salary = cotisable[0].total
		else:
			self.cotisable_ref_salary = 0
		
		if pit:
			self.pit = pit[0].total
		else:
			self.pit = 0

		if act:
			self.act = act[0].total
		else:
			self.act = 0
		
		if ctax:
			self.ctax = ctax[0].total
		else:
			self.ctax = 0
		
		if cfce:
			self.cfce = cfce[0].total
		else:
			self.cfce = 0
		
		if cfcp:
			self.cfcp = cfcp[0].total
		else:
			self.cfcp = 0
		
		if cnpse:
			self.cnpse = cnpse[0].total
		else:
			self.cnpse = 0
		
		if cnpsp:
			self.cnpsp = cnpsp[0].total
		else:
			self.cnpsp = 0

		if ipa:
			self.ipa = ipa[0].total
		else:
			self.ipa = 0
		
		if fcon:
			self.fcon = fcon[0].total
		else:
			self.fcon = 0
			
		if fne:
			self.fne = fne[0].total
		else:
			self.fne = 0
		
		if crtv:
			self.crtv = crtv[0].total
		else:
			self.crtv = 0
			
		if net:
			self.net = net[0].total
		else:
			self.net = 0

		if basic:
			self.basic = basic[0].total
		else:
			self.basic = 0
			
		if employee_deduction:
			self.employee_deduction = employee_deduction[0].total
		else:
			self.employee_deduction = 0
		
		if employer_deduction:
			self.employer_deduction = employer_deduction[0].total
		else:
			self.employer_deduction = 0
		
	def get_allowance(self, allowance):
		if allowance:
			result = self.line_ids.filtered(lambda r: r.salary_rule_id.id == allowance.rule_id.id)
			if result:
				return result[0]
			else:
				return None
		else:
			return None
			
class HR_by_Employee(models.TransientModel):

	_inherit = 'hr.payslip.employees'

	@api.model
	def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
		emp_with_contract_ids = []
		
		res = super(HR_by_Employee,self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
		
		if res['type'] == 'form':
			payslip_run_id = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))[0]
			
			if payslip_run_id and payslip_run_id.date_end:
				emp_ids = self.env['hr.employee'].search([])
				date_start = payslip_run_id.date_start
				
				for emp in emp_ids:
					contract_id = self.env['hr.contract'].search([('employee_id','=',emp.id),('date_end','>',date_start)],order='date_end desc',limit=1)
					if contract_id:
						emp_with_contract_ids.append(emp.id)
				
				res['fields']['employee_ids']['domain'] = [('id','in',emp_with_contract_ids)]

		return res

