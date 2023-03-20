import jwt

def jwt_encode(*args, **kwargs) -> str:
    """
    PyJWT encode wrapper to handle bytes/str
    In PyJWT 2.0.0, tokens are returned as string instead of a byte string
    But in old version, it still returns a byte string
    """
    encoded_jwt = jwt.encode(*args, **kwargs)
    
    if isinstance(encoded_jwt, bytes):
        encoded_jwt = encoded_jwt.decode('utf-8')
        
    return encoded_jwt
