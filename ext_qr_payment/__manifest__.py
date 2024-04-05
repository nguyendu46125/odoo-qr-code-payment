# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Qr Payment',
    'version': "1.01",
    'author': "Du-IT",
    'category': 'Point of Sale',
    'sequence': 41,
    'summary': 'POS QR Payment',
    'description': "",
    'depends': ['base', 'point_of_sale', 'bus'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_payment_method.xml',
        'views/pos_assets_common.xml',
        'views/pos_order_view.xml',
        'views/pos_qr_payment_view.xml',
        'views/pos_qr_payment_log_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'qweb': [
        'static/src/xml/QrPayPopupWidget.xml',
    ],
    'website': 'https://www.giant.com',
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'],
}
