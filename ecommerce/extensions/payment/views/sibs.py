"""SIBS payment processing views."""
import logging

logger = logging.getLogger(__name__)


from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from oscar.apps.payment.exceptions import PaymentError
from oscar.core.loading import get_class, get_model

from ecommerce.extensions.basket.utils import basket_add_organization_attribute
from ecommerce.extensions.checkout.mixins import EdxOrderPlacementMixin
from ecommerce.extensions.checkout.utils import get_receipt_page_url
from ecommerce.extensions.payment.processors.sibs import SIBS

logger = logging.getLogger(__name__)

Applicator = get_class('offer.applicator', 'Applicator')
Basket = get_model('basket', 'Basket')
BillingAddress = get_model('order', 'BillingAddress')
Country = get_model('address', 'Country')
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

    def get(self, request):
        raise NotImplementedError

    def post(self, request):
        raise NotImplementedError


class SIBSPaymentExecutionView(EdxOrderPlacementMixin, View):
    """Execute an approved SIBS payment."""

    @property
    def payment_processor(self):
        return SIBS(self.request.site)

    def _get_basket(self, payment_id):
        raise NotImplementedError

    def get(self, request):
        """Handle an incoming user returned to us by SIBS, (sibs UI)"""
        raise NotImplementedError

    def post(self, request):
        """post"""
        raise NotImplementedError
