from django.urls import reverse
from lti1p3platform.framework.django.request import DjangoRequest
from lti1p3platform.framework.django.response import wrap_json_resp
from .service_connector import NRPS
from ..views import get_registered_platform
from ..helpers import get_url


def _get_service_connector(request, context_id) -> NRPS:
    django_request = DjangoRequest(request)
    platform_config = get_registered_platform()

    service_connector = NRPS(
        django_request,
        platform_config,
        get_url(reverse("nrps", kwargs={"context_id": context_id})),
    )

    return service_connector


def get_membership(request, context_id):
    service_connector = _get_service_connector(request, context_id)

    resp = service_connector.handle_resp(service_connector.handle_get_members)

    return wrap_json_resp(resp)
