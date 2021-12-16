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
from dateutil import parser

class Move_Wizard(models.TransientModel):

	_name = 'ngo.project.account.move'
	
	@api.one
	def _get_number(self):
		if self.move_line_ids:
			self.nb_lines = len(self.move_line_ids)
		else:
			self.nb_lines = 0
	
	wizard_id = fields.Many2one('ngo.project.account.wizard',string="Wizard")
	move_line_ids = fields.One2many('ngo.project.account.move.line','move_id',string="Lines")
	
	name = fields.Char(string="Name")
	ref = fields.Char(string="Reference")
	period_id = fields.Many2one('account.period',string="Period")
	date = fields.Date(string="Date")
	
	nb_lines = fields.Integer(string="Number of Lines", compute='_get_number')
	status = fields.Boolean(string="Status", compute='_get_status')
	
	@api.one
	@api.depends('move_line_ids')
	def _get_status(self):
		self.status = True
		if self.move_line_ids:
			for line in self.move_line_ids:
				if line.nb_analytic > 1:
					self.status = False
	
class Move_Line_Wizard(models.TransientModel):

	_name = 'ngo.project.account.move.line'
	
	move_id = fields.Many2one('ngo.project.account.move',string="Move")
	
	name = fields.Char(string="Name")
	debit = fields.Float(string="Debit")
	credit = fields.Float(string="Credit")
	account_id = fields.Many2one('account.account',string="Account")
	analytic_id = fields.Many2one('account.analytic.account',string="Analytic Account")
	nb_analytic = fields.Integer(String="Number")
	
