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
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning, ValidationError
from openerp import workflow
import base64
from openerp import workflow

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

class HR_DIPE_Info(models.Model):

	_name = 'hr.dipe.info'
	
	name = fields.Char(string="Name",compute='_get_name',readonly=True)
	number = fields.Char(string="Number",size=5,required=True)
	key = fields.Char(string="Key",size=1,required=True)
	line_ids = fields.One2many('hr.dipe.info.line','info_id',string="Lines")
	state = fields.Selection([('draft','Draft'),('confirmed','Confirmed')],string="State",default='draft')
	
	@api.one
	@api.depends('number','key')
	def _get_name(self):
		if self.number and self.key:
			self.name = "%s-%s" % (self.number,self.key)
		else:
			self.name = ""
	
	@api.one
	def confirm(self):
		dipe_line_obj = self.env['hr.dipe.info.line']
		
		for sequence in range(1,17,1):
			vals = {'info_id':self.id,'seq':sequence}
			dipe_line_obj.create(vals)
			
		self.write({'state':'confirmed'})
		
	@api.multi
	def unlink(self):
		for elem in self:
			if elem.line_ids:
				for line in elem.line_ids:
					line.unlink()
		models.Model.unlink(self)
			
class HR_DIPE_Info_Line(models.Model):

	_name = 'hr.dipe.info.line'
	
	name = fields.Char(string="Name",compute='_get_name',readonly=True)
	info_id = fields.Many2one('hr.dipe.info',string="DIPE Sheet",ondelete='cascade')
	seq = fields.Integer(string="Line Number",default=0)
	employee_id = fields.Many2one('hr.employee',string="Employee Assigned")
	
	@api.one
	@api.depends('info_id','seq')
	def _get_name(self):
		if self.info_id and self.seq:
			str_seq = str(self.seq)
			self.name = "%s - %s" % (self.info_id.name,str_seq)
		else:
			self.name = ""
	
	@api.one
	@api.constrains('seq')
	def seq_constraints(self):
		if self.seq:
			if self.seq < 0:
				raise Warning('Sorry the Line Number has to be higher than 0!')
			elif self.seq > 20:
				raise Warning('Sorry the Line Number has to be lower than 20!')
		
	
	@api.one
	@api.constrains('employee_id')
	def check_employee(self):
		dipe_line_obj = self.env['hr.dipe.info.line']
		
		if self.employee_id:
			result = dipe_line_obj.search([('employee_id','=',self.employee_id.id)])
			
			if len(result) > 1:
				raise Warning('Please, %s is already link to another DIPE Sheet Line\nAn employee cannot be linked to two DIPE Lines !' % (self.employee_id.name))
	
