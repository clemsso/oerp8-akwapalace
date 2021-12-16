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
			

class HR_Payroll_Dashboard(models.Model):

	_name = 'hr.payroll.dashboard'
	
	payroll_run_id = fields.Many2one('hr.payslip.run',string="Last Payslip Batch",compute='_get_last_batch',readonly=True)
	name = fields.Char(string="Name")
	color = fields.Integer(string="Color")
	
	current_month = fields.Char(related='payroll_run_id.month_name')
	previous_month = fields.Char(compute='_get_previous_value')
	
	total_gross = fields.Char(compute='_get_current_value')
	total_taxable = fields.Char(compute='_get_current_value')
	total_cotisable = fields.Char(compute='_get_current_value')
	total_taxes_employee = fields.Char(compute='_get_current_value')
	total_taxes_employer = fields.Char(compute='_get_current_value')
	total_net_payment = fields.Char(compute='_get_current_value')
	nb_payslips = fields.Char(compute='_get_current_value')
	
	total_taxes = fields.Char(compute='_get_current_value')
	total_cnps = fields.Char(compute='_get_current_value')
	
	previous_total_gross = fields.Char(compute='_get_previous_value')
	previous_total_taxable = fields.Char(compute='_get_previous_value')
	previous_total_cotisable = fields.Char(compute='_get_previous_value')
	previous_total_taxes_employee = fields.Char(compute='_get_previous_value')
	previous_total_taxes_employer = fields.Char(compute='_get_previous_value')
	previous_total_net_payment = fields.Char(compute='_get_previous_value')
	previous_nb_payslips = fields.Char(compute='_get_previous_value')
	
	previous_total_taxes = fields.Char(compute='_get_previous_value')
	previous_total_cnps = fields.Char(compute='_get_previous_value')
	
	diff_gross = fields.Char(compute='_get_diff_value')
	diff_taxable = fields.Char(compute='_get_diff_value')
	diff_cotisable = fields.Char(compute='_get_diff_value')
	diff_taxes_employee = fields.Char(compute='_get_diff_value')
	diff_taxes_employer = fields.Char(compute='_get_diff_value')
	diff_net_payment = fields.Char(compute='_get_diff_value')
	diff_nb_payslips = fields.Char(compute='_get_diff_value')
	
	diff_taxes = fields.Char(compute='_get_diff_value')
	diff_cnps = fields.Char(compute='_get_diff_value')
	
	@api.one
	def _get_last_batch(self):
		payslip_run_ids = self.env['hr.payslip.run'].search([],order='date_start desc',limit=1)
		if payslip_run_ids:
			self.payroll_run_id = payslip_run_ids[0]
		else:
			self.payroll_run_id = None
	
	@api.one
	@api.depends('total_gross','total_taxable','total_cotisable','total_taxes_employee','total_taxes_employer','total_net_payment','nb_payslips','total_taxes','total_cnps','previous_total_gross','previous_total_taxable','previous_total_cotisable','previous_total_taxes_employee','previous_total_taxes_employer','previous_total_net_payment','previous_nb_payslips','previous_total_taxes','previous_total_cnps')
	def _get_diff_value(self):
		diff_gross = 0
		diff_taxable = 0
		diff_cotisable = 0
		diff_taxes_employee = 0
		diff_taxes_employer = 0
		diff_net_payment = 0
		diff_nb_payslips = 0
		
		diff_taxes = 0
		diff_cnps = 0
		
		if self.payroll_run_id:
			diff_gross = self.payroll_run_id.total_gross
			diff_taxable = self.payroll_run_id.total_taxable
			diff_cotisable = self.payroll_run_id.total_cotisable
			diff_taxes_employee = self.payroll_run_id.total_taxes_employee
			diff_taxes_employer = self.payroll_run_id.total_taxes_employer
			diff_net_payment = self.payroll_run_id.total_net_payment
			diff_nb_payslips = self.payroll_run_id.nb_payslips
			
			diff_taxes = self.payroll_run_id.total_pit + self.payroll_run_id.total_act + self.payroll_run_id.total_ctax
			diff_taxes += self.payroll_run_id.total_cfce + self.payroll_run_id.total_cfcp + self.payroll_run_id.total_fne
			diff_taxes += self.payroll_run_id.total_crtv
			
			diff_cnps = self.payroll_run_id.total_cnpse + self.payroll_run_id.total_cnpsp + self.payroll_run_id.total_fcon
			diff_cnps += self.payroll_run_id.total_ipa 
			
			if self.payroll_run_id.previous_payslip_run_id:
				diff_gross -= self.payroll_run_id.previous_payslip_run_id.total_gross
				diff_taxable -= self.payroll_run_id.previous_payslip_run_id.total_taxable
				diff_cotisable -= self.payroll_run_id.previous_payslip_run_id.total_cotisable
				diff_taxes_employee -= self.payroll_run_id.previous_payslip_run_id.total_taxes_employee
				diff_taxes_employer -= self.payroll_run_id.previous_payslip_run_id.total_taxes_employer
				diff_net_payment -= self.payroll_run_id.previous_payslip_run_id.total_net_payment
				diff_nb_payslips -= self.payroll_run_id.previous_payslip_run_id.nb_payslips
				
				diff_taxes -= (self.payroll_run_id.previous_payslip_run_id.total_pit + self.payroll_run_id.previous_payslip_run_id.total_act + self.payroll_run_id.previous_payslip_run_id.total_ctax)
				diff_taxes -= (self.payroll_run_id.previous_payslip_run_id.total_cfce + self.payroll_run_id.previous_payslip_run_id.total_cfcp + self.payroll_run_id.previous_payslip_run_id.total_fne)
				diff_taxes -= self.payroll_run_id.previous_payslip_run_id.total_crtv
			
				diff_cnps -= (self.payroll_run_id.previous_payslip_run_id.total_cnpse + self.payroll_run_id.previous_payslip_run_id.total_cnpsp + self.payroll_run_id.previous_payslip_run_id.total_fcon)
				diff_cnps -= self.payroll_run_id.previous_payslip_run_id.total_ipa 
				
			self.diff_gross = "%s" % ('{0:,.0f}'.format(diff_gross))
			self.diff_taxable = "%s" % ('{0:,.0f}'.format(diff_taxable))
			self.diff_cotisable = "%s" % ('{0:,.0f}'.format(diff_cotisable))
			self.diff_taxes_employee = "%s" % ('{0:,.0f}'.format(diff_taxes_employee))
			self.diff_taxes_employer = "%s" % ('{0:,.0f}'.format(diff_taxes_employer))
			self.diff_net_payment = "%s" % ('{0:,.0f}'.format(diff_net_payment))
			self.diff_nb_payslips = "%s" % ('{0:,.0f}'.format(diff_nb_payslips))
			
			self.diff_taxes = "%s" % ('{0:,.0f}'.format(diff_taxes))
			self.diff_cnps = "%s" % ('{0:,.0f}'.format(diff_cnps))
			
		else:
			self.diff_gross = "N/A"
			self.diff_taxable = "N/A"
			self.diff_cotisable = "N/A"
			self.diff_taxes_employee = "N/A"
			self.diff_taxes_employer = "N/A"
			self.diff_net_payment = "N/A"
			self.diff_nb_payslips = "N/A"
			
			self.diff_taxes = "N/A"
			self.diff_cnps = "N/A"
	
	@api.one
	@api.depends('payroll_run_id')
	def _get_current_value(self):
		if self.payroll_run_id:
			self.total_gross = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.total_gross))
			self.total_taxable = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.total_taxable))
			self.total_cotisable = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.total_cotisable))
			self.total_taxes_employee = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.total_taxes_employee))
			self.total_taxes_employer = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.total_taxes_employer))
			self.total_net_payment = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.total_net_payment))
			self.nb_payslips = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.nb_payslips))
			
			total_taxes = self.payroll_run_id.total_pit + self.payroll_run_id.total_act + self.payroll_run_id.total_ctax
			total_taxes += self.payroll_run_id.total_cfce + self.payroll_run_id.total_cfcp + self.payroll_run_id.total_fne
			total_taxes += self.payroll_run_id.total_crtv
			self.total_taxes = "%s" % ('{0:,.0f}'.format(total_taxes))
			total_cnps = self.payroll_run_id.total_cnpse + self.payroll_run_id.total_cnpsp + self.payroll_run_id.total_fcon
			total_cnps += self.payroll_run_id.total_ipa 
			self.total_cnps = "%s" % ('{0:,.0f}'.format(total_cnps))
			
		else:
			self.total_gross = "N/A"
			self.total_taxable = "N/A"
			self.total_cotisable = "N/A"
			self.total_taxes_employee = "N/A"
			self.total_taxes_employer = "N/A"
			self.total_net_payment = "N/A"
			self.nb_payslips = "N/A"

			self.total_taxes = "N/A"
			self.total_cnps = "N/A"
	
	@api.one
	@api.depends('payroll_run_id')
	def _get_previous_value(self):
		if self.payroll_run_id and self.payroll_run_id.previous_payslip_run_id:
			self.previous_month = self.payroll_run_id.previous_payslip_run_id.month_name
			self.previous_total_gross = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.previous_payslip_run_id.total_gross))
			self.previous_total_taxable = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.previous_payslip_run_id.total_taxable))
			self.previous_total_cotisable = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.previous_payslip_run_id.total_cotisable))
			self.previous_total_taxes_employee = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.previous_payslip_run_id.total_taxes_employee))
			self.previous_total_taxes_employer = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.previous_payslip_run_id.total_taxes_employer))
			self.previous_total_net_payment = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.previous_payslip_run_id.total_net_payment))
			self.previous_nb_payslips = "%s" % ('{0:,.0f}'.format(self.payroll_run_id.previous_payslip_run_id.nb_payslips))

			previous_total_taxes = self.payroll_run_id.previous_payslip_run_id.total_pit + self.payroll_run_id.previous_payslip_run_id.total_act 
			previous_total_taxes += self.payroll_run_id.previous_payslip_run_id.total_ctax + self.payroll_run_id.previous_payslip_run_id.total_cfce 
			previous_total_taxes += self.payroll_run_id.previous_payslip_run_id.total_cfcp + self.payroll_run_id.previous_payslip_run_id.total_fne
			previous_total_taxes += self.payroll_run_id.previous_payslip_run_id.total_crtv
			self.previous_total_taxes = "%s" % ('{0:,.0f}'.format(previous_total_taxes))
			previous_total_cnps = self.payroll_run_id.previous_payslip_run_id.total_cnpse + self.payroll_run_id.previous_payslip_run_id.total_cnpsp 
			previous_total_cnps += self.payroll_run_id.previous_payslip_run_id.total_ipa + self.payroll_run_id.previous_payslip_run_id.total_fcon
			self.previous_total_cnps = "%s" % ('{0:,.0f}'.format(previous_total_cnps))
		else:
			self.previous_month = "N/A"
			self.previous_total_gross = "N/A"
			self.previous_total_taxable = "N/A"
			self.previous_total_cotisable = "N/A"
			self.previous_total_taxes_employee = "N/A"
			self.previous_total_taxes_employer = "N/A"
			self.previous_total_net_payment = "N/A"
			self.previous_nb_payslips = "N/A"

			self.previous_total_taxes = "N/A"
			self.previous_total_cnps = "N/A"
