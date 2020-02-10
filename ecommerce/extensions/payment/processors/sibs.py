""" SIBS payment processing """


import logging
import requests
import json

from django.urls import reverse



from ecommerce.extensions.payment.processors import BasePaymentProcessor, HandledProcessorResponse

logger = logging.getLogger(__name__)


class SIBS(BasePaymentProcessor):
    """
    SIBS payment processor (February 2020)

    For reference, see
    https://sibs.docs.onlinepayments.pt/tutorials/integration-guide
    """

    NAME = 'sibs'

    def __init__(self, site):
        """
        Constructs a new instance of the SIBS processor.
        """
        super(SIBS, self).__init__(site)

        configuration = self.configuration
        self.payment_page_url = configuration['payment_page_url']
        self.bearer = configuration['bearer']
        self.entity_id = configuration['entity_id']
        self.test_mode = configuration['test_mode']
        self.shopperResultUrl = configuration['shopperResultUrl']

    def get_transaction_parameters(self, basket, request=None, use_client_side_checkout=False, **kwargs):
        """
        SIBS payment parameters
        """
        parameters = {
            'amount': str(basket.total_incl_tax),
            'currency': basket.currency,
            'paymentType': 'DB',
            'entityId': self.entity_id
        }
        response = self._prepare_checkout(parameters)
        parameters['payment_page_url'] = reverse('sibs:payment')
        parameters['shopperResultUrl'] = self.shopperResultUrl
        parameters['checkoutId'] = response['id']
        return parameters

    def handle_processor_response(self, response, basket=None):
        """
        Execute an approved SIBS payment
        """
        raise NotImplementedError

    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        raise NotImplementedError


    def _prepare_checkout(self, data):
        """
        Implement checkout, get id
        """
        response = requests.post('https://test.oppwa.com/v1/checkouts',
                                 headers={'Authorization': self.bearer},
                                 data=data).content
        return json.loads(response)
