# -*- encoding: utf-8 -*-
from openerp.tools import amount_to_text_en
from openerp import api, exceptions, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp.exceptions import Warning, ValidationError

V_STATE = [
    ('draft', 'Draft'),
    ('upload', 'Upload'),
    ('send', 'Send By Mail'),
    ('valid', 'Validate'),
    ('cancel', 'Cancelled')
]

class CrossoveredBudgetLines(models.Model):
	_inherit = 'crossovered.budget.lines'

	crossovered_budget_detail_ids = fields.One2many('crossovered.budget.detail', 'crossovered_budget_line_id', 'Budget Details')    
	category_type = fields.Selection([('personnel','Personnel'),('fringe','Fringe'),('supplier','Supplier'),
                                       ('travel','Travel'),('other','Others')],string='Category Type')
	crossovered_budget_personnel_ids = fields.One2many('crossovered.budget.personnel', 'crossovered_budget_line_id', 'Budget Personnel Cost')    
	crossovered_budget_fringe_ids = fields.One2many('crossovered.budget.fringe', 'crossovered_budget_line_id', 'Budget Fringe Benefit')
	crossovered_budget_travel_ids = fields.One2many('crossovered.budget.travel', 'crossovered_budget_line_id', 'Budget Travel Benefit')
	crossovered_budget_other_ids = fields.One2many('crossovered.budget.other', 'crossovered_budget_line_id', 'Budget Other Benefit')
	crossovered_budget_consultancy_ids = fields.One2many('crossovered.budget.consultancy', 'crossovered_budget_line_id', 'Budget Consultancy')
	crossovered_budget_indcost_ids = fields.One2many('crossovered.budget.indcost', 'crossovered_budget_line_id', 'Budget Indirect Cost')
	note = fields.Text(string='Description', help="This, is for more description of activity")
        
class CrossoveredBudgetDetail(models.Model):
    _name = "crossovered.budget.detail"
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

    crossovered_budget_line_id = fields.Many2one(
        string="# Budget Line",
        comodel_name="crossovered.budget.lines",
        required=True,
        ondelete="cascade",
    )
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_line_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_line_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    amount_unit = fields.Float(
        string="Amount Per Unit",
        required=True,
        default=1.0,
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
   
####################
#Personnel Cost ####
####################
class CrossoveredBudgetPersonnel(models.Model):
    _name = "crossovered.budget.personnel"
    _description = "Budget Personnel"
    _rec_name="job_id"

    @api.depends(
        "basic_salary_effort",
        "duration",
    )
    @api.multi
    def _compute_amount_subtotal(self):
        for document in self:
            document.annual_pay = document.basic_salary_effort * \
                document.duration

    @api.depends(
        "basic_salary",
        "percentage_effort",
    )
    @api.multi
    def _compute_basic_salary_effort(self):
        for document in self:
            document.basic_salary_effort = document.basic_salary/100.0 * \
                document.percentage_effort

    crossovered_budget_line_id = fields.Many2one(
        string="# Budget Line",
        comodel_name="crossovered.budget.lines",
        required=True,
        ondelete="cascade",
    )
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_line_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_line_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )
    prefix = fields.Selection([('dr','Dr'),('mrs','Mrs'),('mr','Mr'),('mme','Mme'),('tbh','TBH')],
        string="Prefix",
        required=False,
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        required=False,
    )
    job_id = fields.Many2one(
        string="Project Role",
        comodel_name="hr.job",
        required=True,
    )
    basic_salary = fields.Float(
        string="Basic Salary",
        required=True,
        default=0.0,
    )
    percentage_effort = fields.Integer(
        string="% Efforts",
        required=True,
        default=100,
    )
    basic_salary_effort = fields.Float(
        string="Basic Salary/ %Efforts",
        compute="_compute_basic_salary_effort",
        store=True,
    )
    duration = fields.Integer(
        string="Duration",
        required=True,
        default=12,
    )
    annual_pay = fields.Float(
        string="Annual Pay/Requested pay",
        compute="_compute_amount_subtotal",
        store=True,
    )

####################
#Fringe         ####
####################
class CrossoveredBudgetFringe(models.Model):
    _name = "crossovered.budget.fringe"
    _description = "Budget Fringe"

    @api.depends(
        "basic_salary_effort",
        "duration",
        "percentage_effort",
    )
    @api.multi
    def _compute_amount_subtotal(self):
        for document in self:
            document.annual_pay = document.basic_salary_effort * \
                document.duration * document.percentage_effort

    crossovered_budget_line_id = fields.Many2one(
        string="# Budget Line",
        comodel_name="crossovered.budget.lines",
        required=True,
        ondelete="cascade",
    )
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_line_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_line_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    percentage_effort = fields.Integer(
        string="% Efforts",
        required=True,
        default=100,
    )
    basic_salary_effort = fields.Float(
        string="Basic Salary/ %Efforts",
        required=True,
        default=1,
    )
    duration = fields.Float(
        string="Duration",
        required=True,
        default=1,
    )
    annual_pay = fields.Float(
        string="Annual Pay/Requested pay",
        compute="_compute_amount_subtotal",
        store=True,
    )

    @api.onchange(
        "product_id",
    )
    def onchange_product_id(self):
        self.name = self.product_id.name

