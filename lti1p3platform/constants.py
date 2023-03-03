
LTI_BASE_MESSAGE = {
    # Claim type: fixed key with value `LtiResourceLinkRequest`
    # http://www.imsglobal.org/spec/lti/v1p3/#message-type-claim
    "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiResourceLinkRequest",

    # LTI Claim version
    # http://www.imsglobal.org/spec/lti/v1p3/#lti-version-claim
    "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
}

LTI_DEEP_LINKING_ACCEPTED_TYPES = {
    'ltiResourceLink',
    'link',
    'html',
    'image',
}