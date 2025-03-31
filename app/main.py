from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from typing import Optional,List
from app.utils.openai_client import get_openai_response
from app.utils.file_handler import save_upload_file_temporarily
from bs4 import BeautifulSoup

# Import the functions you want to test directly
from app.utils.functions import *

app = FastAPI(title="IITM Assignment API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/")
async def process_question(
    question: str = Form(...), file: Optional[UploadFile] = File(None)
):
    try:
        # Save file temporarily if provided
        temp_file_path = None
        if file:
            temp_file_path = await save_upload_file_temporarily(file)

        # Get answer from OpenAI
        answer = await get_openai_response(question, temp_file_path)

        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# New endpoint for testing specific functions
@app.post("/debug/{function_name}")
async def debug_function(
    function_name: str,
    file: Optional[UploadFile] = File(None),
    params: str = Form("{}"),
):
    """
    Debug endpoint to test specific functions directly

    Args:
        function_name: Name of the function to test
        file: Optional file upload
        params: JSON string of parameters to pass to the function
    """
    try:
        # Save file temporarily if provided
        temp_file_path = None
        if file:
            temp_file_path = await save_upload_file_temporarily(file)

        # Parse parameters
        parameters = json.loads(params)

        # Add file path to parameters if file was uploaded
        if temp_file_path:
            parameters["file_path"] = temp_file_path

        # Call the appropriate function based on function_name
        if function_name == "analyze_sales_with_phonetic_clustering":
            result = await analyze_sales_with_phonetic_clustering(**parameters)
            return {"result": result}
        elif function_name == "calculate_prettier_sha256":
            # For calculate_prettier_sha256, we need to pass the filename parameter
            if temp_file_path:
                result = await calculate_prettier_sha256(temp_file_path)
                return {"result": result}
            else:
                return {"error": "No file provided for calculate_prettier_sha256"}
        else:
            return {
                "error": f"Function {function_name} not supported for direct testing"
            }

    except Exception as e:
        import traceback

        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/")
def home():
    return {"message": "TDS Solver API is running!"}
@app.post("/api/sum-data-values")
async def sum_data_values(html: str = Form(...)):
    """
    Extracts all `<div>` elements with class 'foo' from the provided HTML
    and sums their `data-value` attributes.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        divs = soup.select("div.foo")

        values = []
        for div in divs:
            raw_value = div.get("data-value", "0").strip()  # Ensure it's stripped of whitespace
            try:
                value = float(raw_value)
                values.append(value)
            except ValueError:
                continue  # Skip invalid values

        total = sum(values)

        return {"answer": total}  # Debugging: Show extracted values

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/convert-json")
async def convert_json(file: UploadFile = File(...)):
    """
    Convert key=value pairs in the uploaded file to a JSON object and return its SHA-256 hash.
    """
    try:
        # Read file contents and strip unnecessary whitespace
        content = await file.read()
        lines = content.decode("utf-8").strip().splitlines()

        # Convert key=value pairs into a dictionary
        json_data = {}
        for line in lines:
            if "=" in line:
                key, value = map(str.strip, line.split("=", 1))
                json_data[key] = value

        # Convert dictionary to sorted and compact JSON string
        json_str = json.dumps(json_data, sort_keys=True, separators=(",", ":"))

        # Compute SHA-256 hash
        json_hash = hashlib.sha256(json_str.encode()).hexdigest()

        # Print only the hash in the console
        print("Generated Hash:", json_hash)

        return {"answer": json_hash}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)