####################
#Travel         ####
####################
class CrossoveredBudgetTravel(models.Model):
    _name = "crossovered.budget.travel"
    _description = "Budget Travel"

    @api.depends(
        "no_trips",
        "no_days",
        "no_person",
        "unit_price",
    )
    @api.multi
    def _compute_total_price(self):
        for document in self:
            document.total_price = document.no_trips * \
                document.no_days * document.unit_price \
                * document.no_person

    crossovered_budget_line_id = fields.Many2one(
        string="# Budget Line",
        comodel_name="crossovered.budget.lines",
        required=True,
        ondelete="cascade",
    )
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_line_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_line_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    no_trips = fields.Integer(
        string="No Trips",
        required=True,
        default=100,
    )
    no_days = fields.Integer(
        string="No of Days",
        required=True,
        default=1,
    )
    no_person = fields.Integer(
        string="No of pers",
        required=True,
        default=1,
    )
    unit_price = fields.Float(
        string="Unit Price",
        required=True,
    )
    total_price = fields.Float(
        string="Total Price",
        compute="_compute_total_price",
        store=True,
    )
    @api.onchange(
        "product_id",
    )
    def onchange_product_id(self):
        self.name = self.product_id.name
####################
#Others         ####
####################
class CrossoveredBudgetOther(models.Model):
    _name = "crossovered.budget.other"
    _description = "Budget Other"

    @api.depends(
        "no_trips",
        "no_days",
        "no_person",
        "unit_price",
    )
    @api.multi
    def _compute_total_price(self):
        for document in self:
            document.total_price = document.no_trips * \
                document.no_days * document.unit_price * \
                document.no_person

    crossovered_budget_line_id = fields.Many2one(
        string="# Budget Line",
        comodel_name="crossovered.budget.lines",
        required=True,
        ondelete="cascade",
    )
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_line_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_line_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    no_trips = fields.Integer(
        string="No Of Trips",
        required=True,
        default=100,
    )
    no_days = fields.Integer(
        string="No of Days",
        required=True,
        default=1,
    )
    no_person = fields.Integer(
        string="No of Pers/Qty",
        required=True,
        default=1,
    )
    quantity = fields.Integer(
        string="Quantity",
        required=True,
        default=1,
    )
    unit_price = fields.Float(
        string="Unit Price",
        required=True,
    )
    total_price = fields.Float(
        string="Total Cost",
        compute="_compute_total_price",
        store=True,
    ) 
    @api.onchange(
        "product_id",
    )
    def onchange_product_id(self):
        self.name = self.product_id.name    


####################
#Consultancy    ####
####################
class CrossoveredBudgetConsultancy(models.Model):
    _name = "crossovered.budget.consultancy"
    _description = "Budget Consultancy"

    # @api.depends(
        # "quantity",
        # "nber_person",
        # "unit_price",
    # )
    # @api.multi
    # def _compute_total_price(self):
        # for document in self:
            # document.total_price = document.quantity * \
                # document.nber_person * document.unit_price

    crossovered_budget_line_id = fields.Many2one(
        string="# Budget Line",
        comodel_name="crossovered.budget.lines",
        required=True,
        ondelete="cascade",
    )
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_line_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_line_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )

    price = fields.Float(
        string="Price",
        required=True,
    )
    
    quantity = fields.Float(
        string="Quantity",
        required=True,
        default = 1,
    )
    
    # total_price = fields.Float(
        # string="Total",
        # compute="_compute_total_price",
        # store=True,
    # ) 
    
    nber_person = fields.Integer(
        string="Number Person",
        required=True,
        default=1
    )

    @api.onchange(
        "product_id",
    )
    def onchange_product_id(self):
        self.name = self.product_id.name 


####################
#Indirect Cost  ####
####################
class CrossoveredBudgetIndCost(models.Model):
    _name = "crossovered.budget.indcost"
    _description = "Budget Indirect Cost"

    # @api.depends(
        # "no_trips",
        # "no_days",
        # "no_person",
        # "unit_price",
    # )
    # @api.multi
    # def _compute_total_price(self):
        # for document in self:
            # document.total_price = document.no_trips * \
                # document.no_days * document.unit_price * \
                # document.no_person

    crossovered_budget_line_id = fields.Many2one(
        string="# Budget Line",
        comodel_name="crossovered.budget.lines",
        required=True,
        ondelete="cascade",
    )
    # analytic_account_id = fields.Many2one('account.analytic.account', 
        # related='crossovered_budget_line_id.analytic_account_id', 
        # string='Account Analytic', store=True, readonly=True,
    # )
    # general_budget_id = fields.Many2one('account.budget.post', 
        # related='crossovered_budget_line_id.general_budget_id', 
        # string='Activity', store=True, readonly=True,
    # )
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )

    price = fields.Float(
        string="Price",
        required=True,
    )

    @api.onchange(
        "product_id",
    )
    def onchange_product_id(self):
        self.name = self.product_id.name 

