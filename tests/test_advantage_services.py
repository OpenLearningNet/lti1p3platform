"""
Tests for AssignmentsGradesService and NamesRoleProvisioningService.

Covers:
- BasicService.handle_resp (LtiServiceException, InvalidRequestData, generic Exception)
- @authenticate decorator (missing/malformed bearer token, wrong method, invalid token)
- AssignmentsGradesService: handle_get_lineitems, handle_create_lineitem,
  handle_get_lineitem, handle_update_lineitem, handle_delete_lineitem,
  handle_update_score, handle_get_results (success, not-found, pagination)
- NamesRoleProvisioningService: clean_members, handle_get_members
"""
import time
import typing as t
from unittest.mock import patch

import pytest

from lti1p3platform.exceptions import InvalidRequestData, LineItemNotFoundException
from lti1p3platform.exceptions import LtiServiceException
from lti1p3platform.jwt_helper import jwt_encode
from lti1p3platform.lineitem import TLineItem
from lti1p3platform.membership import Context
from lti1p3platform.request import RequestBase, TRequest
from lti1p3platform.response import Response
from lti1p3platform.score import TScore, UpdateScoreStatus
from lti1p3platform.service_connector import (
    AssignmentsGradesService,
    BasicService,
    NamesRoleProvisioningService,
)

from .platform_config import PLATFORM_CONFIG, RSA_PRIVATE_KEY_PEM, PlatformConf

# ---------------------------------------------------------------------------
# Scope constants
# ---------------------------------------------------------------------------

AGS_SCOPE_LINEITEM = "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem"
AGS_SCOPE_LINEITEM_READONLY = (
    "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly"
)
AGS_SCOPE_RESULT_READONLY = (
    "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly"
)
AGS_SCOPE_SCORE = "https://purl.imsglobal.org/spec/lti-ags/scope/score"
NRPS_SCOPE = (
    "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
)

LINEITEMS_URL = "https://platform.example/ags/lineitems"
LINEITEM_URL = f"{LINEITEMS_URL}/1"
MEMBERSHIPS_URL = "https://platform.example/nrps/memberships"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_bearer_token(scopes: str) -> str:
    """Generate a valid Bearer token signed by the platform's private key."""
    now = int(time.time())
    claims = {
        "iss": PLATFORM_CONFIG["iss"],
        "sub": "test-tool",
        "iat": now,
        "exp": now + 3600,
        "scopes": scopes,
    }
    return jwt_encode(claims, RSA_PRIVATE_KEY_PEM, algorithm="RS256")


class MockRequest(RequestBase):
    """Request implementation that accepts a pre-built TRequest dict."""

    def __init__(self, request: TRequest) -> None:  # type: ignore[override]
        self.request = request


def make_request(
    method: str = "GET",
    headers: t.Optional[t.Mapping[str, str]] = None,
    get_data: t.Optional[t.Dict[str, t.Any]] = None,
    json: t.Any = None,
) -> MockRequest:
    return MockRequest(
        {
            "method": method,
            "headers": headers or {},
            "get_data": get_data or {},
            "form_data": {},
            "content_type": "application/json",
            "path": "/",
            "json": json if json is not None else {},
        }
    )


# ---------------------------------------------------------------------------
# Concrete AGS implementation
# ---------------------------------------------------------------------------

_INITIAL_LINEITEM: TLineItem = {
    "id": LINEITEM_URL,
    "label": "Test Assignment",
    "scoreMaximum": 100,
    "resourceId": "res-1",
    "tag": "tag-1",
    "resourceLinkId": "link-1",
}


