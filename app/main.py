from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import os
import uuid
from datetime import datetime
import traceback
import json
import numpy as np
import math

# Custom JSON encoder for pandas/numpy objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if pd.isna(obj):
            return None
        elif isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
            return obj.isoformat()
        elif isinstance(obj, pd.Period):
            return str(obj)
        elif isinstance(obj, pd.Timedelta):
            return str(obj)
        elif isinstance(obj, pd.Interval):
            return str(obj)
        elif isinstance(obj, pd.Categorical):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32, np.float16)):
            # Handle problematic float values
            if math.isnan(obj) or math.isinf(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, float):
            # Handle regular Python float values
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        elif hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, 'item'):  # numpy scalars
            item_val = obj.item()
            # Check if the item is a problematic float
            if isinstance(item_val, float) and (math.isnan(item_val) or math.isinf(item_val)):
                return None
            return item_val
        elif hasattr(obj, '__array__'):  # array-like objects
            return obj.tolist()
        return super().default(obj)

def clean_for_json(obj):
    """Recursively clean data structure for JSON serialization"""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(item) for item in obj]
    elif isinstance(obj, (float, np.floating)):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, (int, np.integer)):
        return int(obj)
    elif pd.isna(obj):
        return None
    elif isinstance(obj, (pd.Timestamp, pd.Period, pd.Timedelta)):
        return str(obj)
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj

def safe_json_response(data):
    """Create a JSONResponse with proper handling of pandas/numpy objects"""
    try:
        # First clean the data
        cleaned_data = clean_for_json(data)
        # Then use the custom encoder
        json_str = json.dumps(cleaned_data, cls=CustomJSONEncoder)
        return JSONResponse(content=json.loads(json_str))
    except Exception as e:
        print(f"Error in safe_json_response: {e}")
        # Fallback: convert to string representation
        fallback_data = {
            "success": False,
            "error": "Data serialization error",
            "details": str(e)
        }
        return JSONResponse(content=fallback_data)

try:
    from services.data_processor import DataProcessor
    from services.report_generator import ReportGenerator
except ImportError as e:
    print(f"Warning: Could not import services: {e}")
    print("Make sure services/data_processor.py and services/report_generator.py exist")
    # Create placeholder classes for testing
    class DataProcessor:
        def process_excel_file(self, file_path):
            # Placeholder implementation
            df = pd.read_excel(file_path)
            
            # Clean the dataframe of problematic values
            df = df.replace([np.inf, -np.inf], np.nan)
            
            # Convert problematic pandas types to JSON-serializable formats
            for col in df.columns:
                if df[col].dtype == 'datetime64[ns]' or pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].astype(str)
                elif df[col].dtype == 'period[M]' or pd.api.types.is_period_dtype(df[col]):
                    df[col] = df[col].astype(str)
                elif pd.api.types.is_categorical_dtype(df[col]):
                    df[col] = df[col].astype(str)
                elif pd.api.types.is_numeric_dtype(df[col]):
                    # Handle numeric columns specially
                    df[col] = df[col].replace([np.inf, -np.inf], np.nan)
                elif df[col].dtype == 'object':
                    # Handle mixed types in object columns
                    df[col] = df[col].astype(str)
            
            # Convert to records and ensure all values are JSON serializable
            records = []
            for record in df.to_dict('records'):
                clean_record = {}
                for key, value in record.items():
                    if pd.isna(value):
                        clean_record[key] = None
                    elif isinstance(value, (pd.Timestamp, pd.Period, pd.Timedelta)):
                        clean_record[key] = str(value)
                    elif isinstance(value, (np.int64, np.int32, np.float64, np.float32)):
                        if isinstance(value, (np.float64, np.float32)):
                            if math.isnan(value) or math.isinf(value):
                                clean_record[key] = None
                            else:
                                clean_record[key] = float(value)
                        else:
                            clean_record[key] = int(value)
                    elif isinstance(value, float):
                        if math.isnan(value) or math.isinf(value):
                            clean_record[key] = None
                        else:
                            clean_record[key] = value
                    else:
                        clean_record[key] = str(value)
                records.append(clean_record)
            
            # Calculate summary statistics safely
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            unique_counts = {}
            
            for i, col in enumerate(df.columns):
                if i < 3:  # First 3 columns
                    try:
                        unique_count = df[col].nunique()
                        unique_counts[i] = int(unique_count) if not pd.isna(unique_count) else 0
                    except:
                        unique_counts[i] = 0
            
            return {
                "total_records": len(df),
                "summary_stats": {
                    "unique_officers": unique_counts.get(0, 0),
                    "unique_regions": unique_counts.get(1, 0),
                    "unique_pipe_sizes": unique_counts.get(2, 0),
                    "date_range": {"start": "2024-01-01", "end": "2024-12-31"}
                },
                "grouped_data": {},
                "region_summary": {},
                "pipe_size_summary": {},
                "monthly_trends": {},
                "raw_data": records
            }
        
        def generate_analytics(self, data):
            return {"message": "Analytics placeholder"}
    
    class ReportGenerator:
        def generate_excel_report(self, data):
            # Placeholder implementation
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.xlsx"
            filepath = f"reports/{filename}"
            
            # Create a simple Excel file
            df = pd.DataFrame(data.get('raw_data', []))
            df.to_excel(filepath, index=False)
            return filepath