####################
#Spend Plan Budget##
####################
class BudgetSpendPlan(models.Model):
	_name = 'budget.spendplan'
	_description = 'This is for making the spend plan for activities'
	
	@api.model
	def _get_default_user_id(self):
		return self.env['res.users'].browse(self.env.uid)
    
	@api.depends(
        "spendplan_supplier_activities_ids.planned_amt",
        "spendplan_supplier_activities_ids.consummed_amt"
    )
	@api.multi
	def _supplier_plan_amt(self):
		for s in self:
			montant=mt=0.0
			for line in s.spendplan_supplier_activities_ids:
				montant += line.planned_amt
				mt+= line.consummed_amt
			s.update({
				'supplier_plan_amt':montant,
                'supplier_consu_amt':mt,
            })

	@api.depends(
        "spendplan_personnel_activities_ids.planned_amt",
        "spendplan_personnel_activities_ids.consummed_amt"
    )
	@api.multi
	def _personnel_plan_amt(self):
		for s in self:
			montant=mt=0.0
			for line in s.spendplan_personnel_activities_ids:
				montant += line.planned_amt
				mt+= line.consummed_amt
			s.update({
				'personnel_plan_amt':montant,
                'personnel_consu_amt':mt,
            })
	@api.depends(
        "spendplan_fringe_activities_ids.planned_amt",
        "spendplan_fringe_activities_ids.consummed_amt"
    )
	@api.multi
	def _fringe_plan_amt(self):
		for s in self:
			montant=mt=0.0
			for line in s.spendplan_fringe_activities_ids:
				montant += line.planned_amt
				mt+= line.consummed_amt
			s.update({
				'fringe_plan_amt':montant,
                'fringe_consu_amt':mt,
            })
	@api.depends(
        "spendplan_travel_activities_ids.planned_amt",
        "spendplan_travel_activities_ids.consummed_amt"
    )
	@api.multi
	def _travel_plan_amt(self):
		for s in self:
			montant=mt=0.0
			for line in s.spendplan_travel_activities_ids:
				montant += line.planned_amt
				mt+= line.consummed_amt
			s.update({
				'travel_plan_amt':montant,
                'travel_consu_amt':mt,
            })
	@api.depends(
        "spendplan_other_activities_ids.planned_amt",
        "spendplan_other_activities_ids.consummed_amt"
    )
	@api.multi
	def _others_plan_amt(self):
		for s in self:
			montant=mt=0.0
			for line in s.spendplan_other_activities_ids:
				montant += line.planned_amt
				mt+= line.consummed_amt
			s.update({
				'others_plan_amt':montant,
                'others_consu_amt':mt,
            })
	@api.depends(
        "spendplan_consultancy_activities_ids.planned_amt",
        "spendplan_consultancy_activities_ids.consummed_amt"
    )
	@api.multi
	def _consul_plan_amt(self):
		for s in self:
			montant=mt=0.0
			for line in s.spendplan_consultancy_activities_ids:
				montant += line.planned_amt
				mt+= line.consummed_amt
			s.update({
				'consul_plan_amt':montant,
                'consul_consu_amt':mt,
            })		

	name = fields.Char(string="Name", required=True)
	budget_id = fields.Many2one('crossovered.budget',string="Budget Related")
	date_start = fields.Date(string="Start Date")
	date_end = fields.Date(string="End Date")
	state = fields.Selection(selection=V_STATE, default='draft')
	user_id = fields.Many2one('res.users', required=True, default=_get_default_user_id, string="Responsible", readonly=False)
	b_validate = fields.Boolean(string='Validate ?')
	company = fields.Many2one(
        'res.company',
        default=lambda self:
        self.env['res.company']._company_default_get('budget.spendplan'))
	currency_amount = fields.Float(string="Conversion Rate ($)")
	spendplan_supplier_activities_ids = fields.One2many('spendplan.supplier.activities', 'spendplan_id', 'Budget Details')    
	supplier_plan_amt = fields.Float(compute='_supplier_plan_amt', string='Sup. Plan. Amt')
	supplier_consu_amt = fields.Float(compute='_supplier_plan_amt', string='Cons. Plan. Amt')	
	
	spendplan_personnel_activities_ids = fields.One2many('spendplan.personnel.activities', 'spendplan_id', 'Budget Personnel Cost')    
	personnel_plan_amt = fields.Float(compute='_personnel_plan_amt', string='Pers. Plan. Amt')
	personnel_consu_amt = fields.Float(compute='_personnel_plan_amt', string='Pers. Cons. Amt')	
		
	spendplan_fringe_activities_ids = fields.One2many('spendplan.fringe.activities', 'spendplan_id', 'Budget Fringe Benefit')
	fringe_plan_amt = fields.Float(compute='_fringe_plan_amt', string='fringe Plan. Amt')
	fringe_consu_amt = fields.Float(compute='_fringe_plan_amt', string='fringe Cons. Amt')	
		
	spendplan_travel_activities_ids = fields.One2many('spendplan.travel.activities', 'spendplan_id', 'Budget Travel Benefit')
	travel_plan_amt = fields.Float(compute='_travel_plan_amt', string='travel Plan. Amt')
	travel_consu_amt = fields.Float(compute='_travel_plan_amt', string='travel Cons. Amt')	
		
	spendplan_other_activities_ids = fields.One2many('spendplan.other.activities', 'spendplan_id', 'Budget Other Benefit')
	others_plan_amt = fields.Float(compute='_others_plan_amt', string='others Plan. Amt')
	others_consu_amt = fields.Float(compute='_others_plan_amt', string='others Cons. Amt')
	spendplan_consultancy_activities_ids = fields.One2many('spendplan.consultancy.activities', 'spendplan_id', 'Budget Consultancy')
	consul_plan_amt = fields.Float(compute='_consul_plan_amt', string='consul Plan. Amt')
	consul_consu_amt = fields.Float(compute='_consul_plan_amt', string='consul Cons. Amt')
	@api.multi
	def btn_send_by_mail(self):
		self.state='send'
	
	@api.multi
	def btn_validate(self):
		if self.currency_amount == 0.00:
			raise Warning('Please Insert the conversion rate!')
		self.state='valid'
		self.b_validate=True

	@api.multi
	def btn_delete(self):
	    for s in self.spendplan_supplier_activities_ids:
	        s.unlink()
	    for s in self.spendplan_personnel_activities_ids:
	        s.unlink()
	    for s in self.spendplan_fringe_activities_ids:
	        s.unlink()
	    for s in self.spendplan_travel_activities_ids:
	        s.unlink()
	    for s in self.spendplan_other_activities_ids:
	        s.unlink()
	    for s in self.spendplan_consultancy_activities_ids:
	        s.unlink()
	    self.state='draft'

	@api.multi
	def btn_upload(self):
	    BudgetObj = self.env['crossovered.budget']
	    SupplierActivityObj = self.env['spendplan.supplier.activities']
	    SupplierObj = self.env['spendplan.supplier']
	    PersonnelActivityObj = self.env['spendplan.personnel.activities']
	    PersonnelObj = self.env['spendplan.personnel']
	    FringeActivityObj = self.env['spendplan.fringe.activities']
	    FringeObj = self.env['spendplan.fringe']
	    TravelActivityObj = self.env['spendplan.travel.activities']
	    TravelObj = self.env['spendplan.travel']
	    OtherActivityObj = self.env['spendplan.other.activities']
	    OtherObj = self.env['spendplan.other']
	    ConsultancyActivityObj = self.env['spendplan.consultancy.activities']
	    ConsultancyObj = self.env['spendplan.consultancy']
	    for line in self.budget_id.crossovered_budget_line:
	        if line.category_type=='supplier':
	            val = {'budget_poste_id':line.general_budget_id.id, 'planned_amt':line.planned_amount, 'consummed_amt':0.00, 'spendplan_id':self.id}
	            supplier_activity_id = SupplierActivityObj.create(val)
	            for d in line.crossovered_budget_detail_ids:
	                val_line = {'product_id':d.product_id.id,
	                            'name':d.name,
	                            'amount_unit':d.amount_unit,
	                            'quantity':d.quantity,
	                            'uom_id':d.uom_id.id,
	                            'amount_subtotal':d.amount_subtotal,
                                'crossovered_budget_detail_id':d.id,
	                            'sp_supplier_id':supplier_activity_id.id}
	                supplier_id = SupplierObj.create(val_line)
	        if line.category_type=='personnel':
	            val = {'budget_poste_id':line.general_budget_id.id, 'planned_amt':line.planned_amount, 'consummed_amt':0.00, 'spendplan_id':self.id}
	            personnel_activity_id = PersonnelActivityObj.create(val)
	            for d in line.crossovered_budget_personnel_ids:
	                val_line = {'prefix':d.prefix,
	                            'employee_id':d.employee_id.id,
	                            'job_id':d.job_id.id,
	                            'basic_salary':d.basic_salary,
	                            'duration':d.duration,
	                            'percentage_effort':d.percentage_effort,
	                            'basic_salary_effort':d.basic_salary_effort,
                                'annual_pay':d.annual_pay,
                                'crossovered_budget_detail_id':d.id,
                                'sp_personnel_id':personnel_activity_id.id}
	                personnel_id = PersonnelObj.create(val_line)
	        if line.category_type=='fringe':
	            val = {'budget_poste_id':line.general_budget_id.id, 'planned_amt':line.planned_amount, 'consummed_amt':0.00, 'spendplan_id':self.id}
	            fringe_activity_id = FringeActivityObj.create(val)
	            for d in line.crossovered_budget_fringe_ids:
	                val_line = {'name':d.name,
	                            'product_id':d.product_id.id,
	                            'percentage_effort':d.percentage_effort,
	                            'duration':d.duration,
	                            'basic_salary_effort':d.basic_salary_effort,
	                            'annual_pay':d.annual_pay,
	                            'basic_salary_effort':d.basic_salary_effort,
                                'annual_pay':d.annual_pay,
                                'crossovered_budget_detail_id':d.id,
                                'sp_fringe_id':fringe_activity_id.id}
	                fringe_id = FringeObj.create(val_line)
	        if line.category_type=='travel':
	            val = {'budget_poste_id':line.general_budget_id.id, 'planned_amt':line.planned_amount, 'consummed_amt':0.00, 'spendplan_id':self.id}
	            travel_activity_id = TravelActivityObj.create(val)
	            for d in line.crossovered_budget_travel_ids:
	                val_line = {'name':d.name,
	                            'product_id':d.product_id.id,
	                            'no_trips':d.no_trips,
	                            'no_days':d.no_days,
	                            'no_person':d.no_person,
	                            'unit_price':d.unit_price,
	                            'total_price':d.total_price,
                                'crossovered_budget_detail_id':d.id,
                                'sp_travel_id':travel_activity_id.id}
	                travel_id = TravelObj.create(val_line)
	        if line.category_type=='other':
	            val = {'budget_poste_id':line.general_budget_id.id, 'planned_amt':line.planned_amount, 'consummed_amt':0.00, 'spendplan_id':self.id}
	            other_activity_id = OtherActivityObj.create(val)
	            for d in line.crossovered_budget_other_ids:
	                val_line = {'name':d.name,
	                            'no_trips':d.no_trips,
	                            'no_days':d.no_days,
	                            'no_person':d.no_person,
	                            'quantity':d.quantity,
	                            'unit_price':d.unit_price,
	                            'total_price':d.total_price,
                                'crossovered_budget_detail_id':d.id,
                                'sp_other_id':other_activity_id.id}
	                other_id = OtherObj.create(val_line)
	        if line.category_type=='consultancy':
	            val = {'budget_poste_id':line.general_budget_id.id, 'planned_amt':line.planned_amount, 'consummed_amt':0.00, 'spendplan_id':self.id}
	            consultancy_activity_id = ConsultancyActivityObj.create(val)
	            for d in line.crossovered_budget_other_ids:
	                val_line = {'name':d.name,
	                            'product_id':d.product_id,
	                            'price':d.price,
                                'crossovered_budget_detail_id':d.id,
                                'sp_consultancy_id':consultancy_activity_id.id}
	                consultancy_id = ConsultancyObj.create(val_line)
                    
	    self.write({'state': 'upload'})	     

