# -*- coding: utf-8 -*-
{
    'name': "addon_hotel",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hotel_management_odoo','account', 'event', 'fleet', 'lunch','mail'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/room.xml',
        'views/res_partner.xml',
        'views/account_payment.xml',
        'views/room_booking.xml',
        'report/shift.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'addon_hotel/static/src/css/custom_styles.css',  # Path to your CSS file
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}