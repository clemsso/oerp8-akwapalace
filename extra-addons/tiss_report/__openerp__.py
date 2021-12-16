{
    "name": "GHSS Report Customise By TISS",
    "version": "8.0",
    "author": "tiss",
    "website": "",    
    "category": "Report",
    'description': """
		This module to customize by TISS for GHSS reporting:
			- Header
			- Footer
			- Spend Plan
    """,
    "sequence": 1,
    "depends": ["base", "tiss_ghss", "ghss_hr_report", "ghss_account"],    
    "data": [
		"report/report_call.xml",
        "views/header.xml",
        "views/footer.xml",
        "views/report_spendPlan.xml",
		"views/report_budgetghss.xml",
        "views/cash_recept_view.xml",

        #"report/cheque_request.xml",		
        #"report/report_cash_recept.xml",
        #"views/report_journal_ref.xml",
        #"report/journal_ref_view.xml",
        #"report/travel_request_view.xml",
        #"views/report_travel_request.xml",
        #'views/spendPlan.xml',
    ],
    "installable": True,
    "auto_install": False,
    "application": True,
}


