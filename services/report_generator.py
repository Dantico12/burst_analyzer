import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import xlsxwriter
from datetime import datetime
import os
import io
import base64

class ReportGenerator:
    def __init__(self):
        self.output_dir = "reports"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_excel_report(self, data, report_type="all"):
        """Generate report based on selected type"""
        self.validate_data_structure(data)
        
        if report_type == "all":
            return self.generate_comprehensive_report(data)
        else:
            return self.generate_single_report(data, report_type)

    def validate_data_structure(self, data):
        """Ensure required data structure exists before report generation"""
        required_keys = ['summary_stats', 'raw_data']
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required data key: {key}")
                
        # Additional validation for raw_data
        if not isinstance(data['raw_data'], list) or len(data['raw_data']) == 0:
            raise ValueError("raw_data must be a non-empty list of records")

    def generate_comprehensive_report(self, data):
        """Generate the comprehensive 6-sheet report"""
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"burst_analysis_report_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        # Create Excel writer object
        workbook = xlsxwriter.Workbook(filepath)
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4472C4',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left'
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0'
        })
        
        # 1. Summary Sheet
        self.create_summary_sheet(workbook, data, header_format, cell_format, number_format)
        
        # 2. Raw Data Sheet
        self.create_raw_data_sheet(workbook, data, header_format, cell_format)
        
        # 3. Officer Analysis Sheet
        self.create_officer_analysis_sheet(workbook, data, header_format, cell_format, number_format)
        
        # 4. Regional Analysis Sheet
        self.create_regional_analysis_sheet(workbook, data, header_format, cell_format, number_format)
        
        # 5. Pipe Size Analysis Sheet
        self.create_pipe_size_analysis_sheet(workbook, data, header_format, cell_format, number_format)
        
        # 6. Charts Sheet
        self.create_charts_sheet(workbook, data, header_format)
        
        workbook.close()
        
        return filepath

    def generate_single_report(self, data, report_type):
        """Generate a single-sheet report based on selection"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"burst_{report_type}_report_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        workbook = xlsxwriter.Workbook(filepath)
        
        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4472C4',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'border': 1,
            'align': 'left'
        })
        
        number_format = workbook.add_format({
            'border': 1,
            'num_format': '#,##0'
        })
        
        if report_type == "officer":
            self.create_officer_bursts_sheet(workbook, data, header_format, cell_format, number_format)
        elif report_type == "date":
            self.create_date_bursts_sheet(workbook, data, header_format, cell_format, number_format)
        elif report_type == "pipe":
            self.create_pipe_size_bursts_sheet(workbook, data, header_format, cell_format, number_format)
        elif report_type == "region":
            self.create_region_bursts_sheet(workbook, data, header_format, cell_format, number_format)
        
        workbook.close()
        return filepath
    
    def create_summary_sheet(self, workbook, data, header_format, cell_format, number_format):
        """Create summary statistics sheet - FIXED VERSION"""
        worksheet = workbook.add_worksheet('Summary')
        
        # Title
        worksheet.merge_range('A1:D1', 'BURST ANALYSIS SUMMARY REPORT', 
                             workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
        
        # Generation date
        worksheet.write('A2', f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Summary statistics
        stats = data['summary_stats']
        
        row = 4
        worksheet.write(row, 0, 'OVERVIEW', header_format)
        worksheet.write(row, 1, '', header_format)
        
        row += 1
        worksheet.write(row, 0, 'Total Bursts', cell_format)
        worksheet.write(row, 1, stats['total_bursts'], number_format)
        
        row += 1
        worksheet.write(row, 0, 'Unique Officers', cell_format)
        worksheet.write(row, 1, stats['unique_officers'], number_format)
        
        row += 1
        worksheet.write(row, 0, 'Unique Regions', cell_format)
        worksheet.write(row, 1, stats['unique_regions'], number_format)
        
        row += 1
        worksheet.write(row, 0, 'Unique Pipe Sizes', cell_format)
        worksheet.write(row, 1, stats['unique_pipe_sizes'], number_format)
        
        row += 1
        worksheet.write(row, 0, 'Date Range', cell_format)
        worksheet.write(row, 1, f"{stats['date_range']['start']} to {stats['date_range']['end']}", cell_format)
        
        # Missing data section
        row += 3
        worksheet.write(row, 0, 'MISSING DATA', header_format)
        worksheet.write(row, 1, 'Count', header_format)
        
        for field, count in stats['missing_data'].items():
            row += 1
            worksheet.write(row, 0, field.replace('_', ' ').title(), cell_format)
            worksheet.write(row, 1, count, number_format)
        
        # Top officers - FIX: Calculate from raw_data instead of grouped_data
        row += 3
        worksheet.write(row, 0, 'TOP OFFICERS', header_format)
        worksheet.write(row, 1, 'Bursts Fixed', header_format)
        
        # Get top officers from raw_data
        df = pd.DataFrame(data['raw_data'])
        officer_counts = df.groupby('officer_name').size().sort_values(ascending=False)
        
        # Display top 5 officers
        for officer, count in officer_counts.head(5).items():
            row += 1
            worksheet.write(row, 0, officer, cell_format)
            worksheet.write(row, 1, count, number_format)
        
        # Auto-fit columns
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 15)
    
    def create_raw_data_sheet(self, workbook, data, header_format, cell_format):
        """Create raw data sheet"""
        worksheet = workbook.add_worksheet('Raw Data')
        
        # Convert raw data to DataFrame
        df = pd.DataFrame(data['raw_data'])
        
        # Write headers
        headers = ['Officer Name', 'Burst Date', 'Pipe Size', 'Region', 'Burst Location']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Write data
        for row, record in enumerate(df.itertuples(index=False), 1):
            worksheet.write(row, 0, record.officer_name, cell_format)
            worksheet.write(row, 1, str(record.burst_date), cell_format)
            worksheet.write(row, 2, record.pipe_size, cell_format)
            worksheet.write(row, 3, record.region, cell_format)
            worksheet.write(row, 4, record.burst_location, cell_format)
        
        # Auto-fit columns
        for col in range(5):
            worksheet.set_column(col, col, 18)
    
    def create_officer_analysis_sheet(self, workbook, data, header_format, cell_format, number_format):
        """Create officer analysis sheet - FIXED VERSION"""
        worksheet = workbook.add_worksheet('Officer Analysis')
        
        # Headers
        headers = ['Officer Name', 'Total Bursts', 'Regions Covered', 'Most Common Pipe Size']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # FIX: Calculate directly from raw_data
        df = pd.DataFrame(data['raw_data'])
        
        # Group by officer and calculate all statistics
        officer_analysis = []
        
        for officer_name in df['officer_name'].unique():
            officer_data = df[df['officer_name'] == officer_name]
            
            total_bursts = len(officer_data)
            regions_covered = officer_data['region'].nunique()
            
            # Most common pipe size
            if len(officer_data) > 0:
                pipe_sizes = officer_data['pipe_size'].value_counts()
                most_common_pipe = pipe_sizes.index[0] if len(pipe_sizes) > 0 else 'Unknown'
            else:
                most_common_pipe = 'Unknown'
            
            officer_analysis.append({
                'officer': officer_name,
                'total_bursts': total_bursts,
                'regions_covered': regions_covered,
                'most_common_pipe': most_common_pipe
            })
        
        # Sort by total bursts
        officer_analysis.sort(key=lambda x: x['total_bursts'], reverse=True)
        
        # Write data
        for row, officer_data in enumerate(officer_analysis, 1):
            worksheet.write(row, 0, officer_data['officer'], cell_format)
            worksheet.write(row, 1, officer_data['total_bursts'], number_format)
            worksheet.write(row, 2, officer_data['regions_covered'], number_format)
            worksheet.write(row, 3, officer_data['most_common_pipe'], cell_format)
        
        # Auto-fit columns
        for col in range(4):
            worksheet.set_column(col, col, 20)
    
    def create_regional_analysis_sheet(self, workbook, data, header_format, cell_format, number_format):
        """Create regional analysis sheet"""
        worksheet = workbook.add_worksheet('Regional Analysis')
        
        # Headers
        headers = ['Region', 'Total Bursts', 'Unique Officers', 'Most Common Pipe Size']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Analyze regional data
        df = pd.DataFrame(data['raw_data'])
        regional_stats = df.groupby('region').agg({
            'burst_date': 'count',
            'officer_name': 'nunique',
            'pipe_size': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown'
        }).reset_index()
        
        regional_stats.columns = ['region', 'total_bursts', 'unique_officers', 'most_common_pipe']
        regional_stats = regional_stats.sort_values('total_bursts', ascending=False)
        
        # Write data
        for row, record in enumerate(regional_stats.itertuples(index=False), 1):
            worksheet.write(row, 0, record.region, cell_format)
            worksheet.write(row, 1, record.total_bursts, number_format)
            worksheet.write(row, 2, record.unique_officers, number_format)
            worksheet.write(row, 3, record.most_common_pipe, cell_format)
        
        # Auto-fit columns
        for col in range(4):
            worksheet.set_column(col, col, 20)
    
    def create_pipe_size_analysis_sheet(self, workbook, data, header_format, cell_format, number_format):
        """Create pipe size analysis sheet"""
        worksheet = workbook.add_worksheet('Pipe Size Analysis')
        
        # Headers
        headers = ['Pipe Size', 'Total Bursts', 'Percentage', 'Most Active Officer']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Analyze pipe size data
        df = pd.DataFrame(data['raw_data'])
        pipe_stats = df.groupby('pipe_size').agg({
            'burst_date': 'count',
            'officer_name': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown'
        }).reset_index()
        
        pipe_stats.columns = ['pipe_size', 'total_bursts', 'most_active_officer']
        pipe_stats['percentage'] = (pipe_stats['total_bursts'] / pipe_stats['total_bursts'].sum() * 100).round(2)
        pipe_stats = pipe_stats.sort_values('total_bursts', ascending=False)
        
        # Write data
        for row, record in enumerate(pipe_stats.itertuples(index=False), 1):
            worksheet.write(row, 0, record.pipe_size, cell_format)
            worksheet.write(row, 1, record.total_bursts, number_format)
            worksheet.write(row, 2, f"{record.percentage}%", cell_format)
            worksheet.write(row, 3, record.most_active_officer, cell_format)
        
        # Auto-fit columns
        for col in range(4):
            worksheet.set_column(col, col, 20)
    
    def create_charts_sheet(self, workbook, data, header_format):
        """Create charts sheet with embedded visualizations"""
        worksheet = workbook.add_worksheet('Charts')
        
        # Create chart for officer performance
        chart = workbook.add_chart({'type': 'column'})
        
        # Add data series (this would need to be connected to actual data)
        chart.add_series({
            'name': 'Officer Performance',
            'categories': ['Officer A', 'Officer B', 'Officer C'],
            'values': [10, 20, 15],
        })
        
        chart.set_title({'name': 'Officer Performance Chart'})
        chart.set_x_axis({'name': 'Officers'})
        chart.set_y_axis({'name': 'Bursts Fixed'})
        
        # Insert chart into worksheet
        worksheet.insert_chart('A2', chart)

    def create_officer_bursts_sheet(self, workbook, data, header_format, cell_format, number_format):
        """Create simplified officer bursts sheet with only 2 columns and embedded chart - FIXED"""
        worksheet = workbook.add_worksheet('Officer Bursts Report')
        
        # Title
        worksheet.merge_range('A1:B1', 'OFFICER BURSTS ANALYSIS REPORT', 
                             workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
        
        # Generation date
        worksheet.write('A2', f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Headers - Only 2 columns as requested
        headers = ['Officer Name', 'Total Bursts']
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, header_format)
        
        # FIX: Calculate directly from raw_data
        df = pd.DataFrame(data['raw_data'])
        
        # Group by officer and count bursts
        officer_counts = df.groupby('officer_name').size().reset_index(name='total_bursts')
        officer_counts = officer_counts.sort_values('total_bursts', ascending=False)
        
        # Write data - only 2 columns
        for row, record in enumerate(officer_counts.itertuples(index=False), 5):
            worksheet.write(row, 0, record.officer_name, cell_format)
            worksheet.write(row, 1, record.total_bursts, number_format)
        
        # Auto-fit columns
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 15)
        
        # Create and insert chart only if we have data
        if len(officer_counts) > 0:
            chart = workbook.add_chart({'type': 'column'})
            
            # Calculate data range for chart
            data_rows = len(officer_counts)
            
            # Add data series for the chart
            chart.add_series({
                'name': 'Bursts Fixed',
                'categories': ['Officer Bursts Report', 5, 0, 4 + data_rows, 0],
                'values': ['Officer Bursts Report', 5, 1, 4 + data_rows, 1],
                'fill': {'color': '#4472C4'},
                'border': {'color': '#2F4F8F'}
            })
            
            # Configure chart
            chart.set_title({
                'name': 'Officer Performance - Bursts Fixed',
                'name_font': {'size': 14, 'bold': True}
            })
            chart.set_x_axis({
                'name': 'Officers',
                'name_font': {'size': 12, 'bold': True}
            })
            chart.set_y_axis({
                'name': 'Number of Bursts Fixed',
                'name_font': {'size': 12, 'bold': True}
            })
            
            # Set chart size and position
            chart.set_size({'width': 600, 'height': 400})
            
            # Insert chart to the right of the data
            worksheet.insert_chart('D5', chart)

    def create_date_bursts_sheet(self, workbook, data, header_format, cell_format, number_format):
        """Create simplified date bursts sheet with only 2 columns and embedded chart - FIXED VERSION"""
        worksheet = workbook.add_worksheet('Date Bursts Report')
        
        # Title
        worksheet.merge_range('A1:B1', 'DATE-BASED BURSTS ANALYSIS REPORT', 
                             workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
        
        # Generation date
        worksheet.write('A2', f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Headers - Only 2 columns
        headers = ['Date', 'Total Bursts']
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, header_format)
        
        # Analyze date data - Extract date only (no time)
        df = pd.DataFrame(data['raw_data'])
        
        # Convert burst_date to date only if it contains time information
        if 'burst_date' in df.columns:
            # Handle different date formats and extract date only
            df['date_only'] = df['burst_date'].astype(str).str.split(' ').str[0]  # Remove time part
            df['date_only'] = pd.to_datetime(df['date_only'], errors='coerce').dt.date
        else:
            # If no burst_date column, create dummy data or handle error
            df['date_only'] = pd.to_datetime('2025-06-01').date()
        
        # Group by date only and count bursts
        date_stats = df.groupby('date_only').size().reset_index(name='total_bursts')
        
        # Sort chronologically for better visualization
        date_stats = date_stats.sort_values('date_only')
        
        # Convert date back to string for Excel display
        date_stats['date_display'] = date_stats['date_only'].astype(str)
        
        # Write data - only 2 columns
        for row, record in enumerate(date_stats.itertuples(index=False), 5):
            worksheet.write(row, 0, record.date_display, cell_format)
            worksheet.write(row, 1, record.total_bursts, number_format)
        
        # Auto-fit columns
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 15)
        
        # Create and insert chart
        chart = workbook.add_chart({'type': 'line'})
        
        # Calculate data range for chart
        data_rows = len(date_stats)
        
        # Add data series for the chart
        chart.add_series({
            'name': 'Daily Bursts',
            'categories': ['Date Bursts Report', 5, 0, 4 + data_rows, 0],  # Dates
            'values': ['Date Bursts Report', 5, 1, 4 + data_rows, 1],      # Burst counts
            'line': {'color': '#4472C4', 'width': 3},
            'marker': {'type': 'circle', 'size': 6, 'fill': {'color': '#4472C4'}}
        })
        
        # Configure chart
        chart.set_title({
            'name': 'Daily Burst Incidents Over Time',
            'name_font': {'size': 14, 'bold': True}
        })
        chart.set_x_axis({
            'name': 'Date',
            'name_font': {'size': 12, 'bold': True}
        })
        chart.set_y_axis({
            'name': 'Number of Bursts',
            'name_font': {'size': 12, 'bold': True}
        })
        
        # Set chart size and position
        chart.set_size({'width': 600, 'height': 400})
        
        # Insert chart to the right of the data
        worksheet.insert_chart('D5', chart)

    def create_pipe_size_bursts_sheet(self, workbook, data, header_format, cell_format, number_format):
        """Create simplified pipe size bursts sheet with only 2 columns and embedded chart"""
        worksheet = workbook.add_worksheet('Pipe Size Bursts Report')
        
        # Title
        worksheet.merge_range('A1:B1', 'PIPE SIZE BURSTS ANALYSIS REPORT', 
                             workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
        
        # Generation date
        worksheet.write('A2', f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Headers - Only 2 columns
        headers = ['Pipe Size', 'Total Bursts']
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, header_format)
        
        # Analyze pipe size data
        df = pd.DataFrame(data['raw_data'])
        pipe_stats = df.groupby('pipe_size').size().reset_index(name='total_bursts')
        pipe_stats = pipe_stats.sort_values('total_bursts', ascending=False)
        
        # Write data - only 2 columns
        for row, record in enumerate(pipe_stats.itertuples(index=False), 5):
            worksheet.write(row, 0, record.pipe_size, cell_format)
            worksheet.write(row, 1, record.total_bursts, number_format)
        
        # Auto-fit columns
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 15)
        
        # Create and insert chart
        chart = workbook.add_chart({'type': 'pie'})
        
        # Calculate data range for chart
        data_rows = len(pipe_stats)
        
        # Add data series for the chart
        chart.add_series({
            'name': 'Pipe Size Distribution',
            'categories': ['Pipe Size Bursts Report', 5, 0, 4 + data_rows, 0],  # Pipe sizes
            'values': ['Pipe Size Bursts Report', 5, 1, 4 + data_rows, 1],      # Burst counts
        })
        
        # Configure chart
        chart.set_title({
            'name': 'Burst Distribution by Pipe Size',
            'name_font': {'size': 14, 'bold': True}
        })
        
        # Set chart size and position
        chart.set_size({'width': 600, 'height': 400})
        
        # Insert chart to the right of the data
        worksheet.insert_chart('D5', chart)

    def create_region_bursts_sheet(self, workbook, data, header_format, cell_format, number_format):
        """Create simplified region bursts sheet with only 2 columns and embedded chart"""
        worksheet = workbook.add_worksheet('Region Bursts Report')
        
        # Title
        worksheet.merge_range('A1:B1', 'REGIONAL BURSTS ANALYSIS REPORT', 
                             workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center'}))
        
        # Generation date
        worksheet.write('A2', f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Headers - Only 2 columns
        headers = ['Region', 'Total Bursts']
        for col, header in enumerate(headers):
            worksheet.write(4, col, header, header_format)
        
        # Analyze regional data
        df = pd.DataFrame(data['raw_data'])
        regional_stats = df.groupby('region').size().reset_index(name='total_bursts')
        regional_stats = regional_stats.sort_values('total_bursts', ascending=False)
        
        # Write data - only 2 columns
        for row, record in enumerate(regional_stats.itertuples(index=False), 5):
            worksheet.write(row, 0, record.region, cell_format)
            worksheet.write(row, 1, record.total_bursts, number_format)
        
        # Auto-fit columns
        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 15)
        
        # Create and insert chart
        chart = workbook.add_chart({'type': 'column'})
        
        # Calculate data range for chart
        data_rows = len(regional_stats)
        
        # Add data series for the chart
        chart.add_series({
            'name': 'Regional Bursts',
            'categories': ['Region Bursts Report', 5, 0, 4 + data_rows, 0],  # Region names
            'values': ['Region Bursts Report', 5, 1, 4 + data_rows, 1],      # Burst counts
            'fill': {'color': '#4472C4'},
            'border': {'color': '#2F4F8F'}
        })
        
        # Configure chart
        chart.set_title({
            'name': 'Burst Distribution by Region',
            'name_font': {'size': 14, 'bold': True}
        })
        chart.set_x_axis({
            'name': 'Region',
            'name_font': {'size': 12, 'bold': True}
        })
        chart.set_y_axis({
            'name': 'Number of Bursts',
            'name_font': {'size': 12, 'bold': True}
        })
        
        # Set chart size and position
        chart.set_size({'width': 600, 'height': 400})
        
        # Insert chart to the right of the data
        worksheet.insert_chart('D5', chart)
       
    def generate_chart_image(self, data, chart_type='officer_performance'):
        """Generate chart images for embedding"""
        plt.style.use('seaborn-v0_8')
        fig, ax = plt.subplots(figsize=(12, 8))
        
        if chart_type == 'officer_performance':
            # Officer performance chart
            df = pd.DataFrame(data['raw_data'])
            officer_counts = df.groupby('officer_name').size()
            
            # Get top 10 officers
            top_officers = officer_counts.sort_values(ascending=False)[:10]
            
            ax.barh(top_officers.index, top_officers.values, color='#4472C4')
            ax.set_xlabel('Total Bursts Fixed')
            ax.set_title('Top 10 Officers by Bursts Fixed')
            ax.grid(axis='x', alpha=0.3)
            
        elif chart_type == 'regional_distribution':
            # Regional distribution pie chart
            df = pd.DataFrame(data['raw_data'])
            regional_stats = df.groupby('region').size()
            
            colors = plt.cm.Set3(range(len(regional_stats)))
            ax.pie(regional_stats, labels=regional_stats.index, autopct='%1.1f%%', colors=colors)
            ax.set_title('Burst Distribution by Region')
            
        elif chart_type == 'pipe_size_distribution':
            # Pipe size distribution chart
            df = pd.DataFrame(data['raw_data'])
            pipe_stats = df.groupby('pipe_size').size().sort_values(ascending=False)
            
            ax.bar(range(len(pipe_stats)), pipe_stats.values, color='#4472C4')
            ax.set_xticks(range(len(pipe_stats)))
            ax.set_xticklabels(pipe_stats.index, rotation=45, ha='right')
            ax.set_ylabel('Number of Bursts')
            ax.set_title('Burst Distribution by Pipe Size')
            ax.grid(axis='y', alpha=0.3)
            
        elif chart_type == 'daily_trend':
            # Daily trend chart
            df = pd.DataFrame(data['raw_data'])
            
            # Extract date only from burst_date
            df['date_only'] = df['burst_date'].astype(str).str.split(' ').str[0]
            df['date_only'] = pd.to_datetime(df['date_only'], errors='coerce').dt.date
            
            # Group by date and count bursts
            date_stats = df.groupby('date_only').size().sort_index()
            
            ax.plot(date_stats.index, date_stats.values, marker='o', linewidth=2, markersize=6, color='#4472C4')
            ax.set_xlabel('Date')
            ax.set_ylabel('Number of Bursts')
            ax.set_title('Daily Burst Incidents Over Time')
            ax.grid(True, alpha=0.3)
            
            # Rotate x-axis labels for better readability
            plt.xticks(rotation=45)
            
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save chart to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
        img_buffer.seek(0)
        
        plt.close()
        return img_buffer