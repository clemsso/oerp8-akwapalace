# -*- coding: utf-8 -*-
{
    "name": "Gestion de GHSS en multi projet",
    "author": "TCHAMTCHEU Clement",
    "version": "8.0.1.1.0",
    "category": "Purchase Management",
    "depends": [
        "hr_security",
        "purchase",
        "product",
        "account_budget",
        "sale",
        "ngo_project",
        "hr_payroll",
    ],
    "data": [
        "security/purchase_request.xml",
        "security/ir.model.access.csv",
        "data/purchase_request_sequence.xml",
        "data/purchase_request_data.xml",
        "views/account_view.xml",
        "views/purchase_request_view.xml",
        #"views/views.xml",
        # "views/purchase_order_line_view.xml",
        "views/petty_cash_views.xml",
        "views/petty_cash_voucher_views.xml",
        "views/cash_receipt_acknowledge_views.xml",
        "views/account_bank_transfert_view.xml",
        "views/hr_payroll_view.xml",
        "views/budget.xml",
        "reports/report_purchaserequests.xml",
        "views/purchase_request_report.xml",
        "views/cheque_request_form_views.xml",
        "views/payment_voucher_views.xml",
        "views/hr_contract_view.xml",
		"views/bank_reconciliation_views.xml",
        "wizards/desable_account.xml",
    ],
    'demo': [],
    "license": 'AGPL-3',
    "installable": True
}
