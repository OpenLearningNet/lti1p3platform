# pylint: disable=arguments-differ
import os
import json
import typing as t
from uuid import uuid4

from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from lti1p3platform.framework.django.message_launch import DjangoLTI1P3MessageLaunch
from lti1p3platform.framework.django.oidc_login import DjangoAPIOIDCLogin
from lti1p3platform.framework.django.request import DjangoRequest
from lti1p3platform.ltiplatform import LTI1P3PlatformConfAbstract
from lti1p3platform.registration import Registration

from .helpers import get_url

USER_ID = "user_id"


class LTIPlatformConf(LTI1P3PlatformConfAbstract):
    def init_platform_config(self, platform_settings: t.Dict[str, t.Any]) -> None:
        """
        register platform configuration
        """
        registration = (
            Registration()
            .set_iss(platform_settings["iss"])
            .set_client_id(platform_settings["client_id"])
            .set_deployment_id(platform_settings["deployment_id"])
            .set_launch_url(platform_settings["launch_url"])
            .set_deeplink_launch_url(platform_settings["deeplink_launch_url"])
            .set_oidc_login_url(platform_settings["oidc_login_url"])
            .set_tool_key_set_url(platform_settings["key_set_url"])
            .set_platform_public_key(platform_settings["public_key"])
            .set_platform_private_key(platform_settings["private_key"])
        )

        self._registration = registration

    def get_registration_by_params(self, **kwargs: t.Any) -> Registration:
        return self._registration


class OIDCLogin(DjangoAPIOIDCLogin):
    def set_lti_message_hint(self, lti_message_hint: str) -> "OIDCLogin":
        self._lti_message_hint = lti_message_hint

        return self


def get_registered_platform() -> LTIPlatformConf:
    """
    get registered platform
    """
    config_file = os.path.join(settings.BASE_DIR, "..", "configs", "platform.json")
    configs_dir = os.path.dirname(config_file)
    private_key_file = None
    public_key_file = None

    with open(config_file, encoding="utf-8") as cfg:
        config = json.load(cfg)

        private_key_file = configs_dir + "/" + config.get("private_key_file")
        public_key_file = configs_dir + "/" + config.get("public_key_file")

    if private_key_file:
        with open(private_key_file, encoding="utf-8") as key_file:
            config["private_key"] = key_file.read()

    if public_key_file:
        with open(public_key_file, encoding="utf-8") as key_file:
            config["public_key"] = key_file.read()

    return LTIPlatformConf(platform_settings=config)


def preflight_lti_1p3_launch(request):
    platform = get_registered_platform()
    oidc_login = OIDCLogin(DjangoRequest(request), platform)
    oidc_login.set_lti_message_hint(lti_message_hint=str(uuid4()))

    return oidc_login.initiate_login(USER_ID)


def authorization(request):
    platform = get_registered_platform()
    launch_req = DjangoLTI1P3MessageLaunch(DjangoRequest(request), platform)
    launch_req.set_ags(get_url(reverse("ags-lineitems")), None, True, True, True)
    launch_req.set_user_data(
        USER_ID,
        ["http://purl.imsglobal.org/vocab/lis/v2/system/person#User"],
        full_name="John Doe",
        email_address="john@example.com",
    )
    launch_req.set_resource_link_claim(
        resource_link_id="resource_link_id",
    )

    return launch_req.lti_launch()


@csrf_exempt
def access_token(request):
    platform = get_registered_platform()
    token_data = request.POST.dict()

    return JsonResponse(platform.get_access_token(token_data))


# pylint: disable=unused-argument
def get_jwks(request):
    platform = get_registered_platform()

    return JsonResponse(platform.get_jwks())
