from odoo import fields, models

class LibraryBook(models.Model):
    _name = "library.book"
    _description = 'Library Book'
    _order = "date_release desc, name"
    _rec_name = 'short_name'

    name = fields.Char("Title", required = True)
    author_ids = fields.Many2many(
        'res.parnter',
        string = "Authors"
    )

    notes = fields.Text('Internal Notes')
    state = fields.Selection(
            [('draft', 'Not Available'),
            ('available', 'Available'),
            ('lost', 'Lost')],
            'State')
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