class Account_Wizard(models.TransientModel):

	_name = 'ngo.project.account.wizard'

	move_ids = fields.One2many('ngo.project.account.move','wizard_id',string="Move")
	
	file_move_line = fields.Binary(string="Upload file")
	file_move_name = fields.Char(string="File Name")
	file_decode_text = fields.Text(string="Content")
	
	journal_id = fields.Many2one('account.journal',string="Journal")
	project_id = fields.Many2one('hr.contract.project.template',string="Project",readonly=True)
	budget_id = fields.Many2one('crossovered.budget',string="Budget",readonly=True)
	
	def _is_float(self,value):
		try:
			float(value)
			return True
		except ValueError:
			return False
	
	@api.onchange('file_move_line')
	def get_content(self):
		obj_move = self.env['ngo.project.account.move']
		obj_move_line = self.env['ngo.project.account.move.line']
		obj_period = self.env['account.period']
		obj_account = self.env['account.account']
		obj_account_analytic = self.env['account.analytic.account']
		obj_budget_post = self.env['account.budget.post']
		obj_budget_line = self.env['crossovered.budget.lines']
	
		if self.file_move_line:
			lines = self.file_move_line.decode('base64')
			result = lines.split('\r\n')
			self.file_decode_text = result
			
			list_moves = []
			list_move_lines = []
			temp_tcode = False
			move_id = None
			
			number_line = 0
			
			for line in result:
				number_line = number_line + 1
			
				# Prepare the line
				my_line = line.split(';')
			
				my_date = parser.parse(my_line[3])
			
				my_temp_period = str(my_date.month).rjust(2,'0') + '/' + str(my_date.year)
				result_period = obj_period.search([('code','=',my_temp_period)])
				period_id = False
				
				result_account = obj_account.search([('code','=',my_line[0])])
				account_id = False

				if result_period:
					period_id = result_period[0].id
				else:
					raise Warning('The line number %s has a wrong period: "%s"' % (number_line,line))
					
				if result_account:
					account_id = result_account[0].id
				else:
					raise Warning('the line number %s has a wrong account: "%s"' % (number_line,line))
				
				search_budget_post_ids = obj_budget_post.search([('account_ids','in',[account_id])])

				search_budget_line_ids = obj_budget_line.search([('general_budget_id','in',[])])
				
				if len(search_budget_post_ids) > 0:
					search_budget_line_ids = obj_budget_line.search([('general_budget_id','in',search_budget_post_ids.ids),('crossovered_budget_id','in',[self.budget_id.id])])
				
				analytic_id = False
				
				if search_budget_line_ids and search_budget_line_ids[0].analytic_account_id:
					analytic_id = search_budget_line_ids[0].analytic_account_id.id
				
				move_vals = {
					'name':my_line[2],
					'ref':my_line[4],
					'date': my_date,
					'period_id': period_id
					}

				# Create/Add Move and Move line
				
				if not temp_tcode:
					temp_tcode = my_line[2]
					
					# Create Move and add to wizard
					move_id = obj_move.create(move_vals)
					list_moves.append(move_id.id)
					
				if temp_tcode:
					
					my_debit = 0.0
					my_credit = 0.0
					
					if self._is_float(my_line[5]):
						my_debit = float(my_line[5])
					else:
						Warning('The line number %s has a wrong Debit: "%s"' % (number_line,my_line[5]))
						
					if self._is_float(my_line[6]):
						my_credit = float(my_line[6])
					else:
						Warning('The line number %s has a wrong Credit: "%s"' % (number_line,my_line[6]))
					
					# Create Move Line and add to move
					move_line_vals = {
						'name':my_line[4],
						'debit':my_debit,
						'credit':my_credit,
						'account_id':account_id,
						'analytic_id':analytic_id,
						'nb_analytic': len(search_budget_line_ids),
						}
					
					if temp_tcode != my_line[2]:
						temp_tcode = my_line[2]

						list_move_lines = []
						move_id = None
						
						# Create Move and add to wizard
						#raise Warning("wizard ID: %s" % self._origin.id)
						move_vals.update({'wizard_id':self._origin.id})
						move_id = obj_move.create(move_vals)
						list_moves.append(move_id.id)

						# Create Move Line by the same time
						move_line_vals.update({'move_id':move_id.id})
						
						move_line_id = obj_move_line.create(move_line_vals)
						list_move_lines.append(move_line_id.id)
					else:
						# Create Move Line
						move_line_vals.update({'move_id':move_id.id})

						move_line_id = obj_move_line.create(move_line_vals)
						list_move_lines.append(move_line_id.id)
						
			self.move_ids = obj_move.search([('id','in',list_moves)])
	
	@api.one
	def import_entries(self):
	
		obj_move = self.env['account.move']
		obj_move_line = self.env['account.move.line']
	
		if self.journal_id:
			if self.move_ids:
				#raise Warning("Number of Moves: %s" % len(self.move_ids))
				
				for move in self.move_ids:
					
					move_vals = {
						'name': move.name,
						'ref': move.ref,
						'date': move.date,
						'period_id': move.period_id.id,
						'journal_id': self.journal_id.id
						}
					
					move_id = obj_move.create(move_vals)
					
					for move_line in move.move_line_ids:
					
						move_line_vals = {
							'name': move_line.name,
							'debit': move_line.debit,
							'credit': move_line.credit,
							'move_id': move_id.id,
							'account_id': move_line.account_id.id,
							'project_id': self.project_id.id,
							}
							
						if move_line.analytic_id:
							move_line_vals.update({'analytic_account_id': move_line.analytic_id.id})
				
						move_line_id = obj_move_line.create(move_line_vals)
				
			else:
				raise Warning("Sorry, there is no move to import !!")
		
		else:
			raise Warning('Please, select first a journal !')
	
#				self.move_ids += move_id
#				self.write({'move_ids':[(4,move_id.id)]})

#	@api.onchange('file_move_line')
#	def file_move_change(self):
#		if file_move_line:
	

# class Account_Project(models.Model):

	# _name = ''
	
	# name = fields.Char(string="Name",required=True)
#	allowance_taxable = fields.Boolean(string="Taxable ?",default=False)
	# sequence = fields.Integer(string="Sequence",default=10)
	# taxable_percentage = fields.Float(string="Taxable Percentage",default=0)