class HR_Payslip_Run(models.Model):

	_inherit = 'hr.payslip.run'
	
	dipe_ids = fields.One2many('hr.dipe.dipe','payslip_run_id',string="DIPE Lines")
	generated = fields.Boolean(string="Generated ?", default=False)
	dipe_name = fields.Char("Dipe File Name",compute='_update_dipes')
	month_name = fields.Char("Month Name",compute='_update_dipes')
	monthly_dipe = fields.Binary(string="Monthly DIPE",compute='_update_dipes')
	nb_dipes = fields.Integer(string="Number of DIPEs",compute='_update_dipes')
	company_id = fields.Many2one('res.company',string="The company",compute='_get_company')
	total_gross = fields.Float(string="Gross",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_taxable = fields.Float(string="Taxable",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_cotisable = fields.Float(string="Cotisable",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_cotisable_ref = fields.Float(string="Capped",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_cnpse = fields.Float(string="CNPS Employee",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_cnpsp = fields.Float(string="CNPS Employer",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_ipa = fields.Float(string="I.P. Accident",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_fcon = fields.Float(string="Family Contributory",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_act = fields.Float(string="ACT",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_pit = fields.Float(string="PIT",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_ctax = fields.Float(string="Comm. Tax",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_contribution_cnps = fields.Float(string="Total CNPS",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_cfce = fields.Float(string="CFC Employee",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_cfcp = fields.Float(string="CFC Employer",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_fne = fields.Float(string="FNE",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_crtv = fields.Float(string="CRTV",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_basic = fields.Float(string="Basic Salary",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_net_payment = fields.Float(string="Net Payment",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_other_deductions = fields.Float(string="Other Deductions",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_taxes = fields.Float(string="Total Taxes",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_taxes_employee_basic = fields.Float(string="Total Taxes Employee Basic",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_taxes_employee = fields.Float(string="Total Taxes Employee",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_taxes_employer = fields.Float(string="Total Taxes Employer",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	total_taxes_deductions = fields.Float(string="Total Taxes Deductions",compute='_update_total',digits_compute=dp.get_precision('Payroll'))
	penalities = fields.Float(string="Penalities",digits_compute=dp.get_precision('Payroll'),default=0.0)
	previous_payslip_run_id = fields.Many2one('hr.payslip.run',string="Previous Payslip Batch",compute='_get_previous_batch')
	allowance_set_ids = fields.Many2many('hr.payroll.allowance.set',compute='_get_allowance_set')
	nb_payslips = fields.Integer(string="Number of Payslips",compute='_get_nb_payslips')
	nb_pages = fields.Integer(string="Number of Pages",compute='_get_nb_pages')
	confirmed = fields.Boolean(compute='_is_confirmed')
	
	def get_pages(self):
		tab = []
		if self.slip_ids:
			limit = 0
			temp = []
			for slip in self.slip_ids:
				temp.append(slip)
				limit += 1
				if limit % 16 == 0:
					tab.append(temp)
					temp = []
			if len(temp) > 0:
				tab.append(temp)
		return tab		
	
	def get_alli_compare(self):
		result = None
		temp = []
		
#		if self.previous_payslip_run_id:
#			for slip in self.slip_ids:
#				previous_slip = self.previous_payslip_run_id.slip_ids.filtered(lambda r: r.employee_id.id == slip.employee_id.id)
#				if previous_slip:
#					if previous_slip.
			
#		else:
#			result = self.slip_ids
		
		return result
	
	def get_elem_compare(self,elem):
		result = None
		temp = []
		
		if elem == 'BASIC':
			for slip in self.slip_ids:
				previous_slip = None
				
				if self.previous_payslip_run_id and self.previous_payslip_run_id.slip_ids:
					previous_slip = self.previous_payslip_run_id.slip_ids.filtered(lambda p: p.employee_id.id == slip.employee_id.id)
				
				if not previous_slip:
					temp.append(slip.id)
				else:
					if slip.basic != previous_slip[0].basic:
						temp.append(slip.id)
		
			if self.slip_ids:
				result = self.slip_ids.filtered(lambda p: p.id in temp)
		
		elif elem == 'OTHERDED':
			for slip in self.slip_ids:
				previous_slip = None
				
				if self.previous_payslip_run_id and self.previous_payslip_run_id.slip_ids:
					previous_slip = self.previous_payslip_run_id.slip_ids.filtered(lambda p: p.employee_id.id == slip.employee_id.id)

				if not previous_slip:
					temp.append(slip.id)
				else:
					if slip.other_deductions != previous_slip[0].other_deductions:
						temp.append(slip.id)
		
			if self.slip_ids:
				result = self.slip_ids.filtered(lambda p: p.id in temp)				
				
		elif elem == 'WORKEDDAYS':
			for slip in self.slip_ids:
				previous_slip = None
				
				if self.previous_payslip_run_id and self.previous_payslip_run_id.slip_ids:
					previous_slip = self.previous_payslip_run_id.slip_ids.filtered(lambda p: p.employee_id.id == slip.employee_id.id)

				if not previous_slip:
					temp.append(slip.id)
				else:
					if slip.worked_days != previous_slip[0].worked_days:
						temp.append(slip.id)
		
			if self.slip_ids:
				result = self.slip_ids.filtered(lambda p: p.id in temp)				
		
		elif elem == 'ALLEMPDED':
			for slip in self.slip_ids:
				previous_slip = None
				
				if self.previous_payslip_run_id and self.previous_payslip_run_id.slip_ids:
					previous_slip = self.previous_payslip_run_id.slip_ids.filtered(lambda p: p.employee_id.id == slip.employee_id.id)

				if not previous_slip:
					temp.append(slip.id)
				else:
					if slip.employee_deduction != previous_slip[0].employee_deduction:
						temp.append(slip.id)
		
			if self.slip_ids:
				result = self.slip_ids.filtered(lambda p: p.id in temp)				
				
		elif elem == 'TEMPYDED':
			for slip in self.slip_ids:
				previous_slip = None
				
				if self.previous_payslip_run_id and self.previous_payslip_run_id.slip_ids:
					previous_slip = self.previous_payslip_run_id.slip_ids.filtered(lambda p: p.employee_id.id == slip.employee_id.id)

				if not previous_slip:
					temp.append(slip.id)
				else:
					if slip.employer_deduction != previous_slip[0].employer_deduction:
						temp.append(slip.id)
		
			if self.slip_ids:
				result = self.slip_ids.filtered(lambda p: p.id in temp)	

		elif elem == 'NET':
			for slip in self.slip_ids:
				previous_slip = None
				
				if self.previous_payslip_run_id and self.previous_payslip_run_id.slip_ids:
					previous_slip = self.previous_payslip_run_id.slip_ids.filtered(lambda p: p.employee_id.id == slip.employee_id.id)

				if not previous_slip:
					temp.append(slip.id)
				else:
					if slip.net != previous_slip[0].net:
						temp.append(slip.id)
		
			if self.slip_ids:
				result = self.slip_ids.filtered(lambda p: p.id in temp)				
		
		else:
			allowance_list = self.allowance_set_ids.filtered(lambda a: a.code == elem)
			if allowance_list:
				allowance_set = allowance_list[0]
			
				for slip in self.slip_ids:
					previous_slip = None
				
					if self.previous_payslip_run_id and self.previous_payslip_run_id.slip_ids:
						previous_slip = self.previous_payslip_run_id.slip_ids.filtered(lambda p: p.employee_id.id == slip.employee_id.id)
					
					if not previous_slip:
						temp.append(slip.id)
					else:
						allowance_id = slip.get_allowance(allowance_set)
						previous_allowance_id = previous_slip[0].get_allowance(allowance_set)
						
						if (allowance_id and not previous_allowance_id) or (not allowance_id and previous_allowance_id):
							temp.append(slip.id)
						elif allowance_id and previous_allowance_id and allowance_id.total != previous_allowance_id.total:
							temp.append(slip.id)
							
			if self.slip_ids:
				result = self.slip_ids.filtered(lambda p: p.id in temp)
						
		
		return result
	
	@api.one
	@api.depends('slip_ids')
	def _is_confirmed(self):
		self.confirmed = True
		if self.slip_ids:
			for slip in self.slip_ids:
				if slip.state == 'draft':
					self.confirmed = False
					break
	
	@api.multi
	def confirm_all_payslip(self):
		if self.slip_ids:
			wizard_form = self.env.ref('hr_payroll_allowance.hr_payslip_confirm_view',False)
			view_id = self.env['hr.payslip.confirm']
			vals = {
				'payslip_run_id' : self.id
				}
			new_info = view_id.create(vals)
		
			return {
				'name'		:	_('Payslip Batched'),
				'type'		:	'ir.actions.act_window',
				'res_model'	:	'hr.payslip.confirm',
				'res_id'	:	new_info.id,
				'view_id'	:	wizard_form.id,
				'view_type'	:	'form',
				'view_mode'	:	'form',
				'target'	:	'new'
				}
			
#			for slip in self.slip_ids:
#				if slip.state == 'draft':
#					workflow.trg_validate(self.env.uid,'hr.payslip',slip.id,'hr_verify_sheet',self.env.cr)
	
	@api.one
	@api.depends('slip_ids')
	def _get_nb_payslips(self):
		self.nb_payslips = len(self.slip_ids)
		
	@api.one
	@api.depends('nb_payslips')
	def _get_nb_pages(self):
		self.nb_pages = (self.nb_payslips // 16) + 1
	
	@api.one
	def _get_allowance_set(self):
		self.allowance_set_ids = self.env['hr.payroll.allowance.set'].search([]).sorted(key=lambda r: r.sequence)
		self.nb_allowances = len(self.allowance_set_ids)
	
	@api.one
	@api.depends('dipe_ids')
	def _get_company(self):
		if self.slip_ids:
			self.company_id = self.slip_ids[0].company_id
		else:
			None
	
	@api.one
	def _get_previous_batch(self):
		payslip_run_ids = self.env['hr.payslip.run'].search([('date_start','<',self.date_start)],order='date_start desc',limit=1)
		if payslip_run_ids:
			self.previous_payslip_run_id = payslip_run_ids[0]
		else:
			self.previous_payslip_run_id = None
	
	@api.one
	def generate_dipe(self):
		if self.slip_ids:
			dipe_obj = self.env['hr.dipe.dipe']
			dipe_line_obj = self.env['hr.dipe.dipe.line']
			dipe_info_obj = self.env['hr.dipe.info']
			dipe_info_line_obj = self.env['hr.dipe.info.line']
			payslip_obj = self.env['hr.payslip']
			employee_obj = self.env['hr.employee']
			
			the_date = datetime.strptime(self.date_start,'%Y-%m-%d')
			
			employee_ids =  employee_obj.search([('id','in',[s.employee_id.id for s in self.slip_ids])]) #self.slip_ids.employee_id
			dipe_ids = dipe_info_obj.search([])
			line_temp = 17
			dipe_temp = None
			dipe_line_temp = None
			name = "%s %s" % (MONTHS[the_date.month - 1],the_date.year)
	
			for slip in self.slip_ids:
				if line_temp == 17:
					line_temp = 1
					dipe_vals = {'name':name,'payslip_run_id': self.id}
					dipe_temp = dipe_obj.create(dipe_vals)
				
				dipe_line_ids = dipe_info_line_obj.search([('employee_id','=',slip.employee_id.id)])
				if dipe_line_ids:
					dipe_line_temp = dipe_line_ids[0]
				else:
					dipe_line_temp = None
				dipe_line_vals = {'name':name,'dipe_id':dipe_temp.id,'dipe_line_id':None,'payslip_id':slip.id,'line_number':line_temp}
				dipe_line_obj.create(dipe_line_vals)
				line_temp += 1
					
	
		self.generated = True
	
#			for dipe in dipe_ids:
#				dipe_line_ids = dipe_info_line_obj.search([('info_id','=',dipe.id),('employee_id','in',[e.id for e in employee_ids])])
#				raise Warning("DIPE lines 1 Values : %s " % (dipe_line_ids1))
#				if len(dipe_line_ids) > 0:
#					name = "%s %s" % (MONTHS[the_date.month - 1],the_date.year)
#					dipe_vals = {'name':name,'info_id':dipe.id,'payslip_run_id':self.id}
#					raise Warning("DIPE Values : %s " % (dipe_vals))
#					dipe_id = dipe_obj.create(dipe_vals)
					
#					for dipe_line in dipe_line_ids:
#						name = "%s: %s" % (name,dipe_line.employee_id.name)
#						payslip_ids = self.slip_ids.search([('employee_id','=',dipe_line.employee_id.id),('payslip_run_id','=',self.id)])
#						if payslip_ids:
#							for payslip in payslip_ids:
#								dipe_line_vals = {'name':name,'dipe_id':dipe_id.id,'dipe_line_id':dipe_line.id,'payslip_id':payslip.id}
#								raise Warning("DIPE Values : %s " % (dipe_line_vals))
#								dipe_line_obj.create(dipe_line_vals)

		

	
	@api.one
	def cancel_dipe(self):
		if self.dipe_ids:
			for dipe in self.dipe_ids:
				dipe.unlink()
		
		self.generated = False
		
	@api.one
	@api.depends('dipe_ids')
	def _update_total(self):
		global_gross = 0
		global_taxable = 0
		global_basic = 0
		global_cotisable = 0
		global_cotisable_ref = 0
		global_cnpse = 0
		global_cnpsp = 0
		global_ipa = 0
		global_fcon = 0
		global_pit = 0
		global_act = 0
		global_ctax = 0
		global_cfce = 0
		global_cfcp = 0
		global_fne = 0
		global_crtv = 0
		global_other_deductions = 0
		global_net_payment = 0
		
		if self.dipe_ids:
			for dipe in self.dipe_ids:
				global_gross = global_gross + dipe.total_gross
				global_taxable = global_taxable + dipe.total_taxable
				global_basic = global_basic + dipe.total_basic
				global_cotisable = global_cotisable + dipe.total_cotisable
				global_cotisable_ref = global_cotisable_ref + dipe.total_cotisable_ref
				global_cnpse = global_cnpse + dipe.total_cnpse
				global_cnpsp = global_cnpsp + dipe.total_cnpsp
				global_ipa = global_ipa + dipe.total_ipa
				global_fcon = global_fcon + dipe.total_fcon
				global_pit = global_pit + dipe.total_pit
				global_act = global_act + dipe.total_act
				global_ctax = global_ctax + dipe.total_ctax
				global_cfce = global_cfce + dipe.total_cfce
				global_cfcp = global_cfcp + dipe.total_cfcp
				global_fne = global_fne + dipe.total_fne
				global_crtv = global_crtv + dipe.total_crtv
				global_other_deductions = global_other_deductions + dipe.total_other_deductions
				global_net_payment = global_net_payment + dipe.total_net_payment
		
		self.total_gross = global_gross
		self.total_taxable = global_taxable
		self.total_basic = global_basic
		self.total_cotisable = global_cotisable
		self.total_cotisable_ref = global_cotisable_ref
		self.total_cnpse = global_cnpse
		self.total_cnpsp = global_cnpsp
		self.total_ipa = global_ipa
		self.total_fcon = global_fcon
		self.total_pit = global_pit
		self.total_act = global_act
		self.total_ctax = global_ctax
		self.total_cfce = global_cfce
		self.total_cfcp = global_cfcp
		self.total_fne = global_fne
		self.total_crtv = global_crtv
		self.total_other_deductions = global_other_deductions
		self.total_net_payment = global_net_payment
		
		self.total_contribution_cnps = global_cnpse + global_cnpsp + global_ipa + global_fcon
		self.total_taxes = global_pit + global_act + global_cfce + global_cfcp + global_crtv + global_ctax + global_fne	+ self.penalities
		self.total_taxes_employee_basic = global_pit + global_act + global_cfce + global_crtv + global_ctax + global_cnpse
		self.total_taxes_employee = self.total_taxes_employee_basic + self.total_other_deductions
		self.total_taxes_employer = self.total_cfcp + self.total_fne + self.total_fcon + self.total_cnpsp + self.total_ipa
		self.total_taxes_deductions = self.total_taxes_employee + self.total_taxes_employer
		
	@api.one
	@api.depends('dipe_ids')
	def _update_dipes(self):
		content = ""
		
		the_date = datetime.strptime(self.date_start,'%Y-%m-%d')
		self.nb_dipes = 0
		
		if self.dipe_ids:
			self.nb_dipes = len(self.dipe_ids)
			
			line_num = 1
			
			for dipe in self.dipe_ids:
				if len(dipe.line_ids) > 0:
#					DIPE sheet information
#					dipe_number = "%+5s" % (dipe.info_id.number)
#					dipe_key = "%+1s" % (dipe.info_id.key)

					dipe_number = "00000"
					dipe_key = " "
					
					for dipe_line in dipe.line_ids:

# 						Register Code: CD04 (3 Characters)
						line = "C04"

#						DIPE Number & Key (5 + 1 Characters)
						line = line + dipe_number + dipe_key

#						Contribuable Number (14 Characters)
						niu = "              "
						
						if dipe_line.payslip_id.employee_id.company_id.niu:
							niu = "%+14s" % (dipe_line.payslip_id.employee_id.company_id.niu)
						line = line + niu

						#						Month (2 Characters)
						month = str(the_date.month)
						if the_date.month < 10:
							month = '0' + month
						line = line + month

#						Employer Number and key (13 + 1 Characters)
						employer_number_key = "              "

						if dipe_line.payslip_id.employee_id.company_id.ssnid:
							employer_number_key = "%+14s" % (dipe_line.payslip_id.employee_id.company_id.ssnid.replace('-',''))
						
						line = line + employer_number_key

#						Employer Regime (1 Character)
						employer_regime = " "
						
						if dipe_line.payslip_id.employee_id.company_id.regime:
							temp = dipe_line.payslip_id.employee_id.company_id.regime
							if temp == 'general':
								employer_regime = "1"
							elif temp == 'agriculture':
								employer_regime = "2"
							else:
								employer_regime = "3"
						
						line = line + employer_regime

#						DIPE Year (4 Characters)
						year = "%+4s" % (str(the_date.year))
						line = line + year

#						Employee Number and key (10 + 1 Characters)
						employee_number_key = "           "
						
						if dipe_line.payslip_id.employee_id.ssnid:
							employee_number_key = "%+11s" % (dipe_line.payslip_id.employee_id.ssnid.replace('-',''))

						line = line + employee_number_key

#						Number of days (2 Characters)
						days = "%+2s" % (str(dipe_line.payslip_id.worked_days))

						line = line + days

#						Gross Salary (10 Characters)
						gross_int = int(dipe_line.payslip_id.gross_salary)
						gross = "%+10s" % (str(gross_int))
						
						line = line + gross
						
#						Exceptinal Salary (10 Characters)
						except_int = int(dipe_line.payslip_id.except_salary)
						except_sal = "%+10s" % (str(except_int))
						
						line = line + except_sal

#						Taxable Salary (10 Characters)
						taxable_int = int(dipe_line.payslip_id.taxable_salary)
						taxable = "%+10s" % (str(taxable_int))
						
						line = line + taxable

#						Cotiable Salary (10 Characters)
						cotisable_int = int(dipe_line.payslip_id.cotisable_salary)
						cotisable = "%+10s" % (str(cotisable_int))
						
						line = line + cotisable
						
#						Reference Cotisable Salary (10 Characters)
						cotisable_ref_int = int(dipe_line.payslip_id.cotisable_ref_salary)
						cotisable_ref = "%+10s" % (str(cotisable_ref_int))
						
						line = line + cotisable_ref

#						PIT deduction (8 Characters)
						pit_int = int(dipe_line.payslip_id.pit)
						pit = "%+8s" % (str(pit_int))
						
						line = line + pit

#						Local taxes (6 Characters)
						ctax_int = int(dipe_line.payslip_id.ctax)
						ctax = "%+6s" % (str(ctax_int))
						
						line = line + "000000" #ctax

#						Line Number (2 Characters)
#						line_number = "%+2s" % (str(dipe_line.dipe_line_id.seq))
						line_number = str(line_num)
						
						if line_num < 10:
							line_number = '0' + line_number
						
						line_num += 1
						if line_num == 17:
							line_num = 1

						line = line + line_number
						
#						Matricule (14 Characters)
						employee_matricule = "              "
						
						if dipe_line.payslip_id.employee_id.matricule:
							employee_matricule = "%+14s" % (dipe_line.payslip_id.employee_id.matricule)

						line = line + employee_matricule

#						Employee Name (60 Characters)
						employee_name = "                                                             "
						if dipe_line.payslip_id.employee_id:
							real_name = dipe_line.payslip_id.employee_id.name_related.strip()
							if dipe_line.payslip_id.employee_id.real_name:
								real_name = dipe_line.payslip_id.employee_id.real_name.strip()
#							real_name = real_name.replace('é','e').replace('è','e').replace('ê','e').replace('ë','e').replace('ü','u').replace('à','a').replace('â','a').replace('ä','a').replace('ç','c').replace('ï','i').replace('ù','u').replace('û','u')
							employee_name = "%+60s" % (real_name)
						
						line = line + employee_name
						
#						if line.employee_id.ssnid:
#							dipe_number = "%6s" % (line.employee_id.ssnid.replace('-',''))
						
						if dipe_line.payslip_id.worked_days > 0 and gross_int != 0:
							content = content + line + "\r\n"
						elif dipe_line.payslip_id.worked_days == 0:
							content = content + line + "\r\n"
						
		
		self.monthly_dipe = base64.b64encode(content)
		self.dipe_name = "monthly_dipe_%s_%s.txt" % (MONTHS[the_date.month - 1],the_date.year)
		self.month_name = "%s %s" % (MONTHS[the_date.month - 1],the_date.year)
		
	@api.multi
	def get_dipe_file(self):
		the_date = datetime.strptime(self.date_start,'%Y-%m-%d')
		
		return {
			'type':'ir.actions.act_url',
			'url':'/web/binary/download_document?model=hr.payslip.run&field=monthly_dipe&id=%s&filename=monthly_dipe_%s_%s.txt'%(self.id,MONTHS[the_date.month - 1],the_date.year),
			'target':'self',
		}
			
	@api.multi
	def report_dipe_cnps(self):
		return self.env['report'].get_action(self,'hr_payroll_allowance.dipe_cnps_template')
	
	@api.multi
	def report_dipe_pit(self):
		return self.env['report'].get_action(self,'hr_payroll_allowance.dipe_pit_template')
		
	@api.multi
	def report_dipe_compare(self):
		return self.env['report'].get_action(self,'hr_payroll_allowance.dipe_compare_template')
		
	@api.multi
	def report_payroll_compare(self):
#		result = self.get_pages()
#		raise Warning("Value of Elem List: %s" % self.get_elem_compare("DPOST"))
		return self.env['report'].get_action(self,'hr_payroll_allowance.payroll_compare_template')
		
	def get_previous_payslip(self, slip):
		if slip and self.previous_payslip_run_id and self.previous_payslip_run_id.slip_ids:
			result = self.previous_payslip_run_id.slip_ids.filtered(lambda r: r.employee_id.id == slip.employee_id.id)
			if result:
				return result[0]
			else:
				return None
		else:
			return None
	
class HR_DIPE_DIPE(models.Model):

	_name = 'hr.dipe.dipe'
	
	name = fields.Char(string="DIPE Name")
	payslip_run_id = fields.Many2one('hr.payslip.run',string="Payslip Run")
	info_id = fields.Many2one('hr.dipe.info',string="DIPE Info")
	line_ids = fields.One2many('hr.dipe.dipe.line','dipe_id',string="Lines")
	nb_lines = fields.Integer(string="Number of lines",compute='_get_nb_lines',store=True)
	total_gross = fields.Float(string="Total Gross", compute='_get_total',digits_compute=dp.get_precision('Payroll'))
	total_taxable = fields.Float(string="Total Taxable",compute='_get_total')
	total_basic = fields.Float(string="Total Basic",compute='_get_total')
	total_except = fields.Float(string="Total Exceptional", compute='_get_total')
	total_cotisable = fields.Float(string="Total Cotisable",compute='_get_total')
	total_cotisable_ref = fields.Float(string="Total Cotisable Ref", compute='_get_total')
	total_pit = fields.Float(string="Total PIT",compute='_get_total')
	total_act = fields.Float(string="Total ACT", compute='_get_total')
	total_ctax = fields.Float(string="Total Com. Tax",compute='_get_total')
	total_cfce = fields.Float(string="Total CFC Employee", compute='_get_total')
	total_cfcp = fields.Float(string="Total CFC Employer",compute='_get_total')
	total_cnpse = fields.Float(string="CNPS Employees", compute='_get_total')
	total_cnpsp = fields.Float(string="CNPS Employer",compute='_get_total')
	total_ipa = fields.Float(string="Total IPA", compute='_get_total')
	total_fcon = fields.Float(string="Total Family Contribution",compute='_get_total')
	total_fne = fields.Float(string="Total FNE", compute='_get_total')
	total_crtv = fields.Float(string="Total CRTV",compute='_get_total')
	total_other_deductions = fields.Float(string="Other Deductions",compute='_get_total')
	total_net_payment = fields.Float(string="Net Payment",compute='_get_total')
	
	@api.one
	@api.depends('line_ids')
	def _get_total(self):
		total_gross = 0
		total_taxable = 0
		total_basic = 0
		total_except = 0
		total_cotisable = 0
		total_cotisable_ref = 0
		total_pit = 0
		total_act = 0
		total_ctax = 0
		total_cfce = 0
		total_cfcp = 0
		total_cnpse = 0
		total_cnpsp = 0
		total_ipa = 0
		total_fcon = 0
		total_fne = 0
		total_crtv = 0
		total_other_deductions = 0
		total_net_payment = 0
		
		if self.line_ids:
			for line in self.line_ids:
				total_gross = total_gross + line.payslip_id.gross_salary
				total_taxable = total_taxable + line.payslip_id.taxable_salary
				total_basic = total_basic + line.payslip_id.basic
				total_except = total_except + line.payslip_id.except_salary
				total_cotisable = total_cotisable + line.payslip_id.cotisable_salary
				total_cotisable_ref = total_cotisable_ref + line.payslip_id.cotisable_ref_salary
				total_pit = total_pit + line.payslip_id.pit
				total_act = total_act + line.payslip_id.act
				total_ctax = total_ctax + line.payslip_id.ctax
				total_cfce = total_cfce + line.payslip_id.cfce
				total_cfcp = total_cfcp + line.payslip_id.cfcp
				total_cnpse = total_cnpse + line.payslip_id.cnpse
				total_cnpsp = total_cnpsp + line.payslip_id.cnpsp
				total_ipa = total_ipa + line.payslip_id.ipa
				total_fcon = total_fcon + line.payslip_id.fcon
				total_fne = total_fne + line.payslip_id.fne
				total_crtv = total_crtv + line.payslip_id.crtv
				total_other_deductions = total_other_deductions + line.payslip_id.extra_deduction
				total_net_payment = total_net_payment + line.payslip_id.net
				
		self.total_gross = total_gross
		self.total_taxable = total_taxable
		self.total_basic = total_basic
		self.total_except = total_except
		self.total_cotisable = total_cotisable
		self.total_cotisable_ref = total_cotisable_ref
		self.total_pit = total_pit
		self.total_act = total_act
		self.total_ctax = total_ctax
		self.total_cfce = total_cfce
		self.total_cfcp = total_cfcp
		self.total_cnpse = total_cnpse
		self.total_cnpsp = total_cnpsp
		self.total_ipa = total_ipa
		self.total_fcon = total_fcon
		self.total_fne = total_fne
		self.total_crtv = total_crtv
		self.total_other_deductions = total_other_deductions
		self.total_net_payment = total_net_payment
	
	@api.one
	@api.depends('line_ids')
	def _get_nb_lines(self):
		if self.line_ids:
			self.nb_lines = len(self.line_ids)
		else:
			self.nb_lines = 0
	
	@api.multi
	def unlink(self):
		if self.line_ids:
			for line in self.line_ids:
				line.unlink()
		models.Model.unlink(self)
	
class HR_DIPE_Line(models.Model):

	_name = 'hr.dipe.dipe.line'

	name = fields.Char(string="DIPE Line Name")
	dipe_id = fields.Many2one('hr.dipe.dipe',string="DIPE",ondelete='cascade')
	dipe_line_id = fields.Many2one('hr.dipe.info.line',string="DIPE Line")
	payslip_id = fields.Many2one('hr.payslip',string="Payslip related")
	line_number = fields.Integer(string="Line Number")

class HR_Payslips_Confirm(models.TransientModel):

	_name = 'hr.payslip.confirm'
	
	payslip_run_id = fields.Many2one('hr.payslip.run')
	
	@api.multi
	def confirm_all_payslip(self):
#		raise Warning('Ready to run !')
		if self.payslip_run_id.slip_ids:
			for slip in self.payslip_run_id.slip_ids:
				if slip.state == 'draft':
					workflow.trg_validate(self.env.uid,'hr.payslip',slip.id,'hr_verify_sheet',self.env.cr)
	
	
