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
MIIEpQIBAAKCAQEA13RQ2jOgxvTtyJIn/RvLWD9Wa2Vjm91gulIfZJ1gVAhKMWSu
grecxEKkebQjCNGifNUJJdICNPBbWNeHN0QyGXXQ12odlOMaC60MUPhD9XE7lSwr
kuWdb+YICTKfjV9WQdT3zfGWAjwqZPp1+uRysaukS3ChZ8gkrWiZtKIcn0hoBsql
zBAjT0Tr5TSrqYKDkUKqLPFSPktQYB2ynKHah23/E9kdb02Wc1XYFMa5XCjil6qE
ZBaXaC88x4ccJaahqzO4pmRkuNnz3VoiiPbUluVUlxspMLrTMI9TBUW7tl9omo9r
lXpwZ7zVFINx85f3Wle88TQoXMQWFTlYu/qcTQIDAQABAoIBAQCFrV904s+AYfse
lMBG5HXX/QRLgg65aDNZpxZfQN3BhZsy5jr4U5/qjUarVD7ge+EK/sq8Mn64BeFH
UAJPIfrLnTPEU8yi0f0Y/XdEzaSspmLHfS5T6C80fE7EFiq0dlB4bACMQLZIELhl
Cpkk35Th85LuU6VxVNac2Od1EZgcopaO6FcmB7VZ6LMdlwSkmDe1AwG1m5GOV1vY
/HGV+l/FsYfuILRaftf5xOcy8L/NI9JY6pUMiSo+uhIwNyK0bFsaGlgdBS6g3xE2
6/1ARhx+rX+U2wvRNRwG6RCXu2l/LTSeCRg8kl40pcTisw/d5SaZwOs7DhC4ag9B
qVRJfgIpAoGBAPFIOO6yTiFdrHHEwh+c6MHKFw3ArKnkU8OO/K2O6xE6iKcT5wpm
ZGKAoNvSPcHkeh53a2x//wabU/XSKAJiUb0skPEHdvIUQAbENAd9xPh+PxGEo95v
YZDm0jcYXym0ORHzb7so7ze6w+6qy7TegsKMScc2cv3fvR+Yg2MTES0LAoGBAOSY
xrASeXiieDk3FhkXG/PIvWRi6svsXSaLsm/HAyspdHMjCM/QMNihPw8Sn9DWT51T
mg4pyQbfVsuL26njrDsfPs0Qe6wZID2FWoLFkTLVvNmG6/yfa8k4N4cgFeT7v7Fn
w75W/uu40jV/drl820GuMC18PdyxxL7iZZzlecMHAoGBAKk32M33eXpHIykLMIZR
WqCG5lI73hysyN5vSuFCSbRkk/BxsekGVMMMqURiF/QDFG6HnGyU/Dwa9fCCepLp
d6AwQFr6vD4dW6YjNsZGO713dS4JE5BuF0Qzzhzb1+n8vsXLMIJXvCYes0mQuZtZ
LuXY0+mGU3Gf2Bjvsr3qYnJvAoGBAI/FTmD6nY8zj61cafeJwzjF7eevFsD+fW96
uNT4M5P31Jd9V1NsOuxkLYbLTdxIjXYDWIbD3P0Hhk0qPxNQb8gXVKYgUcfhXZeT
wWMx4qo4JzggVVdi5KV/R90iXuLPOrbW7hNOH7IdYYfoDMGIN1XNudtBop6k53qu
ZP4SjUwNAoGAP2J8zmk1bCiOFeEr09RoklDrxrQNsTVxq62CTI4fbLkFrUKU39oP
phmY0dz+06Y0cG1sVb6nTPTSlgnFYcbt1bxrSHDhBfKYUpFfsnzdjmOcFi/V66Gj
RknVRS1vcTKNlcfdmUJk5Y8z87nFETwsdACzVMJnnvTj9Ct0CpAwk0A=
-----END RSA PRIVATE KEY-----
"""

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
            .set_tool_key_set_url(PLATFORM_CONFIG["key_set_url"])
        )

    def get_registration_by_params(self, **kwargs):
        return self._registration
