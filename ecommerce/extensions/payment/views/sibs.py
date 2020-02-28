"""SIBS payment processing views."""
import logging
import json

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from oscar.apps.partner import strategy
from oscar.apps.payment.exceptions import TransactionDeclined
from oscar.core.loading import get_class, get_model

from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.processors.sibs import SIBS

logger = logging.getLogger(__name__)

Applicator = get_class('offer.applicator', 'Applicator')
Basket = get_model('basket', 'Basket')
NoShippingRequired = get_class('shipping.methods', 'NoShippingRequired')
OrderNumberGenerator = get_class('order.utils', 'OrderNumberGenerator')
OrderTotalCalculator = get_class('checkout.calculators', 'OrderTotalCalculator')


class SIBSView(LoginRequiredMixin, View):

    # Disable CSRF validation. The internal POST requests to render this view
    # don't include the CSRF token as hosted-side payment processor are
    # excepted to be externally hosted, but this is not the case.
    # Instead of changing the checkout flow for all the payment processors
    # this view is marked as exempt.
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SIBSView, self).dispatch(request, *args, **kwargs)

    def post(self, request):
        """Create the payment form."""
        url = '{api_root_url}/v1/paymentWidgets.js?checkoutId={checkoutId}'.format(
            api_root_url=request.POST['api_root_url'],
            checkoutId=request.POST['checkoutId']
        )
        try:
            context = {
                'locale': request.LANGUAGE_CODE,
                'url': url,
                'shopperResultUrl': request.POST['shopperResultUrl']
            }
        except Exception as err:  # pylint: disable=broad-except
            logger.error('SIBS failed with error [%s]', str(err))
        return render(request, 'payment/sibs.html', context)


class SIBSPaymentExecutionView(EdxOrderPlacementMixin, View):
    """Execute an approved SIBS payment."""

    @property
    def payment_processor(self):
        return SIBS(self.request.site)

    def _get_basket(self, basket_id):
        """Return basket object from the basket_id."""
        if not basket_id:
            return None

        try:
            basket_id = int(basket_id)
            basket = Basket.objects.get(id=basket_id)
            basket.strategy = strategy.Default()
            Applicator().apply(basket, basket.owner, self.request)
            return basket
        except (ValueError, ObjectDoesNotExist):
            return None

    def get(self, request):
        """Handle the order and SIBS status."""
        sibs_status = self.payment_processor.get_payment_status(request.GET['resourcePath'])
        basket = None

        try:
            transaction_id = sibs_status.get('id')
            order_number = sibs_status.get('customParameters', {}).get('orderNumber')
            basket_id = OrderNumberGenerator().basket_id(order_number)
            basket = self._get_basket(basket_id)
            logger.info(
                'Received SIBS payment status for transaction [%s], associated with basket [%d].',
                transaction_id,
                basket_id
            )
        finally:
            ppr = self.payment_processor.record_processor_response(
                json.dumps(sibs_status),
                transaction_id=transaction_id,
                basket=basket
            )

        try:
            self.handle_payment(sibs_status, basket)
            receipt_url = get_receipt_page_url(
                order_number=order_number,
                site_configuration=basket.site.siteconfiguration
            )
        except TransactionDeclined:
            logger.exception(
                'Received an invalid SIBS response. The payment response [%d].',
                ppr.id
            )
            return redirect(reverse('payment_error'))

        try:
            shipping_method = NoShippingRequired()
            shipping_charge = shipping_method.calculate(basket)
            user = basket.owner
            order_total = OrderTotalCalculator().calculate(basket, shipping_charge)
            billing_address = None
            self.handle_order_placement(
                order_number,
                user,
                basket,
                None,
                shipping_method,
                shipping_charge,
                billing_address,
                order_total,
                request=request
            )
        except:  # pylint: disable=bare-except
            payment_processor = self.payment_processor.NAME.title() if self.payment_processor else None
            logger.exception(self.order_placement_failure_msg, payment_processor, basket.id)
        return redirect(receipt_url)
