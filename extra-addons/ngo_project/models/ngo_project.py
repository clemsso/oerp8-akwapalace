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

class HR_Project(models.Model):

	_inherit = 'hr.contract.project.template'

	@api.one
	def _check_project(self):
		self.check_project = False
		if (self.id in self.env.user.allowed_project_ids.ids):
			self.check_project = True

	move_line_ids = fields.One2many('account.move.line','project_id',string="Entry Lines")
	move_ids = fields.One2many('account.move','project_id',string="Entries")

	general_account_ids = fields.Many2many('account.account','account_project_rel','project_id','account_id',string="Related Accounts")
	budget_ids = fields.One2many('crossovered.budget','project_id',string="Budgets Related")

	check_project = fields.Boolean(string="Check Project",readony=True,compute='_check_project')

class Budget_Related(models.Model):

	_inherit = 'crossovered.budget'
	
	project_id = fields.Many2one('hr.contract.project.template',string="Project")
	activity_ids = fields.One2many('ngo.budget.activity','budget_id',string="Actitivies")
	
class NGO_Activity(models.Model):

	_name = 'ngo.budget.activity'
	
	name = fields.Char(string="Activity Name", required=True)
	budget_id = fields.Many2one('crossovered.budget',string="Budget")
	note = fields.Text(string="Description")
	move_line_ids = fields.One2many('account.move.line','activity_id',string="Move Lines")
	move_ids = fields.One2many('account.move','activity_id',string="Entries")
	
class Res_Users(models.Model):
	_inherit = 'res.users'
	
	allowed_project_ids = fields.Many2many('hr.contract.project.template','projects_and_users','user_ids','project_ids',string="Allowed Projects")
	