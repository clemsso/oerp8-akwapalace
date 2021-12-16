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
from openerp import models, fields, api, exceptions
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning, ValidationError
import logging

MONTHS = ["January","February","March","April","May","June","July","August",
	"September","October","November","December"]

class School_Template_Fee(models.Model):

	_name = 'school.fee.template.fee'

#	@api.model
#	def _get_default_account(self):
#		account_obj = self.env['account.account']
#		account = account_obj.search([('code','like','706100%')],limit=1)
#		if account:
#			return account[0].id
#		return False
	
	name = fields.Char(string="Name",compute="_get_name",readonly=True,store=True)
	display_name = fields.Char(string="Name",required=True)
	code = fields.Char(string="Code")
	fee_parent_id = fields.Many2one('school.fee.template.fee',string="Parent Template Fee",domain=[('type_fee','=','view')])
	fee_children_ids = fields.One2many('school.fee.template.fee','fee_parent_id',string="Children Template Fees")
	type_fee = fields.Selection([('view','View'),('normal','Normal')],string="Fee Type",default='normal',required=True)
	type_amount = fields.Selection([('amount','Amount'),('percentage','Percentage')],string="Amount Type",default='amount')
	amount = fields.Float(string="Amount",digits=dp.get_precision('Account'))
	amount1 = fields.Float(string="Amount",digits=dp.get_precision('Account'),compute="_get_amount")
	percentage = fields.Float(string="Percentage",digits=(5,2))
	deadline = fields.Char(string="Deadline",compute="_get_deadline",readonly=True)
	deadline1 = fields.Date(string="Deadline",default=fields.Date.today(),required=True)
	fee_item_ids = fields.One2many('school.fee.template.structure.item','template_fee_id',string="Fees Template Structure")
	is_view_and_has_children = fields.Boolean(compute="_is_view_and_has_children")
	is_normal_and_no_parent = fields.Boolean(compute="_is_normal_and_no_parent")
#	account_id = fields.Many2one('account.account',string="Account",required=True,domain=[('code','like','70%'),('type','like','other')],default=_get_default_account)

	@api.one
	@api.depends('fee_children_ids')
	def _get_amount(self):
		self.amount1 = 0
		if self.fee_children_ids:
			for fee in self.fee_children_ids:
				self.amount1 += fee.amount;
		else:
			self.amount1 = self.amount
	
	@api.one
	@api.depends('deadline1')
	def _get_deadline(self):
		if self.type_fee == 'view' and self.fee_children_ids:
			result = self.fee_children_ids[0]
			temp1 = datetime.strptime(result.deadline1,'%Y-%m-%d')
			for fee in self.fee_children_ids:
				temp = datetime.strptime(fee.deadline1,'%Y-%m-%d')
				if temp > temp1:
					result = fee
					temp1 = temp
			self.deadline1 = result.deadline1
			
		if self.deadline1:
			deadline = datetime.strptime(self.deadline1,'%Y-%m-%d')
			today = date.today()
			year = today.year
			if deadline.month <= 8:
				year += 1				
			self.deadline = "%s %s %s" % (deadline.day,MONTHS[deadline.month - 1],year)
	
	@api.one
	@api.depends('display_name','fee_parent_id.display_name')
	def _get_name(self):
		if self.display_name and self.fee_parent_id:
			self.name = self.fee_parent_id.display_name + " / " + self.display_name
		else:
			self.name = self.display_name
	
	@api.one
	@api.constrains('type_fee','fee_parent_id','fee_children_ids')
	def check_parent_view(self):
		if self.type_fee:
			if self.type_fee == 'view' and self.fee_parent_id:
				raise Warning('Sorry, a view template fee cannot have parent !')
			if self.type_fee == 'normal' and self.fee_children_ids:
				raise Warning('Sorry, a normal template fee cannot have children !')
	
	@api.one
	@api.depends('type_fee','fee_children_ids')
	def _is_view_and_has_children(self):
		temp = False
		if self.type_fee:
			if self.type_fee == 'view' and self.fee_children_ids:
				temp = True
		self.is_view_and_has_children = temp
		
	@api.one
	@api.depends('type_fee','fee_parent_id')
	def _is_normal_and_no_parent(self):
		temp = False
		if self.type_fee:
			if self.type_fee == 'normal' and not self.fee_parent_id:
				temp = True
		self.is_normal_and_no_parent = temp

	_sql_constraints = [
		('unique_template_fee_code',
		'UNIQUE(code)',
		"Code has to be unique !"),
		('unique_template_fee_name',
		'UNIQUE(name)',
		"Name has to be unique !"),
		]

