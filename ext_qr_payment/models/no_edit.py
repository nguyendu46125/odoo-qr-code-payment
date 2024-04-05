# -*- coding: utf-8 -*-
# ngày 15-03-2024 du-it edit api của cả hệ thống
# để phù hợp theo yêu cầu cảu vietinbank
# file này tuyệt đối không được sửa
import json
from odoo.http import Controller, route, JsonRequest, Response
from odoo.tools import date_utils


def _json_response(self, result=None, error=None):
    response = {
        'jsonrpc': '2.0',
        'id': self.jsonrequest.get('id')
    }
    try:
        if self.endpoint.routing:
            lover = self.endpoint.routing
            if lover.get('auth') == 'public':
                if error is not None:
                    response['error'] = error
                if result is not None:
                    if 'api' in result:
                        if result['api'] == 'api_vtb_call_qr':
                            del result['api']
                            response = result
                        else:
                            response['result'] = result
                    else:
                        response['result'] = result

                mime = 'application/json'
                body = json.dumps(response, default=date_utils.json_default)

                return Response(
                    body, status=error and error.pop('http_status', 200) or 200,
                    headers=[('Content-Type', mime), ('Content-Length', len(body))]
                )
            else:
                if error is not None:
                    response['error'] = error
                if result is not None:
                    response['result'] = result

                mime = 'application/json'
                body = json.dumps(response, default=date_utils.json_default)

                return Response(
                    body, status=error and error.pop('http_status', 200) or 200,
                    headers=[('Content-Type', mime), ('Content-Length', len(body))]
                )
        else:
            if error is not None:
                response['error'] = error
            if result is not None:
                response['result'] = result

            mime = 'application/json'
            body = json.dumps(response, default=date_utils.json_default)

            return Response(
                body, status=error and error.pop('http_status', 200) or 200,
                headers=[('Content-Type', mime), ('Content-Length', len(body))]
            )

    except Exception as e:
        if error is not None:
            response['error'] = error
        if result is not None:
            response['result'] = result

        mime = 'application/json'
        body = json.dumps(response, default=date_utils.json_default)

        return Response(
            body, status=error and error.pop('http_status', 200) or 200,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )


setattr(JsonRequest, '_json_response', _json_response)
