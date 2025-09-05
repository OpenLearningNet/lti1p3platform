from lti1p3platform.ltiplatform import LTI1P3PlatformConfAbstract
from lti1p3platform.registration import Registration

RSA_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1du+3Vg1huBld4X7y8FS
y7bOFbEje00BJlpzCGYLAhKQL+kV4eeu6fQRJJ8rvknlElXUHs99/jTHAe0em0kr
Uvkw+Q0Yiy1AAdhz6TNjoFPmD7NIhru0Qshm1LzQ1av5P/nbPDW5h9HgPXnxsBJ/
Kzpeqx80WqUJ7GYvEbdVr76xxRebhI2iZN6YXLm0xoz0EUrN6FRPB2sdsMG1rhfY
+g6t9QvjW1aByiG0SQviRyTD8iQKV1QcwMC13pPYmXapzxrJ+QvFogzjXyKMQeRm
fony3AP5P5Tha4j5E/jDlWIkEkb66Hzl9bjdJCADXH4vINVPxR6WhDsAUVgO4dI4
oQIDAQAB
-----END PUBLIC KEY-----"""

RSA_PRIVATE_KEY_PEM = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA1du+3Vg1huBld4X7y8FSy7bOFbEje00BJlpzCGYLAhKQL+kV
4eeu6fQRJJ8rvknlElXUHs99/jTHAe0em0krUvkw+Q0Yiy1AAdhz6TNjoFPmD7NI
hru0Qshm1LzQ1av5P/nbPDW5h9HgPXnxsBJ/Kzpeqx80WqUJ7GYvEbdVr76xxReb
hI2iZN6YXLm0xoz0EUrN6FRPB2sdsMG1rhfY+g6t9QvjW1aByiG0SQviRyTD8iQK
V1QcwMC13pPYmXapzxrJ+QvFogzjXyKMQeRmfony3AP5P5Tha4j5E/jDlWIkEkb6
6Hzl9bjdJCADXH4vINVPxR6WhDsAUVgO4dI4oQIDAQABAoIBAQCzdu3r5/s7TZI4
xDoymfB2PdkhwP5KmatuWRcRpDh2q8dOPWb8paVWdVfxiJV34aEXSulwVaWgrv+W
MTuvCq8NuUqMpZ3EJdwB8HgM6fAf+mglIsmpL1mtdWk9+5mwxdmsA2wkUd15CfoI
/Q2COXN4fko1hkE0FC2IsZOsZVLF4FMXgnqe302MXk2uGusEmYShrvCEbCveIYSC
47uPMPAMfWAtkXfKHVTWHBC8src5++50btODiKoBHwUrHLG6D2e/dv+szJQcQol2
ZIOQltc2j7QG/mUQJ44kQknViVXP3yQBiUcCFLJzq7eBLR/HqGZUYXTvGhrKc7Hr
zE3x5rfxAoGBAPcp6wJEW5OhF+CYTTqhFVU3kSDpaJuJbdZn5JldKuZUuBFir0Eo
0ckrSw7rHaaCPwVBhbe0jE3wjXgxbHO09tWohFDar1+ihiXUqpayIAnho5AWkj1K
hB8T/2BHkVrjbms2s7UxuzGhYqa3nHRtAEkKJocV/O3uTy5RvOLt+ki1AoGBAN2B
AvcrRJYjHKP7g+GCJ+H59jcUJxci0sXCHr7vwRuZ+CYOXzvkNc7/qdSMj231ZSKo
ytwzvnyICWSXAvr5SEsO5WKh2AfDMnY+YG8fBqIQtjS2o9onso8AGFcr1ytIjIor
7NQACKx02rqwxNn2bAUO2YcI7VIKf5SdAwRNTj+9AoGBAMx40COS+5OZHJDATnun
UWerTZPFpLWvrr9GObaqfdgI1DIFyuiD5XGgMDsKRQBAFfS6LO46HixISjDZ6lea
qO0+uR/OmnDqmkHnuqxqddjW4yJLmfW8lKrFN2qmKljfd7SYj3jhyHQZh+xWT8d9
eVPzYsY0aYdItBakpjeyGnFVAoGAfNZhHXy9QwC2+5SdV1NLtwhxw8kP3vI5aEtn
mKT3aN72BDzFX7PWv7tHtAskKwzK2yXWbxSanwTshky12Uz1eZgDn/snDfjtT8cI
Apix3FUe28azwhftgrrC/R4wPqy8yILJDxKV0NxrChzmVRGU/6TG5FwbpMlV7iQv
txT6rOECgYEAgQPBBktcreK7xv7fNd0OC0kyHG49pYpnGOLddszOe8vae78SunN4
zc5Ogmn/fqk8UzBpa49wGNtMnavHlvyEfI+ZFZzAMsOv9iN8qXQo8i06gRW3S2YV
iq+9uBNvlRDE76fLDfRg/X5jd3SOw4NC8b2bwJtSqiYMQol2nLXdZJc=
-----END RSA PRIVATE KEY-----"""

