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

class Origin_Region(models.Model):

	_name = 'res.origin.region'

	name = fields.Char(string="Name",required=True)
	code = fields.Char(string="Code")
	country = fields.Many2one('res.country')
	division_ids = fields.One2many('res.origin.division','region_id',string="Divisions",readonly=True)

	_sql_constraints = [
		('unique_region_name',
		'UNIQUE(name)',
		"Name has to be unique !"),
		]
	
class Origin_Division(models.Model):

	_name = 'res.origin.division'

	name = fields.Char(string="Name",compute="_get_name",readonly=True,store=True)
	display_name = fields.Char("Name",required=True)
	code = fields.Char(string="Code")
	region_id = fields.Many2one('res.origin.region',string="Region")
	subdivision_ids = fields.One2many('res.origin.subdivision','division_id',string="Sub Divisions")
	
	@api.one
	@api.depends('display_name','region_id')
	def _get_name(self):
		if self.region_id and self.display_name:
			self.name = self.region_id.name + " / " + self.display_name
		else:
			self.name = ""
	
class Origin_SubDivision(models.Model):

	_name = 'res.origin.subdivision'

	name = fields.Char(string="Name",compute="_get_name",readonly=True,store=True)
	display_name = fields.Char("Name",required=True)
	code = fields.Char(string="Code")
	division_id = fields.Many2one('res.origin.division',string="Region")
	village_ids = fields.One2many('res.origin.village','subdivision_id',string="Villages")
	
	@api.one
	@api.depends('display_name','division_id')
	def _get_name(self):
		if self.division_id and self.display_name:
			self.name = self.division_id.name + " / " + self.display_name
		else:
			self.name = ""

class Origin_Village(models.Model):

	_name = 'res.origin.village'

	name = fields.Char(string="Name",compute="_get_name",readonly=True,store=True)
	display_name = fields.Char("Name",required=True)
	code = fields.Char(string="Code")
	subdivision_id = fields.Many2one('res.origin.subdivision',string="Region")
	
	@api.one
	@api.depends('display_name','subdivision_id')
	def _get_name(self):
		if self.subdivision_id and self.display_name:
			self.name = self.subdivision_id.name + " / " + self.display_name
		else:
			self.name = ""
