""" SIBS payment processing """


import logging
import requests


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

    def get_transaction_parameters(self, basket, request=None, use_client_side_checkout=False, **kwargs):
        """
        SIBS payment parameters
        """
        parameters = {
            'payment_page_url': self.payment_page_url,
            'amount': str(basket.total_incl_tax),
            'currency': basket.currency,
            'paymentType': 'DB',
            'entityId': self.entity_id
        }
        # response = self._server_side_checkout(**parameters)
        return parameters

    def handle_processor_response(self, response, basket=None):
        """
        Execute an approved SIBS payment
        """
        pass

    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        pass


    def _server_side_checkout(self, **kwargs):
        """
        Implement checkout, get id
        """
        pass
