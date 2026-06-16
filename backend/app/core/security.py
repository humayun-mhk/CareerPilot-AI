from .config import ENVIRONMENT, JWT_SECRET_KEY


def get_jwt_secret_key() -> str:
    if JWT_SECRET_KEY:
        return JWT_SECRET_KEY
    if ENVIRONMENT == "production":
        raise RuntimeError("JWT_SECRET_KEY must be set in production.")
    return ""
