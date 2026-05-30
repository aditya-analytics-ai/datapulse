import httpx
import secrets
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, FRONTEND_URL
from app.auth import create_access_token, get_user_by_email, create_user

router = APIRouter(prefix="/api/auth", tags=["google-auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

print(f"[Google OAuth] Loaded CLIENT_ID: {'SET' if GOOGLE_CLIENT_ID else 'MISSING'}")
print(f"[Google OAuth] Loaded REDIRECT_URI: {GOOGLE_REDIRECT_URI}")


@router.get("/google")
def google_login():
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    print(f"[Google OAuth] /google hit — redirect_uri={GOOGLE_REDIRECT_URI}")

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    query = urllib.parse.urlencode(params)
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{query}")


@router.get("/google/callback")
async def google_callback(code: str = None, error: str = None, db: Session = Depends(get_db)):
    if error or not code:
        print(f"[Google OAuth] Callback error param: {error}")
        return RedirectResponse(f"{FRONTEND_URL}/login?error=google_denied")

    print(f"[Google OAuth] Got code, exchanging for token...")

    # Exchange code for tokens
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_res = await client.post(GOOGLE_TOKEN_URL, data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            })

        print(f"[Google OAuth] Token exchange status: {token_res.status_code}")
        print(f"[Google OAuth] Token exchange body: {token_res.text[:500]}")

        if token_res.status_code != 200:
            return RedirectResponse(f"{FRONTEND_URL}/login?error=token_failed")

        tokens = token_res.json()
        access_token = tokens.get("access_token")

        if not access_token:
            print("[Google OAuth] No access_token in response!")
            return RedirectResponse(f"{FRONTEND_URL}/login?error=token_failed")

    except Exception as e:
        print(f"[Google OAuth] Token exchange exception: {e}")
        return RedirectResponse(f"{FRONTEND_URL}/login?error=token_failed")

    # Get user info from Google
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            user_res = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )

        print(f"[Google OAuth] Userinfo status: {user_res.status_code}")

        if user_res.status_code != 200:
            return RedirectResponse(f"{FRONTEND_URL}/login?error=userinfo_failed")

        google_user = user_res.json()

    except Exception as e:
        print(f"[Google OAuth] Userinfo exception: {e}")
        return RedirectResponse(f"{FRONTEND_URL}/login?error=userinfo_failed")

    email = google_user.get("email")
    name = google_user.get("name", email or "User")
    google_id = str(google_user.get("id", ""))
    picture = google_user.get("picture", "")

    if not email:
        return RedirectResponse(f"{FRONTEND_URL}/login?error=no_email")

    print(f"[Google OAuth] User: {email} ({name})")

    # Find or create user in DB
    try:
        user = get_user_by_email(db, email)
        if not user:
            user = create_user(db, name, email, secrets.token_hex(32))
            user.google_id = google_id
            user.avatar = picture
            db.commit()
            db.refresh(user)
        else:
            # Update avatar/google_id if missing
            if not user.google_id:
                user.google_id = google_id
                user.avatar = picture
                db.commit()
    except Exception as e:
        print(f"[Google OAuth] DB exception: {e}")
        return RedirectResponse(f"{FRONTEND_URL}/login?error=db_error")

    # Generate JWT
    jwt_token = create_access_token({"sub": user.email})

    # Redirect to frontend with token
    encoded_name = urllib.parse.quote(name)
    encoded_avatar = urllib.parse.quote(picture)
    redirect_url = f"{FRONTEND_URL}/auth/google/callback?token={jwt_token}&name={encoded_name}&avatar={encoded_avatar}"
    print(f"[Google OAuth] Redirecting to frontend: success")
    return RedirectResponse(redirect_url)