class _AGSImpl(AssignmentsGradesService):
    """In-memory AssignmentsGradesService for unit tests."""

    def __init__(
        self,
        request: MockRequest,
        platform_config: PlatformConf,
        **kwargs: t.Any,
    ) -> None:
        super().__init__(
            request,  # type: ignore[arg-type]
            platform_config,
            lineitems_url=LINEITEMS_URL,
            lineitem_url=LINEITEM_URL,
            allow_creating_lineitems=True,
        )
        self._lineitems: t.List[TLineItem] = [dict(_INITIAL_LINEITEM)]  # type: ignore[misc]
        self._scores: t.Dict[str, TScore] = {}

    def find_lineitems(
        self,
        page: int = 1,
        limit: t.Optional[int] = None,
        line_item_id: t.Optional[str] = None,
        resource_link_id: t.Optional[str] = None,
        resource_id: t.Optional[str] = None,
        tag: t.Optional[str] = None,
    ) -> t.Any:
        results = list(self._lineitems)
        if tag:
            results = [li for li in results if li.get("tag") == tag]
        has_next = False
        if limit and len(results) > limit:
            results = results[:limit]
            has_next = True
        return {"content": results, "has_next": has_next}

    def find_lineitem(self, line_item_id: str) -> TLineItem:
        for li in self._lineitems:
            if li.get("id") == line_item_id:
                return li
        raise LineItemNotFoundException

    def create_lineitem(self, creation_data: TLineItem) -> TLineItem:
        item: TLineItem = dict(creation_data)  # type: ignore[misc]
        item["id"] = f"{LINEITEMS_URL}/{len(self._lineitems) + 1}"
        self._lineitems.append(item)
        return item

    def update_lineitem(self, update_data: TLineItem) -> TLineItem:
        item_id = update_data.get("id")
        for li in self._lineitems:
            if li.get("id") == item_id:
                li.update(update_data)  # type: ignore[typeddict-item]
                return li
        raise LineItemNotFoundException

    def delete_lineitem(self, line_item_id: str) -> None:
        for li in list(self._lineitems):
            if li.get("id") == line_item_id:
                self._lineitems.remove(li)
                return
        raise LineItemNotFoundException

    def update_score(self, line_item_id: str, score: TScore) -> UpdateScoreStatus:
        for li in self._lineitems:
            if li.get("id") == line_item_id:
                is_new = line_item_id not in self._scores
                self._scores[line_item_id] = score
                return UpdateScoreStatus.CREATED if is_new else UpdateScoreStatus.SUCCESS
        raise LineItemNotFoundException

    def get_results(
        self,
        line_item_id: str,
        page: int = 1,
        limit: t.Optional[int] = None,
        user_id: t.Optional[str] = None,
    ) -> t.Any:
        for li in self._lineitems:
            if li.get("id") == line_item_id:
                score = self._scores.get(line_item_id)
                results = [score] if score else []
                return {"content": results, "has_next": False}
        raise LineItemNotFoundException


# ---------------------------------------------------------------------------
# Concrete NRPS implementation
# ---------------------------------------------------------------------------


class _NRPSImpl(NamesRoleProvisioningService):
    """In-memory NamesRoleProvisioningService for unit tests."""

    _CONTEXT = Context(id="course-1", label="CS101", title="Introduction to CS")

    def get_member_data_page(
        self,
        page: int = 1,
        limit: t.Optional[int] = None,
        role: t.Optional[str] = None,
        since: t.Optional[str] = None,
    ) -> t.Any:
        members = [
            {"user_id": "user-1", "roles": ["Learner"], "status": "Active"},
            {"user_id": "user-2", "roles": ["Instructor"], "status": "Active"},
        ]
        return {"content": members, "has_next": False}

    def get_context_by_id(self) -> Context:
        return self._CONTEXT


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def platform() -> PlatformConf:
    return PlatformConf()


@pytest.fixture()
def ags_token() -> str:
    return make_bearer_token(
        f"{AGS_SCOPE_LINEITEM} {AGS_SCOPE_RESULT_READONLY} {AGS_SCOPE_SCORE}"
    )


@pytest.fixture()
def nrps_token() -> str:
    return make_bearer_token(NRPS_SCOPE)


def _make_ags(
    platform: PlatformConf,
    token: str,
    method: str = "GET",
    get_data: t.Optional[t.Dict[str, t.Any]] = None,
    json: t.Any = None,
) -> _AGSImpl:
    req = make_request(
        method=method,
        headers={"Authorization": f"Bearer {token}"},
        get_data=get_data,
        json=json,
    )
    return _AGSImpl(req, platform)


def _make_nrps(
    platform: PlatformConf,
    token: str,
    method: str = "GET",
    get_data: t.Optional[t.Dict[str, t.Any]] = None,
) -> _NRPSImpl:
    req = make_request(
        method=method,
        headers={"Authorization": f"Bearer {token}"},
        get_data=get_data,
    )
    return _NRPSImpl(req, platform, context_memberships_url=MEMBERSHIPS_URL)  # type: ignore[arg-type]


