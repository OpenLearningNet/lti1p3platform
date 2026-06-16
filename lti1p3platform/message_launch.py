from __future__ import annotations

import typing as t
from urllib.parse import urlencode, urlparse

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


# pylint: disable=too-many-instance-attributes,too-many-public-methods
class MessageLaunchAbstract(ABC):
    """
    Abstract base class for LTI 1.3 Message Launch handling

    LTI 1.3 Launch Process (end-to-end):
    1. User clicks "launch tool" in platform
    2. Platform redirects browser to tool's OIDC login endpoint
    3. Tool validates login initiation request and redirects to platform auth endpoint
    4. Platform validates authorization request and prepares OIDC response
    5. Platform authenticates user if needed
    6. Platform sends POST with id_token + state to tool's launch_url
    7. Tool validates JWT signature and claims
    8. Tool displays interface with user's context

    This class handles:
    - Step 5 via an authentication hook implemented by the platform layer
    - Step 6 on the platform side (build and POST id_token + state)
    - Receiving and parsing launch requests
    - Validating JWT signatures and claims
    - Extracting LTI claims (user roles, resource context, etc.)
    - Building response data
    - Interfacing with LTI Advantage services (AGS, NRPS)

    Message Contents:
    The id_token JWT contains many claims about the launch context:
    - User identity: sub (subject/user ID), email, name, roles
    - Resource: resource_link (content being launched)
    - Context: context (course/organization info)
    - Custom parameters: Custom data platform passes to tool
        - Roles: User roles (e.g.,
            'http://purl.imsglobal.org/vocab/lis/v2/institution/person#Instructor')

    HTTPS Requirement:
    - All Platform/Tool URLs must use HTTPS for production
    - Except localhost (127.0.0.1, ::1) allowed for development
    - Prevents man-in-the-middle attacks on tokens

    Reference:
    - LTI 1.3 Resource Link Request: https://www.imsglobal.org/spec/lti/v1p3/#resource-link-request
    - LTI Deep Link Launch: https://www.imsglobal.org/spec/lti-dl/v2p0/#lifecycle
    """

    _request = None
    _registration: t.Optional[Registration] = None

    def __init__(
        self, request: Request, platform_config: LTI1P3PlatformConfAbstract
    ) -> None:
        self._request = request
        self._platform_config = platform_config
        self._launch_url: t.Optional[str] = None
        self._redirect_url: t.Optional[str] = None

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
        if self._request is None:
            raise exceptions.PlatformNotReadyException("Request context not available")
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
        Set user data/roles and convert to IMS LTI 1.3 Standard Claims

        LTI 1.3 User Claims:
        The platform includes these claims in the LTI launch JWT to tell the tool
        about the user launching the tool.

        User Identity Claims:
        - sub: Locally stable opaque user identifier
          * Does NOT need to be user's actual username
          * Must be stable (same user always gets same sub value)
          * Example: "user-123" (platform-specific ID)
          * Tool uses this to correlate requests from same user

        Roles Claim:
        - https://purl.imsglobal.org/spec/lti/claim/roles
        - Array of URIs representing user's roles in the context
        - Role examples:
          * http://purl.imsglobal.org/vocab/lis/v2/institution/person#Instructor
          * http://purl.imsglobal.org/vocab/lis/v2/institution/person#Student
          * http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator
        - Tool uses roles to determine what user can do (e.g., grading UI for instructors only)

        Optional Identity Claims:
        - name: Full name of the user
        - email: Email address (if available and privacy rules allow)
        - preferred_username: Username if appropriate

        Privacy Considerations:
        - Platform should only include claims that:
          1. User has agreed to share
          2. Tool legitimately needs to function
          3. Comply with institutional privacy policies
        - PII (Personally Identifiable Information) should be minimal and necessary

        Usage by Tool:
        1. Tool receives JWT with these claims
        2. Tool validates JWT signature (verify platform signed it)
        3. Tool extracts user claims to identify user
        4. Tool can check roles to enable/disable features
        5. Tool registers/creates user account if first time

        Reference (User Identity Claims):
        - https://www.imsglobal.org/spec/lti/v1p3/#user-identity-claims
        - https://www.imsglobal.org/spec/lti/v1p3/#roles-claim
        - https://www.imsglobal.org/spec/lti/v1p3/#core-recommended-claims

        Parameters:
            user_id: Unique, stable user identifier (sub claim)
            lis_roles: List of role URIs from IMS LIS vocabulary
            full_name: User's full name (optional)
            email_address: User's email address (optional, privacy-sensitive)
            preferred_username: User's preferred username (optional)
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
        if self._registration is None:
            raise exceptions.PlatformNotReadyException("Registration not yet set")

        if not self._launch_url:
            self._launch_url = self._registration.get_launch_url()

        return self._launch_url

    def get_launch_message(
        self, include_extra_claims: bool = True
    ) -> t.Dict[str, t.Any]:
        if self._registration is None:
            raise exceptions.PlatformNotReadyException("Registration not yet set")

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
        Validate LTI launch preflight response from platform's authorization endpoint

        OpenID Connect Authorization Endpoint Response:
        When the platform's OIDC authorization endpoint processes the login request,
        it returns parameters that the tool must validate before granting access.

        Validation Checks:
        ==================

        1. response_type = "id_token"
           - OIDC Implicit Flow: Request JWT token directly, no authorization code exchange
           - Alternative flows use "code" (Authorization Code Flow)
           - LTI 1.3 uses "id_token" response type

        2. scope = "openid"
           - OIDC scope indicating OpenID Connect authentication
           - (Not the same as OAuth 2.0 scope for API permissions)
           - Tell authorization server we want OIDC identity token

        3. nonce present and valid
           - Random value generated by tool before redirect to platform
           - Platform must include exact same nonce in response
           - Prevents authorization code/token interception attacks
           - Replay attack protection (See OIDC spec)
           - Example: Tool generates nonce='abc123', validates response has nonce='abc123'

        4. state present and valid
           - Random value generated by tool before redirect to platform
           - Platform must include exact same state in response
           - Prevents Cross-Site Request Forgery (CSRF) attacks
           - Example attack prevented: Attacker tricks user into visiting evil.com which
             sends them to wrong authorization endpoint, tries to get them logged in there

        5. redirect_uri validation
           - Must match one of tool's pre-registered redirect URIs
           - HTTPS REQUIRED in production
           - Prevents open redirect attacks
           - Ensures response goes only to legitimate tool endpoint
           - Allows http://localhost for local development
           - Allows http://127.0.0.1 for local development
           - Allows http://::1 for local IPv6 localhost development

        6. client_id validation
           - Must match tool's registered client_id at platform
           - Ensures response is for correct tool instance

        HTTPS Requirement (Production Security):
        =========================================
        - All redirect_uri values must use HTTPS
        - Prevents man-in-the-middle attacks
        - Attackers cannot intercept tokens in transit
        - Exceptions: localhost addresses for development/testing

        Token Flow After Validation:
        =============================
        After these validations pass, the tool will:
        1. Extract id_token from response parameters
        2. Validate JWT signature (verify platform signed it)
        3. Verify all claims in id_token
        4. Extract user/context information from claims
        5. Grant access to user

        Security Considerations:
        ========================
        - Validate AGAINST a whitelist of known-good values
        - Never trust input parameters directly
        - HTTPS encryption prevents token interception
        - JWT signature proves platform created this response

        Reference:
        - OIDC Implicit Flow: https://openid.net/specs/openid-connect-core-1_0.html#ImplicitFlow
        - OIDC Nonce: https://openid.net/specs/openid-connect-core-1_0.html#NonceNotes
        - OAuth 2.0 CSRF: https://tools.ietf.org/html/rfc6749#section-10.12
                - LTI 1.3 Preflight Response Validation:  # pylint: disable=line-too-long
                    https://www.imsglobal.org/spec/lti/v1p3/#authorization

        Parameters:
            preflight_response: Dict with response parameters from authorization endpoint

        Raises:
            InvalidRequestData: If required parameters are missing
            UnauthorizedClient: If client_id is unknown
            UnsupportedResponseType: If response_type is invalid
            InvalidScopeException: If scope is invalid
            InvalidRequestUri: If redirect_uri is invalid
        """
        if self._registration is None:
            raise exceptions.PlatformNotReadyException("Registration not yet set")

        required_params = [
            "client_id",
            "response_type",
            "scope",
            "nonce",
            "state",
            "redirect_uri",
        ]
        missing_params = [
            param for param in required_params if not preflight_response.get(param)
        ]
        if missing_params:
            raise exceptions.InvalidRequestData(
                f"Missing required parameters: {', '.join(missing_params)}"
            )

        if preflight_response.get("client_id") != self._registration.get_client_id():
            raise exceptions.UnauthorizedClient(
                "Invalid client_id in preflight response"
            )

        if preflight_response.get("response_type") != "id_token":
            raise exceptions.UnsupportedResponseType(
                "Invalid response_type: expected 'id_token'"
            )

        if preflight_response.get("scope") != "openid":
            raise exceptions.InvalidScopeException("Invalid scope: expected 'openid'")

        redirect_uri = preflight_response.get("redirect_uri")
        registered_redirect_uris = self._registration.get_tool_redirect_uris()
        if not registered_redirect_uris or redirect_uri not in registered_redirect_uris:
            raise exceptions.InvalidRequestUri(
                f"redirect_uri '{redirect_uri}' not registered for this tool"
            )

        parsed_redirect_uri = urlparse(redirect_uri)
        if parsed_redirect_uri.scheme != "https":
            is_allowed_loopback = (
                parsed_redirect_uri.scheme == "http"
                and parsed_redirect_uri.hostname in {"localhost", "127.0.0.1", "::1"}
            )
            if not is_allowed_loopback:
                raise exceptions.InvalidRequestUri(
                    "redirect_uri must use HTTPS (except localhost for development)"
                )

        self._redirect_url = redirect_uri

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

        if self._registration is None:
            raise exceptions.PlatformNotReadyException("Registration not yet set")

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

    @abstractmethod
    def get_redirect(self, url: str) -> t.Any:
        raise NotImplementedError

    @abstractmethod
    def render_error_page(self, message: str, status_code: int) -> t.Any:
        raise NotImplementedError

    def build_error_redirect_url(
        self,
        redirect_uri: str,
        error: Exception,
        state: t.Optional[str] = None,
    ) -> str:
        params = {
            "error": exceptions.get_error_code(error),
            "error_description": str(error),
        }
        if state:
            params["state"] = state

        separator = "&" if urlparse(redirect_uri).query else "?"
        return f"{redirect_uri}{separator}{urlencode(params)}"

    def get_error_response(
        self,
        error: Exception,
        redirect_uri: t.Optional[str] = None,
        state: t.Optional[str] = None,
    ) -> t.Any:
        if redirect_uri and exceptions.get_error_response_behavior(error) == "redirect":
            return self.get_redirect(
                self.build_error_redirect_url(redirect_uri, error, state)
            )

        return self.render_error_page(
            str(error),
            exceptions.get_error_page_status_code(error),
        )

    def lti_launch(self, **kwargs: t.Any) -> t.Any:
        # This should render a form, and then submit it to the tool's launch URL, as
        # described in http://www.imsglobal.org/spec/lti/v1p3/#lti-message-general-details

        self._registration = self._platform_config.get_registration()
        preflight_response: t.Dict[str, t.Any] = {}

        try:
            preflight_response = self.get_preflight_response()

            # validate preflight request response from tool
            self.validate_preflight_response(preflight_response)

            self.prepare_launch(preflight_response)

            launch_data = self.generate_launch_request()

            launch_data_copy = dict(launch_data)
            launch_data_copy.update({"launch_url": self._redirect_url})

            return self.render_launch_form(launch_data_copy, **kwargs)
        except Exception as err:  # pylint: disable=broad-exception-caught
            redirect_uri = preflight_response.get("redirect_uri")
            state = preflight_response.get("state")
            return self.get_error_response(err, redirect_uri=redirect_uri, state=state)


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
        accept_multiple: bool = False,
        auto_create: bool = True,
        accept_types: t.Optional[t.Set[str]] = None,
        extra_data: t.Optional[t.Dict[str, t.Any]] = None,
        accept_presentation_document_targets: t.Optional[t.Set[str]] = None,
    ) -> LTIAdvantageMessageLaunchAbstract:
        self._dl = LtiDeepLinking(deep_link_return_url)
        self._deep_linking_launch_data = self._dl.get_lti_deep_linking_launch_claim(
            title,
            description,
            accept_multiple,
            auto_create,
            accept_types,
            extra_data,
            accept_presentation_document_targets,
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
        if self._registration is None:
            raise exceptions.PlatformNotReadyException("Registration is required")

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
