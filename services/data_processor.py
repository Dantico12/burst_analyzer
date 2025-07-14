import pandas as pd
import numpy as np
import re
from datetime import datetime
import json

class DataProcessor:
    def __init__(self):
        self.expected_columns = ['officer_name', 'burst_date', 'pipe_size', 'region', 'burst_location']
    
    def process_excel_file(self, file_path):
        """Process the uploaded Excel file and return structured data"""
        try:
            # Read Excel file
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, engine='openpyxl')
            else:
                df = pd.read_excel(file_path)
            
            # Clean column names
            df.columns = [self.clean_column_name(col) for col in df.columns]
            
            # Map columns to expected names
            column_mapping = self.map_columns(df.columns)
            df = df.rename(columns=column_mapping)
            
            # Ensure all required columns exist
            for col in self.expected_columns:
                if col not in df.columns:
                    df[col] = None
            
            # Process and clean data
            processed_data = self.clean_and_sort_data(df)
            
            return processed_data
            
        except Exception as e:
            raise Exception(f"Error processing Excel file: {str(e)}")
    
    def clean_column_name(self, name):
        """Clean and standardize column names"""
        if not isinstance(name, str):
            return str(name)
        return re.sub(r'\W+', '_', name.lower().strip())
    
    def map_columns(self, columns):
        """Map actual columns to expected columns"""
        mapping = {}
        for col in columns:
            col_lower = col.lower()
            if 'officer' in col_lower or 'name' in col_lower:
                mapping[col] = 'officer_name'
            elif 'date' in col_lower or 'time' in col_lower:
                mapping[col] = 'burst_date'
            elif 'pipe' in col_lower or 'size' in col_lower:
                mapping[col] = 'pipe_size'
            elif 'region' in col_lower or 'area' in col_lower:
                mapping[col] = 'region'
            elif 'location' in col_lower or 'address' in col_lower:
                mapping[col] = 'burst_location'
        return mapping
    
    def clean_and_sort_data(self, df):
        """Clean and sort the data according to requirements"""
        
        # Convert date column to datetime
        if 'burst_date' in df.columns:
            df['burst_date'] = pd.to_datetime(df['burst_date'], errors='coerce')
        
        # Fill NaN values with 'Unknown' for categorical columns
        categorical_cols = ['officer_name', 'region', 'burst_location']
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].fillna('Unknown')
        
        # Handle pipe size - convert to string and fill NaN
        if 'pipe_size' in df.columns:
            df['pipe_size'] = df['pipe_size'].astype(str).replace('nan', 'Unknown')
        
        # Sort data by officer name, then by burst date
        df_sorted = df.sort_values(['officer_name', 'burst_date'], na_position='last')
        
        # Group data by officer
        grouped_data = self.group_by_officer(df_sorted)
        
        # Generate summary statistics
        summary_stats = self.generate_summary_stats(df_sorted)
        
        # Generate region and pipe size summaries
        region_summary = self.generate_region_summary(df_sorted)
        pipe_size_summary = self.generate_pipe_size_summary(df_sorted)
        monthly_trends = self.generate_monthly_trends(df_sorted)
        
        return {
            'raw_data': df_sorted.to_dict('records'),
            'grouped_data': grouped_data,
            'summary_stats': summary_stats,
            'region_summary': region_summary,
            'pipe_size_summary': pipe_size_summary,
            'monthly_trends': monthly_trends,
            'total_records': len(df_sorted)
        }
    
    def group_by_officer(self, df):
        """Group data by officer name"""
        grouped = {}
        
        for officer in df['officer_name'].unique():
            officer_data = df[df['officer_name'] == officer]
            
            # Get pipe size counts
            pipe_size_counts = officer_data['pipe_size'].value_counts().to_dict()
            most_common_pipe = officer_data['pipe_size'].mode().iloc[0] if not officer_data['pipe_size'].empty else 'Unknown'
            
            # Get unique regions
            unique_regions = officer_data['region'].nunique()
            
            grouped[officer] = {
                'count': len(officer_data),
                'unique_regions': unique_regions,
                'pipe_size_counts': pipe_size_counts,
                'most_common_pipe_size': most_common_pipe,
                'records': officer_data.to_dict('records')
            }
        
        return grouped
    
    def generate_region_summary(self, df):
        """Generate region summary statistics"""
        region_summary = {}
        
        for region in df['region'].unique():
            region_data = df[df['region'] == region]
            
            # Get top officer in this region
            top_officer = region_data['officer_name'].value_counts().index[0] if not region_data['officer_name'].empty else 'Unknown'
            
            # Get most common pipe size
            most_common_pipe = region_data['pipe_size'].mode().iloc[0] if not region_data['pipe_size'].empty else 'Unknown'
            
            region_summary[region] = {
                'count': len(region_data),
                'top_officer': top_officer,
                'most_common_pipe_size': most_common_pipe,
                'unique_officers': region_data['officer_name'].nunique()
            }
        
        return region_summary
    
    def generate_pipe_size_summary(self, df):
        """Generate pipe size summary statistics"""
        pipe_size_summary = {}
        
        for pipe_size in df['pipe_size'].unique():
            pipe_data = df[df['pipe_size'] == pipe_size]
            
            # Get top region for this pipe size
            top_region = pipe_data['region'].value_counts().index[0] if not pipe_data['region'].empty else 'Unknown'
            
            # Get top officer for this pipe size
            top_officer = pipe_data['officer_name'].value_counts().index[0] if not pipe_data['officer_name'].empty else 'Unknown'
            
            pipe_size_summary[pipe_size] = {
                'count': len(pipe_data),
                'top_region': top_region,
                'top_officer': top_officer
            }
        
        return pipe_size_summary
    
    def generate_monthly_trends(self, df):
        """Generate monthly trends data"""
        if 'burst_date' not in df.columns or df['burst_date'].isna().all():
            return {}
        
        # Group by month
        df['month'] = df['burst_date'].dt.to_period('M')
        monthly_counts = df.groupby('month').size().to_dict()
        
        # Convert period keys to strings
        return {str(k): v for k, v in monthly_counts.items()}
    
    def generate_summary_stats(self, df):
        """Generate summary statistics for the data"""
        stats = {
            'total_bursts': len(df),
            'unique_officers': df['officer_name'].nunique(),
            'unique_regions': df['region'].nunique(),
            'unique_pipe_sizes': df['pipe_size'].nunique(),
            'date_range': {
                'start': df['burst_date'].min().strftime('%Y-%m-%d') if pd.notna(df['burst_date'].min()) else 'Unknown',
                'end': df['burst_date'].max().strftime('%Y-%m-%d') if pd.notna(df['burst_date'].max()) else 'Unknown'
            },
            'missing_data': {
                'officer_name': df['officer_name'].isna().sum(),
                'burst_date': df['burst_date'].isna().sum(),
                'pipe_size': (df['pipe_size'] == 'Unknown').sum(),
                'region': (df['region'] == 'Unknown').sum(),
                'burst_location': (df['burst_location'] == 'Unknown').sum()
            }
        }
        
        # Top performers
        officer_counts = df.groupby('officer_name').size().sort_values(ascending=False)
        stats['top_officers'] = officer_counts.head(10).to_dict()
        
        # Region distribution
        region_counts = df.groupby('region').size().sort_values(ascending=False)
        stats['region_distribution'] = region_counts.to_dict()
        
        # Pipe size distribution
        pipe_size_counts = df.groupby('pipe_size').size().sort_values(ascending=False)
        stats['pipe_size_distribution'] = pipe_size_counts.to_dict()
        
        return stats
    
    def generate_analytics(self, data):
        """Generate analytics data for visualization"""
        try:
            raw_data = data['raw_data']
            df = pd.DataFrame(raw_data)
            
            # Convert date strings back to datetime
            df['burst_date'] = pd.to_datetime(df['burst_date'])
            
            analytics = {
                'daily_trends': self.get_daily_trends(df),
                'officer_performance': self.get_officer_performance(df),
                'regional_analysis': self.get_regional_analysis(df),
                'pipe_size_analysis': self.get_pipe_size_analysis(df)
            }
            
            return analytics
            
        except Exception as e:
            raise Exception(f"Error generating analytics: {str(e)}")
    
    def get_daily_trends(self, df):
        """Get daily burst trends"""
        daily_counts = df.groupby(df['burst_date'].dt.date).size().reset_index(name='count')
        return {
            'dates': daily_counts['burst_date'].astype(str).tolist(),
            'counts': daily_counts['count'].tolist()
        }
    
    def get_officer_performance(self, df):
        """Get officer performance data"""
        officer_stats = df.groupby('officer_name').agg({
            'burst_date': 'count',
            'pipe_size': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown'
        }).reset_index()
        
        officer_stats.columns = ['officer', 'total_bursts', 'most_common_pipe_size']
        officer_stats = officer_stats.sort_values('total_bursts', ascending=False)
        
        return officer_stats.to_dict('records')
    
    def get_regional_analysis(self, df):
        """Get regional analysis data"""
        regional_stats = df.groupby('region').agg({
            'burst_date': 'count',
            'officer_name': 'nunique'
        }).reset_index()
        
        regional_stats.columns = ['region', 'total_bursts', 'unique_officers']
        regional_stats = regional_stats.sort_values('total_bursts', ascending=False)
        
        return regional_stats.to_dict('records')
    
    def get_pipe_size_analysis(self, df):
        """Get pipe size analysis data"""
        pipe_stats = df.groupby('pipe_size').size().reset_index(name='count')
        pipe_stats = pipe_stats.sort_values('count', ascending=False)
        
        return {
            'pipe_sizes': pipe_stats['pipe_size'].tolist(),
            'counts': pipe_stats['count'].tolist()
        }