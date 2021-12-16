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

class HR_Allowance_Set(models.Model):

	_name = 'hr.payroll.allowance.set'
	
	name = fields.Char(string="Name",required=True)
#	allowance_taxable = fields.Boolean(string="Taxable ?",default=False)
	sequence = fields.Integer(string="Sequence",default=10)
	taxable_percentage = fields.Float(string="Taxable Percentage",default=0)
#	allowance_contributory = fields.Boolean(string="Contributory ?",default=False)
	contributory_percentage = fields.Float(string="Contributory Percentage",default=0)
	code = fields.Char(string="Code",required=True)
	allowance_ids = fields.One2many('hr.payroll.allowance','set_id',string="Allowances")
	rule_id = fields.Many2one('hr.salary.rule',string="Rule",readonly=True)	
	
	@api.multi
	def write(self,vals):
		res = super(HR_Allowance_Set,self).write(vals)
		if 'name' in vals:
			my_vals = {'name':vals['name']}
			self.rule_id.write(my_vals)
		return res
			
	@api.one
	@api.onchange('allowance_taxable','allowance_contributory')
	def check_allowance(self):
		if not self.allowance_taxable:
			self.taxable_percentage = 0
		if not self.allowance_contributory:
			self.contributory_percentage = 0
	
	@api.one
	@api.constrains('code')
	def _check_code(self):
		set_ids = self.env['hr.payroll.allowance.set'].search([('code','=',self.code)])
		
		if len(set_ids) > 1:
			raise Warning('Sorry Category Code has to be unique !')
	
	@api.multi
	def write(self,vals):
		res = super(HR_Allowance_Set,self).write(vals)
		if 'sequence' in vals and self.rule_id:
			self.rule_id.sequence = vals['sequence']
		return res
	
	@api.model
	def create(self,vals):
		rule_obj = self.env['hr.salary.rule']
		category_obj = self.env['hr.salary.rule.category']
		salary_structure_obj = self.env['hr.payroll.structure']
		
		rec = super(HR_Allowance_Set,self).create(vals)

		category_id = category_obj.search([('code','=','ALW')])
		
		result_condition = '''
temp = False
for elem in contract.allowance_ids:
    if elem.code == \'''' + vals['code'] + '''\':
        temp = True
        break
result = temp	
'''
		
		rule_vals = {'name':vals['name'],'sequence':sequence,'code':vals['code'],'appears_on_payslip':1}
		rule_vals.update({'active':1,'category_id':category_id.id,'condition_select':'python'})
		rule_vals.update({'condition_python':result_condition,'amount_select':'code'})
		
		result_compute = '''
amount = 0
for elem in contract.allowance_ids:
    if elem.code == \'''' + vals['code'] + '''\':
        amount = elem.amount
        break
result = amount * worked_days / 30
'''	
		rule_vals.update({'amount_python_compute':result_compute})
		
		rule_id = rule_obj.create(rule_vals)
		rec.write({'rule_id':rule_id.id})
		
		salary_structure_id = salary_structure_obj.search([('code','=','STDS')])
		
		salary_structure_id.rule_ids = [(4,rule_id.id)]
		
		return rec
	
	@api.multi
	def unlink(self):
		if self.allowance_ids:
			raise Warning('Sorry You cannot delete a Category which is linked to Allowances !')
		if self.rule_id:
			self.rule_id.unlink()
		models.Model.unlink(self)
	
class HR_Allowance_Template(models.Model):

	_name = 'hr.payroll.allowance.template'
	
	name = fields.Char(string="Name",required=True)
	type = fields.Selection([('duty_post','Duty Post'),('repres','Representation'),('housinng','Housing'),('water_elec','Water and Electricity'),('car','Car'),('risk','Risk')])
	amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))

class HR_Allowance(models.Model):

	_name = 'hr.payroll.allowance'
	
	name = fields.Char(string="Name",related='set_id.name',readonly=True)
	code = fields.Char(string="Code",related='set_id.code',readonly=True)
	type = fields.Selection([('fix','Fix')],string="Type",required=True,default='fix')
	local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	amount = fields.Float(string="Amount",compute='_amount',digits_compute=dp.get_precision('Payroll'))
	set_id = fields.Many2one('hr.payroll.allowance.set',string="Category")
	contract_id = fields.Many2one('hr.contract',string="Contract")
	rule_id = fields.Many2one(related='set_id.rule_id',string="Rule")
	
#	@api.one
#	@api.constrains('set_id','contract_id')
#	def check_set_id(self):
#		allowance_obj = self.env['hr.payroll.allowance']
		
#		if self.set_id and self.contract_id:
#			allowance_ids = allowance_obj.search([('set_id','=',self.set_id.id),('contract_id','=',self.contract_id)])
#			raise Warning('Sorry You can have only one category of allowance per contract !')
			
