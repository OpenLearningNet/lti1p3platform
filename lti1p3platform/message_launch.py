from __future__ import annotations

import typing as t

from abc import ABC, abstractmethod
from typing_extensions import TypedDict

from .constants import LTI_BASE_MESSAGE
from .deep_linking import LtiDeepLinking
from .ags import LtiAgs
from .nrps import LtiNrps
from .request import Request
from . import exceptions

if t.TYPE_CHECKING:
    from .registration import Registration
    from .ltiplatform import LTI1P3PlatformConfAbstract


class LaunchData(TypedDict):
    id_token: str
    state: str


# pylint: disable=too-many-instance-attributes
class MessageLaunchAbstract(ABC):
    _request = None
    _registration: t.Optional[Registration] = None

    def __init__(
        self, request: Request, platform_config: LTI1P3PlatformConfAbstract
    ) -> None:
        self._request = request
        self._platform_config = platform_config
        self._launch_url: t.Optional[str] = None

        # IMS LTI Claim data
        self.lti_claim_user_data: t.Optional[t.Dict[str, t.Any]] = None
        self.lti_claim_resource_link: t.Optional[t.Dict[str, t.Any]] = None
        self.lti_claim_launch_presentation: t.Optional[t.Dict[str, t.Any]] = None
        self.lti_claim_context: t.Optional[t.Dict[str, t.Any]] = None
        self.lti_claim_custom_parameters: t.Optional[t.Dict[str, t.Any]] = None

        # Extra claims - used by LTI Advantage
        self.extra_claims: t.Dict[str, t.Any] = {}

        self.id_token_expiration = 5 * 60

    def get_preflight_response(self) -> t.Dict[str, t.Any]:
        assert self._request is not None
        # pylint: disable=protected-access
        return self._request.get_data or self._request.form_data

    def prepare_launch(self, preflight_response: t.Dict[str, t.Any]) -> None:
        pass

    # pylint: disable=too-many-arguments
    def set_user_data(
        self,
        user_id: str,
        lis_roles: t.List[str],
        full_name: t.Optional[str] = None,
        email_address: t.Optional[str] = None,
        preferred_username: t.Optional[str] = None,
    ) -> None:
        """
        Set user data/roles and convert to IMS Specification

        User Claim doc: http://www.imsglobal.org/spec/lti/v1p3/#user-identity-claims
        Roles Claim doc: http://www.imsglobal.org/spec/lti/v1p3/#roles-claim
        """
        self.lti_claim_user_data = {
            # User identity claims
            # sub: locally stable identifier for user that initiated the launch
            "sub": user_id,
            # Roles claim
            # Array of URI values for roles that the user has within the message's context
            "https://purl.imsglobal.org/spec/lti/claim/roles": lis_roles,
        }

        # Additonal user identity claims
        # Optional user data that can be sent to the tool, if the block is configured to do so
        if full_name:
            self.lti_claim_user_data.update(
                {
                    "name": full_name,
                }
            )

        if email_address:
            self.lti_claim_user_data.update(
                {
                    "email": email_address,
                }
            )

        if preferred_username:
            self.lti_claim_user_data.update(
                {
                    "preferred_username": preferred_username,
                }
            )

    def set_resource_link_claim(
        self,
        resource_link_id: str,
        description: t.Optional[str] = None,
        title: t.Optional[str] = None,
    ) -> None:
        """
        Set resource_link claim. The resource link must be stable and
        unique to each deployment_id. This value MUST
        change if the link is copied or exported from one system or
        context and imported into another system or context

        https://www.imsglobal.org/spec/lti/v1p3#resource-link-claim

        Arguments:
        * id (string): opaque, unique value identifying the placement of an LTI resource link
        * description (string): description for the placement of an LTI resource link
        * title (string): title for the placement of an LTI resource link
        """
        resource_link_claim_data = {
            "id": resource_link_id,
        }

        if description:
            resource_link_claim_data["description"] = description

        if title:
            resource_link_claim_data["title"] = title

        self.lti_claim_resource_link = {
            "https://purl.imsglobal.org/spec/lti/claim/resource_link": resource_link_claim_data
        }

    def set_launch_presentation_claim(
        self,
        document_target: t.Optional[str] = None,
        return_url: t.Optional[str] = None,
    ) -> None:
        """
        Optional: Set launch presentation claims

        http://www.imsglobal.org/spec/lti/v1p3/#launch-presentation-claim
        """
        if document_target is not None and document_target not in [
            "iframe",
            "frame",
            "window",
        ]:
            raise ValueError("Invalid launch presentation format.")

        lti_claim_launch_presentation = {}

        if document_target:
            lti_claim_launch_presentation.update({"document_target": document_target})

        if return_url:
            lti_claim_launch_presentation.update({"return_url": return_url})

        self.lti_claim_launch_presentation = {
            "https://purl.imsglobal.org/spec/lti/claim/launch_presentation": lti_claim_launch_presentation,  # pylint: disable=line-too-long
        }

    def set_launch_context_claim(
        self,
        context_id: str,
        context_types: t.Optional[t.List[str]] = None,
        context_title: t.Optional[str] = None,
        context_label: t.Optional[str] = None,
    ) -> None:
        """
        Optional: Set context claims

        https://www.imsglobal.org/spec/lti/v1p3/#context-claim

        Arguments:
            context_id (string):  Unique value identifying the user
            context_types (list):  A list of context type values for the claim
            context_title (string):  Plain text title of the context
            context_label (string):  Plain text label for the context
        """
        # Set basic claim data
        context_claim_data: t.Dict[str, t.Union[str, t.List[str]]] = {
            "id": context_id,
        }

        # Default context_types to a list if nothing is passed in
        context_types = context_types or []

        # Ensure the value of context_types is a list
        if not isinstance(context_types, list):
            raise TypeError("Invalid type for context_types. It must be a list.")

        if context_types:
            context_claim_data["type"] = context_types

        if context_title:
            context_claim_data["title"] = context_title

        if context_label:
            context_claim_data["label"] = context_label

        self.lti_claim_context = {
            # Context claim
            "https://purl.imsglobal.org/spec/lti/claim/context": context_claim_data
        }

    def set_custom_parameters_claim(
        self, custom_parameters: t.Dict[str, t.Any]
    ) -> None:
        """
        Stores custom parameters configured for LTI launch
        """
        if not isinstance(custom_parameters, t.Dict):
            raise ValueError("Custom parameters must be a key/value t.Dictionary.")

        self.lti_claim_custom_parameters = {
            "https://purl.imsglobal.org/spec/lti/claim/custom": custom_parameters
        }

    def set_launch_url(self, launch_url: str) -> MessageLaunchAbstract:
        self._launch_url = launch_url

        return self

    def set_id_token_expiration(
        self, id_token_expiration: int
    ) -> MessageLaunchAbstract:
        self.id_token_expiration = id_token_expiration

        return self

    def get_launch_url(self) -> t.Optional[str]:
        assert self._registration

        if not self._launch_url:
            self._launch_url = self._registration.get_launch_url()

        return self._launch_url

    def get_launch_message(
        self, include_extra_claims: bool = True
    ) -> t.Dict[str, t.Any]:
        assert self._registration

        launch_message: t.Dict[str, t.Any] = LTI_BASE_MESSAGE.copy()

        # Add base parameters
        launch_message.update(
            {
                # Issuer
                "iss": self._registration.get_iss(),
                # JWT aud and azp
                "aud": self._registration.get_client_id(),
                "azp": self._registration.get_client_id(),
                # LTI Deployment ID Claim:
                # String that identifies the platform-tool integration governing the message
                "https://purl.imsglobal.org/spec/lti/claim/deployment_id": self._registration.get_deployment_id(),  # pylint: disable=line-too-long
                # Target Link URI: actual endpoint for the LTI resource to display
                # MUST be the same value as the target_link_uri passed by the platform
                # in the OIDC login request
                # http://www.imsglobal.org/spec/lti/v1p3/#target-link-uri
                "https://purl.imsglobal.org/spec/lti/claim/target_link_uri": self.get_launch_url(),
            }
        )

        if include_extra_claims:
            if self.lti_claim_context:
                launch_message.update(self.lti_claim_context)

            if self.lti_claim_resource_link:
                launch_message.update(self.lti_claim_resource_link)

            if self.lti_claim_launch_presentation:
                launch_message.update(self.lti_claim_launch_presentation)

            if self.lti_claim_custom_parameters:
                launch_message.update(self.lti_claim_custom_parameters)

            if self.lti_claim_user_data:
                launch_message.update(self.lti_claim_user_data)

            if self.extra_claims:
                launch_message.update(self.extra_claims)

        return launch_message

    def set_extra_claims(self, extra_claims: t.Dict[str, t.Any]) -> None:
        self.extra_claims.update(extra_claims)

    def validate_preflight_response(
        self, preflight_response: t.Dict[str, t.Any]
    ) -> None:
        """
        Validates a preflight response to be used in a launch request

        Raises ValueError in case of validation failure

        :param response: the preflight response to be validated
        """
        assert self._registration

        try:
            assert preflight_response.get("nonce")
            assert preflight_response.get("state")
            assert preflight_response.get("redirect_uri")
            assert (
                preflight_response.get("client_id")
                == self._registration.get_client_id()
            )
        except AssertionError as err:
            raise exceptions.PreflightRequestValidationException from err

    def get_launch_data(self) -> t.Tuple[t.Dict[str, t.Any], str]:
        preflight_response = self.get_preflight_response()

        # get launch message
        launch_message = self.get_launch_message()

        # Nonce from OIDC preflight launch request
        launch_message.update({"nonce": preflight_response["nonce"]})

        state = preflight_response.get("state", "")

        return launch_message, state

    def generate_launch_request(self) -> LaunchData:
        """
        Build LTI 1.3 launch request
        """
        launch_message, state = self.get_launch_data()

        assert self._registration

        # sign launch message with private key
        id_token = self._registration.platform_encode_and_sign(
            launch_message, expiration=self.id_token_expiration
        )  # pylint: disable=line-too-long

        return {"state": state, "id_token": id_token}

    @abstractmethod
    def render_launch_form(
        self, launch_data: t.Dict[str, t.Any], **kwargs: t.Any
    ) -> t.Any:
        raise NotImplementedError

    def lti_launch(self, **kwargs: t.Any) -> t.Any:
        # This should render a form, and then submit it to the tool's launch URL, as
        # described in http://www.imsglobal.org/spec/lti/v1p3/#lti-message-general-details

        self._registration = self._platform_config.get_registration()

        preflight_response = self.get_preflight_response()

        # validate preflight request response from tool
        self.validate_preflight_response(preflight_response)

        self.prepare_launch(preflight_response)

        launch_data = self.generate_launch_request()

        launch_data_copy = dict(launch_data)
        launch_data_copy.update({"launch_url": self.get_launch_url()})

        return self.render_launch_form(launch_data_copy, **kwargs)


