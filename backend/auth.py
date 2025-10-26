from fastapi import HTTPException, Request, status
from jose import jwt, JWTError
import httpx
import os
from dotenv import load_dotenv
from typing import Any, Dict, Optional

load_dotenv()

AUTH0_DOMAIN: str = os.getenv("AUTH0_DOMAIN", "")
API_AUDIENCE: str = os.getenv("API_AUDIENCE", "")
ALGORITHMS: list[str] = [os.getenv("ALGORITHMS", "RS256")]

_jwks_cache: Optional[Dict[str, Any]] = None


async def get_jwks() -> Dict[str, Any]:
    """Fetch and cache the JSON Web Key Set (JWKS) from Auth0."""
    global _jwks_cache

    if _jwks_cache is None:
        if not AUTH0_DOMAIN:
            raise RuntimeError(
                "AUTH0_DOMAIN not set in environment variables.")

        domain = AUTH0_DOMAIN if AUTH0_DOMAIN.startswith(
            "https://") else f"https://{AUTH0_DOMAIN}"
        url = f"{domain}/.well-known/jwks.json"

        timeout = httpx.Timeout(30.0, connect=10.0)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
                response.raise_for_status()
                _jwks_cache = response.json()
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch JWKS from Auth0 (timeout)"
            )
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to fetch JWKS from Auth0: {str(e)}"
            )

    return _jwks_cache


async def verify_jwt(request: Request) -> Dict[str, Any]:
    """Verify the JWT in the Authorization header and return its payload."""
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.split(" ")[1]
    jwks = await get_jwks()

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid JWT header")

    rsa_key = next(
        (
            {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
            for key in jwks["keys"]
            if key["kid"] == unverified_header.get("kid")
        ),
        None,
    )

    if rsa_key is None:
        raise HTTPException(
            status_code=401, detail="Invalid header: no matching key"
        )

    domain = AUTH0_DOMAIN if AUTH0_DOMAIN.startswith(
        "https://") else f"https://{AUTH0_DOMAIN}"
    issuer = f"{domain}/"

    expected_audience = API_AUDIENCE.rstrip('/')

    try:
        payload_unverified = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            issuer=issuer,
            options={"verify_aud": False}
        )

        token_audiences = payload_unverified.get("aud", [])
        if isinstance(token_audiences, str):
            token_audiences = [token_audiences]

        normalized_audiences = [aud.rstrip('/') for aud in token_audiences]

        if expected_audience not in normalized_audiences:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid audience. Expected: {expected_audience}, Got: {normalized_audiences}"
            )

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            issuer=issuer,
            options={"verify_aud": False}
        )

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTClaimsError as e:
        raise HTTPException(status_code=401, detail=f"Invalid claims: {e}")
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token invalid: {e}")

    return payload


def require_scope(payload: Dict[str, Any], required_scope: str) -> None:
    """Ensure the token contains the required scope."""
    token_scopes = payload.get("scope", "")

    if isinstance(token_scopes, str):
        scopes = token_scopes.split() if token_scopes else []
    else:
        scopes = token_scopes if token_scopes else []

    permissions = payload.get("permissions", [])
    all_scopes = scopes + permissions

    if required_scope not in all_scopes:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient scope. Required: {required_scope}"
        )
