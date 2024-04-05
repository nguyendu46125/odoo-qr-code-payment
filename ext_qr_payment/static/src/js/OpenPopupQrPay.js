odoo.define('ext_qr_payment.OpenPopupQrPay', function (require) {
    'use strict';

    const {_t} = require('web.core');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const {useBarcodeReader} = require('point_of_sale.custom_hooks');
    const {Component} = owl;
    const rpc = require('web.rpc');
    const NumberBuffer = require('point_of_sale.NumberBuffer');

    const QrPaymentScreen = (payment_screen) => class extends payment_screen {
        setup() {
            super.setup()
        }

        formatTimestampToString(timestamp) {
            var dateObject = new Date(timestamp);

            // Lấy các thành phần của thời gian
            var day = dateObject.getDate();
            var month = dateObject.getMonth() + 1; // Tháng bắt đầu từ 0
            var year = dateObject.getFullYear();
            var hours = dateObject.getHours();
            var minutes = dateObject.getMinutes();
            var seconds = dateObject.getSeconds();

            // Chuyển đổi thành chuỗi và đảm bảo rằng định dạng là dd/mm/yyyy hh:mm:ss
            var dateString = year + this.formatTime(month) + this.formatTime(day) + this.formatTime(hours) + this.formatTime(minutes) + this.formatTime(seconds);

            return dateString;
        }

        formatTime(time) {
            return (time < 10) ? '0' + time : time;
        }

        async callQrRpcValidatePath(paymentLineId) {
            return rpc.query({
                model: 'pos.payment.method',
                method: 'search_read',
                domain: [['id', '=', paymentLineId]],
                fields: ['is_qr_count'],
            }).then(async function (check_rpc_pos) {
                return check_rpc_pos[0]
            });
        }

        async callQrStatusBeforeValidate(paymentLines) {
            var self = this;
            var paymentCheckData = false
            var count1 = 0
            for (var line of paymentLines) {
                count1 += 1
                var lineIdQrPaymentMethod = line.payment_method.id
                var isQrCount = await self.callQrRpcValidatePath(lineIdQrPaymentMethod)
                if (isQrCount.is_qr_count) {
                    paymentCheckData = true
                }
            }
            return paymentCheckData;
        }

        async validateOrder(isForceValidate) {

            var self = this;
            var paymentLines = self.paymentLines;
            var order = self.env.pos.get_order();
            var paymentCheckCall = await self.callQrStatusBeforeValidate(paymentLines)
            if (paymentCheckCall) {
                return await self.showQrPaymentFromPos()
            }
            // else{
            //     console.log("Paymentasssssssssssssssssss")
            // }

            //     // var confirmed = await self.showPopup("ConfirmPopup", {
            //     //     title: "Có thanh toán bằng mã QR",
            //     //     body: "Trong đơn có thanh toán bằng mã QR. Bạn có chắc chắn muốn tiếp tục không?",
            //     // });
            //     // if (confirmed) {
            //     //     return;
            //     // }
            // }
            await super.validateOrder(isForceValidate)
        }

        async addNewPaymentLine({detail: paymentMethod}) {
            var self = this;
            var payment_id = paymentMethod.id;
            var pyment_check = rpc.query({
                model: 'pos.payment.method',
                method: 'search_read',
                domain: [['id', '=', payment_id]],
                fields: ['is_qr_count', 'bank_code'],
            }).then(async function (check) {
                let qr_check = false;
                if (check && check.length > 0) {
                    var order = self.env.pos.get_order();
                    qr_check = check[0].is_qr_count;
                    if (order.get_orderlines().length > 0) {
                        if (qr_check) {
                            if (check[0].bank_code === 'vietinbank') {
                                await self.showQrPaymentFromPos()
                            }
                        }
                    } else {
                        self.deletePaymentLine({detail: {cid: self.selectedPaymentLine.cid}});
                        await self.showPopup('ErrorPopup', {
                            title: self.env._t('Error'),
                            body: self.env._t('There is already an electronic payment in progress.'),
                        });
                    }

                }
            });

            super.addNewPaymentLine({detail: paymentMethod})

        }

        async callRpcDataQrOrderPopup(qrDataOpenOrderPopup) {
            var self = this;
            return await self.rpc({
                model: 'pos.qr.payment',
                method: 'creat_from_ui',
                args: [qrDataOpenOrderPopup],
            }).catch(error => {
                self.deletePaymentLine({detail: {cid: self.selectedPaymentLine.cid}});
                console.error('Lỗi khi gọi RPC qrDataOpenOrderPopup[\'qrRequestId\']:', error);
            })
        }

        async showQrPaymentFromPos() {
            var self = this;
            var order = self.env.pos.get_order();
            if (order.get_orderlines().length <= 0) {
                await self.showPopup('ErrorPopup', {
                    title: self.env._t('Nothing to Order!!!'),
                    body: self.env._t('There are no order lines'),
                });
            }

            var qrDataOpenOrderPopup = {};
            var selectedPaymentLine = order.selected_paymentline;
            var oderName = order.name;
            var oderPosSessionId = order.pos_session_id;
            var orderQrClient = order.attributes
            if (!orderQrClient.client) {
                self.deletePaymentLine({detail: {cid: self.selectedPaymentLine.cid}});
                return await self.showPopup('ErrorPopup', {
                    title: self.env._t('Khách Hàng Đâu???'),
                    body: self.env._t('There are no partner_id in order!!!'),
                });
            }
            var oderPartnerId = order.attributes.client.id;
            var qrOrderId = oderName.replace('Đơn hàng ', "");

            var qrAmountOrder = selectedPaymentLine.amount;
            var qrNamePayment = selectedPaymentLine.name;

            qrDataOpenOrderPopup['qrOrderId'] = qrOrderId
            qrDataOpenOrderPopup['qrOderName'] = oderName
            qrDataOpenOrderPopup['qrAmountOrder'] = qrAmountOrder
            qrDataOpenOrderPopup['qrNamePayment'] = qrNamePayment
            qrDataOpenOrderPopup['qrPaymentStatus'] = 'draft'
            qrDataOpenOrderPopup['qrPosSessionId'] = oderPosSessionId
            qrDataOpenOrderPopup['qrPartnerId'] = oderPartnerId

            var current_user = self.env.pos.get_cashier();
            if (current_user.id){
                qrDataOpenOrderPopup['qrUserId'] = current_user.id
            } else {
                qrDataOpenOrderPopup['qrUserId'] = current_user.user_id[0]
            }

            var date_now = new Date().getTime();
            qrDataOpenOrderPopup['qrRequestId'] = self.formatTimestampToString(date_now) + oderPosSessionId.toString();

            qrDataOpenOrderPopup['qrPosQrPaymentId'] = await self.callRpcDataQrOrderPopup(qrDataOpenOrderPopup)

            qrDataOpenOrderPopup['qrDataBank'] = await self.rpc({
                model: 'pos.qr.payment',
                method: 'call_api_vtb',
                args: [qrDataOpenOrderPopup, 'vietinbank'],
            }).catch(async error => {
                qrDataOpenOrderPopup['qrDataBank'] = '01'
                // self.deletePaymentLine({detail: {cid: self.selectedPaymentLine.cid}});
                console.error('Lỗi khi gọi RPC call_vtb_create_data_qr_rpc:', error);
            })

            const {confirmed, payload} = await self.showPopup('QrPayPopupWidget', {
                dataQrOpenPopup: qrDataOpenOrderPopup
            }).catch(async error => {
                self.deletePaymentLine({detail: {cid: self.selectedPaymentLine.cid}});
                console.error('Lỗi khi gọi Popup QR PAY:', error);
            });
            if (confirmed) {
                if (self.env.pos.config.cash_rounding) {
                    if (!self.env.pos.get_order().check_paymentlines_rounding()) {
                        self.deletePaymentLine({detail: {cid: self.selectedPaymentLine.cid}});
                        await self.showPopup('ErrorPopup', {
                            title: self.env._t('Rounding error in payment lines'),
                            body: self.env._t("The amount of your payment lines must be rounded to validate the transaction."),
                        });
                        return;
                    }
                } else {
                    for (let line of self.paymentLines) {
                        if (!line.is_done()) self.currentOrder.remove_paymentline(line);
                    }
                    await self._finalizeValidation();
                }
                NumberBuffer.reset();
                console.log('bam yes');
                return true;
            } else {
                self.deletePaymentLine({detail: {cid: self.selectedPaymentLine.cid}});
                console.log('bam no');
                return false;
            }

        }

        go_next() {
            console.log("You clicked next from payment screen.")
        }

    }

    Registries.Component.extend(PaymentScreen, QrPaymentScreen)
    return PaymentScreen;
})
;
