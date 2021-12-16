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
from xlwt import Workbook, Formula, easyxf
import base64
import locale
import StringIO

class Budget_Category(models.Model):

	_name = 'ngo.budget.category'
	
	@api.one
	@api.depends('budget_line_ids')
	def _get_amount(self):
		self.planned_amount = 0
		
		if self.budget_line_ids:
			for line in self.budget_line_ids:
				self.planned_amount = self.planned_amount + line.planned_amount
	
	name = fields.Char(string="Name")
	display_name = fields.Char(string="Name",compute='get_name')
	budget_id = fields.Many2one('crossovered.budget',string="Budget Related")
	budget_line_ids = fields.One2many('crossovered.budget.lines','budget_category_id',string="Budget Lines")
	budget_line_number = fields.Integer(string="Budget Line Number",compute='get_nb_budget')
	code = fields.Char(string="Class",compute='get_code')
	planned_amount = fields.Float(string="Planned Amount",compute='_get_amount')
	
	@api.one
	@api.depends('name','budget_id')
	def get_name(self):
		if self.name and self.budget_id:
			self.display_name = self.budget_id.name + ' / ' + self.name
	
	@api.one
	@api.depends('budget_line_ids')
	def get_nb_budget(self):
		self.budget_line_number = 0
		if self.budget_line_ids:
			self.budget_line_number = len(self.budget_line_ids)
			
	@api.one
	@api.depends('budget_line_ids')
	@api.onchange('budget_line_ids')
	def get_code(self):
		if self.budget_line_ids:
			self.code = self.budget_line_ids[0].line_code
			
	@api.one
	def get_amount(self, period):
	
		result = 0
#		obj_period = self.env['account.period']
		obj_analytic_line = self.env['account.analytic.line']
		
#		period_ids = obj_period.search([('id','=',period)])
		
		if period:
			period_id = period
			
			acc_ids = []
			if self.budget_line_ids:
				for line in self.budget_line_ids:
					if line.analytic_account_id and (line.analytic_account_id.id not in acc_ids):
						acc_ids.append(line.analytic_account_id.id)
			
			start_date = period_id.date_start
			stop_date = period_id.date_stop
			project_id = None
			
			if self.budget_id:
				project_id = self.budget_id.project_id.id
			
			temp = obj_analytic_line.search([('date','>=',start_date),
											('date','<=',stop_date),
											('account_id','in',acc_ids),
											('project_id','=',project_id)])
			
#			raise Warning("Category name: %s and period: %s  and length: %s " % (self.name,period_id.code,len(temp)))
			
			if temp:
				for line in temp:
					result = result + line.amount
	
		return abs(result)
	
class Budget_Related1(models.Model):

	_inherit = 'crossovered.budget'
	
	@api.one
	def _get_periods(self):
		if self.date_from:
			obj_period = self.env['account.period']
			obj_fiscal = self.env['account.fiscalyear']
			
			date_from = datetime.strptime(self.date_from,'%Y-%m-%d')
			period = str(date_from.month).rjust(2,'0') + '/' + str(date_from.year)
			period_id = obj_period.search([('code','=',period)])
			
			if period_id and period_id.fiscalyear_id:
				self.fiscalyear_id = period_id.fiscalyear_id
				self.period_ids = period_id.fiscalyear_id.period_ids[1:]

	@api.one
	def _get_planned_amount(self):
		self.planned_amount = 0
		if self.crossovered_budget_line:
			for line in self.crossovered_budget_line:
				self.planned_amount = self.planned_amount + line.planned_amount
				
	budget_category_ids = fields.One2many('ngo.budget.category','budget_id',string="Categories")
	period_ids = fields.Many2many('account.period',string="Periods", compute='_get_periods')
	fiscalyear_id = fields.Many2many('account.fiscalyear',string="Fiscal Year", compute='_get_periods')
	planned_amount = fields.Float(string="Planned Amount",compute='_get_planned_amount')
	currency_amount = fields.Float(string="Conversion Rate ($)",default=500)
	budget_ytd_file = fields.Binary(string="YTD XLS File",compute='get_budget_ytd_file')
	budget_ytd_file_name = fields.Char(string="File Name",compute='get_budget_ytd_file')
	
	@api.one
	def get_expense_periods(self):
		result = []
		acc_ids = []
		position = -1
		
		obj_analytic_line = self.env['account.analytic.line']
		
		if self.crossovered_budget_line:
			for line in self.crossovered_budget_line:
				if line.analytic_account_id and (line.analytic_account_id.id not in acc_ids):
					acc_ids.append(line.analytic_account_id.id)
		
		if self.period_ids:
			for period_id in self.period_ids:
				position = position + 1
				start_date = period_id.date_start
				stop_date = period_id.date_stop
			
				temp = obj_analytic_line.search([('date','>=',start_date),
											('date','<=',stop_date),
											('account_id','in',acc_ids),
											('project_id','=',self.project_id.id)])
				
				result.append(0)
				
				if temp:
					for elem in temp:
						result[position] = result[position] + abs(elem.amount)
				
		return result
	
	@api.multi
	def print_budget_ytd(self):
		#Print Budget Year to Date consumption
		if self.budget_category_ids and self.crossovered_budget_line:
			#return self.env['report'].get_action(self,'hr_payroll_allowance.project_compare_history_template')
			raise Warning('number of period: %s ' % self.period_ids)
		else:
			raise Warning('Sorry, there is no budget lines or Category !')

	@api.multi
	def budget_ytd_cfa(self):
