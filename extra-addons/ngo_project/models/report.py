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

from openerp.osv import osv
from openerp import api
from openerp.report import report_sxw

class budget_ytd_report(report_sxw.rml_parse):

	def __init__(self, cr, uid, name, context):
		super(budget_ytd_report,self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'get_category_period': self.get_category_period,
		})

	@api.multi
	def get_category_period(self, obj, period_id):
		
		res = [100]
		
		return res
		
#	def get_payslip_lines_code(self, obj,code):
#		payslip_line = self.pool.get('hr.payslip.line')
		
#		res = []
#		ids = []
#		for id in range(len(obj)):
#			if obj[id].appears_on_payslip is True and obj[id].code == code: 
#				ids.append(obj[id].id)
				
#		if ids:
#			res = payslip_line.browse(self.cr, self.uid, ids)
			
#		return res
		
#	def get_payslip_lines_allowance(self, obj, code):
#		payslip_line = self.pool.get('hr.payslip.line')
		
#		res = []
#		ids = []
#		for id in range(len(obj)):
#			if obj[id].appears_on_payslip is True and obj[id].salary_rule_id.category_id.code == code: 
#				ids.append(obj[id].id)
				
#		if ids:
#			res = payslip_line.browse(self.cr, self.uid, ids)
			
#		return res

#	def get_remain_lines(self, nbr):
		
#		res = []
#		n = 8 - nbr
		
#		if n > 0:
#			for i in range(n+1):
#				res.append(i)
			
#		return res
		
class wrapped_report_budget_ytd(osv.AbstractModel):
	_name = 'report.ngo_project.budget_ytd_template'
	_inherit = 'report.abstract_report'
	_template = 'ngo_project.budget_ytd_template'
	_wrapped_report_class = budget_ytd_report
	