"""SIBS payment processing views."""
import logging

logger = logging.getLogger(__name__)


from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
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


class SIBSPaymentExecutionView(EdxOrderPlacementMixin, View):
    """Execute an approved SIBS payment."""

    @property
    def payment_processor(self):
        return SIBS(self.request.site)

    def _get_basket(self, payment_id):
        pass

    def get(self, request):
        """Handle an incoming user returned to us by SIBS, (sibs UI)"""
        pass

    def post(self, request):
        """post"""
        pass
