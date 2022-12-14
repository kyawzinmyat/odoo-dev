from odoo import fields, models, api
from datetime import timedelta
from odoo.exceptions import UserError
from odoo.tools.translate import _


class LibraryBook(models.Model):
    _name = "library.book"
    _description = 'Library Book'
    _order = "date_release desc, name"
    _rec_name = 'short_name'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', "Book title must be unique"),
        ('positive_numbersof_page', 'CHECK(pages>0)', 'No. of pages must be positive')
    ]

    name = fields.Char("Title", required = True)
    author_ids = fields.Many2many(
        'res.partner',
        string = "Authors"
    )

    notes = fields.Text('Internal Notes')
    state = fields.Selection(
            [('draft', 'Not Available'),
            ('available', 'Available'),
            ('lost', 'Lost'), ('borrowed', 'Borrowed')],
            'State', default = 'draft')
    description = fields.Html('Description')
    cover = fields.Binary('Book Cover')
    out_of_print = fields.Boolean('Out of Print?')
    date_release = fields.Date('Release Date')
    date_updated = fields.Datetime('Last Updated')
    pages = fields.Integer('Number of Pages')
    reader_rating = fields.Float(
                    'Reader Average Rating',
                    digits=(14, 4), # Optional precision decimals,
                    )
    short_name = fields.Char('Short Title', required=True)
    cost_price = fields.Float('Book Cost', digits = 'Book Price') 
    currency_id = fields.Many2one('res.currency', string='Currency')
    retail_price = fields.Monetary('Retail Price')
    publisher_id = fields.Many2one('res.partner', string = "Publisher", ondelete = 'set null')
    category_id = fields.Many2one('library.book.category')
    age_days = fields.Integer(string = 'Day since Release', compute = "_compute_age", inverse = "_inverse_age", search = "_search_age")
    publisher_city = fields.Char('Publisher City', related='publisher_id.city', readonly=True)
    author_ids = fields.Many2many('res.partner', string='Authors')
    
    @api.constrains('date_release')
    def _check_release_date(self):
        for record in self:
            if record.date_release and record.date_release > fields.Date.today():
                raise models.ValidationError("Error in the date release")

    @api.depends('date_release')
    def _compute_age(self):
        for record in self:
            if record.date_release:
                record.age_days = (fields.Date.today() - record.date_release).days
            else:
                record.age_days = 0
    @api.model
    def is_allowed_transition(self, old_state, new_state):
        print(old_state)
        allowed = [('draft', 'available'),
                    ('available', 'borrowed'),
                    ('borrowed', 'available'),
                    ('available', 'lost'),
                    ('borrowed', 'lost'),
                    ('lost', 'available')]
        return (old_state, new_state) in allowed
    
    def change_state(self, new_state):
        for book in self:
            if book.is_allowed_transition(book.state, new_state):
                book.state = new_state
            else:
                msg = _("Moving from %s to %s is not allowed") % (book.state, new_state)
                raise UserError(msg)
            
    def make_available(self):
        self.change_state("available")

    def make_borrowed(self):
        self.change_state("borrowed")
    
    def make_lost(self):
        self.change_state("lost")


    def _inverse_age(self):
        for record in self:
            record.date_release = fields.Date.today() - timedelta(days = record.age_days)

    def log_all_library_members(self):
        library_member_model = self.env['library.member']
        all_members = library_member_model.search([])
        print("ALL MEMBERS:", all_members)
        return True

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    published_book_ids = fields.One2many('library.book', 'publisher_id', string = 'Published Book')
    authored_book_ids = fields.Many2many('library.book', string='Authored Books')
    count_books = fields.Integer( 'Number of Authored Books', compute='_compute_count_books' )

    @api.depends('authored_book_ids')
    def _compute_count_books(self):
        for record in self:
            self.count_books = len(self.authored_book_ids)
            
        

class LibraryMember(models.Model):
    _name = 'library.member'
    _inherits = {'res.partner' : 'partner_id'}
    partner_id = fields.Many2one('res.partner', ondelete = "cascade")
    date_start = fields.Date('Member Since')
    date_end = fields.Date('Termination Date')
    member_number = fields.Char()
    date_of_birth = fields.Date('Date of birth')