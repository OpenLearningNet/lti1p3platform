"""
LTI Names and Role Provisioning Service implementation
"""
from __future__ import annotations

import typing as t


class LtiNrps:
    """
    LTI NRPS Consumer

    Implements Names and Role Provisioning Services and ties
    them in with the LTI Consumer.

    Available services:
    * Context Membership Service

    Reference: https://www.imsglobal.org/spec/lti-nrps/v2p0#overview
    """

    def __init__(
        self,
        context_memberships_url: str,
    ):
        self.context_memberships_url = context_memberships_url

    def get_available_scopes(self) -> t.List[str]:
        """
        Retrieves list of available token scopes in this instance.
        """

        return [
            "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
        ]

    def get_lti_nrps_launch_claim(self) -> t.Dict[str, t.Any]:
        """
        Returns LTI NRPS Claim to be injected in the LTI launch message.
        """

        return {
            "https://purl.imsglobal.org/spec/lti-nrps/claim/namesroleservice": {
                "context_memberships_url": self.context_memberships_url,
                "service_versions": ["2.0"],
            }
        }