class SpendplanSupplierActivities(models.Model):
    _name = "spendplan.supplier.activities"
    _description = "Spend plan Supplier activities"
    _rec_name = "budget_poste_id"

    @api.onchange('budget_poste_id')
    def onchange_budget_poste_id(self):
        if self.budget_poste_id:
            search_vals = [('crossovered_budget_id','=',self.spendplan_id.budget_id.id),
                           ('general_budget_id','=',self.budget_poste_id.id)]
            line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            self.planned_amt = line_id.planned_amount

    spendplan_id = fields.Many2one(
        string="# Spend Plan",
        comodel_name="budget.spendplan",
        required=True,
        ondelete="cascade",
    )
    budget_poste_id = fields.Many2one(
        string="Activity",
        comodel_name="account.budget.post",
    )
    planned_amt = fields.Float(string="Planned Amount", required=True)
    consummed_amt = fields.Float(string="Consummed Amount", compute="_compute_amt_requested",)
    requested_amt = fields.Float(string="Requested Amount", compute="_compute_amt_requested",)
    spendplan_supplier_ids = fields.One2many('spendplan.supplier', 'sp_supplier_id', 'Budget Details')

    @api.depends(
        "spendplan_supplier_ids.amount_subtotal",
        "spendplan_supplier_ids.consummed_amt"
    )
    @api.multi
    def _compute_amt_requested(self):
        for s in self:
            montant=mt=0.0
            for line in s.spendplan_supplier_ids:
                montant += line.amount_subtotal
                mt+= line.consummed_amt
            s.update({
                'requested_amt':montant,
                'consummed_amt':mt,
            })   

