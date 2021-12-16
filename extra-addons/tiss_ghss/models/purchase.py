# -*- coding: utf-8 -*-

from openerp import api, fields, models
import openerp.addons.decimal_precision as dp

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    project_id = fields.Many2one('hr.contract.project.template', 'Project/Contract',
                        required=True, track_visibility='onchange')


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    project_id = fields.Many2one('hr.contract.project.template', 'Project/Contract',
                        required=True, track_visibility='onchange')