app = FastAPI(title="Burst Data Analyzer", version="1.0.0")

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("reports", exist_ok=True)
os.makedirs("app/static", exist_ok=True)
os.makedirs("app/templates", exist_ok=True)

# Initialize services
data_processor = DataProcessor()
report_generator = ReportGenerator()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        print(f"1. Received file: {file.filename}")
        
        # Validate file type
        if not file.filename or not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files are allowed")
        
        print("2. File validation passed")
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_path = f"uploads/{file_id}_{file.filename}"
        
        print(f"3. Saving file to: {file_path}")
        
        # Ensure uploads directory exists
        os.makedirs("uploads", exist_ok=True)
        
        # Read and save file content
        content = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        print(f"4. File saved successfully, size: {len(content)} bytes")
        
        # Verify file was saved
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")
        
        print("5. File existence verified")
        
        # Process the data
        print("6. Processing data...")
        try:
            processed_data = data_processor.process_excel_file(file_path)
            print("7. Data processing completed successfully")
        except Exception as process_error:
            print(f"8. Error during data processing: {process_error}")
            traceback.print_exc()
            # Clean up file before raising error
            try:
                os.remove(file_path)
            except:
                pass
            raise HTTPException(status_code=500, detail=f"Data processing error: {str(process_error)}")
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
            print("9. Temporary file cleaned up")
        except Exception as cleanup_error:
            print(f"10. Warning: Could not clean up file: {cleanup_error}")
        
        print("11. About to return JSON response")
        
        response_data = {
            "success": True,
            "data": processed_data,
            "file_id": file_id
        }
        
        return safe_json_response(response_data)
        
    except HTTPException as he:
        print(f"HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        print(f"Error type: {type(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.post("/generate-report")
async def generate_report(request: Request):
    try:
        body = await request.json()
        data = body.get("data")
        report_type = body.get("report_type", "all")  # Default to all reports
        
        if not data:
            raise HTTPException(status_code=400, detail="No data provided")
        
        # Generate report based on selection
        report_path = report_generator.generate_excel_report(data, report_type)
        
        return safe_json_response({
            "success": True,
            "report_path": report_path,
            "download_url": f"/download/{os.path.basename(report_path)}"
        })
        
    except Exception as e:
        print(f"Report generation error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/download/{filename}")
async def download_report(filename: str):
    file_path = f"reports/{filename}"
    if os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename
        )
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/analytics")  # Changed from GET to POST
async def get_analytics(request: Request):
    try:
        body = await request.json()
        data = body.get("data")
        
        if not data:
            raise HTTPException(status_code=400, detail="No data provided")
        
        # Generate analytics
        analytics = data_processor.generate_analytics(data)
        
        return safe_json_response({
            "success": True,
            "analytics": analytics
        })
        
    except Exception as e:
        print(f"Analytics error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)