class LTIAdvantageMessageLaunchAbstract(MessageLaunchAbstract):
    _dl = None  # deep linking service
    _nrps = None  # Names and Role Provisioning Service
    _ags = None  # Assignments and Grades services
    _nrps = None  # Names and Role Provisioning Service
    _deep_linking_launch_data = None

    # pylint: disable=too-many-arguments
    def set_dl(
        self,
        deep_link_return_url: str,
        title: str = "",
        description: str = "",
        accept_types: t.Optional[t.Set[str]] = None,
        extra_data: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> LTIAdvantageMessageLaunchAbstract:
        self._dl = LtiDeepLinking(deep_link_return_url)
        self._deep_linking_launch_data = self._dl.get_lti_deep_linking_launch_claim(
            title, description, accept_types, extra_data
        )

        return self

    # pylint: disable=too-many-arguments
    def set_ags(
        self,
        lineitems_url: str,
        lineitem_url: t.Optional[str] = None,
        allow_creating_lineitems: bool = True,
        results_service_enabled: bool = True,
        scores_service_enabled: bool = True,
    ) -> LTIAdvantageMessageLaunchAbstract:
        self._ags = LtiAgs(
            lineitems_url,
            lineitem_url,
            allow_creating_lineitems,
            results_service_enabled,
            scores_service_enabled,
        )

        # Include LTI AGS claim inside the LTI Launch message
        self.set_extra_claims(self._ags.get_lti_ags_launch_claim())

        return self

    def set_nrps(
        self, context_memberships_url: str
    ) -> LTIAdvantageMessageLaunchAbstract:
        self._nrps = LtiNrps(context_memberships_url)

        self.set_extra_claims(self._nrps.get_lti_nrps_launch_claim())

        return self

    def generate_launch_request(self) -> LaunchData:
        assert self._registration, "Registration is required"

        deep_linking_launch_url = self._registration.get_deeplink_launch_url()

        if self._dl and deep_linking_launch_url:
            self.set_launch_url(deep_linking_launch_url)

            launch_message, state = self.get_launch_data()
            # Update message type to LtiDeepLinkingRequest,
            # replacing the normal launch request.
            launch_message.update(
                {
                    "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingRequest",  # pylint: disable=line-too-long
                }
            )

            if self._deep_linking_launch_data:
                launch_message.update(self._deep_linking_launch_data)

            return {
                "state": state,
                "id_token": self._registration.platform_encode_and_sign(
                    launch_message, expiration=self.id_token_expiration
                ),  # pylint: disable=line-too-long
            }

        return super().generate_launch_request()