# ===========================================================================
# BasicService.handle_resp
# ===========================================================================


class _ConcreteBasicService(BasicService):
    """Minimal concrete subclass so handle_resp can be called directly."""


def test_handle_resp_returns_function_result() -> None:
    svc = _ConcreteBasicService()
    resp = svc.handle_resp(lambda: Response(result={"ok": True}, code=200, message="ok"))
    assert resp.code == 200
    assert resp.result == {"ok": True}


def test_handle_resp_catches_lti_service_exception() -> None:
    svc = _ConcreteBasicService()

    def _raise() -> Response:
        raise LtiServiceException("bad auth", 401)

    resp = svc.handle_resp(_raise)
    assert resp.code == 401
    assert "bad auth" in resp.message


def test_handle_resp_catches_invalid_request_data() -> None:
    svc = _ConcreteBasicService()

    def _raise() -> Response:
        raise InvalidRequestData("missing field xyz")

    resp = svc.handle_resp(_raise)
    assert resp.code == 400
    assert "missing field xyz" in resp.message


def test_handle_resp_catches_generic_exception() -> None:
    svc = _ConcreteBasicService()

    def _raise() -> Response:
        raise RuntimeError("unexpected crash")

    resp = svc.handle_resp(_raise)
    assert resp.code == 500


# ===========================================================================
# @authenticate decorator
# ===========================================================================


def test_missing_authorization_header(platform: PlatformConf) -> None:
    req = make_request(method="GET", headers={})
    ags = _AGSImpl(req, platform)
    resp = ags.handle_resp(ags.handle_get_lineitems)
    assert resp.code == 401


def test_authorization_not_bearer(platform: PlatformConf) -> None:
    req = make_request(method="GET", headers={"Authorization": "Basic abc123"})
    ags = _AGSImpl(req, platform)
    resp = ags.handle_resp(ags.handle_get_lineitems)
    assert resp.code == 401


def test_bearer_token_only_scheme(platform: PlatformConf) -> None:
    """Authorization header with just "Bearer" and no token value."""
    req = make_request(method="GET", headers={"Authorization": "Bearer"})
    ags = _AGSImpl(req, platform)
    resp = ags.handle_resp(ags.handle_get_lineitems)
    assert resp.code == 401


def test_bearer_token_too_many_parts(platform: PlatformConf) -> None:
    """Authorization header with extra token parts."""
    req = make_request(method="GET", headers={"Authorization": "Bearer tok1 tok2"})
    ags = _AGSImpl(req, platform)
    resp = ags.handle_resp(ags.handle_get_lineitems)
    assert resp.code == 401


def test_method_not_allowed(platform: PlatformConf, ags_token: str) -> None:
    """POST to a GET-only endpoint returns 405."""
    ags = _make_ags(platform, ags_token, method="POST")
    resp = ags.handle_resp(ags.handle_get_lineitems)
    assert resp.code == 405


def test_invalid_token_rejected(platform: PlatformConf) -> None:
    req = make_request(method="GET", headers={"Authorization": "Bearer not.a.jwt"})
    ags = _AGSImpl(req, platform)
    resp = ags.handle_resp(ags.handle_get_lineitems)
    # Invalid JWT — expect auth failure (401) or server error (500)
    assert resp.code in (401, 500)


def test_token_wrong_scope_rejected(platform: PlatformConf) -> None:
    """Token whose scope does not include any allowed AGS scope."""
    token = make_bearer_token(NRPS_SCOPE)  # NRPS scope, not AGS
    ags = _make_ags(platform, token)
    resp = ags.handle_resp(ags.handle_get_lineitems)
    assert resp.code == 401


# ===========================================================================
# handle_get_lineitems
# ===========================================================================


def test_handle_get_lineitems_returns_items(
    platform: PlatformConf, ags_token: str
) -> None:
    ags = _make_ags(platform, ags_token)
    resp = ags.handle_resp(ags.handle_get_lineitems)
    assert resp.code == 200
    assert "content" in resp.result
    assert len(resp.result["content"]) == 1