#		period_id = self.env['account.period'].search([('code','=','12/2017')])
		
#		if period_id and self.budget_category_ids:
#			self.budget_category_ids[0].get_amount(period_id)

#		result = self.get_expense_periods()
#		raise Warning('Lenght Expenses Periods: %s ' % result[0])

#		raise Warning('Printing Ready !!!')
		return self.env['report'].get_action(self,'ngo_project.budget_ytd_cfa_template')

	@api.multi
	def budget_ytd_xls(self):
#		raise Warning('Printing Ready !!!')
		return {
			'type':'ir.actions.act_url',
			'url':'/web/binary/download_document?model=crossovered.budget&field=budget_ytd_file&id=%s&filename=budget_ytd_%s_%s.xls'%(self.id,self.name,self.fiscalyear_id.name),
			'target':'self',
			}

	@api.one
	def get_budget_ytd_file(self):
		content = ""
		wb = Workbook()
		sheet = wb.add_sheet('GHSS Budget YTD')
		
		sheet.col(0).width = 256 * 20
		sheet.col(1).width = 256 * 15
		sheet.col(2).width = 256 * 20
		sheet.col(3).width = 256 * 12
		sheet.col(4).width = 256 * 12
		sheet.col(5).width = 256 * 12
		sheet.col(6).width = 256 * 12
		sheet.col(7).width = 256 * 12
		sheet.col(8).width = 256 * 12
		sheet.col(9).width = 256 * 12
		sheet.col(10).width = 256 * 12
		sheet.col(11).width = 256 * 12
		sheet.col(12).width = 256 * 12
		sheet.col(13).width = 256 * 12
		sheet.col(14).width = 256 * 12
		sheet.col(15).width = 256 * 25
		sheet.col(16).width = 256 * 15
		sheet.col(17).width = 256 * 10
		
		style_total_title = easyxf('font: bold on; align: horiz center;')
		style_align_right = easyxf('align: horiz right;')
		style_total_amount = easyxf('font: bold on;')
		style_percentage = easyxf('font: bold on;')
		style_amount = easyxf()
		style_total_amount.num_format_str = '#,##0'
		style_amount.num_format_str = '#,##0'
		style_percentage.num_format_str = '0.00%'
		
		line_number = 0
		xls_file = StringIO.StringIO()
		
		
		sheet.write(0,0,"COMPANY",style_total_amount)
		sheet.write_merge(0,0,1,3,self.company_id.name,style_total_amount)
		
		sheet.write(1,0,"PROJECT",style_total_amount)
		sheet.write_merge(1,1,1,3,self.project_id.name,style_total_amount)
		
		sheet.write(2,0,"Fiscal Year",style_total_amount)
		sheet.write_merge(2,2,1,3,self.fiscalyear_id.name,style_total_amount)
		
		sheet.write(3,0,"BUDGET",style_total_amount)
		sheet.write_merge(3,3,1,3,self.name,style_total_amount)
		
		sheet.write(5,0,"BUDGET CATEGORY",style_total_title)
		sheet.write(5,1,"OBJECT CLASS",style_total_title)
		sheet.write(5,2,"BUDGETED AMOUNT",style_total_title)
		
		col_number = 3
		
		if self.period_ids:
			for period_id in self.period_ids:
				sheet.write(5,col_number,period_id.name,style_total_title)
				col_number += 1
		
		line_number = 7
		total_planned_amount = 0
		
		if self.budget_category_ids:
			for category in self.budget_category_ids:
				sheet.write(line_number,0,category.name)
				sheet.write(line_number,1,category.code, style_align_right)
				sheet.write(line_number,2,category.planned_amount,style_total_amount)
				
				col_number = 3
				pratical_amount = 0
				
				if self.period_ids:
					for period_id in self.period_ids:
						temp = category.get_amount(period_id)[0]
						pratical_amount = pratical_amount + temp
						sheet.write(line_number,col_number,temp,style_amount)
						col_number += 1
				
				sheet.write(line_number,15,pratical_amount,style_total_amount)
				
				balance = category.planned_amount - pratical_amount
				sheet.write(line_number,16,balance,style_total_amount)
				
				variance = pratical_amount / category.planned_amount
				sheet.write(line_number,17,variance,style_percentage)
				
				total_planned_amount = total_planned_amount + category.planned_amount
				line_number += 2
		
		sheet.write_merge(line_number,line_number,0,1,"TOTAL",style_total_amount)
		sheet.write(line_number,2,total_planned_amount,style_total_amount)
		
		sheet.write(5,15,"TOTAL EXPENDITURE",style_total_title)
		sheet.write(5,16,"BALANCE",style_total_title)	
		sheet.write(5,17,"VARIANCE",style_total_title)
		
		total_expenditure = 0
		col_number = 3
		
		for elem in self.get_expense_periods()[0]:
			sheet.write(line_number,col_number,elem,style_total_amount)
			total_expenditure = total_expenditure + elem
			col_number += 1

		balance = total_planned_amount - total_expenditure
		variance = total_expenditure / total_planned_amount
		
		sheet.write(line_number,15,total_expenditure,style_total_amount)
		sheet.write(line_number,16,balance,style_total_amount)
		sheet.write(line_number,17,variance,style_percentage)
		
		wb.save(xls_file)
		xls_content = xls_file.getvalue()
		xls_file.close()
		self.budget_ytd_file = base64.b64encode(xls_content)
		self.budget_ytd_file_name = "budget_ytd_%s.xls" % (self.name)

		
	@api.multi
	def budget_detail(self):
