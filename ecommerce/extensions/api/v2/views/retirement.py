"""
Endpoints to facilitate retirement actions
"""
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from social_django.models import UserSocialAuth
from user_util import user_util

from ecommerce.core.models import User
from ecommerce.extensions.analytics.utils import ECOM_TRACKING_ID_FMT


class EcommerceIdView(APIView):
    """
    Allows synchronization of the ecommerce user id and tracking id with
    other systems. Specifically this is used to retire users identified
    by "ecommerce-{id}" from Segment.

     Side effects:
        If the given user does not have an LMS user id, tries to find it. If found, adds the id to the user and
        saves the user. If the id cannot be found, writes custom metrics to record this fact.
    """
    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    def get(self, _, username):
        """
        Returns the old-style ecommerce tracking id (ecommerce-{id}) and the newer-style LMS user id of the given LMS
        user, identified by username.
        """
        try:
            if not username:
                raise User.DoesNotExist()

            user = User.objects.get(username=username)

            # If the user does not already have an LMS user id, add it. Note that we allow a missing LMS user id here
            # because this API only reads data from the db.
            called_from = u'retirement API'
            user.add_lms_user_id('ecommerce_missing_lms_user_id_retirement', called_from, allow_missing=True)

            return Response(
                {
                    'id': user.pk,
                    'ecommerce_tracking_id': ECOM_TRACKING_ID_FMT.format(user.pk),
                    'lms_user_id': user.lms_user_id_with_metric(usage='retirement API', allow_missing=True)
                }
            )
        except User.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={'message': 'Invalid user.'}
            )

class EcommerceUserRetireView(APIView):
    """
    Provides API endpoint for retiring a ecommerce's user.
    """
    authentication_classes = (JwtAuthentication,)
    permission_classes = (permissions.IsAuthenticated, permissions.IsAdminUser)

    def post(self, request):
        """
        POST /api/v2/user/retire/

        ```
        {
            'username': 'user_to_retire'
        }
        ```

        Retires the user with the given username.  This includes
        retiring this username, retiring the email address, and
        deleting the social_auth associated with the lms user.
        """
        try:
            username = request.data['username']
            if not username:
                raise User.DoesNotExist()

            user = User.objects.get(username=username)

            # Delete social_auth asssociated with the lms user 
            UserSocialAuth.objects.filter(uid=username).delete()

            # Generate retired email based on retirement settings 
            user.email = user_util.get_retired_email(user.email, settings.RETIRED_USER_SALTS, settings.RETIRED_EMAIL_FMT)
            user.username = user_util.get_retired_username(username, settings.RETIRED_USER_SALTS, settings.RETIRED_USERNAME_FMT)
            user.save()

            return Response(
                {
                    'id': user.pk,
                    'ecommerce_tracking_id': ECOM_TRACKING_ID_FMT.format(user.pk),
                }
            )
        except User.DoesNotExist:
            return Response(
                status=status.HTTP_404_NOT_FOUND,
                data={'message': 'User does not exist on ecommerce service.'}
            )
