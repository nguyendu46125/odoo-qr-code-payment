# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import requests


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    is_qr_count = fields.Boolean(string='QR', default=False)
    bank_code = fields.Char(string='Bank Short Name')
    function_name = fields.Char(string='Function Name')
    client_secret = fields.Char(string='x-ibm-client-secret')
    client_id = fields.Char(string='x-ibm-client-id')
    provider_id = fields.Char(string='providerId')
    merchant_id = fields.Char(string='merchantId')
    terminal_id = fields.Char(string='terminalId')

    def write(self, vals):
        result = super(PosPaymentMethod, self).write(vals)
        if self.is_qr_count:
            if not self.bank_code:
                raise UserError(_("Bank code is required!!!"))
            if not self.function_name:
                raise UserError(_("Function Name is required!!!"))
            if not self.client_secret:
                raise UserError(_("x-ibm-client-secret is required!!!"))
            if not self.client_id:
                raise UserError(_("x-ibm-client-id is required!!!"))
            if not self.provider_id:
                raise UserError(_("providerId is required!!!"))
            if not self.merchant_id:
                raise UserError(_("merchantId is required!!!"))
            if not self.terminal_id:
                raise UserError(_("terminalId is required!!!"))
        return result
class PosPayment(models.Model):
    _inherit = 'pos.payment'

    is_qr_order_pos = fields.Boolean(string='QR Code', default=False)
    pos_qr_payment_id = fields.Many2one('pos.qr.payment', string='QR Pos Payment')

    @api.model_create_multi
    def create(self, vals):
        events = super(PosPayment, self).create(vals)
        if events.payment_method_id:
            payment_id = events.payment_method_id

            if payment_id.is_qr_count:
                pos_reference = events.pos_order_id.pos_reference
                search_qr_order = self.env['pos.qr.payment'].search([('name', '=', pos_reference)], limit=1)
                # self.env['pos.qr.payment'].search(payment_id)
                events.write({
                    'is_qr_order_pos': True,
                    'pos_qr_payment_id': search_qr_order.id
                })
        return events
