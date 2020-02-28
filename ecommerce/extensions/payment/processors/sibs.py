""" SIBS payment processing """
import logging

import json
import requests

from django.urls import reverse
from oscar.apps.payment.exceptions import TransactionDeclined

from ecommerce.extensions.payment.processors import BasePaymentProcessor, HandledProcessorResponse

logger = logging.getLogger(__name__)


class SIBS(BasePaymentProcessor):
    """
    SIBS payment processor (February 2020)

    For reference, see
    https://sibs.docs.onlinepayments.pt/tutorials/integration-guide
    """

    NAME = 'sibs'
    TRANSACTION_ACCEPTED = '000.100.112'
    VALID_TEST_MODE = 'EXTERNAL'

    def __init__(self, site):
        """
        Constructs a new instance of the SIBS processor.
        """
        super(SIBS, self).__init__(site)

        configuration = self.configuration
        self.bearer = configuration['bearer']
        self.entity_id = configuration['entity_id']
        self.test_mode = configuration['test_mode']
        self.api_root_url = configuration['api_root_url']

    def get_transaction_parameters(self, basket, request=None, use_client_side_checkout=False, **kwargs):
        """
        SIBS payment parameters
        """
        parameters = {
            'amount': str(basket.total_incl_tax),
            'currency': basket.currency,
            'paymentType': 'DB',
            'entityId': self.entity_id,
            'customParameters[orderNumber]': basket.order_number
        }

        if self.test_mode:
            parameters['testMode'] = self.VALID_TEST_MODE
            parameters['customParameters[SIBS_ENV]'] = 'QLY'

        response = self._prepare_checkout(parameters)
        parameters['api_root_url'] = self.api_root_url
        parameters['payment_page_url'] = reverse('sibs:payment')
        parameters['shopperResultUrl'] = reverse('sibs:execute')
        parameters['checkoutId'] = response.get('id')
        return parameters

    def handle_processor_response(self, response, basket=None):
        """
        Handle a SIBS payment status.

        Arguments:
            response (dict): Dictionary of parameters received from the payment processor.

        Keyword Arguments:
            basket (Basket): Basket being purchased via the payment processor

        Raises:
            TransactionDeclined: Indicates the payment was declined by the processor.
        """
        payment_code_status = response.get('result', {}).get('code')
        if payment_code_status != self.TRANSACTION_ACCEPTED:
            raise TransactionDeclined

        transaction_id = response.get('id')
        total = basket.total_incl_tax
        currency = basket.currency
        card_number = response.get('card', {}).get('last4Digits')
        card_type = response.get('paymentBrand')
        return HandledProcessorResponse(
            transaction_id=transaction_id,
            total=total,
            currency=currency,
            card_number=card_number,
            card_type=card_type
        )

    def issue_credit(self, order_number, basket, reference_number, amount, currency):
        raise NotImplementedError

    def _prepare_checkout(self, data):
        """
        Perform a server-to-server POST request to prepare the checkout with the required data.
        """
        try:
            response = requests.post('{0}/v1/checkouts'.format(self.api_root_url),
                                     headers={'Authorization': self.bearer},
                                     data=data).content
        except requests.exceptions.RequestException as err:
            logger.error('Error preparing checkout [%s]', str(err))
        return json.loads(response)

    def get_payment_status(self, payment_url):
        """
        Obtain the payment status. No need to verify multiple times.
        """
        try:
            url = {
                'api_root_url': self.api_root_url,
                'payment_url': payment_url,
                'entity_id': self.entity_id
            }
            response = requests.get('{api_root_url}{payment_url}?entityId={entity_id}'.format(**url),
                                    headers={'Authorization': self.bearer}).content
        except requests.exceptions.RequestException as err:
            logger.error('Error preparing checkout [%s]', str(err))
        return json.loads(response)