TOOL_PRIVATE_KEY_PEM = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEArmvKMXDFoYZLcntMz03TubvlFaMX2Xz/91znD1dmenUjT20s
WwL2ksjV0Sh87lrbD3p19pNTaqxt/16b48bqePkfWh5IustQ3HVxoQslD1DTiMpE
qliqYtVRCST4e0fHOaAzWmqhS5Ve8CJpK0hAlKoukj4zqCNOjGm1t/aIJNVeZjun
MnqOvJB2KU3cp624CDOEaLv4k+PF3NynMM6+gp/GBVDQtmMe0K6A9Yi957aHstxS
zBHNWQLV2Ng5xuX4XKOC27xk1H62U3VfFevPb25ipatcHffe3d1R8NV6ZgLrAXTK
ZH/FsnZsFoVkgFiqIPSbI5EyBg/FekX1BlAB9wIDAQABAoIBAEp7eSJXt+1b/cfr
Y0d7Qpij5hWxSbP0LxIguALTHc3ZS7TVOAW9ZDIWVUg18/ONFNKtRsZ+7zY0X9yX
OBaykNoL+BlxqTkrLWKXPGi66554s3xMc7oSluARm8M96GYspqSzBnrr4ej25k3B
RAvZlMpnSe/lZAW+3gIT+ieOvWCMkCLhqu9txHsbKKiWnfHSG56IcQK2clpOyw/x
bd1D2iE/xldBY93IS7HRHl83IeV1+hSNpEm+eYalzCJ4hyP47iBqlUOUIH5hssiQ
G3vSnC9mcPYWzmOxYVdx61Ts21pTVVL1hqVWtxIpxA0fJmJQrNyfZGkDqEKAEAU3
3Jv4vwECgYEA4Xx6wW8770yGPrPzJcF6rAIzCYHOpKDZLS/icroy4F5ShmSB6Mbw
LMjQ3CufGkBSX0Jx3USiVUhclH2LmjfJQ1bD+J6qrieildxRXr7UktHP2jRIcYZ1
2B7JhL/l2FM+Jbu0WW3+igCCM51pGQ6bttMXv4UoAXvBJ0ZUekjDlTcCgYEAxgZC
Ob6OAUn0C6BRO5sr9CSNwdbHFPi4ef0MqozgVSh5TmtVtegOcDDpeo+l5spj9f7O
q6/899gpPUZBEIHGSAKEzOdO9s/3SLYx4v7x/QXNgsjynj4obUzCb+qN04N1bdIC
uicaEJDskkZCE/9ZUvlyqkFq4R7uffSk5hPxWUECgYEAkfh9l1+lEyMc/NaNn3GD
MnsyAwOPfK/MKB6Jn+++I9Wr4uiJ2OGAdd2CqCVtGBdvu89N2woldMQletNTXoCi
v/8ZWoeMwrVR4WYBHy62el1tCzsxcpyzCTfVCSUZbFNnNhIvjH1SfJAbucI7WUdF
srMw+oD/BwbQYdZ7tbYJNz0CgYEAhEHL23tMpsm4yEcT2iaiLZZ4Yz1Ki9QuibMb
0ZDzh4zXsCt5/Ft3wTC5z5S/bixApRzA9eQ9pV7m9DjG3fp+7rtX7O6US73MX/Dn
0r8J6j8E6lPBzzSelZmNx2e1v83uESIRljjlbKkOiAeKvIZwJz3ZeqLkemTJTrCl
rdEmAcECgYEA1cxZ3PbIPeb5xj8voI21NOgRypeKkOCpQAu3F1fNt2bEclCpwdKf
lMC6tgLPIf0DfSH29CAMXWYsd5AbviY+j/r1IeOBg/gcS+TivQoZ1x/ofOtrjiNf
jy6zm1iI9fl68rWRir5C4G7x3Rhre1ftDCbOk8q/6puixj2zzQrLuN4=
-----END RSA PRIVATE KEY-----
"""

TOOL_KEY_SET = {
    "keys": [
        {
            "kty": "RSA",
            "e": "AQAB",
            # pylint: disable=line-too-long
            "n": "rmvKMXDFoYZLcntMz03TubvlFaMX2Xz_91znD1dmenUjT20sWwL2ksjV0Sh87lrbD3p19pNTaqxt_16b48bqePkfWh5IustQ3HVxoQslD1DTiMpEqliqYtVRCST4e0fHOaAzWmqhS5Ve8CJpK0hAlKoukj4zqCNOjGm1t_aIJNVeZjunMnqOvJB2KU3cp624CDOEaLv4k-PF3NynMM6-gp_GBVDQtmMe0K6A9Yi957aHstxSzBHNWQLV2Ng5xuX4XKOC27xk1H62U3VfFevPb25ipatcHffe3d1R8NV6ZgLrAXTKZH_FsnZsFoVkgFiqIPSbI5EyBg_FekX1BlAB9w",
            "kid": "GJG742QQDFgOPSqJMQdr_Q-nkiJgYjd-WVXPRWkS7D8",
            "alg": "RS256",
            "use": "sig",
        }
    ]
}

PLATFORM_CONFIG = {
    "iss": "http://test-platform.example/",
    "client_id": "test-platform",
    "deployment_id": 1,
    "launch_url": "https://lti-ri.imsglobal.org/lti/tools/3674/launches",
    "oidc_login_url": "https://lti-ri.imsglobal.org/lti/tools/3674/login_initiations",
    "key_set_url": "https://lti-ri.imsglobal.org/lti/tools/3674/.well-known/jwks.json",
    "deeplink_launch_url": "https://lti-ri.imsglobal.org/lti/tools/3674/deep_link_launches",
}


class TestPlatform(LTI1P3PlatformConfAbstract):
    """
    Test platform configuration
    """

    def init_platform_config(self, **kwargs) -> None:
        self._registration = (
            Registration()
            .set_iss(PLATFORM_CONFIG["iss"])
            .set_client_id(PLATFORM_CONFIG["client_id"])
            .set_deployment_id(PLATFORM_CONFIG["deployment_id"])
            .set_oidc_login_url(PLATFORM_CONFIG["oidc_login_url"])
            .set_launch_url(PLATFORM_CONFIG["launch_url"])
            .set_platform_public_key(RSA_PUBLIC_KEY_PEM)
            .set_platform_private_key(RSA_PRIVATE_KEY_PEM)
            .set_tool_key_set(TOOL_KEY_SET)
        )

    def get_registration_by_params(self, **kwargs):
        return self._registration