class SpendplanSupplier(models.Model):
    _name = "spendplan.supplier"
    _description = "Spend plan Supplier"

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

    @api.onchange('crossovered_budget_detail_id')
    def onchange_crossovered_budget_detail_id(self):
        if self.crossovered_budget_detail_id:
            self.name = self.crossovered_budget_detail_id.name
            self.product_id = self.crossovered_budget_detail_id.product_id.id
            self.amount_unit = self.crossovered_budget_detail_id.amount_unit
            self.quantity = self.crossovered_budget_detail_id.quantity
            self.amount_subtotal = self.crossovered_budget_detail_id.amount_subtotal

    sp_supplier_id = fields.Many2one(
        string="# Spend Plan Supplier Activity",
        comodel_name="spendplan.supplier.activities",
        required=True,
        ondelete="cascade",
    )
    crossovered_budget_detail_id = fields.Many2one(string="Details Budget", comodel_name="crossovered.budget.detail")
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_detail_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_detail_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    amount_unit = fields.Float(
        string="Amount Per Unit",
        required=True,
        default=0.0,
        store = True
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
    consummed_amt = fields.Float(string="Consummed Amount", required=False)

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
   
####################
#Personnel Cost ####
####################
class SpendplanPersonnelActivities(models.Model):
    _name = "spendplan.personnel.activities"
    _description = "Spend plan Personnel activities"

    @api.onchange('budget_poste_id')
    def onchange_budget_poste_id(self):
        if self.budget_poste_id:
            search_vals = [('crossovered_budget_id','=',self.spendplan_id.budget_id.id),
                           ('general_budget_id','=',self.budget_poste_id.id),('category_type','=','personnel')]
            line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            self.planned_amt = line_id.planned_amount

    spendplan_id = fields.Many2one(
        string="# Spend Plan",
        comodel_name="budget.spendplan",
        required=True,
        ondelete="cascade",
    )
    budget_poste_id = fields.Many2one(
        string="Activity",
        comodel_name="account.budget.post",
    )
    planned_amt = fields.Float(string="Planned Amount", required=True)
    consummed_amt = fields.Float(string="Consummed Amount", compute="_compute_amt_requested",)
    requested_amt = fields.Float(string="Requested Amount", compute="_compute_amt_requested",)
    spendplan_personnel_ids = fields.One2many('spendplan.personnel', 'sp_personnel_id', 'Budget Personnel Cost')    

    @api.depends(
        "spendplan_personnel_ids.annual_pay",
        "spendplan_personnel_ids.consummed_amt",
    )
    @api.multi
    def _compute_amt_requested(self):
        for s in self:
            montant=mt=0.0
            for line in s.spendplan_personnel_ids:
                montant += line.annual_pay
                mt += line.consummed_amt
            s.update({
                'requested_amt':montant,
                'consummed_amt':mt
            }) 

class SpendplanPersonnel(models.Model):
    _name = "spendplan.personnel"
    _description = "Budget Personnel"
    _rec_name="employee_id"

    @api.depends(
        "basic_salary",
        "duration",
    )
    @api.multi
    def _compute_amount_subtotal(self):
        for document in self:
            document.annual_pay = document.basic_salary * \
                document.duration

    @api.onchange('crossovered_budget_detail_id')
    def onchange_crossovered_budget_detail_id(self):
        if self.crossovered_budget_detail_id:
            self.prefix = self.crossovered_budget_detail_id.prefix
            self.employee_id = self.crossovered_budget_detail_id.employee_id.id
            self.job_id = self.crossovered_budget_detail_id.job_id.id
            self.basic_salary = self.crossovered_budget_detail_id.basic_salary
            self.percentage_effort = self.crossovered_budget_detail_id.percentage_effort
            self.basic_salary_effort = self.crossovered_budget_detail_id.basic_salary_effort
            self.duration = self.crossovered_budget_detail_id.duration
            self.annual_pay = self.crossovered_budget_detail_id.annual_pay

    sp_personnel_id = fields.Many2one(
        string="# Spend Plan Personnel Activity",
        comodel_name="spendplan.personnel.activities",
        required=True,
        ondelete="cascade",
    )
    crossovered_budget_detail_id = fields.Many2one(string="Details Budget", comodel_name="crossovered.budget.personnel")
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_detail_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_detail_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )
    prefix = fields.Selection([('dr','Dr'),('mrs','Mrs'),('mr','Mr'),('mme','Mme'),('tbh','TBH')],
        string="Prefix",
        required=False,
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        required=True,
    )
    job_id = fields.Many2one(
        string="Project Role",
        comodel_name="hr.job",
        required=True,
    )
    basic_salary = fields.Float(
        string="Basic Salary",
        required=True,
        default=0.0,
    )
    percentage_effort = fields.Integer(
        string="% Efforts",
        required=True,
        default=100,
    )
    basic_salary_effort = fields.Integer(
        string="Basic Salary/ %Efforts",
        required=True,
        default=100,
    )
    duration = fields.Integer(
        string="Duration",
        required=True,
        default=12,
    )
    annual_pay = fields.Float(
        string="Annual Pay/Requested pay",
        compute="_compute_amount_subtotal",
        store=True,
    )
    consummed_amt = fields.Float(string="Consummed Amount", required=False)