#	allowance_contributory = fields.Boolean(string="Contributory ?",default=False)
	# contributory_percentage = fields.Float(string="Contributory Percentage",default=0)
	# code = fields.Char(string="Code",required=True)
	# allowance_ids = fields.One2many('hr.payroll.allowance','set_id',string="Allowances")
	# rule_id = fields.Many2one('hr.salary.rule',string="Rule",readonly=True)	
	
	# @api.multi
	# def write(self,vals):
		# res = super(HR_Allowance_Set,self).write(vals)
		# if 'name' in vals:
			# my_vals = {'name':vals['name']}
			# self.rule_id.write(my_vals)
		# return res
			
	# @api.one
	# @api.onchange('allowance_taxable','allowance_contributory')
	# def check_allowance(self):
		# if not self.allowance_taxable:
			# self.taxable_percentage = 0
		# if not self.allowance_contributory:
			# self.contributory_percentage = 0
	
	# @api.one
	# @api.constrains('code')
	# def _check_code(self):
		# set_ids = self.env['hr.payroll.allowance.set'].search([('code','=',self.code)])
		
		# if len(set_ids) > 1:
			# raise Warning('Sorry Category Code has to be unique !')
	
	# @api.multi
	# def write(self,vals):
		# res = super(HR_Allowance_Set,self).write(vals)
		# if 'sequence' in vals and self.rule_id:
			# self.rule_id.sequence = vals['sequence']
		# return res
	
	# @api.model
	# def create(self,vals):
		# rule_obj = self.env['hr.salary.rule']
		# category_obj = self.env['hr.salary.rule.category']
		# salary_structure_obj = self.env['hr.payroll.structure']
		
		# rec = super(HR_Allowance_Set,self).create(vals)

		# category_id = category_obj.search([('code','=','ALW')])
		
		# result_condition = '''
# temp = False
# for elem in contract.allowance_ids:
    # if elem.code == \'''' + vals['code'] + '''\':
        # temp = True
        # break
# result = temp	
# '''
		
		# rule_vals = {'name':vals['name'],'sequence':sequence,'code':vals['code'],'appears_on_payslip':1}
		# rule_vals.update({'active':1,'category_id':category_id.id,'condition_select':'python'})
		# rule_vals.update({'condition_python':result_condition,'amount_select':'code'})
		
		# result_compute = '''
# amount = 0
# for elem in contract.allowance_ids:
    # if elem.code == \'''' + vals['code'] + '''\':
        # amount = elem.amount
        # break
# result = amount * worked_days / 30
# '''	
		# rule_vals.update({'amount_python_compute':result_compute})
		
		# rule_id = rule_obj.create(rule_vals)
		# rec.write({'rule_id':rule_id.id})
		
		# salary_structure_id = salary_structure_obj.search([('code','=','STDS')])
		
		# salary_structure_id.rule_ids = [(4,rule_id.id)]
		
		# return rec
	
	# @api.multi
	# def unlink(self):
		# if self.allowance_ids:
			# raise Warning('Sorry You cannot delete a Category which is linked to Allowances !')
		# if self.rule_id:
			# self.rule_id.unlink()
		# models.Model.unlink(self)
	
# class HR_Allowance_Template(models.Model):

	# _name = 'hr.payroll.allowance.template'
	
	# name = fields.Char(string="Name",required=True)
	# type = fields.Selection([('duty_post','Duty Post'),('repres','Representation'),('housinng','Housing'),('water_elec','Water and Electricity'),('car','Car'),('risk','Risk')])
	# amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))

# class HR_Allowance(models.Model):

	# _name = 'hr.payroll.allowance'
	
	# name = fields.Char(string="Name",related='set_id.name',readonly=True)
	# code = fields.Char(string="Code",related='set_id.code',readonly=True)
	# type = fields.Selection([('fix','Fix')],string="Type",required=True,default='fix')
	# local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	# amount = fields.Float(string="Amount",compute='_amount',digits_compute=dp.get_precision('Payroll'))
	# set_id = fields.Many2one('hr.payroll.allowance.set',string="Category")
	# contract_id = fields.Many2one('hr.contract',string="Contract")
	# rule_id = fields.Many2one(related='set_id.rule_id',string="Rule")
	
#	@api.one
#	@api.constrains('set_id','contract_id')
#	def check_set_id(self):
#		allowance_obj = self.env['hr.payroll.allowance']
		
#		if self.set_id and self.contract_id:
#			allowance_ids = allowance_obj.search([('set_id','=',self.set_id.id),('contract_id','=',self.contract_id)])
#			raise Warning('Sorry You can have only one category of allowance per contract !')
			
#			if len(allowance_ids) > 1:
#				raise Warning('Sorry You can have only one category of allowance per contract !')
	
	# @api.one
	# @api.depends('type','local_amount','set_id')
	# def _amount(self):
		# if self.type == 'fix':
			# self.amount = self.local_amount
		# else:
			# self.amount = 0
	
	
