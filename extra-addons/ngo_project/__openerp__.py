# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2012 Tiny SPRL (<http://tiny.be>).
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

{
    'name': "Accounting Management by Project",
    'author': 'Open IT World',
    'version': '0.1',
    'depends': ['account','account_budget','ghss_hr_report'],
    'category' : 'NGO',
    'summary': """Manage Projects for an NGO Company""",
    'description': """
		This module helps to handle these functions:
			- Create, Modify adjust information inside project
			- Assign some basic function to a project
    """,
    'data': [
		# 'security/ngo_project_security.xml',
		'security/ir.model.access.csv',
		'views/ngo_project.xml',
		'views/account.xml',
		'views/budget.xml',
		'views/account_wizard.xml',
		'report/report_view.xml',
		'report/report_budget_detail.xml',
		'report/report_budget_ytd.xml',
		'report/report_budget_ytd_cfa.xml',
#		'report/layout.xml',
#		'report/report_fee_receipt.xml',
    ],
    'demo': [
#		'demo.xml',
	],
    'installable': True,
    'website': 'https://www.openitworld-cm.com',
    'application' : True,
}