def test_handle_get_lineitems_filtered_by_tag(
    platform: PlatformConf, ags_token: str
) -> None:
    ags = _make_ags(platform, ags_token, get_data={"tag": "tag-1"})
    resp = ags.handle_resp(ags.handle_get_lineitems)
    assert resp.code == 200
    assert all(li["tag"] == "tag-1" for li in resp.result["content"])


def test_handle_get_lineitems_pagination_next_link(
    platform: PlatformConf, ags_token: str
) -> None:
    """When has_next is True, a 'next' URL is added to the result."""
    ags = _make_ags(platform, ags_token, get_data={"limit": 1, "page": 1})
    # Add a second line item so limit=1 triggers has_next
    ags._lineitems.append(  # type: ignore[attr-defined]
        {"id": f"{LINEITEMS_URL}/2", "label": "Second", "scoreMaximum": 50}
    )
    with patch.object(
        ags,
        "find_lineitems",
        return_value={"content": [_INITIAL_LINEITEM], "has_next": True},
    ):
        resp = ags.handle_resp(ags.handle_get_lineitems)
    assert resp.code == 200
    assert "next" in resp.result


# ===========================================================================
# handle_create_lineitem
# ===========================================================================


def test_handle_create_lineitem_success(platform: PlatformConf) -> None:
    token = make_bearer_token(AGS_SCOPE_LINEITEM)
    new_item = {"label": "New Quiz", "scoreMaximum": 50}
    ags = _make_ags(platform, token, method="POST", json=new_item)
    resp = ags.handle_resp(ags.handle_create_lineitem)
    assert resp.code == 201
    assert resp.result["label"] == "New Quiz"
    assert "id" in resp.result


# ===========================================================================
# handle_get_lineitem
# ===========================================================================


def test_handle_get_lineitem_success(
    platform: PlatformConf, ags_token: str
) -> None:
    ags = _make_ags(platform, ags_token)
    resp = ags.handle_resp(ags.handle_get_lineitem, line_item_id=LINEITEM_URL)
    assert resp.code == 200
    assert resp.result["label"] == "Test Assignment"


def test_handle_get_lineitem_not_found(
    platform: PlatformConf, ags_token: str
) -> None:
    ags = _make_ags(platform, ags_token)
    resp = ags.handle_resp(
        ags.handle_get_lineitem, line_item_id=f"{LINEITEMS_URL}/999"
    )
    assert resp.code == 404


# ===========================================================================
# handle_update_lineitem
# ===========================================================================


def test_handle_update_lineitem_success(platform: PlatformConf) -> None:
    token = make_bearer_token(AGS_SCOPE_LINEITEM)
    ags = _make_ags(
        platform, token, method="PUT", json={"label": "Updated Label"}
    )
    resp = ags.handle_resp(ags.handle_update_lineitem, line_item_id=LINEITEM_URL)
    assert resp.code == 200
    assert resp.result["label"] == "Updated Label"


def test_handle_update_lineitem_not_found(platform: PlatformConf) -> None:
    token = make_bearer_token(AGS_SCOPE_LINEITEM)
    ags = _make_ags(platform, token, method="PUT", json={"label": "X"})
    resp = ags.handle_resp(
        ags.handle_update_lineitem, line_item_id=f"{LINEITEMS_URL}/999"
    )
    assert resp.code == 404


# ===========================================================================
# handle_delete_lineitem
# ===========================================================================


def test_handle_delete_lineitem_success(platform: PlatformConf) -> None:
    token = make_bearer_token(AGS_SCOPE_LINEITEM)
    ags = _make_ags(platform, token, method="DELETE")
    resp = ags.handle_resp(ags.handle_delete_lineitem, line_item_id=LINEITEM_URL)
    assert resp.code == 204
    # Verify item was removed
    assert len(ags._lineitems) == 0  # type: ignore[attr-defined]


def test_handle_delete_lineitem_not_found(platform: PlatformConf) -> None:
    token = make_bearer_token(AGS_SCOPE_LINEITEM)
    ags = _make_ags(platform, token, method="DELETE")
    resp = ags.handle_resp(
        ags.handle_delete_lineitem, line_item_id=f"{LINEITEMS_URL}/999"
    )
    assert resp.code == 404


# ===========================================================================
# handle_update_score
# ===========================================================================


