LTI_BASE_MESSAGE = {
    # Claim type: fixed key with value `LtiResourceLinkRequest`
    # http://www.imsglobal.org/spec/lti/v1p3/#message-type-claim
    "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",
    # LTI Claim version
    # http://www.imsglobal.org/spec/lti/v1p3/#lti-version-claim
    "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
}

LTI_DEEP_LINKING_ACCEPTED_TYPES = {"ltiResourceLink", "link", "html", "image", "file"}

LTI_1P3_ACCESS_TOKEN_REQUIRED_CLAIMS = {
    "grant_type",
    "client_assertion_type",
    "client_assertion",
    "scope",
}

LTI_1P3_ACCESS_TOKEN_SCOPES = [
    # LTI-AGS Scopes
    "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly",
    "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
    "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
    "https://purl.imsglobal.org/spec/lti-ags/scope/score",
    # LTI-NRPS Scopes
    "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
]
