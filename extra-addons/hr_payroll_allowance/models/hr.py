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

class Field_Education(models.Model):
	_name = 'hr.education.field'
	
	name = fields.Char(string="Field of Education")

class HR_Employee_Extra(models.Model):

	_inherit = 'hr.employee'
	
	matricule = fields.Char(string="Matricule",default=lambda self: self._get_matricule())
	direct_supervisor = fields.Many2one('hr.employee',string="Supervisor")
	real_name = fields.Char(string="Real Name",required=True)
	bank_account_ids = fields.One2many('hr.bank.account','employee_id',string="Bank Accounts")
	field_id = fields.Many2one('hr.education.field',string="Field")
	first_bank_account_id = fields.Char(string="Bank Account Number",compute='_get_first_bank_account',readonly=True)
	expiration_date = fields.Date(string="Expiration Date",default=fields.Date.today())
	address_home = fields.Text(string="Home Address")
	expiration_date_card = fields.Integer(string="Reamaining Time of expiration",compute='_get_remaining_time')
	
	@api.model
	def _get_matricule(self):
		return self.env['ir.sequence'].get('hr.employee.matricule')

	@api.one
	@api.onchange('name_related')
	def change_real_name(seld):
		self.real_name = self.name_related
		
	@api.one
	@api.constrains('matricule')
	def check_matricule(self):
		mat_ids = self.env['hr.employee'].search([('matricule','=',self.matricule)])
		
		if len(mat_ids) > 1:
			raise Warning('Sorry ! Matrcule has to be Unique !')
	
	@api.one
	@api.depends('expiration_date')
	def _get_remaining_time(self):
		return 7
	
	@api.one
	@api.depends('bank_account_ids')
	def _get_first_bank_account(self):
		if self.bank_account_ids:
			self.first_bank_account_id = "%s (%s)" % (self.bank_account_ids[0].name,self.bank_account_ids[0].bank_id.name)
		else:
			self.first_bank_account_id = None
	
class Company_Extra_SSNID(models.Model):

	_inherit = 'res.company'
	
	ssnid = fields.Char(string="SSN No", help="Employer Social Security Number")
	regime = fields.Selection([('general','General'),('agriculture','Agriculture'),('education','Education')],string="Regime",default='general')
	niu = fields.Char(string="NIU")

class Bank_Account(models.Model):
	_name = 'hr.bank'
		
	name = fields.Char(string="Bank Name",required=True)
	bank_account_ids = fields.One2many('hr.bank.account','bank_id',string="Accounts")
		
class Bank_Account(models.Model):
	_name = 'hr.bank.account'
	
	name = fields.Char(string="Account Number",required=True)
	bank_id = fields.Many2one('hr.bank',string="Bank",required=True)
	employee_id = fields.Many2one('hr.employee',string="Employee")
	