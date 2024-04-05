odoo.define('ext_qr_payment.QrPayPopupWidget', function (require) {
    'use strict';

    const {
        useState,
        useRef
    } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const BusService = require('bus.BusService');
    const BusLongpolling = require('bus.Longpolling');

    class QrPayPopupWidget extends AbstractAwaitablePopup {

        setup() {
            const bus_service = owl.Component.env.services.bus_service;
            const channel = 'pos_confirm_qr_payment_channel';
            bus_service.addChannel(channel);
            bus_service.onNotification(this, this.updateQrPaymentStatus);
            bus_service.startPolling();

        }

        click_check_qr_paid() {
            console.log('QrPayPopupWidgetsssssssssssssssssssss')
        }

        click_print_qr_code() {
            console.log('print sssssssss')
        }

        constructor() {
            super(...arguments);
            this.state = useState({
                typeValue: this.props.startingValue,
            });
        }

        async getPayload() {

            var self = this;
            var orderPayload = self.env.pos.get_order();
            var selectedLine = orderPayload.get_selected_orderline();
            var selectedPaymentLine = orderPayload.selected_paymentline;

            if (selectedLine) {
                if (selectedPaymentLine) {
                    var qrDataPayloadPopup = {};
                    var amountPayment = selectedPaymentLine.amount
                    var namePayment = selectedPaymentLine.name
                    var payment_method = selectedPaymentLine.payment_method

                    qrDataPayloadPopup['qrOderName'] = orderPayload.name
                    qrDataPayloadPopup['qrAmountOrder'] = amountPayment
                    qrDataPayloadPopup['qrNamePayment'] = namePayment

                    return qrDataPayloadPopup
                }
            }


        }


        // genQrCode(){
        //     String result = "";
        //     QRBean bean = QRBean.builder()
        //         .payLoad("01") // Mac dinh
        //         .pointOIMethod("12") // Mac dinh
        //         .masterMerchant("970489") // Mac dinh
        //         .merchantCode("0401294050")// merchant_code ,nghiep vu VTB gui
        //         .merchantName("TRUONG THCS LY THUONG KIET") // merchant_name ,nghiep vu VTB gui
        //         .merchantCC("8211") // nghiep vu VTB gui
        //         .ccy("704") // Mac dinh
        //         .countryCode("VN") // Mac dinh
        //         .merchantCity("HANOI") // Ten viet tat cua tinh thanh cua Merchant
        //         .amount("10000") // so tien cho so hoa don do
        //         .build();
        //     QRAddtionalBean addBean = QRAddtionalBean.builder()
        //         .billNumber("1b3535d41bAC") // so hoa don duy nhat trong 1 ngay
        //         .storeID("108002788339") // TerminalID ,nghiep vu VTB gui
        //         .terminalID("108002788339") // Ma TerminalID ,nghiep vu VTB gui
        //         .purpose("TTHP.Ky_1_nam_2023") //Ghi chu dinh kem <= 19 ky tu
        //         .expDate("2304241215") // Thoi gian het han thanh toan Qr yyMMddHHmm
        //         .referenceID("01123456789AA")
        //         .build();
        //     bean.setAddtionalBean(addBean);
        //     QRPack pack = new QRPack();
        //     QRPackBean dataBean = pack.pack(bean, "");
        //     result = dataBean.getQrData();
        //
        // }

        updateQrPaymentStatus(notification) {
            if (notification && notification[0] && notification[0][1]) {
                for (var i = 0; i < notification.length; i++) {
                    var chanel_cal = notification[i]
                    if (chanel_cal[0] === 'pos_confirm_qr_payment_channel') {
                        if (chanel_cal[1]) {
                            var chanel_payment = chanel_cal[1]
                            var chanel_type = chanel_payment['type']
                            var chanel_amount = parseInt(chanel_payment['amount'])
                            var chanel_payment_state = chanel_payment['payment_state']
                            var chanel_request_id = chanel_payment['request_id']
                            var chanel_order_id = chanel_payment['order_id']

                            var dataQrOpenPopup = this.props.dataQrOpenPopup;
                            var qrAmountOrderCheck = dataQrOpenPopup.qrAmountOrder
                            var qrOrderIdCheck = dataQrOpenPopup.qrOrderId

                            if (chanel_type === 'qr_payment_status' && chanel_amount === qrAmountOrderCheck && chanel_order_id === qrOrderIdCheck) {
                                dataQrOpenPopup.qrPaymentStatus = '00';
                                console.log('dataQrOpenPopup', dataQrOpenPopup)
                                this.render();
                            }
                        }
                    }
                }
            }
        }

        async generateQRCode(data) {
            const qrCodeElement = document.querySelector('.qr-code-content-payment-waiting');
            qrCodeElement.innerHTML = '';

            const qr = new QRCode(qrCodeElement, {
                text: data,
                width: 200,
                height: 200,
                colorDark: "#000000",
                colorLight: "#ffffff",
                correctLevel: QRCode.CorrectLevel.H
            });
        }

        calculateCRC16(data) {
            var crc = 0xFFFF;
            var polynomial = 0x1021;

            for (var i = 0; i < data.length; i++) {
                crc ^= (data.charCodeAt(i) << 8);

                for (var j = 0; j < 8; j++) {
                    if ((crc & 0x8000) !== 0) {
                        crc = (crc << 1) ^ polynomial;
                    } else {
                        crc = crc << 1;
                    }
                }
            }

            return crc & 0xFFFF;
        }


        async checkPaymentQrPay(qrOrderId, QrAmount) {
            var checkQrPay = await this.rpc({
                model: 'pos.qr.payment',
                method: 'check_qr_payment_from_pos',
                args: [qrOrderId, QrAmount],
            }).catch(async error => {
                // self.deletePaymentLine({detail: {cid: self.selectedPaymentLine.cid}});
                console.error('Lỗi khi gọi RPC check_qr_payment_from_pos:', error);
            })
            return checkQrPay
        }

        async mounted() {
            // var dataQrCallBank = '000201010212262400069704890110031389131552045940530370454062200005802VN5916CTP CP VONG XANH6003HCM627101097558034230308VONGXANH05210124031818127558034230708VONGXANH08052436763045169'

            var dataQrOpenPopup = this.props.dataQrOpenPopup;
            var qrOrderId = dataQrOpenPopup.qrOrderId;
            var qrOrderName = dataQrOpenPopup.qrOderName;
            var QrAmount = dataQrOpenPopup.qrAmountOrder;
            var QrPayment = dataQrOpenPopup.qrNamePayment;

            var dataQrBankOpenPopup = dataQrOpenPopup.qrDataBank;
            var dataRequestId = dataQrOpenPopup.requestId;

            var dataQrBankCheckRequest = dataQrBankOpenPopup.requestId
            console.log('dataQrBankCheckRequest', dataQrBankCheckRequest)

            var crcValue = this.calculateCRC16(dataQrBankOpenPopup);
            var crcValueData = crcValue.toString(16).toUpperCase();

            var checkQrPayment = await this.checkPaymentQrPay(qrOrderId, QrAmount)
            if (checkQrPayment === '00') {
                dataQrOpenPopup.qrPaymentStatus = '00';
                this.render();
            } else {
                var dataQrCallBank = dataQrBankOpenPopup.qrData
                console.log('dataQrCallBank', dataQrCallBank)
                if (dataQrBankCheckRequest === dataRequestId) {
                    dataQrCallBank = dataQrBankOpenPopup.qrData
                }
                await this.generateQRCode(dataQrCallBank)
            }

            const qrDataTextOrderName = this.el.querySelector('.qr-data-order-id');
            if (qrDataTextOrderName) {
                qrDataTextOrderName.textContent = qrOrderId;
            } else {
                qrDataTextOrderName.textContent = 'No Order';
            }
            const qrDataTextAmount = this.el.querySelector('.qr-data-amount');
            if (qrDataTextAmount) {
                qrDataTextAmount.textContent = QrAmount;
            } else {
                qrDataTextAmount.textContent = 'No Amount';
            }
            const qrDataTextPaymentName = this.el.querySelector('.qr-data-transaction-code');
            if (qrDataTextPaymentName) {
                qrDataTextPaymentName.textContent = QrPayment;
            } else {
                qrDataTextAmount.textContent = 'No Transaction Code';
            }
            const qrDataTextTerminalCode = this.el.querySelector('.qr-data-terminal-code');
            if (qrDataTextTerminalCode) {
                qrDataTextTerminalCode.textContent = 'No Terminal Code';
            } else {
                qrDataTextTerminalCode.textContent = 'No Terminal Code';
            }
        }
    }

    QrPayPopupWidget.template = 'QrPayPopupWidget';
    QrPayPopupWidget.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        array: [],
        title: 'Qr Payment',
        body: '',
        startingValue: '',
        priceValue: 1,
        list: [],
    };

    Registries.Component.add(QrPayPopupWidget);

    return QrPayPopupWidget;
});