#			if len(allowance_ids) > 1:
#				raise Warning('Sorry You can have only one category of allowance per contract !')
	
	@api.one
	@api.depends('type','local_amount','set_id')
	def _amount(self):
		if self.type == 'fix':
			self.amount = self.local_amount
		else:
			self.amount = 0
	
	
class HR_Contract(models.Model):

	_inherit = 'hr.contract'

	allowance_ids = fields.One2many('hr.payroll.allowance','contract_id',string="Allowances")
			
	@api.one
	@api.constrains('allowance_ids')
	def check_allowance(self):
		error = False
		
		if self.allowance_ids:
			set_ids = []
			
			for elem in self.allowance_ids:
				if elem.set_id.id in set_ids:
					error = True
					break
				else:
					set_ids.append(elem.set_id.id)
			
		if error:
			raise Warning('There are two allowances from the same Category !\nPlease remove one !')
		
#	@api.multi
#	def write(self,vals):
#		if vals['allowance_ids']:
#			allowance_obj = self.env['hr.payroll.allowance']
#			for elem in vals['allowance_ids']:
#				elem[2].update({'contract_id':self.id})
#				allowance_obj.create(elem[2])
#		else:
#		raise Warning('Values %s ' % vals)
#			res = super(HR_Contract,self).write(vals)
#			return res
#				raise Warning('Values %s ' % elem)
#		raise Warning('Values %s ' % vals)
			
	
	@api.multi
	def unlink(self):
		if self.allowance_ids:
			for elem in self.allowance_ids:
				elem.unlink()
		models.Model.unlink(self)
	
	duty_post_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	duty_post_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','duty_post')])
	duty_post_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	duty_post_amount = fields.Float(string="Amount",compute='_duty_post_amount',digits_compute=dp.get_precision('Payroll'))
	
	@api.one
	@api.depends('duty_post_type','duty_post_template_id','duty_post_local_amount')
	def _duty_post_amount(self):
		if self.duty_post_type == 'fix':
			self.duty_post_amount = self.duty_post_local_amount
		elif self.duty_post_type == 'template':
			self.duty_post_amount = self.duty_post_template_id.amount
	
	representation_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	representation_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','repres')])
	representation_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	representation_amount = fields.Float(string="Amount",compute='_representation_amount',digits_compute=dp.get_precision('Payroll'))
	
	@api.one
	@api.depends('representation_type','representation_template_id','representation_local_amount')
	def _representation_amount(self):
		if self.representation_type == 'fix':
			self.representation_amount = self.representation_local_amount
		elif self.representation_type == 'template':
			self.representation_amount = self.representation_template_id.amount
	
	housing_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	housing_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','housing')])
	housing_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	housing_amount = fields.Float(string="Amount",compute='_housing_amount',digits_compute=dp.get_precision('Payroll'))
	
	@api.one
	@api.depends('housing_type','housing_template_id','housing_local_amount')
	def _housing_amount(self):
		if self.housing_type == 'fix':
			self.housing_amount = self.housing_local_amount
		elif self.housing_type == 'template':
			self.housing_amount = self.housing_template_id.amount
	
	water_elec_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	water_elec_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','water_elec')])
	water_elec_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	water_elec_amount = fields.Float(string="Amount",compute='_water_elec_amount',digits_compute=dp.get_precision('Payroll'))
	
	@api.one
	@api.depends('water_elec_type','water_elec_template_id','water_elec_local_amount')
	def _water_elec_amount(self):
		if self.water_elec_type == 'fix':
			self.water_elec_amount = self.water_elec_local_amount
		elif self.water_elec_type == 'template':
			self.water_elec_amount = self.water_elec_template_id.amount
	
	car_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	car_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','car')])
	car_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	car_amount = fields.Float(string="Amount",compute='_car_amount',digits_compute=dp.get_precision('Payroll'))
	
	@api.one
	@api.depends('car_type','car_template_id','car_local_amount')
	def _car_amount(self):
		if self.car_type == 'fix':
			self.car_amount = self.car_local_amount
		elif self.car_type == 'template':
			self.car_amount = self.car_template_id.amount
	
	risk_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	risk_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','risk')])
	risk_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	risk_amount = fields.Float(string="Amount",compute='_risk_amount',digits_compute=dp.get_precision('Payroll'))
	
	@api.one
	@api.depends('risk_type','risk_template_id','risk_local_amount')
	def _risk_amount(self):
		if self.risk_type == 'fix':
			self.risk_amount = self.risk_local_amount
		elif self.risk_type == 'template':
			self.risk_amount = self.risk_template_id.amount

	