# class HR_Contract(models.Model):

	# _inherit = 'hr.contract'

	# allowance_ids = fields.One2many('hr.payroll.allowance','contract_id',string="Allowances")
			
	# @api.one
	# @api.constrains('allowance_ids')
	# def check_allowance(self):
		# error = False
		
		# if self.allowance_ids:
			# set_ids = []
			
			# for elem in self.allowance_ids:
				# if elem.set_id.id in set_ids:
					# error = True
					# break
				# else:
					# set_ids.append(elem.set_id.id)
			
		# if error:
			# raise Warning('There are two allowances from the same Category !\nPlease remove one !')
		
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
			
	
	# @api.multi
	# def unlink(self):
		# if self.allowance_ids:
			# for elem in self.allowance_ids:
				# elem.unlink()
		# models.Model.unlink(self)
	
	# duty_post_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	# duty_post_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','duty_post')])
	# duty_post_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	# duty_post_amount = fields.Float(string="Amount",compute='_duty_post_amount',digits_compute=dp.get_precision('Payroll'))
	
	# @api.one
	# @api.depends('duty_post_type','duty_post_template_id','duty_post_local_amount')
	# def _duty_post_amount(self):
		# if self.duty_post_type == 'fix':
			# self.duty_post_amount = self.duty_post_local_amount
		# elif self.duty_post_type == 'template':
			# self.duty_post_amount = self.duty_post_template_id.amount
	
	# representation_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	# representation_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','repres')])
	# representation_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	# representation_amount = fields.Float(string="Amount",compute='_representation_amount',digits_compute=dp.get_precision('Payroll'))
	
	# @api.one
	# @api.depends('representation_type','representation_template_id','representation_local_amount')
	# def _representation_amount(self):
		# if self.representation_type == 'fix':
			# self.representation_amount = self.representation_local_amount
		# elif self.representation_type == 'template':
			# self.representation_amount = self.representation_template_id.amount
	
	# housing_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	# housing_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','housing')])
	# housing_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	# housing_amount = fields.Float(string="Amount",compute='_housing_amount',digits_compute=dp.get_precision('Payroll'))
	
	# @api.one
	# @api.depends('housing_type','housing_template_id','housing_local_amount')
	# def _housing_amount(self):
		# if self.housing_type == 'fix':
			# self.housing_amount = self.housing_local_amount
		# elif self.housing_type == 'template':
			# self.housing_amount = self.housing_template_id.amount
	
	# water_elec_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	# water_elec_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','water_elec')])
	# water_elec_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	# water_elec_amount = fields.Float(string="Amount",compute='_water_elec_amount',digits_compute=dp.get_precision('Payroll'))
	
	# @api.one
	# @api.depends('water_elec_type','water_elec_template_id','water_elec_local_amount')
	# def _water_elec_amount(self):
		# if self.water_elec_type == 'fix':
			# self.water_elec_amount = self.water_elec_local_amount
		# elif self.water_elec_type == 'template':
			# self.water_elec_amount = self.water_elec_template_id.amount
	
	# car_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	# car_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','car')])
	# car_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	# car_amount = fields.Float(string="Amount",compute='_car_amount',digits_compute=dp.get_precision('Payroll'))
	
	# @api.one
	# @api.depends('car_type','car_template_id','car_local_amount')
	# def _car_amount(self):
		# if self.car_type == 'fix':
			# self.car_amount = self.car_local_amount
		# elif self.car_type == 'template':
			# self.car_amount = self.car_template_id.amount
	
	# risk_type = fields.Selection([('fix','Fix Amount'),('template','Template')],string="Type",required=True,default='fix')
	# risk_template_id = fields.Many2one('hr.payroll.allowance.template',string="Template",domain=[('type','=','risk')])
	# risk_local_amount = fields.Float(string="Amount",digits_compute=dp.get_precision('Payroll'))
	# risk_amount = fields.Float(string="Amount",compute='_risk_amount',digits_compute=dp.get_precision('Payroll'))
	
	# @api.one
	# @api.depends('risk_type','risk_template_id','risk_local_amount')
	# def _risk_amount(self):
		# if self.risk_type == 'fix':
			# self.risk_amount = self.risk_local_amount
		# elif self.risk_type == 'template':
			# self.risk_amount = self.risk_template_id.amount

	