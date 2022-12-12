from odoo import models, Command

class EstateProperty(models.Model):
    _inherit = "estate.property"

    # override
    def sold_property(self):
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        print(self.selling_price, "testing")
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.env['estate.property'].id,
            'journal_id': journal.id,  # company comes from the journal
            'invoice_line_ids': [
                Command.create({
                    "name" : "unit price - 6% of the selling price plus additional 100.00 for administrative fees",
                    "quantity" : 1,
                    "price_unit" : self.selling_price * (6/100) + 100 + self.selling_price,
                })
            ],
        }
        self.env['account.move'].create(invoice_vals)
        return super().sold_property()