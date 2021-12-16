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

class Account_Move_Project(models.Model):

	_inherit = 'account.move'

	@api.one
	def _check_project(self):
		self.check_project = False
		if self.project and (self.project.id in self.env.user.allowed_project_ids.ids):
			self.check_project = True

	@api.depends('line_id')
	@api.one
	def _get_project(self):
		if self.line_id:
			self.project = self.line_id[0].project_id
	
	check_project = fields.Boolean(string="Check Project",readonly=True,compute='_check_project', store=True,)
	project = fields.Many2one('hr.contract.project.template',readonly=True,compute='_get_project',string="Project",store=True)
	project_id = fields.Many2one('hr.contract.project.template',string="Project")
	activity_id = fields.Many2one('ngo.budget.activity',string="Activity")

	
class Account_Move_Line_Project(models.Model):

	_inherit = 'account.move.line'
	
	@api.one
	def _check_project(self):
		self.check_project = False
		if self.project_id and (self.project_id in self.env.user.allowed_project_ids):
			self.check_project = True
	
	check_project = fields.Boolean(string="Check Project",readonly=True,compute='_check_project')
	project_id = fields.Many2one('hr.contract.project.template',string="Project")
	activity_id = fields.Many2one('ngo.budget.activity',string="Activity")
	
	
	@api.onchange('project_id')
	def project_change(self):
		res = {}
		if self.project_id:
			res['domain'] = {'activity_id': [('id','in',[elem.id for elem in [elem1.activity_ids for elem1 in self.project_id.budget_ids]])]}

			if (len(self.project_id.general_account_ids) > 0):
				res['domain'] = {'account_id': [('id','in',[elem.id for elem in self.project_id.general_account_ids])]}
		else:
			res['domain'] = {'account_id': []}
			res['domain'] = {'activity_id': []}
		
		return res
	
class Account_move_analytic(models.Model):

	_inherit = 'account.analytic.line'
	
	@api.one
	def _check_project(self):
		self.check_project = False
		if self.project_id and (self.project_id in self.env.user.allowed_project_ids):
			self.check_project = True
	
	check_project = fields.Boolean(string="Check Project",readonly=True,compute='_check_project')
	project_id = fields.Many2one('hr.contract.project.template',string="Project")
	
	def _prepare_analytic_line(self,obj_line):
		raise Warning('We are going in here !!')
#		return {'name': obj_line.name,
#				'date': obj_line.date,
#				'account_id': obj_line.analytic_account_id.id,
#				'unit_amount': obj_line.quantity,
#				'product_id': obj_line.product_id and obj_line.product_id.id or False,
#				'product_uom_id': obj_line.product_uom_id and obj_line.product_uom_id.id or False,
#				'amount': (obj_line.credit or  0.0) - (obj_line.debit or 0.0),
#				'general_account_id': obj_line.account_id.id,
#				'journal_id': obj_line.journal_id.analytic_journal_id.id,
#				'ref': obj_line.ref,
#				'move_id': obj_line.id,
#				'user_id': obj_line.invoice.user_id.id or uid,
#				'project_id': obj_line.project_id and obj_line.project_id.id or False,
#              }

