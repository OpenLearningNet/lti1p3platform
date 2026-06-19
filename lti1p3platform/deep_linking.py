"""
LTI 1.3 Advantage - Deep Linking Service

Deep Linking is an LTI Advantage service that allows platforms to let users
(usually instructors) browse and select content from external tools.

Use Case:
- Instructor in LMS wants to add content from external tool to course
- Rather than navigating to external tool, then copying URLs back
- Instructor uses Deep Linking UI within LMS to find and select content
- Tool returns structured content reference to LMS
- LMS records the content selection and embeds it in course

Reference:
- LTI Deep Linking Spec: https://www.imsglobal.org/spec/lti-dl/v2p0/
- Deep Linking Launch: https://www.imsglobal.org/spec/lti-dl/v2p0/#launch
- Deep Linking Response: https://www.imsglobal.org/spec/lti-dl/v2p0/#deep_linking_response
"""
import typing as t
from .constants import LTI_DEEP_LINKING_ACCEPTED_TYPES
from .exceptions import LtiDeepLinkingContentTypeNotSupported


# pylint: disable=too-few-public-methods
class LtiDeepLinking:
    """
    LTI 1.3 Advantage - Deep Linking Service Handler

    Deep Linking Launch Flow:
    1. Instructor clicks "Select Content from External Tool" in LMS
    2. Platform sends special LTI message to tool (includes deep_linking data)
    3. Tool displays content browser/selection UI
    4. User selects one or more items
    5. Tool creates Deep Link Response (signed JWT) with selected content
    6. Tool redirects back to platform with response
    7. Platform validates response and records selection
    8. Content appears in course

    This class handles:
    - Creating Deep Linking launch claims (Step 2)
    - Validating Deep Linking responses (Step 6)
    - Creating Deep Linking response returns (Step 5)

    Deep Linking Claims in Launch Message:
    - accept_types: What types of content the platform can accept
    - accept_media_types: What media types are acceptable
    - accept_presentation_document_targets: Where to embed (window, frame, etc.)
    - title: Prefill title for content browser
    - text: Prefill description for content browser
    - data: Additional custom data from platform
    - auto_create: Allow tool to auto-select instead of showing UI (optional)
    - accept_unsigned: Allow unsigned deep links (default: false, require signature)
    - accept_multiple: Allow selecting multiple items (default: false, single item)
    - accept_lineitem: Platform accepts a grading item (AGS)

    Deep Linking Response Format:
    - Signed JWT with claims:
      * https://purl.imsglobal.org/spec/lti-dl/claim/content_items:
        Array of selected content items
      * https://purl.imsglobal.org/spec/lti-dl/claim/data: Echo back platform's data
      * nonce: Echoed from request (replay protection)
      * aud: Platform's deep link return URL
      * Plus standard claims (iss, sub, iat, exp, jti)

    Security Mechanisms:
    - Only platform's registered deep_linking_launch_url can receive launch
    - Tool must validate authorization before showing content browser
    - Deep Link Response is signed JWT (can't be forged)
    - Nonce prevents replay of old responses
    - JTI prevents token reuse
    - Return URL (aud claim) prevents sending response to wrong platform

    Reference:
    - LTI Advantage Services: https://www.imsglobal.org/spec/lti/v1p3/#lti-advantage-services
    - Deep Linking Spec: https://www.imsglobal.org/spec/lti-dl/v2p0/
    """

    def __init__(
        self,
        deep_linking_return_url: str,
    ) -> None:
        """
        Initialize Deep Linking response handler

        Parameters:
            deep_linking_return_url: URL where to POST Deep Link Response
                - Is provided by platform in the launch message
                - Is also the audience (aud claim) for the response JWT
                - MUST use HTTPS in production
        """
        self.deep_linking_return_url = deep_linking_return_url

    # pylint: disable=too-many-arguments
    def get_lti_deep_linking_launch_claim(
        self,
        title: str = "",
        description: str = "",
        accept_multiple: bool = False,
        auto_create: bool = True,
        accept_types: t.Optional[t.Set[str]] = None,
        accept_lineitem: bool = False,
        extra_data: t.Optional[t.Dict[str, t.Any]] = None,
        accept_presentation_document_targets: t.Optional[t.Set[str]] = None,
    ) -> t.Dict[str, t.Dict[str, t.Any]]:
        """
        Generate Deep Linking Launch Claim for LTI message

        This claim is included in the LTI launch message when the platform wants
        the tool to display a content selection interface (Deep Linking).

        Platform -> Tool Communication:
        The platform includes this claim in the id_token JWT to tell the tool:
        "Display content selection UI and return what the user selects"

        Claim Structure:
        ================
        {
            "https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings": {
                "accept_types": [content type URIs],
                "accept_media_types": [media type filter],
                "accept_presentation_document_targets": [embed options],
                "accept_multiple": false/true,              # Single or multiple selection
                "auto_create": false/true,                  # Show UI or auto-create
                "accept_unsigned": false/true,              # Require signed response JWT
                "accept_lineitem": false/true,              # Include grading item
                "title": "Prefill title for content browser",
                "text": "Prefill description",
                "data": "Custom data to echo back"           # Platform can pass arbitrary data
            }
        }

        Parameters:
            title: Prefill title in tool's content browser UI
            description: Prefill description/text in tool's content browser UI
            accept_types: What content types the platform can store
                - "ltiResourceLink": Standard LTI launch content
                - "file": File upload (document, video, etc.)
                - "html": HTML/inline content
                - "image": Image content
                - "link": External URL/link
                - If None: all types accepted

            extra_data: Custom data returned in Deep Link Response
                - Platform can include any opaque data
                - Tool must echo this back in response
                - Allows platform to remember context (course ID, module ID, etc.)

        Returns:
            dict: The deep_linking_settings claim to inject into LTI launch message

        Raises:
            LtiDeepLinkingContentTypeNotSupported: If invalid content types requested
        """
        if not accept_types:
            accept_types = LTI_DEEP_LINKING_ACCEPTED_TYPES

        # Check if required types are accepted, if not throw
        accept_types_claim = []
        for content_type in accept_types:
            if content_type in LTI_DEEP_LINKING_ACCEPTED_TYPES:
                accept_types_claim.append(content_type)
            else:
                raise LtiDeepLinkingContentTypeNotSupported

        # Consctruct Deep Linking Claim
        deep_linking_claim: t.Dict[str, t.Any] = {
            "accept_types": accept_types_claim,
            "accept_presentation_document_targets": accept_presentation_document_targets
            or ["iframe", "window", "embed"],
            # Accept multiple items on from Deep Linking responses.
            "accept_multiple": accept_multiple,
            # Automatically saves Content Items without asking to user
            "auto_create": auto_create,
            # Accept line items in Content Items from Deep Linking responses.
            "accept_lineitem": accept_lineitem,
            # Other parameters
            "title": title,
            "text": description,
            "deep_link_return_url": self.deep_linking_return_url,
        }

        # Extra data is an optional parameter that can be sent.
        # It's opaque to the tool, but WILL be sent back in the
        # deep link response.
        if extra_data:
            deep_linking_claim.update(
                {
                    "data": extra_data,
                }
            )

        return {
            "https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings": deep_linking_claim
        }
