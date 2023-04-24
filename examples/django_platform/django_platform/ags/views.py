from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from lti1p3platform.framework.django.request import DjangoRequest
from lti1p3platform.framework.django.response import wrap_json_resp

from .service_connector import AGS
from ..views import get_registered_platform
from ..helpers import get_url

allow_creating_lineitems = True
results_service_enabled = True
scores_service_enabled = True


def _get_service_connector(request):
    django_request = DjangoRequest(request)
    platform_config = get_registered_platform()

    service_connector = AGS(
        django_request,
        platform_config,
        get_url(reverse("ags-lineitems")),
        allow_creating_lineitems,
        results_service_enabled,
        scores_service_enabled,
    )

    return service_connector


class LineItemView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(LineItemView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        service_connector = _get_service_connector(request)
        resp = service_connector.handle_resp(
            service_connector.handle_get_lineitem, line_item_id=kwargs["lineitem_id"]
        )

        return wrap_json_resp(resp)

    def put(self, request, *args, **kwargs):
        service_connector = _get_service_connector(request)
        resp = service_connector.handle_resp(
            service_connector.handle_update_lineitem, line_item_id=kwargs["lineitem_id"]
        )

        return wrap_json_resp(resp)


class LineItemsView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(LineItemsView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        service_connector = _get_service_connector(request)

        resp = service_connector.handle_resp(service_connector.handle_get_lineitems)

        return wrap_json_resp(resp)

    def post(self, request, *args, **kwargs):
        service_connector = _get_service_connector(request)

        resp = service_connector.handle_resp(service_connector.handle_create_lineitem)

        return wrap_json_resp(resp)


def get_results(request, lineitem_id):
    service_connector = _get_service_connector(request)

    resp = service_connector.handle_resp(
        service_connector.handle_get_results, line_item_id=lineitem_id
    )

    return wrap_json_resp(resp)


@method_decorator(csrf_exempt)
def update_scores(request, lineitem_id):
    service_connector = _get_service_connector(request)

    resp = service_connector.handle_resp(
        service_connector.handle_update_score, line_item_id=lineitem_id
    )

    return wrap_json_resp(resp)
