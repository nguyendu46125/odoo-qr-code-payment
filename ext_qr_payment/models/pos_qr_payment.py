# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import requests

class PosQrPaymentLogs(models.Model):
    _name = 'pos.qr.payment.logs'

    name = fields.Char(string='Order', readonly=True)
    log = fields.Char(string='Logs', readonly=True)

class PosQrPayment(models.Model):
    _name = 'pos.qr.payment'

    state_payment = fields.Char(string='Status Pair')

    name = fields.Char(string='Name', readonly=True)
    order_id = fields.Char(string='Order ID', readonly=True)
    request_id = fields.Char(string='Request ID', readonly=True)
    session_id = fields.Many2one('pos.session', string='POS Session Id', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', readonly=True)
    user_id = fields.Many2one('res.users', 'User Cashier', readonly=True)
    date_pay = fields.Char(string='Date Pair', readonly=True)
    date_create_pos = fields.Char(string='Date Pair', readonly=True)
    name_payment = fields.Char(string='Name Payment', readonly=True)
    amount = fields.Float(string='Amount', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('paid', 'Paid'),
        ('false', 'False')
    ], default='draft', readonly=True)

    qr_payment_line = fields.One2many('pos.qr.payment.line', 'qr_payment_id', string='Payment Request')

    @api.model
    def check_qr_payment_from_pos(self, qr_order_id, qr_amount):
        check = '01'
        if qr_order_id and qr_amount:
            a = qr_order_id
            b = qr_amount
            search_payment = self.search([('order_id', '=', qr_order_id)])
            if search_payment:
                for request in search_payment.qr_payment_line:
                    if request.amount == qr_amount and request.payment_state == '00':
                        check = '00'
        return check

    @api.model
    def bus_confirm_qr_payment(self, data):
        payment_method_obj = self.env['pos.payment.method']

        if data:
            vtb_status_code = data.get('statusCode')
            vtb_amount = data.get('amount')
            vtb_terminal_id = data.get('terminalId')
            vtb_bank_transaction_id = data.get('bankTransactionId')
            vtb_request_id = data.get('requestId')

            vtb_merchant_name = data.get('merchantName')
            vtb_merchant_id = data.get('merchantId')
            vtb_transaction_date = data.get('transactionDate')
            vtb_order_id = data.get('orderId')
            vtb_status_mes = data.get('statusMessage')
            vtb_product_id = data.get('productId')
            vtb_signature = data.get('signature')
            try:
                mes = str(vtb_status_code) + '-' + str(vtb_amount) + '-' + str(vtb_status_mes)
                self.env['pos.qr.payment.logs'].sudo().create({
                    'name': str(vtb_order_id),
                    'log': mes,
                })
                self.env.cr.commit()
            except Exception as e:
                print('Error Qr Call API')

            return_val = {
                "requestId": vtb_request_id,
                "paymentStatus": '00',
                "signature": vtb_signature
            }

            search_vtb = payment_method_obj.sudo().search([('is_qr_count', '=', True), ('bank_code', '=', 'vietinbank')], limit=1)
            if not search_vtb:
                return_val.update({'paymentStatus': 'No Payment Method!!!'})
                return return_val
            merchant_id = search_vtb.merchant_id
            if vtb_merchant_id != merchant_id:
                return_val.update({'paymentStatus': 'MerchantId not found!!!'})
                return return_val
            terminal_id = search_vtb.terminal_id
            if vtb_terminal_id != terminal_id:
                return_val.update({'paymentStatus': 'TerminalId not found!!!'})
                return return_val
            time_now = datetime.now()

            search_qr_order = self.search([('order_id', '=', vtb_order_id)], limit=1)
            if search_qr_order:
                search_qr_request = search_qr_order.qr_payment_line
                reversed_tuple = tuple(search_qr_request)[::-1]
                check = 0
                for request in reversed_tuple:
                    # if request.payment_state == '00':
                    #     return {
                    #         "requestId": vtb_request_id,
                    #         "paymentStatus": '00',
                    #         "signature": vtb_signature
                    #     }
                    if request.amount == float(vtb_amount):
                        try:
                            check = 1
                            search_qr_order.write({
                                'date_pay': time_now,
                                'state': 'paid',
                            })
                            request.write({
                                'payment_state': vtb_status_code,
                                'request_id_vtb': vtb_request_id,
                                'transaction_date': vtb_transaction_date,
                                'vtb_bank_transaction_id': vtb_bank_transaction_id,
                                'vtb_status_mes': vtb_status_mes,
                            })
                            self.env['bus.bus'].sudo().sendone(
                                'pos_confirm_qr_payment_channel',
                                {
                                    'type': 'qr_payment_status',
                                    'payment_state': vtb_status_code,
                                    'request_id': request.request_id,
                                    'order_id': vtb_order_id,
                                    'amount': vtb_amount,
                                }
                            )
                            self.env.cr.commit()
                            break
                        except Exception as e:
                            print(e)
                if check == 0:
                    return_val.update({'paymentStatus': 'Your funds are not enough, please contact your bank!!!'})
                    return return_val
                if check == 1:
                    return {
                        "requestId": vtb_request_id,
                        "paymentStatus": '00',
                        "signature": vtb_request_id + '00',
                    }
            else:
                return_val.update({'paymentStatus': 'OrderID not found!!!'})
                return return_val

    @api.model
    def creat_from_ui(self, data):
        try:
            if data:
                request_id = data.get('qrRequestId')
                qr_order_id = data.get('qrOrderId')
                qr_oder_name = data.get('qrOderName')
                qr_amount_order = data.get('qrAmountOrder')
                qr_name_payment = data.get('qrNamePayment')
                qr_payment_status = data.get('qrPaymentStatus')
                qr_pos_session_id = data.get('qrPosSessionId')
                qr_partner_id = data.get('qrPartnerId')
                qr_user_id = data.get('qrUserId')

                # time_now = datetime.now() + timedelta(hours=7)
                time_now = datetime.now()

                search_order = self.search([('order_id', '=', qr_order_id)], limit=1)
                if search_order and search_order.user_id.id != qr_user_id:
                    search_order.write({'user_id': qr_user_id})
                if not search_order:
                    qr_val = {
                        'name': qr_oder_name,
                        'order_id': qr_order_id,
                        'name_payment': qr_name_payment,
                        'session_id': qr_pos_session_id,
                        'partner_id': qr_partner_id,
                        'user_id': qr_user_id,
                        'state': 'draft',
                    }
                    search_order = self.sudo().create(qr_val)

                qr_val_line = {
                    'qr_payment_id': search_order.id,

                    'request_id': request_id,
                    'date_create_pos': time_now,
                    'amount': qr_amount_order,
                    'payment_state': qr_payment_status,
                    # 'payment_state': 'draft',
                }
                self.env['pos.qr.payment.line'].sudo().create(qr_val_line)
                return search_order.id
        except Exception as e:
            print(f"Error: {e}")

    @api.model
    def call_api_vtb(self, data, bank_code):

        client_secret = ''
        client_id = ''
        function_name = ''
        data_call = {}

        if data:
            qr_request_id = data.get('qrRequestId')
            qr_order_id = data.get('qrOrderId')
            qr_oder_name = data.get('qrOderName')
            qr_amount_order = data.get('qrAmountOrder')
            qr_name_payment = data.get('qrNamePayment')
            qr_payment_status = data.get('qrPaymentStatus')

            merchant_name = 'Cty CP Vong Xanh'
            qr_pos_session_id = data.get('qrPosSessionId')
            if qr_pos_session_id:
                merchant_name = self.env['pos.session'].browse(int(qr_pos_session_id)).config_id.name

            qr_partner_id = str(data.get('qrPartnerId'))
            qr_user_id = data.get('qrUserId')

            product_id = ""
            payment_method = "QR"
            currency_code = "VND"

            time_now = datetime.now() + timedelta(hours=7)
            qr_date_create = time_now
            qr_date_expire = time_now + timedelta(minutes=10)
            str_date_create_qr = qr_date_create.strftime("%Y%m%d%H%M%S")
            str_qr_date_expire = qr_date_expire.strftime("%Y%m%d%H%M%S")

            method = self.env['pos.payment.method'].search([('bank_code', '=', bank_code)], limit=1)
            provider_id = method.provider_id
            merchant_id = method.merchant_id
            terminal_id = method.terminal_id
            client_secret = method.client_secret
            client_id = method.client_id
            function_name = method.function_name

            sing_data = qr_request_id + provider_id + merchant_id + terminal_id + product_id + str(
                qr_amount_order) + payment_method + str_qr_date_expire + "VND" + qr_partner_id + "14.161.36.234" + "POS" + "1.0.1" + "vi"

            data_call = {
                "requestId": qr_request_id,
                "providerId": provider_id,
                "merchantId": merchant_id,
                "merchantName": 'CTP CP VONG XANH',
                "terminalId": terminal_id,
                "productId": product_id,
                "orderId": qr_order_id,
                "amount": qr_amount_order,
                "payMethod": payment_method,
                "transactionDate": str_qr_date_expire,
                "currencyCode": currency_code,
                "remark": qr_partner_id,
                "transTime": str_date_create_qr,
                "channel": "POS",
                "version": "1.0",
                "language": "vi",
                "signature": sing_data
            }
            print(data_call)

        # Đặt các thông tin cơ bản
        # main_url = "https://api-uat.vietinbank.vn/vtb-api-uat/development/qrcode/utilities/qrGenerator"
        main_url = "https://api-uat.vietinbank.vn/vtb-api-uat/development/qrcode/utilities/" + function_name
        base_headers = {
            "Content-Type": "application/json",
            "x-ibm-client-secret": client_secret,
            "x-ibm-client-id": client_id
        }

        try:
            response = requests.post(main_url, json=data_call, headers=base_headers)

            if response.status_code == 200:
                result = response.json()
                if result.get('status').get('code') == '00':
                    request_id = result.get('requestId')
                    data_qr = result.get('qrData')
                    return {
                        'requestId': request_id,
                        'qrData': data_qr,
                    }
            else:
                print(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
            return '01'


class PosQrPaymentLine(models.Model):
    _name = "pos.qr.payment.line"

    qr_payment_id = fields.Many2one('pos.qr.payment', readonly=True)

    request_id = fields.Char(string='Request Id', readonly=True)
    request_id_vtb = fields.Char(string='Request Id Vietinbank', readonly=True)
    transaction_date = fields.Char(string='Transaction Date', readonly=True)
    vtb_bank_transaction_id = fields.Char(string='Transaction ID', readonly=True)
    vtb_status_mes = fields.Char(string='Status Messenger', readonly=True)
    date_create_pos = fields.Datetime(string='Create Request', readonly=True)
    amount = fields.Float(string='Amount', readonly=True)
    payment_state = fields.Selection([(
        'draft', 'Draft'),
        ('00', 'Thành công'),
        ('01', 'Giao dịch đã được thanh toán trước đó'),
        ('02', 'Giao dịch không hợp lệ'),
        ('03', 'Giao dịch không tìm thấy'),
        ('04', 'Số tiền không hợp lệ'),
        ('05', 'Giao dịch đã hết hạn thanh toán.'),
        ('08', 'Timeout Chưa xác định được'),
        ('09', 'Bảo trì'),
        ('blocked', 'Blocked')], default='draft', readonly=True)
