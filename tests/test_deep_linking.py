"""
Tests for lti1p3platform.deep_linking.LtiDeepLinking.
"""
import pytest

from lti1p3platform.deep_linking import LtiDeepLinking
from lti1p3platform.exceptions import LtiDeepLinkingContentTypeNotSupported
from lti1p3platform.constants import LTI_DEEP_LINKING_ACCEPTED_TYPES


def test_get_lti_deep_linking_launch_claim_defaults():
    """No accept_types → all types included."""
    dl = LtiDeepLinking("https://platform.example.com/deeplink_return")
    claim = dl.get_lti_deep_linking_launch_claim()
    settings = claim["https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"]
    for t in LTI_DEEP_LINKING_ACCEPTED_TYPES:
        assert t in settings["accept_types"]
    assert settings["deep_link_return_url"] == "https://platform.example.com/deeplink_return"


def test_get_lti_deep_linking_launch_claim_custom_types():
    dl = LtiDeepLinking("https://platform.example.com/deeplink_return")
    claim = dl.get_lti_deep_linking_launch_claim(
        accept_types={"ltiResourceLink", "link"}
    )
    settings = claim["https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"]
    assert "ltiResourceLink" in settings["accept_types"]
    assert "link" in settings["accept_types"]
    # Others should not be present
    assert "html" not in settings["accept_types"]


def test_get_lti_deep_linking_launch_claim_invalid_type_raises():
    dl = LtiDeepLinking("https://platform.example.com/deeplink_return")
    with pytest.raises(LtiDeepLinkingContentTypeNotSupported):
        dl.get_lti_deep_linking_launch_claim(accept_types={"bogusType"})


def test_get_lti_deep_linking_launch_claim_with_title_and_description():
    dl = LtiDeepLinking("https://platform.example.com/deeplink_return")
    claim = dl.get_lti_deep_linking_launch_claim(
        title="My Title", description="My Description"
    )
    settings = claim["https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"]
    assert settings["title"] == "My Title"
    assert settings["text"] == "My Description"


def test_get_lti_deep_linking_launch_claim_with_extra_data():
    dl = LtiDeepLinking("https://platform.example.com/deeplink_return")
    extra = {"course_id": "course-123", "module_id": "module-456"}
    claim = dl.get_lti_deep_linking_launch_claim(extra_data=extra)
    settings = claim["https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"]
    assert settings["data"] == extra


def test_get_lti_deep_linking_launch_claim_without_extra_data():
    dl = LtiDeepLinking("https://platform.example.com/deeplink_return")
    claim = dl.get_lti_deep_linking_launch_claim()
    settings = claim["https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"]
    assert "data" not in settings


def test_get_lti_deep_linking_launch_claim_accept_multiple_and_auto_create():
    dl = LtiDeepLinking("https://platform.example.com/deeplink_return")
    claim = dl.get_lti_deep_linking_launch_claim()
    settings = claim["https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"]
    assert settings["accept_multiple"] is True
    assert settings["auto_create"] is True


def test_get_lti_deep_linking_launch_claim_presentation_targets():
    dl = LtiDeepLinking("https://platform.example.com/deeplink_return")
    claim = dl.get_lti_deep_linking_launch_claim()
    settings = claim["https://purl.imsglobal.org/spec/lti-dl/claim/deep_linking_settings"]
    assert "iframe" in settings["accept_presentation_document_targets"]
    assert "window" in settings["accept_presentation_document_targets"]
