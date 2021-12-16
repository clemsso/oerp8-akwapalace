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
    'name': "Payroll Allowances Management",
    'author': 'Open IT World',
    'version': '0.1',
    'depends': ['hr','hr_contract','hr_payroll'],
    'category' : 'Human Resources',
    'summary': """Manage Allowances in Payroll""",
    'description': """
		This module helps to handle these functions:
			- Extra information - Cameroon
			- Allowances
			- Type of Allowances
			- Process inside Payslip
    """,
    'data': [
		'security/hr_payroll_security.xml',
		'security/ir.model.access.csv',
		'views/hr.xml',
		'views/allowance.xml',
		'views/allowance_data.xml',
		'views/deduction.xml',
		'views/dipe.xml',
		'views/hr_payroll.xml',
		'views/group_project.xml',
		'views/hr_data.xml',
#		'report/layout.xml',
#		'report/report_fee_receipt.xml',
		'report/report_view.xml',
		'report/report_dipe.xml',
		'report/report_pit_project.xml',
		'report/report_pit_project_history.xml',
		'report/report_employee_taxes.xml',
		'report/report_net_payment.xml',
		'report/report_net_payment_history.xml',
		'report/report_letter_payment_history.xml',
		'report/report_allowances.xml',
		'report/report_allowances_history.xml',
		'report/report_dipe_compare.xml',
		'report/report_project_compare.xml',
		'report/report_project_compare_history.xml',
		'report/report_payroll_compare.xml',
		'views/hr_dashboard.xml',
		'views/hr_dashboard_data.xml',
    ],
    'demo': [
#		'demo.xml',
	],
    'installable': True,
    'website': 'https://www.openitworld-cm.com',
    'application' : True,
}
