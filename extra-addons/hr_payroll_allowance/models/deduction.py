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

class Company_Extra_SSNID(models.Model):

	_inherit = 'res.company'
	
	ipa = fields.Selection([('group_a','Group A'),('group_b','Group B'),('group_c','Group C')],string="Ind. Group Accident",default='group_a')
	cnps_employee = fields.Float(string="CNPS Percentage - Employee",default=4.2)
	cnps_employer = fields.Float(string="CNPS Percentage - Employer",default=4.2)
	cfc = fields.Float(string="CFC percentage",default=1.5)
	fne = fields.Float(string="FNE(NEF) percentage",default=1)
	familly_contributory = fields.Float(string="Familly Contributory",default=7)
	lbr = fields.Float(string="Land Bank Rate", default=1)