class School_Structure_Item(models.Model):
	_name = 'school.fee.template.structure.item'

	name = fields.Char(string="Name",related='template_fee_id.name',readonly=True)
	template_fee_id = fields.Many2one('school.fee.template.fee',string="Template Fee",required=True,domain=[('is_view_and_has_children','=',True)])
	type = fields.Selection([('mandatory','Mandatory'),('optionnal','Optionnal')],required=True,string="Type",default='mandatory')
	student_type = fields.Selection([('new','New'),('old','Old'),('both','Both')],string="Student Type",default='both',required=True)
	student_sex = fields.Selection([('male','Male'),('female','Female'),('both','Both')],string="Sex",required=True,default='both')
	deadline = fields.Char(string="Deadline",related='template_fee_id.deadline',readonly=True)
	fee_structure_ids = fields.Many2many('school.fee.template.structure','school_fee_structure_item_rel','fee_structure_item_ids','fee_structure_ids')
	amount = fields.Float(string="Amount",related='template_fee_id.amount1',digits=dp.get_precision('Account'),readonly=True)
	amount_new = fields.Float(string="New Student",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	amount_old = fields.Float(string="Old student",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	amount_new_boy = fields.Float(string="New Student",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	amount_old_boy = fields.Float(string="New Student",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	amount_new_girl = fields.Float(string="New Student",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	amount_old_girl = fields.Float(string="New Student",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	
	@api.one
	@api.depends('template_fee_id')
	def _get_amount(self):
		self.amount_new = 0
		self.amount_old = 0
		self.amount_new_boy = 0
		self.amount_new_girl = 0
		self.amount_old_boy = 0
		self.amount_old_girl = 0
		if self.template_fee_id:
			if self.type == 'mandatory':
				if self.student_type == 'new' or self.student_type == 'both':
					self.amount_new = self.amount
					if self.student_sex == 'male' or self.student_sex == 'both':
						self.amount_new_boy = self.amount
					if self.student_sex == 'female' or self.student_sex == 'both':
						self.amount_new_girl = self.amount
				if self.student_type == 'old' or self.student_type == 'both':
					self.amount_old = self.amount
					if self.student_sex == 'male' or self.student_sex == 'both':
						self.amount_old_boy = self.amount
					if self.student_sex == 'female' or self.student_sex == 'both':
						self.amount_old_girl = self.amount
	
class School_Structure(models.Model):
	_name = 'school.fee.template.structure'

	name = fields.Char(string="Name",required=True)
	code = fields.Char(string="Code")
	fee_structure_item_ids = fields.Many2many('school.fee.template.structure.item','school_fee_structure_item_rel','fee_structure_ids','fee_structure_item_ids')
	section_ids = fields.One2many('school.academic.section','fee_structure_id',string="Sections Assigned")
	cycle_ids = fields.One2many('school.academic.cycle','fee_structure_id',string="Sections Assigned")
	level_ids = fields.One2many('school.academic.level','fee_structure_id',string="Sections Assigned")
	amount = fields.Float(string="Amount",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	amount_new = fields.Float(string="New Student",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	amount_old = fields.Float(string="Old student",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	amount_new_boy = fields.Float(string="New Boy",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	amount_new_girl = fields.Float(string="New Girl",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	amount_old_boy = fields.Float(string="Old Boy",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	amount_old_girl = fields.Float(string="Old Girl",digits=dp.get_precision('Account'),compute="_get_amount",readonly=True)
	
	@api.one
	@api.depends('fee_structure_item_ids')
	def _get_amount(self):
		self.amount = 0
		self.amount_new = 0
		self.amount_old = 0
		self.amount_new_boy = 0
		self.amount_new_girl = 0
		self.amount_old_boy = 0
		self.amount_old_girl = 0
		
		if self.fee_structure_item_ids:
			for fee in self.fee_structure_item_ids:
				if fee.template_fee_id:
					if fee.type == 'mandatory':
						self.amount += fee.amount
						self.amount_new += fee.amount_new
						self.amount_old += fee.amount_old
						self.amount_new_boy += fee.amount_new_boy
						self.amount_new_girl += fee.amount_new_girl
						self.amount_old_boy += fee.amount_old_boy
						self.amount_old_girl += fee.amount_old_girl
						
	
	_sql_constraints = [
		('unique_template_item_code',
		'UNIQUE(code)',
		"Code has to be unique !"),
		('unique_template_item_name',
		'UNIQUE(name)',
		"Name has to be unique !"),
		]
	
class School_Structure_Section(models.Model):
	_inherit = 'school.academic.section'
	
	fee_structure_id = fields.Many2one('school.fee.template.structure',string="Fees template structure")
	
class School_Structure_Cycle(models.Model):
	_inherit = 'school.academic.cycle'
	
	fee_structure_id = fields.Many2one('school.fee.template.structure',string="Fees template structure")
	
class School_Structure_Lavel(models.Model):
	_inherit = 'school.academic.level'
	
	fee_structure_id = fields.Many2one('school.fee.template.structure',string="Fees template structure")
	amount_new = fields.Float(string="New Student",compute="_get_amount",digits=dp.get_precision('Account'),readonly=True)
	amount_old = fields.Float(string="New Student",compute="_get_amount",digits=dp.get_precision('Account'),readonly=True)
	amount_new_boy = fields.Float(string="New Boy",compute="_get_amount",digits=dp.get_precision('Account'),readonly=True)
	amount_new_girl = fields.Float(string="New Girl",compute="_get_amount",digits=dp.get_precision('Account'),readonly=True)
	amount_old_boy = fields.Float(string="Old Boy",compute="_get_amount",digits=dp.get_precision('Account'),readonly=True)
	amount_old_girl = fields.Float(string="Old Girl",compute="_get_amount",digits=dp.get_precision('Account'),readonly=True)
	
	@api.one
	@api.depends('fee_structure_id')
	def _get_amount(self):
		self.amount_new = 0
		self.amount_old = 0
		self.amount_new_boy = 0
		self.amount_new_girl = 0
		self.amount_old_boy = 0
		self.amount_old_girl = 0
		
		if self.fee_structure_id:
			self.amount_new += self.fee_structure_id.amount_new
			self.amount_old += self.fee_structure_id.amount_old
			self.amount_new_boy += self.fee_structure_id.amount_new_boy
			self.amount_new_girl += self.fee_structure_id.amount_new_girl
			self.amount_old_boy += self.fee_structure_id.amount_old_boy
			self.amount_old_girl += self.fee_structure_id.amount_old_girl
			
		if self.cycle_id and self.cycle_id.fee_structure_id:
			self.amount_new += self.cycle_id.fee_structure_id.amount_new
			self.amount_old += self.cycle_id.fee_structure_id.amount_old
			self.amount_new_boy += self.cycle_id.fee_structure_id.amount_new_boy
			self.amount_new_girl += self.cycle_id.fee_structure_id.amount_new_girl
			self.amount_old_boy += self.cycle_id.fee_structure_id.amount_old_boy
			self.amount_old_girl += self.cycle_id.fee_structure_id.amount_old_girl
			
		if self.cycle_id.section_id and self.cycle_id.section_id.fee_structure_id:
			self.amount_new += self.cycle_id.section_id.fee_structure_id.amount_new
			self.amount_old += self.cycle_id.section_id.fee_structure_id.amount_old
			self.amount_new_boy += self.cycle_id.section_id.fee_structure_id.amount_new_boy
			self.amount_new_girl += self.cycle_id.section_id.fee_structure_id.amount_new_girl
			self.amount_old_boy += self.cycle_id.section_id.fee_structure_id.amount_old_boy
			self.amount_old_girl += self.cycle_id.section_id.fee_structure_id.amount_old_girl
		
	@api.one
	def dummy(self):
		_logger = logging.getLogger(__name__)
		_logger.info('It\'s Okay !!')