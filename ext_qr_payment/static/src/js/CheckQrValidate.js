odoo.define('ext_qr_payment.CheckQrValidate', function (require) {

    var models = require('point_of_sale.models');
    var PosModelSuper = models.PosModel;
    const rpc = require('web.rpc');


    models.PosModel = models.PosModel.extend({
        validateOrder: function (isForceValidate) {

            var self = this;
            var paymentLines = self.paymentLines
            var order = this.env.pos.get_order();
            self.env.pos.config['check_qr_state'] = false;
            for (let line of paymentLines) {
                console.log('line', line)
                var pyment_check = rpc.query({
                    model: 'pos.payment.method',
                    method: 'search_read',
                    domain: [['id', '=', line.payment_method.id], ['is_qr_count', '=', true]],
                    fields: ['name'],
                }).then(async function (check) {
                    if (check && check.length > 0) {
                        console.log('check_qr_statesssss')
                         self.env.pos.config.check_qr_state = true;
                    }
                })
            }
            console.log('check_qr_s111111111111', self.env.pos.config.check_qr_state)
            if (self.env.pos.config.check_qr_state) {
                console.log('check_qr_state', self.env.pos.config.check_qr_state)
                PosModelSuper.prototype.validateOrder.apply(self, arguments);
            } else {
                self.showPopup('ErrorPopup', {
                    title: self.env._t('Custom Condition Error'),
                    body: self.env._t('Your custom condition is not met. Unable to validate the order.'),
                });
                self.currentOrder.rollback();
            }

        },
    });
});

