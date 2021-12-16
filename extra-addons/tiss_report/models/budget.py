# -*- encoding: utf-8 -*-
from openerp.tools import amount_to_text_en
from openerp import api, exceptions, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError

####################
#Spend Plan Budget##
####################
class BudgetSpendPlan(models.Model):
	_inherit = 'budget.spendplan'

	company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
	@api.multi
	def button_print_variance(self):
		if self.id:
			return self.env['report'].get_action(self,'tiss_report.report_spendPlan')
		else:
			raise Warning('Sorry there is no SpendPlan')