from openerp import models, api, fields, _
from lxml import etree

from openerp.exceptions import Warning as UserError

class DesableAccount(models.TransientModel):
    """
    Ce wizard a pour but de slectionner plusieurs compte et de les desactiver tous ensemble
    """
    _name = 'desable.account'
    _description = 'This is for desable selected account'

    @api.multi
    def desable_account(self):
        context = self._context or {} 
        for record in context['active_ids']:
            if record:
                account_id = self.env['account.account'].search([('id','=',record)])
                account_id.write({'active':False})

        return {'type': 'ir.actions.act_window_close'}