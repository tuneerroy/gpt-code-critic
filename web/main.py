from typing import List

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from code_checker import get_sarif_report, is_valid_key

app = FastAPI()


class File(BaseModel):
    name: str
    code: str


class CodeChanges(BaseModel):
    key: str
    files: List[File]


"""
Test endpoint to check if the server is running

Returns:
    status of the server
"""


@app.get("/")
def test():
    return {"status": "ok"}


"""
Analysis endpoint for code changes

Args:
    code_changes: the code changes to analyze 

Returns:
    analysis: the analysis of the code changes
"""


@app.post("/analyze")
def analyze_code(code_changes: CodeChanges):
    # check if key and files are present
    if not (code_changes.key and code_changes.files):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Key and files are required",
        )

    # check if file limit is not exceeded
    if len(code_changes.files) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files are allowed",
        )

    # check that each file is valid
    for file in code_changes.files:
        if not (file.name and file.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name and code are required for each file",
            )

    # check that key is valid
    if not is_valid_key(code_changes.key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid key",
        )

    # get SARIF report
    code_strings = {file.name: file.code for file in code_changes.files}
    analysis = get_sarif_report(code_changes.key, code_strings)

    # TODO: remove this after testing
    print(analysis)

    return {"analysis": analysis}


"""
Starts the server
"""
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
