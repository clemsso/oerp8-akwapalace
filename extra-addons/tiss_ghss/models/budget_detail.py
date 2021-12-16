# -*- coding: utf-8 -*-
# Copyright 2020 OpenSynergy Indonesia
# Copyright 2020 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class BudgetDetail(models.Model):
    _name = "budget.detail"
    _description = "Budget Detail"

    @api.depends(
        "amount_unit",
        "quantity",
    )
    @api.multi
    def _compute_amount_subtotal(self):
        for document in self:
            document.amount_subtotal = document.amount_unit * \
                document.quantity

    @api.depends(
        "product_id"
    )
    @api.multi
    def _compute_allowed_uom_ids(self):
        obj_uom = self.env["product.uom"]
        for document in self:
            result = []
            if document.product_id:
                uom_categ = document.product_id.uom_id.category_id
                criteria = [
                    ("category_id", "=", uom_categ.id)
                ]
                result = obj_uom.search(criteria).ids
            document.allowed_uom_ids = result

    budget_id = fields.Many2one(
        string="# Budget",
        comodel_name="budget.budget",
        required=True,
        ondelete="cascade",
    )
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    account_id = fields.Many2one(
        string="Account",
        comodel_name="account.account",
        required=True,
    )
    amount_unit = fields.Float(
        string="Amount Per Unit",
        required=True,
        default=0.0,
    )
    quantity = fields.Float(
        string="Qty.",
        required=True,
        default=1.0,
    )
    allowed_uom_ids = fields.Many2many(
        string="Allowed UoMs",
        comodel_name="product.uom",
        compute="_compute_allowed_uom_ids",
        store=False,
    )
    uom_id = fields.Many2one(
        string="UoM",
        comodel_name="product.uom",
    )
    amount_subtotal = fields.Float(
        string="Amount Subtotal",
        compute="_compute_amount_subtotal",
        store=True,
    )

    @api.onchange(
        "product_id",
    )
    def onchange_name(self):
        self.name = ""
        if self.product_id:
            self.name = self.product_id.name

    @api.onchange(
        "product_id",
    )
    def onchange_uom_id(self):
        self.uom_id = False