#		raise Warning('Printing Ready !!!')
		return self.env['report'].get_action(self,'ngo_project.budget_detail_template')

	@api.multi
	def budget_ytd(self):
#		period_id = self.env['account.period'].search([('code','=','12/2017')])
		
#		if period_id and self.budget_category_ids:
#			self.budget_category_ids[0].get_amount(period_id)

#		result = self.get_expense_periods()
#		raise Warning('Lenght Expenses Periods: %s ' % result[0])

#		raise Warning('Printing Ready !!!')
		return self.env['report'].get_action(self,'ngo_project.budget_ytd_template')
		
	@api.multi
	def import_entries(self):
#		raise Warning("Ready to get the Wizard !!!")
		wizard_form = self.env.ref('ngo_project.ngo_project_account_wizard_form',False)
		view_id = self.env['ngo.project.account.wizard']
		
		if not self.project_id:
			raise Warning('Please select a project first for the budget')
		
		vals = {
			'project_id'	: self.project_id.id,
			'budget_id'		: self.id,
#			'cash'		: 0,
			}
			
		new_info = view_id.create(vals)

		return {
			'name'		:	_('Import Journal Entries'),
			'type'		:	'ir.actions.act_window',
			'res_model'	:	'ngo.project.account.wizard',
			'res_id'	:	new_info.id,
			'view_id'	:	wizard_form.id,
			'view_type'	:	'form',
			'view_mode'	:	'form',
			'target'	:	'new'
			}


			
class Budget_Lines(models.Model):

	_inherit = 'crossovered.budget.lines'
		
	budget_category_id = fields.Many2one('ngo.budget.category',string="Category")	
	line_code = fields.Char(string="Class",compute='get_code')
	sequence = fields.Integer(string="Seq",default=100)
	
	_order = 'sequence'
	
	@api.one
	@api.depends('general_budget_id')
	def get_code(self):
		if self.general_budget_id:
			self.line_code = self.general_budget_id.code
			
class Bugetary_Position(models.Model):

	_inherit = 'account.budget.post'
	
	@api.one
	def _is_linked(self):
		if self.crossovered_budget_line and len(self.crossovered_budget_line) > 0:
			self.linked = True
		else:
			self.linked = False
	
	linked = fields.Boolean('Is linked',compute='_is_linked')

