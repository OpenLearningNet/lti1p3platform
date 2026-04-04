from __future__ import annotations

import typing as t

from urllib.parse import urlencode, urlparse, parse_qsl
from abc import ABC, abstractmethod

from . import exceptions

if t.TYPE_CHECKING:
    from .registration import Registration
    from .ltiplatform import LTI1P3PlatformConfAbstract


class OIDCLoginAbstract(ABC):
    """
    Abstract base class for OIDC (OpenID Connect) Login Initiation

    LTI 1.3 Launch Flow Overview (Step 1: OIDC Login Initiation):
    ============================================================

    The LTI 1.3 specification uses OpenID Connect 3rd-Party-Initiated Login.
    This is how the launch process begins.

    Flow:
    1. User visits platform, clicks "Launch Tool" button
    2. Platform initiates OIDC login by redirecting to tool's OIDC login endpoint
       GET /tool/login?iss=<platform-iss>&target_link_uri=<tool-launch-url>&login_hint=<user-id>&...
    3. Tool receives login request, validates parameters
    4. Tool redirects to platform's OIDC authorization endpoint
       GET /platform/auth?client_id=<client-id>&redirect_uri=<callback>&response_type=id_token&...
    5. Platform authenticates user (usually already authenticated, quick consent screen)
    6. Platform redirects to tool's callback with id_token (signed JWT with user/context claims)
       POST /tool/callback with id_token=<jwt>&state=<state>
    7. Tool validates id_token JWT signature and claims
    8. Tool grants access to user with appropriate context

    This class handles Step 2 (prepare the login request) and Step 3 (initiate redirect).

    OpenID Connect 3rd-Party-Initiated Login Details:
    - 'iss' (Issuer): Identifies the platform doing the login
    - 'client_id' (optional): If multiple registrations, tells tool which one to use
    - 'login_hint': Helps tool identify which user to prompt for (can be opaque platform identifier)
    - 'lti_message_hint': Identifies the message/resource being launched
    - 'target_link_uri': Where tool should take user after launch (platform's tool URL)
    - 'lti_deployment_id' (optional): If issuer has multiple deployments

    Security:
    - HTTPS only (production)
    - State/nonce parameters prevent CSRF attacks
    - ID Token JWT must be validated before granting access

    References:
    - OpenID Connect Core (3rd-Party-Initiated):
      https://openid.net/specs/openid-connect-core-1_0.html#ThirdPartyInitiatedLogin
    - LTI 1.3 Deep Linking:
      https://www.imsglobal.org/spec/lti/v1p3/#third-party-initiated-login
    - LTI Deep Linking Launch:
      https://www.imsglobal.org/spec/lti-dl/v2p0/#lifecycle
    """

    _request = None
    _platform_config = None
    _registration = None  # type: Registration
    _launch_url = None
    _lti_message_hint = None

    def __init__(
        self, request: t.Any, platform_config: LTI1P3PlatformConfAbstract
    ) -> None:
        self._request = request
        self._platform_config = platform_config
        self._registration = self._platform_config.get_registration()

    @abstractmethod
    def set_lti_message_hint(self, **kwargs: t.Any) -> None:
        raise NotImplementedError

    def get_lti_message_hint(self) -> t.Optional[str]:
        return getattr(self, "_lti_message_hint", None)

    def set_launch_url(self, launch_url: str) -> OIDCLoginAbstract:
        self._launch_url = launch_url

        return self

    def set_deeplinking_launch_url(self) -> OIDCLoginAbstract:
        launch_url = self._registration.get_deeplink_launch_url()

        if launch_url:
            self.set_launch_url(launch_url)

        return self

    def get_launch_url(self) -> t.Optional[str]:
        if not self._launch_url:
            launch_url = self._registration.get_launch_url()

            if not launch_url:
                raise exceptions.InvalidRequestUri(
                    "Launch URL is not configured in registration"
                )
            self.set_launch_url(launch_url)

        return self._launch_url

    def prepare_preflight_url(self, user_id: str) -> str:
        """
        Prepare OIDC preflight url for 3rd-party-initiated login

        This creates the URL that redirects the user to the platform's OIDC login endpoint.
        This is Step 2 in the LTI launch flow.

        URL Parameters:
        ===============

        REQUIRED:
        - iss: Issuer (platform) identifier
          * Uniquely identifies learning platform
          * Example: "https://canvas.instructure.com" or "https://moodle.example.edu"
          * Tool uses this to look up platform configuration

        - target_link_uri: The tool URL to launch
          * Where user should be taken after successful launch
          * Should match the tool's registered URLs
          * Must use HTTPS in production
          * Example: "https://tool.example.com/launch/resource/123"

        - lti_message_hint: Identifier for the message/resource
          * Helps platform remember which content triggered the launch
          * Opaque to platform, meaningful to tool
          * Platform generated value (e.g., "resource-link-id-456")
          * Prevents mix-ups if user trying to launch different content

        - login_hint: User identifier
          * Helps platform identify user without additional authentication
          * Often opaque ID assigned by platform (not email/username)
          * Used to prevent "username confusion" attacks
          * Format depends on platform (could be "user:12345" or UUID)

        OPTIONAL:
        - client_id: Platform's OAuth client ID at tool
          * Used when tool has multiple registrations from same platform
          * Allows tool to select correct configuration
          * If not provided, tool uses first registration for issuer

        - lti_deployment_id: Deployment identifier
          * Used when single platform instance supports multiple orgs
          * Helps tool route to correct customer/tenant config
          * Example: university with multiple campuses

        CSRF Protection:
        - Platform will add 'state' parameter before redirect to authorization endpoint
        - Tool receives state back in callback, validates it matches
        - Prevents Cross-Site Request Forgery attacks
        - Example attack prevented: attacker tricks user into launching tool from wrong platform

        Example Flow:
        1. User at https://myuniversity.edu clicks "Launch Tool"
        2. Platform creates login URL:
           https://tool.example.com/login?iss=https://myuniversity.edu&client_id=uni-client-123&
           target_link_uri=https://myuniversity.edu/courses/101/tool&login_hint=user-987&
           lti_message_hint=resource-link-456&lti_deployment_id=university-main
        3. Platform redirects browser to this URL
        4. Tool receives these parameters, validates platform is registered
        5. Tool generates state + nonce for security
        6. Tool redirects to: https://myuniversity.edu/auth?client_id=uni-client-123&...&state=...
        7. University authenticates the user (already logged in? quick redirect)
        8. University redirects back to tool with id_token containing user/context claims

        Security Considerations:
        - Validate iss is registered before processing
        - Validate target_link_uri matches platform's list of allowed URLs
        - Check that user (from login_hint) is allowed to access resource (lti_message_hint)
        - Use HTTPS to prevent credential theft
        - Validate state parameter when receiving callback

        Reference:
        - OpenID Connect 3rd-Party-Initiated Login:
          https://openid.net/specs/openid-connect-core-1_0.html#ThirdPartyInitiatedLogin
        - LTI 1.3 Step 1 (3rd-Party-Initiated Login):
          https://www.imsglobal.org/spec/lti/v1p3/#step-1-third-party-initiated-login

        Parameters:
            user_id: Opaque user identifier from platform

        Returns:
            str: The complete preflight URL (includes iss, client_id, target_link_uri, etc.)

        Raises:
            PreflightRequestValidationException: If required fields not configured
        """
        launch_url = self.get_launch_url()

        if not self._registration.get_iss():
            raise exceptions.PlatformNotReadyException(
                "Issuer (iss) is not configured in registration"
            )

        if not launch_url:
            raise exceptions.InvalidRequestUri("Launch URL is not configured")

        if not self.get_lti_message_hint():
            raise exceptions.InvalidRequestData(
                "LTI message hint (lti_message_hint) is not set"
            )

        if not user_id:
            raise exceptions.InvalidRequestData(
                "User ID is required for preflight request"
            )

        params = {
            "iss": self._registration.get_iss(),
            "target_link_uri": launch_url,
            "login_hint": user_id,
            "lti_message_hint": self.get_lti_message_hint(),
        }

        client_id = self._registration.get_client_id()
        if client_id:
            params["client_id"] = client_id

        deployment_id = self._registration.get_deployment_id()
        if deployment_id:
            params["lti_deployment_id"] = deployment_id

        # Encode the new query parameters
        encoded_params = urlencode(params)

        oidc_login_url = self._registration.get_oidc_login_url()
        if not oidc_login_url:
            raise exceptions.PlatformNotReadyException(
                "OIDC login URL is not configured in registration"
            )
        parsed_url = urlparse(oidc_login_url)
        query = parsed_url.query

        if isinstance(query, bytes):
            query = query.decode("utf-8")

        query_dict = dict(parse_qsl(query))
        if parsed_url.query and not query_dict:
            # handle some weird cases when query is not empty but parse_qsl returns empty dict
            return f"{oidc_login_url}&{encoded_params}"

        return f"{oidc_login_url}?{encoded_params}"

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

    def initiate_login(self, user_id: str) -> t.Any:
        """
        Initiate OIDC login by redirecting to platform's OIDC login endpoint

        This is the main entry point for starting an LTI launch.

        Process:
        1. Prepare login URL with all required parameters (iss, client_id, target_link_uri, etc.)
        2. Redirect user's browser to platform's login endpoint

        The platform's login endpoint will:
        1. Validate all parameters
        2. Authenticate user if needed
        3. Generate state + nonce for CSRF/replay protection
        4. Redirect to authorization endpoint
        5. Eventually redirect back to tool's callback with id_token

        This is an abstract method; implementing frameworks (Django, FastAPI, Flask)
        override this to return appropriate HTTP redirects.

        Returns:
            HTTP redirect response (specific to framework)

        Raises:
            PreflightRequestValidationException: If configuration validation fails
        """
        try:
            preflight_url = self.prepare_preflight_url(user_id)
            return self.get_redirect(preflight_url)
        except Exception as err:  # pylint: disable=broad-exception-caught
            launch_url = self._launch_url or self._registration.get_launch_url()
            return self.get_error_response(err, redirect_uri=launch_url)
