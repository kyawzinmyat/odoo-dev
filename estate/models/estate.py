from odoo import models, fields, api
import datetime
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare

def set_default_date():
    current = datetime.datetime.today()
    return datetime.date(
        current.year, (current.month + 3) % 12, current.day
    )

class EstateProperty(models.Model):
    _name = "estate.property"
    _sql_constraints = [
        ('check_selling_price_positive', "CHECK(selling_price >= 0)", "Selling Price cannot be a negative number"),
        ('check_expected_price_positive', "CHECK(expected_price >= 0)", "Expected Price cannot be a negative number")
    ]
    _order = "id desc"

    active = fields.Boolean('Active', default = 1)
    name = fields.Char()
    description = fields.Text()
    postcode = fields.Integer()
    date_availability = fields.Date(copy = False, default = set_default_date())
    expected_price = fields.Float()
    selling_price = fields.Float(readonly= True, copy = False)
    bedrooms = fields.Integer(default = 2)
    living_area = fields.Float(string = "Living Area(sqm)")
    facades = fields.Integer()
    garage = fields.Boolean()
    garden = fields.Boolean()
    best_offer = fields.Float(compute = "_compute_best_offer")
    garden_area = fields.Float(string = "Garden Area(sqm)")
    garden_orientation = fields.Selection([('option1', 'NORTH'), ('option2', 'EAST')
                                            ,('option3', 'SOUTH'), ('option4', 'WEST')
                                        ])
    property_type_id = fields.Many2one("estate.property.type", string = 'Type')
    property_tags_ids = fields.Many2many("estate.property.tags", string = 'Tags')
    offer_ids = fields.One2many('estate.property.offer', 'property_id')
    buyer_id = fields.Many2one("res.partner", ondelete = "set null")
    seller_id = fields.Many2one("res.users", default = lambda self: self.env.user, copy = False, ondelete = "set null") 
    state = fields.Selection([
            ('option1', 'New'), ('option2', 'Offer Received'), ('option3', 'Offer Accepted'),
            ('option4', 'Sold'), ('option5', 'Canceled')
        ], default = 'option1', string = 'status'
    )
    total_area = fields.Float(compute = "_compute_total_area", string = "Total Area(sqm)")

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area
    
    @api.depends('offer_ids.price')
    def _compute_best_offer(self):
        for record in self:
            record.best_offer = max(record.offer_ids.mapped('price') + [0])

    @api.onchange('garden')
    def _onchange_(self):
        self.garden_area = 0
        self.garden_orientation = ''
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'option1'
    
    # override
    @api.ondelete(at_uninstall=True)
    def filter_delete(self):
        for record in self:
            if record.state != 'option1' and record.state != 'option5':
                raise ValidationError("You can only delete state with new or cancled")

   


    def sold_property(self):
        for record in self:
            if record.state[-1] != '4' and record.state[-1] != '5':
                record.state = 'option4'
    
    def cancle_property(self):
        for record in self:
            if record.state[-1] != '4' and record.state[-1] != '5':
                record.state = 'option5'
        
    

class PropertyType(models.Model):
    _name = "estate.property.type"
    _sql_constraints = [
        ('check_uniqueness', "UNIQUE(name)", "Type must be unique")
    ]
    _order = "name"

    property_ids =  fields.One2many('estate.property', 'property_type_id', string='')
    sequence = fields.Integer("Sequence", )

    name = fields.Char()
    offer_ids = fields.One2many('estate.property.offer', 'property_type_id')
    offer_count = fields.Integer(compute = "_compute_offer_count")

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)
    



class PropertyTags(models.Model):
    _name = "estate.property.tags"
    _sql_constraints = [
        ('check_uniqueness', "UNIQUE(name)", "Tags must be unique")
    ]
    _order = "name"

    name = fields.Char()
    color = fields.Integer()

class PropertyOffers(models.Model):
    _name = "estate.property.offer"
    _sql_constraints = [
        ('check_price_positive', "CHECK(price >= 0)", "Price cannot be a negative number")
    ]
    _order = "price desc"

    price = fields.Float()
    status = fields.Selection([
        ('option1', 'Accepted'), ('option2', 'Canceled')
    ],copy = False)
    partner_id = fields.Many2one("res.partner", required=True)
    property_id = fields.Many2one("estate.property", required=True)
    property_type_id = fields.Many2one('estate.property.type', related = "property_id.property_type_id", stored = 'True')

    @api.constrains('price')
    def _check_price(self):
        for record in self:
            if float_compare(record.price, record.property_id.expected_price * (90/100), precision_digits=3) < 0:
                raise ValidationError("Price needed to be at least 90percent of the expected price")

    def accept_offer(self):
        for record in self:
            if not record.property_id.buyer_id:
                record.status = 'option1'
                record.property_id.state = 'option3'
                record.property_id.selling_price = record.price
                record.property_id.buyer_id = record.partner_id

    def refuse_offer(self):
        for record in self:
            if not record.status or record.status[-1] != '1':
                record.status = 'option2'
    
    
    #override   
    @api.model
    def create(self, vals):
        #if vals['price'] < max_price:
        #    raise ValidationError("Price need to be at least ", max_price)

        best_offer = self.env['estate.property'].browse(vals['property_id']).best_offer
        if vals['price'] < best_offer:
            raise ValidationError(f"Offer need to be at least {best_offer}")

        self.env['estate.property'].browse(vals['property_id']).state = 'option2'
        return super(PropertyOffers, self).create(vals)