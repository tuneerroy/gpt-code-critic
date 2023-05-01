import os
import secrets
from code_checker import analyze_code_with_gpt3

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI()
security = HTTPBasic()
auth_user = os.getenv("ADMIN_USERNAME", None)
auth_password = os.getenv("ADMIN_PASSWORD", None)
auth_required = os.getenv("AUTH_REQUIRED", "false").lower() in ["true", "t"]


def get_admin_username(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    if not auth_required:
        return "guestuser"
    correct_username = secrets.compare_digest(credentials.username, auth_user)
    correct_password = secrets.compare_digest(credentials.password, auth_password)
    if auth_required and not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/")
def test():
    return {"status": "ok"}

@app.post("/analysis")
def analyze_code(code: str, username: str = Depends(get_admin_username)):
    print(analyze_code_with_gpt3(code))
    return {"analysis": "chill"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)