# ####################
# #Fringe         ####
# ####################
class SpendplanFringeActivities(models.Model):
    _name = "spendplan.fringe.activities"
    _description = "Spend plan fringe activities"

    @api.onchange('budget_poste_id')
    def onchange_budget_poste_id(self):
        if self.budget_poste_id:
            search_vals = [('crossovered_budget_id','=',self.spendplan_id.budget_id.id),
                           ('general_budget_id','=',self.budget_poste_id.id),('category_type','=','fringe')]
            line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            self.planned_amt = line_id.planned_amount

    spendplan_id = fields.Many2one(
        string="# Spend Plan",
        comodel_name="budget.spendplan",
        required=True,
        ondelete="cascade",
    )
    budget_poste_id = fields.Many2one(
        string="Activity",
        comodel_name="account.budget.post",
    )
    planned_amt = fields.Float(string="Planned Amount", required=True)
    consummed_amt = fields.Float(string="Consummed Amount", compute="_compute_amt_requested",)
    requested_amt = fields.Float(string="Requested Amount", compute="_compute_amt_requested",)
    spendplan_fringe_ids = fields.One2many('spendplan.fringe', 'sp_fringe_id', 'Budget Fringe Benefit')

    @api.depends(
        "spendplan_fringe_ids.annual_pay",
        "spendplan_fringe_ids.consummed_amt",
    )
    @api.multi
    def _compute_amt_requested(self):
        for s in self:
            montant=mt=0.0
            for line in s.spendplan_fringe_ids:
                montant += line.annual_pay
                mt += line.consummed_amt
            s.update({
                'requested_amt':montant,
                'consummed_amt':mt
            }) 

class SpendplanFringe(models.Model):
    _name = "spendplan.fringe"
    _description = "SpendPlan Fringe"

    @api.depends(
        "basic_salary_effort",
        "duration",
    )
    @api.multi
    def _compute_amount_subtotal(self):
        for document in self:
            document.annual_pay = document.basic_salary_effort * \
                document.duration * document.percentage_effort

    @api.onchange('crossovered_budget_detail_id')
    def onchange_crossovered_budget_detail_id(self):
        if self.crossovered_budget_detail_id:
            self.name = self.crossovered_budget_detail_id.name
            self.product_id = self.crossovered_budget_detail_id.product_id.id
            #self.job_id = self.crossovered_budget_detail_id.job_id.id
            #self.percentage_effort = self.crossovered_budget_detail_id.percentage_effort
            self.percentage_effort = self.crossovered_budget_detail_id.percentage_effort
            self.basic_salary_effort = self.crossovered_budget_detail_id.basic_salary_effort
            self.duration = self.crossovered_budget_detail_id.duration
            self.annual_pay = self.crossovered_budget_detail_id.annual_pay

    sp_fringe_id = fields.Many2one(
        string="# Spend Plan Fringe Activity",
        comodel_name="spendplan.fringe.activities",
        required=True,
        ondelete="cascade",
    )
    crossovered_budget_detail_id = fields.Many2one(string="Details Budget", comodel_name="crossovered.budget.fringe")
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_detail_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_detail_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    percentage_effort = fields.Integer(
        string="% Efforts",
        required=True,
        default=100,
    )
    basic_salary_effort = fields.Float(
        string="Basic Salary/ %Efforts",
        required=True,
        default=1,
    )
    duration = fields.Float(
        string="Duration",
        required=True,
        default=1,
    )
    annual_pay = fields.Float(
        string="Annual Pay/Requested pay",
        compute="_compute_amount_subtotal",
        store=True,
    )
    consummed_amt = fields.Float(string="Consummed Amount", required=False)