def test_handle_update_score_created(platform: PlatformConf) -> None:
    token = make_bearer_token(AGS_SCOPE_SCORE)
    score_data: TScore = {
        "userId": 42,
        "scoreGiven": 85.0,
        "scoreMaximum": 100.0,
        "activityProgress": "Completed",  # type: ignore[typeddict-item]
        "gradingProgress": "FullyGraded",  # type: ignore[typeddict-item]
    }
    ags = _make_ags(platform, token, method="POST", json=score_data)
    resp = ags.handle_resp(ags.handle_update_score, line_item_id=LINEITEM_URL)
    assert resp.code == 201


def test_handle_update_score_success_on_second_call(platform: PlatformConf) -> None:
    """Updating the same line item twice yields 200 (UpdateScoreStatus.SUCCESS)."""
    token = make_bearer_token(AGS_SCOPE_SCORE)
    score_data: TScore = {
        "userId": 42,
        "scoreGiven": 90.0,
        "scoreMaximum": 100.0,
        "activityProgress": "Completed",  # type: ignore[typeddict-item]
        "gradingProgress": "FullyGraded",  # type: ignore[typeddict-item]
    }
    ags = _make_ags(platform, token, method="POST", json=score_data)
    # First call: creates
    ags.handle_resp(ags.handle_update_score, line_item_id=LINEITEM_URL)
    # Second call: updates (new request object needed for repeated auth)
    req2 = make_request(
        method="POST",
        headers={"Authorization": f"Bearer {token}"},
        json=score_data,
    )
    ags.request = req2  # type: ignore[assignment]
    resp = ags.handle_resp(ags.handle_update_score, line_item_id=LINEITEM_URL)
    assert resp.code == 200


def test_handle_update_score_not_found(platform: PlatformConf) -> None:
    token = make_bearer_token(AGS_SCOPE_SCORE)
    ags = _make_ags(
        platform, token, method="POST", json={"userId": 1, "scoreGiven": 5.0}
    )
    resp = ags.handle_resp(
        ags.handle_update_score, line_item_id=f"{LINEITEMS_URL}/999"
    )
    assert resp.code == 404


# ===========================================================================
# handle_get_results
# ===========================================================================


def test_handle_get_results_empty(
    platform: PlatformConf, ags_token: str
) -> None:
    ags = _make_ags(platform, ags_token)
    resp = ags.handle_resp(ags.handle_get_results, line_item_id=LINEITEM_URL)
    assert resp.code == 200
    assert resp.result["content"] == []


def test_handle_get_results_after_score_submitted(
    platform: PlatformConf, ags_token: str
) -> None:
    """Results endpoint reflects a score submitted via handle_update_score."""
    score_data: TScore = {
        "userId": 42,
        "scoreGiven": 80.0,
        "scoreMaximum": 100.0,
        "activityProgress": "Completed",  # type: ignore[typeddict-item]
        "gradingProgress": "FullyGraded",  # type: ignore[typeddict-item]
    }
    # Set up state via the public service API (POST score)
    ags = _make_ags(platform, ags_token, method="POST", json=score_data)
    ags.handle_resp(ags.handle_update_score, line_item_id=LINEITEM_URL)
    # Switch to a GET request and query results
    ags.request = make_request(  # type: ignore[assignment]
        method="GET",
        headers={"Authorization": f"Bearer {ags_token}"},
    )
    resp = ags.handle_resp(ags.handle_get_results, line_item_id=LINEITEM_URL)
    assert resp.code == 200
    assert len(resp.result["content"]) == 1


def test_handle_get_results_not_found(
    platform: PlatformConf, ags_token: str
) -> None:
    ags = _make_ags(platform, ags_token)
    resp = ags.handle_resp(
        ags.handle_get_results, line_item_id=f"{LINEITEMS_URL}/999"
    )
    assert resp.code == 404


def test_handle_get_results_pagination_next_link(
    platform: PlatformConf, ags_token: str
) -> None:
    """When get_results reports has_next=True, a 'next' URL is added."""
    ags = _make_ags(platform, ags_token, get_data={"limit": 1, "page": 1})
    with patch.object(
        ags,
        "get_results",
        return_value={"content": [{"userId": 1}], "has_next": True},
    ):
        resp = ags.handle_resp(ags.handle_get_results, line_item_id=LINEITEM_URL)
    assert resp.code == 200
    assert "next" in resp.result


