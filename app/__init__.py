"""
Burst Analyzer Application Package

This package contains the FastAPI application for analyzing water pipe burst data.
"""

__version__ = "1.0.0"
__author__ = "Burst Analyzer Team"
__description__ = "Water Pipe Burst Analysis Application"

# Import main components for easy access
from .main import app
from .models import (
    BurstRecord,
    SummaryStats,
    OfficerData,
    ProcessedData,
    UploadResponse,
    ReportRequest,
    ReportResponse
)

__all__ = [
    "app",
    "BurstRecord",
    "SummaryStats", 
    "OfficerData",
    "ProcessedData",
    "UploadResponse",
    "ReportRequest",
    "ReportResponse"
]