# ####################
# #Travel         ####
# ####################
class SpendplanTravelActivities(models.Model):
    _name = "spendplan.travel.activities"
    _description = "Spend plan Travel activities"

    @api.onchange('budget_poste_id')
    def onchange_budget_poste_id(self):
        if self.budget_poste_id:
            search_vals = [('crossovered_budget_id','=',self.spendplan_id.budget_id.id),
                           ('general_budget_id','=',self.budget_poste_id.id),('category_type','=','travel')]
            line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            self.planned_amt = line_id.planned_amount

    spendplan_id = fields.Many2one(
        string="# Spend Plan",
        comodel_name="budget.spendplan",
        required=True,
        ondelete="cascade",
    )
    budget_poste_id = fields.Many2one(
        string="Activity",
        comodel_name="account.budget.post",
    )
    planned_amt = fields.Float(string="Planned Amount", required=True)
    consummed_amt = fields.Float(string="Consummed Amount", compute="_compute_amt_requested")
    requested_amt = fields.Float(string="Requested Amount", compute="_compute_amt_requested",)
    spendplan_travel_ids = fields.One2many('spendplan.travel', 'sp_travel_id', 'Budget Travel Benefit')

    @api.depends(
        "spendplan_travel_ids.total_price",
        "spendplan_travel_ids.consummed_amt",
    )
    @api.multi
    def _compute_amt_requested(self):
        for s in self:
            montant=mt=0.0
            for line in s.spendplan_travel_ids:
                montant += line.total_price
                mt += line.consummed_amt
            s.update({
                'requested_amt':montant,
                'consummed_amt':mt
            }) 

class SpendplanTravel(models.Model):
    _name = "spendplan.travel"
    _description = "spendplan Travel"

    @api.depends(
        "no_trips",
        "no_days",
        "unit_price",
    )
    @api.multi
    def _compute_total_price(self):
        for document in self:
            document.total_price = document.no_trips * \
                document.no_days * document.unit_price * document.no_person

    @api.onchange('crossovered_budget_detail_id')
    def onchange_crossovered_budget_detail_id(self):
        if self.crossovered_budget_detail_id:
            self.name = self.crossovered_budget_detail_id.name
            self.product_id = self.crossovered_budget_detail_id.product_id.id
            #self.job_id = self.crossovered_budget_detail_id.job_id.id
            #self.percentage_effort = self.crossovered_budget_detail_id.percentage_effort
            self.no_trips = self.crossovered_budget_detail_id.no_trips
            self.no_days = self.crossovered_budget_detail_id.no_days
            self.no_person = self.crossovered_budget_detail_id.no_person
            self.unit_price = self.crossovered_budget_detail_id.unit_price
            self.total_price = self.crossovered_budget_detail_id.total_price

    sp_travel_id = fields.Many2one(
        string="# spendplan Travel activity",
        comodel_name="spendplan.travel.activities",
        required=True,
        ondelete="cascade",
    )
    crossovered_budget_detail_id = fields.Many2one(string="Details Budget", comodel_name="crossovered.budget.travel")
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_detail_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_detail_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )    
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    no_trips = fields.Integer(
        string="No Trips",
        required=True,
        default=100,
    )
    no_days = fields.Integer(
        string="No of Days",
        required=True,
        default=1,
    )
    no_person = fields.Integer(
        string="No of pers",
        required=True,
        default=1,
    )
    unit_price = fields.Float(
        string="Unit Price",
        required=True,
    )
    total_price = fields.Float(
        string="Total Price",
        compute="_compute_total_price",
        store=True,
    )
    consummed_amt = fields.Float(string="Consummed Amount", required=False)
    
# ####################
# #Others         ####
# ####################
class SpendplanOtherActivities(models.Model):
    _name = "spendplan.other.activities"
    _description = "Spend plan Other activities"
    _rec_name = "budget_poste_id"

    @api.onchange('budget_poste_id')
    def onchange_budget_poste_id(self):
        if self.budget_poste_id:
            search_vals = [('crossovered_budget_id','=',self.spendplan_id.budget_id.id),
                           ('general_budget_id','=',self.budget_poste_id.id),('category_type','=','other')]
            line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            self.planned_amt = line_id.planned_amount

    spendplan_id = fields.Many2one(
        string="# Spend Plan",
        comodel_name="budget.spendplan",
        required=True,
        ondelete="cascade",
    )
    budget_poste_id = fields.Many2one(
        string="Activity",
        comodel_name="account.budget.post",
    )
    planned_amt = fields.Float(string="Planned Amount", required=True)
    consummed_amt = fields.Float(string="Consummed Amount", compute="_compute_amt_requested",)
    requested_amt = fields.Float(string="Requested Amount", compute="_compute_amt_requested",)
    spendplan_other_ids = fields.One2many('spendplan.other', 'sp_other_id', 'Budget Other Benefit')

    @api.depends(
        "spendplan_other_ids.total_price",
        "spendplan_other_ids.consummed_amt",
    )
    @api.multi
    def _compute_amt_requested(self):
        for s in self:
            montant=mt=0.0
            for line in s.spendplan_other_ids:
                montant += line.total_price
                mt += line.consummed_amt
            s.update({
                'requested_amt':montant,
                'consummed_amt':mt
            })

