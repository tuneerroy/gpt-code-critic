import os
import secrets
from code_checker import get_sarif_report

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import List

app = FastAPI()
security = HTTPBasic()
auth_user = os.getenv("ADMIN_USERNAME", None)
auth_password = os.getenv("ADMIN_PASSWORD", None)
auth_required = os.getenv("AUTH_REQUIRED", "false").lower() in ["true", "t"]

class File(BaseModel):
    name: str
    code: str

class CodeChanges(BaseModel):
    key: str
    files: List[File]


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

@app.get("/test")
def test():
    return {"status": "success"}

@app.post("/analyze")
def analyze_code(code_changes: CodeChanges, username: str = Depends(get_admin_username)):
    code_strings = {file.name: file.code for file in code_changes.files}
    analysis = get_sarif_report(code_changes.key, code_strings)
    print(analysis)
    return {"analysis": analysis}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
