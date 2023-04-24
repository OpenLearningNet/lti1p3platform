"""
LTI Advantage Assignments and Grades service implementation
"""
from __future__ import annotations

import typing as t


class LtiAgs:
    """
    LTI Advantage Consumer

    Implements LTI Advantage Services and ties them in
    with the LTI Consumer. This only handles the LTI
    message claim inclusion and token handling.

    Available services:
    * Assignments and Grades services claim

    Reference: https://www.imsglobal.org/spec/lti-ags/v2p0/#assignment-and-grade-service-claim
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        lineitems_url: t.Optional[str] = None,
        lineitem_url: t.Optional[str] = None,
        allow_creating_lineitems: bool = False,
        results_service_enabled: bool = True,
        scores_service_enabled: bool = True,
    ) -> None:
        """
        Instance class with LTI AGS Global settings.
        """
        # If the platform allows creating lineitems, set this
        # to True.
        self.allow_creating_lineitems = allow_creating_lineitems

        # Result and scores services
        self.results_service_enabled = results_service_enabled
        self.scores_service_enabled = scores_service_enabled

        # Lineitems urls
        self.lineitems_url = lineitems_url
        self.lineitem_url = lineitem_url

    def get_available_scopes(self) -> t.List[str]:
        """
        Retrieves list of available token scopes in this instance.
        """
        scopes = []

        if self.allow_creating_lineitems:
            # Tool can fully managed its line items, including adding and removing line items
            scopes.append("https://purl.imsglobal.org/spec/lti-ags/scope/lineitem")
        else:
            # Tool can query the line items, no modification is allowed
            scopes.append(
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly"
            )

        if self.results_service_enabled:
            scopes.append(
                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly"
            )

        if self.scores_service_enabled:
            scopes.append("https://purl.imsglobal.org/spec/lti-ags/scope/score")

        return scopes

    def get_lti_ags_launch_claim(self) -> t.Dict[str, t.Any]:
        """
        Returns LTI AGS Claim to be injected in the LTI launch message.
        """

        claim_values: t.Dict[str, t.Any] = {
            "scope": self.get_available_scopes(),
        }

        if self.lineitem_url:
            # link has no line item (or many), tool can query and add line items
            claim_values["lineitem"] = self.lineitem_url

            if not self.lineitems_url:
                # link has a single line item, tool can only POST score
                for scope in claim_values["scope"]:
                    if scope != "https://purl.imsglobal.org/spec/lti-ags/scope/score":
                        claim_values["scope"].remove(scope)

        if self.lineitems_url:
            # link has a single line item, tool can only POST score
            claim_values["lineitems"] = self.lineitems_url

        return {
            "https://purl.imsglobal.org/spec/lti-ags/claim/endpoint": claim_values,
        }
