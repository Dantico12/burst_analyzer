from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class BurstRecord(BaseModel):
    """Model for individual burst record"""
    officer_name: Optional[str] = Field(None, description="Name of the officer who fixed the burst")
    burst_date: Optional[datetime] = Field(None, description="Date when the burst occurred")
    pipe_size: Optional[str] = Field(None, description="Size of the pipe that burst")
    region: Optional[str] = Field(None, description="Region where the burst occurred")
    burst_location: Optional[str] = Field(None, description="Specific location of the burst")

class SummaryStats(BaseModel):
    """Model for summary statistics"""
    total_bursts: int = Field(description="Total number of bursts")
    unique_officers: int = Field(description="Number of unique officers")
    unique_regions: int = Field(description="Number of unique regions")
    unique_pipe_sizes: int = Field(description="Number of unique pipe sizes")
    date_range: Dict[str, str] = Field(description="Start and end dates")
    missing_data: Dict[str, int] = Field(description="Count of missing data by field")
    top_officers: Dict[str, int] = Field(description="Top officers by burst count")
    region_distribution: Dict[str, int] = Field(description="Distribution by region")
    pipe_size_distribution: Dict[str, int] = Field(description="Distribution by pipe size")

class OfficerData(BaseModel):
    """Model for officer-specific data"""
    total_bursts: int = Field(description="Total bursts fixed by officer")
    burst_by_date: List[Dict[str, Any]] = Field(description="Bursts grouped by date")
    burst_by_pipe_size: List[Dict[str, Any]] = Field(description="Bursts grouped by pipe size")
    burst_by_region: List[Dict[str, Any]] = Field(description="Bursts grouped by region")
    raw_records: List[Dict[str, Any]] = Field(description="Raw records for this officer")

class ProcessedData(BaseModel):
    """Model for processed data response"""
    raw_data: List[Dict[str, Any]] = Field(description="Raw data records")
    grouped_data: Dict[str, OfficerData] = Field(description="Data grouped by officer")
    summary_stats: SummaryStats = Field(description="Summary statistics")
    total_records: int = Field(description="Total number of records")

class UploadResponse(BaseModel):
    """Model for upload response"""
    success: bool = Field(description="Upload success status")
    message: str = Field(description="Response message")
    file_id: Optional[str] = Field(None, description="Unique identifier for uploaded file")
    filename: Optional[str] = Field(None, description="Original filename")
    processed_data: Optional[ProcessedData] = Field(None, description="Processed data if successful")

class ReportRequest(BaseModel):
    """Model for report generation request"""
    file_id: str = Field(description="File identifier")
    report_type: str = Field(description="Type of report (summary, detailed, officer_specific)")
    officer_name: Optional[str] = Field(None, description="Specific officer for officer_specific reports")
    include_graphs: bool = Field(True, description="Whether to include graphs in report")

class ReportResponse(BaseModel):
    """Model for report generation response"""
    success: bool = Field(description="Report generation success status")
    message: str = Field(description="Response message")
    report_url: Optional[str] = Field(None, description="URL to download the report")
    report_filename: Optional[str] = Field(None, description="Generated report filename")