class SpendPlanOther(models.Model):
    _name = "spendplan.other"
    _description = "Budget Other"

    @api.multi
    def write(self, vals):
        if 'no_trips' in vals:
            if  vals['no_trips']>self.crossovered_budget_detail_id.no_trips :
                raise ValidationError('Please that value is greater than the one budgeted')
        return super(SpendPlanOther, self).write(vals)

    @api.depends(
        "no_trips",
        "no_days",
        "no_person",
        "unit_price",
    )
    @api.multi
    def _compute_total_price(self):
        for document in self:
            document.total_price = document.no_trips * \
                document.no_days * document.unit_price * \
                document.no_person
    # @api.onchange(
    #     "no_trips",
    # )  
    # def onchange_no_trips(self):
    #     if self.no_trips:
    #         if self.no_trips >= self.crossovered_budget_detail_id.no_trips:
    #             raise ValidationError('Please that value is greater than the one budgeted')

    @api.onchange('crossovered_budget_detail_id')
    def onchange_crossovered_budget_detail_id(self):
        if self.crossovered_budget_detail_id:
            self.name = self.crossovered_budget_detail_id.name
            self.product_id = self.crossovered_budget_detail_id.product_id.id
            #self.job_id = self.crossovered_budget_detail_id.job_id.id
            self.quantity = self.crossovered_budget_detail_id.quantity
            self.no_trips = self.crossovered_budget_detail_id.no_trips
            self.no_days = self.crossovered_budget_detail_id.no_days
            self.no_person = self.crossovered_budget_detail_id.no_person
            self.unit_price = self.crossovered_budget_detail_id.unit_price
            self.total_price = self.crossovered_budget_detail_id.total_price

    sp_other_id = fields.Many2one(
        string="# Spend Plan Other",
        comodel_name="spendplan.other.activities",
        required=True,
        ondelete="cascade",
    )
    crossovered_budget_detail_id = fields.Many2one(string="Details Budget", comodel_name="crossovered.budget.other")
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_detail_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_detail_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    no_trips = fields.Integer(string="No Of Trips", required=True, default=100,)
    no_days = fields.Integer(
        string="No of Days",
        required=True,
        default=1,
    )
    no_person = fields.Integer(
        string="No of Pers/Qty",
        required=True,
        default=1,
    )
    quantity = fields.Integer(
        string="Quantity",
        required=True,
        default=1,
    )
    unit_price = fields.Float(
        string="Unit Price",
        required=True,
    )
    total_price = fields.Float(
        string="Total Cost",
        compute="_compute_total_price",
        store=True,
    )
    consummed_amt = fields.Float(string="Consummed Amount", required=False)
    
    @api.onchange(
        "product_id",
    )
    def onchange_product_id(self):
        self.name = self.product_id.name
        
##################
##SP CONSULTANCY##
##################
class SpendplanConsultancyActivities(models.Model):
    _name = "spendplan.consultancy.activities"
    _description = "Spend plan Consultancy activities"

    @api.onchange('budget_poste_id')
    def onchange_budget_poste_id(self):
        if self.budget_poste_id:
            search_vals = [('crossovered_budget_id','=',self.spendplan_id.budget_id.id),
                           ('general_budget_id','=',self.budget_poste_id.id)]
            line_id = self.env['crossovered.budget.lines'].search(search_vals, limit=1)
            self.planned_amt = line_id.planned_amount

    spendplan_id = fields.Many2one(
        string="# Spend Plan",
        comodel_name="budget.spendplan",
        required=True,
        ondelete="cascade",
    )
    budget_poste_id = fields.Many2one(
        string="Activity",
        comodel_name="account.budget.post",
    )
    planned_amt = fields.Float(string="Planned Amount", required=True)
    consummed_amt = fields.Float(string="Consummed Amount", compute="_compute_amt_requested",)
    requested_amt = fields.Float(string="Requested Amount", compute="_compute_amt_requested",)
    spendplan_consultancy_ids = fields.One2many('spendplan.consultancy', 'sp_consultancy_id', 'Budget Details')

    @api.depends(
        "spendplan_consultancy_ids.price",
        "spendplan_consultancy_ids.consummed_amt"
    )
    @api.multi
    def _compute_amt_requested(self):
        for s in self:
            montant=mt=0.0
            for line in s.spendplan_consultancy_ids:
                montant += line.price
                mt+= line.consummed_amt
            s.update({
                'requested_amt':montant,
                'consummed_amt':mt,
            })   

class SpendplanConsultancy(models.Model):
    _name = "spendplan.consultancy"
    _description = "Spend plan Consultancy"

    sp_consultancy_id = fields.Many2one(
        string="# Spend Plan Consultancy Activity",
        comodel_name="spendplan.consultancy.activities",
        required=True,
        ondelete="cascade",
    )
    crossovered_budget_detail_id = fields.Many2one(string="Details Budget", comodel_name="crossovered.budget.detail")
    analytic_account_id = fields.Many2one('account.analytic.account', 
        related='crossovered_budget_detail_id.analytic_account_id', 
        string='Account Analytic', store=True, readonly=True,
    )
    general_budget_id = fields.Many2one('account.budget.post', 
        related='crossovered_budget_detail_id.general_budget_id', 
        string='Activity', store=True, readonly=True,
    )
    
    name = fields.Char(
        string="Description",
        required=True,
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    price = fields.Float(
        string="Price",
        required=True,
    )
    consummed_amt = fields.Float(string="Consummed Amount", required=False)
    nber_person = fields.Integer(
        string="Number Person",
        required=True,
        default = 1,
    )
    quantity = fields.Float(
        string="Quantity",
        required=True,
        default = 1,
    )
    # total_price = fields.Float(
        # string="Total",
        # compute="_compute_total_price",
        # store=True,
    # )
    
    @api.onchange(
        "product_id",
    )
    def onchange_product_id(self):
        self.name = self.product_id.name 