# ===========================================================================
# NamesRoleProvisioningService – clean_members
# ===========================================================================


def test_clean_members_valid(platform: PlatformConf, nrps_token: str) -> None:
    nrps = _make_nrps(platform, nrps_token)
    members = [{"user_id": "u1", "roles": ["Learner"]}]
    cleaned = nrps.clean_members(members)
    assert len(cleaned) == 1
    assert cleaned[0]["status"] == "Active"


def test_clean_members_preserves_existing_status(
    platform: PlatformConf, nrps_token: str
) -> None:
    nrps = _make_nrps(platform, nrps_token)
    members = [{"user_id": "u1", "roles": ["Learner"], "status": "Inactive"}]
    cleaned = nrps.clean_members(members)
    assert cleaned[0]["status"] == "Inactive"


def test_clean_members_missing_user_id_raises(
    platform: PlatformConf, nrps_token: str
) -> None:
    nrps = _make_nrps(platform, nrps_token)
    with pytest.raises(InvalidRequestData, match="user_id"):
        nrps.clean_members([{"roles": ["Learner"]}])


def test_clean_members_missing_roles_raises(
    platform: PlatformConf, nrps_token: str
) -> None:
    nrps = _make_nrps(platform, nrps_token)
    with pytest.raises(InvalidRequestData, match="roles"):
        nrps.clean_members([{"user_id": "u1"}])


def test_clean_members_multiple_valid(
    platform: PlatformConf, nrps_token: str
) -> None:
    nrps = _make_nrps(platform, nrps_token)
    members = [
        {"user_id": "u1", "roles": ["Learner"]},
        {"user_id": "u2", "roles": ["Instructor"], "status": "Inactive"},
    ]
    cleaned = nrps.clean_members(members)
    assert len(cleaned) == 2
    assert cleaned[0]["status"] == "Active"
    assert cleaned[1]["status"] == "Inactive"


# ===========================================================================
# NamesRoleProvisioningService – handle_get_members
# ===========================================================================


def test_handle_get_members_success(
    platform: PlatformConf, nrps_token: str
) -> None:
    nrps = _make_nrps(platform, nrps_token)
    resp = nrps.handle_resp(nrps.handle_get_members)
    assert resp.code == 200
    assert "members" in resp.result
    assert len(resp.result["members"]) == 2
    assert resp.result["context"]["id"] == "course-1"


def test_handle_get_members_invalid_member_data_returns_400(
    platform: PlatformConf, nrps_token: str
) -> None:
    """clean_members raising InvalidRequestData is caught by handle_resp → 400."""
    nrps = _make_nrps(platform, nrps_token)
    with patch.object(
        nrps,
        "get_member_data_page",
        return_value={
            "content": [{"roles": ["Learner"]}],  # missing user_id
            "has_next": False,
        },
    ):
        resp = nrps.handle_resp(nrps.handle_get_members)
    assert resp.code == 400


def test_handle_get_members_pagination_next_link(
    platform: PlatformConf, nrps_token: str
) -> None:
    """When has_next is True and limit is set, a 'next' URL appears in result."""
    nrps = _make_nrps(platform, nrps_token, get_data={"limit": 1, "page": 1})
    with patch.object(
        nrps,
        "get_member_data_page",
        return_value={
            "content": [{"user_id": "u1", "roles": ["Learner"]}],
            "has_next": True,
        },
    ):
        resp = nrps.handle_resp(nrps.handle_get_members)
    assert resp.code == 200
    assert "next" in resp.result


def test_handle_get_members_missing_auth(platform: PlatformConf) -> None:
    req = make_request(method="GET", headers={})
    nrps = _NRPSImpl(req, platform, context_memberships_url=MEMBERSHIPS_URL)  # type: ignore[arg-type]
    resp = nrps.handle_resp(nrps.handle_get_members)
    assert resp.code == 401


def test_handle_get_members_method_not_allowed(
    platform: PlatformConf, nrps_token: str
) -> None:
    nrps = _make_nrps(platform, nrps_token, method="POST")
    resp = nrps.handle_resp(nrps.handle_get_members)
    assert resp.code == 405
