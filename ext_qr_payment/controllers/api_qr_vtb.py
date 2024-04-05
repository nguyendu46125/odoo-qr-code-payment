import logging
from odoo import http
from odoo.tools import date_utils
from odoo.http import request, WebRequest, Response
from datetime import datetime
import json
import odoo

_logger = logging.getLogger(__name__)


class PublicApiController(http.Controller):

    @http.route('/api/v1/public_web/api_vtb_qr', methods=["POST"], type="json", auth="public", csrf=False)
    def get_api_vtb_qr(self, **post):

        try:
            data = json.loads(request.httprequest.data)
            # parameters = json.loads(http.request.httprequest.data)
            data_qr = request.jsonrequest

            if not data_qr:
                return {
                    "api": "api_vtb_call_qr",
                    "error": "Body is required!!!"
                }
            # check = 'ci7J+pN378zwfV/foY87tKyvpBpmcsE4nyK8ARq86JBviUImZzLUplvf2bOrF2smr/tk7wuw2XuF9XH1qzsmgaqYrgRkh9wHCImONHJEak9gVX0shlbpLhZweHv3pzm3Pf6WFaPow5tL3U2Vcfe1D8MH38cKc9mfgp68SIGNB+IpGCf0NzHWTSwNQ2lYfvFRiLR45Hhnmu0cKggjgvtkhJSxK37mKJF048WYWYSFPjloFn8sr0WSUZg2bcVxRR8Yo9XX0Z6ETxJnv2HuSM6QdwlFzHZeaizRsqyQ2qlkYq0s3jstGDvLpKKjQjQuFl1fkKG3lNPjCABRN1VuCfxCrQ=='
            # if data_qr.get('signature') != check:
            #     return {
            #         "api": "api_vtb_call_qr",
            #         "error": "signature does not match!!!"
            #     }
            data_notification = request.env['pos.qr.payment'].bus_confirm_qr_payment(data_qr)
            du_iu_meme = {'api': 'api_vtb_call_qr'}
            data_notification.update(du_iu_meme)
            return data_notification
        except Exception as e:
            return {
                "api": "api_vtb_call_qr",
                "error": "Data Fail!!!"
            }
