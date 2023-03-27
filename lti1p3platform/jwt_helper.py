import typing as t
import jwt


def jwt_encode(
    payload: t.Mapping[str, t.Any],
    key: str,
    algorithm: str = "HS256",
    headers: t.Optional[t.Mapping[str, t.Any]] = None,
    json_encoder: t.Optional[t.Callable[(...), t.Any]] = None,
) -> str:
    """
    PyJWT encode wrapper to handle bytes/str
    In PyJWT 2.0.0, tokens are returned as string instead of a byte string
    But in old version, it still returns a byte string
    """
    encoded_jwt = jwt.encode(payload, key, algorithm, headers, json_encoder)

    if isinstance(encoded_jwt, bytes):
        encoded_jwt = encoded_jwt.decode("utf-8")  # type: ignore

    return encoded_jwt  # type: ignore
