// Burst Analyzer Frontend Application
class BurstAnalyzer {
    constructor() {
        this.currentFileId = null;
        this.processedData = null;
        this.charts = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDropzone();
    }

    setupEventListeners() {
        // File input change listener
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        // Officer selection
        const officerSelect = document.getElementById('officerSelect');
        if (officerSelect) {
            officerSelect.addEventListener('change', (e) => this.handleOfficerSelect(e));
        }

        // Table view buttons
        const tableButtons = ['officers', 'regions', 'pipes', 'raw'];
        tableButtons.forEach(type => {
            const btn = document.querySelector(`[onclick="showTable('${type}')"]`);
            if (btn) {
                btn.removeAttribute('onclick');
                btn.addEventListener('click', () => this.showTable(type));
            }
        });

        // Export buttons
        const exportExcelBtn = document.querySelector('[onclick="exportToExcel()"]');
        if (exportExcelBtn) {
            exportExcelBtn.removeAttribute('onclick');
            exportExcelBtn.addEventListener('click', () => this.exportToExcel());
        }

        const exportCSVBtn = document.querySelector('[onclick="exportToCSV()"]');
        if (exportCSVBtn) {
            exportCSVBtn.removeAttribute('onclick');
            exportCSVBtn.addEventListener('click', () => this.exportToCSV());
        }

        // Report generation button
        const generateReportBtn = document.querySelector('[onclick="generateSelectedReport()"]');
        if (generateReportBtn) {
            generateReportBtn.removeAttribute('onclick');
            generateReportBtn.addEventListener('click', () => this.generateSelectedReport());
        }
    }

    setupDropzone() {
        const dropzone = document.getElementById('dropzone');
        if (!dropzone) return;

        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('dragover');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const fileInput = document.getElementById('fileInput');
                fileInput.files = files;
                this.handleFileSelect({ target: fileInput });
            }
        });

        dropzone.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file type
        if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
            this.showError('Please select an Excel file (.xlsx or .xls)');
            return;
        }

        // Update UI
        const fileName = document.getElementById('fileName');
        if (fileName) {
            fileName.textContent = `Selected: ${file.name}`;
            fileName.classList.remove('hidden');
        }

        // Upload and process file
        this.uploadFile(file);
    }

    async uploadFile(file) {
        const uploadStatus = document.getElementById('uploadStatus');
        const resultsSection = document.getElementById('resultsSection');
        const errorMessage = document.getElementById('errorMessage');
        
        if (uploadStatus) uploadStatus.classList.remove('hidden');
        if (resultsSection) resultsSection.classList.add('hidden');
        if (errorMessage) errorMessage.classList.add('hidden');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                this.processedData = result.data;
                this.currentFileId = result.file_id;
                this.displayResults(this.processedData);
                if (resultsSection) resultsSection.classList.remove('hidden');
            } else {
                this.showError('Error processing file: ' + result.message);
            }
        } catch (error) {
            this.showError('Error uploading file: ' + error.message);
        } finally {
            if (uploadStatus) uploadStatus.classList.add('hidden');
        }
    }

    displayResults(data) {
        if (!data) return;

        // Update summary statistics
        const totalBursts = document.getElementById('totalBursts');
        const uniqueOfficers = document.getElementById('uniqueOfficers');
        const uniqueRegions = document.getElementById('uniqueRegions');
        const uniquePipeSizes = document.getElementById('uniquePipeSizes');
        const dateRange = document.getElementById('dateRange');

        if (totalBursts) totalBursts.textContent = data.total_records;
        if (uniqueOfficers) uniqueOfficers.textContent = data.summary_stats.unique_officers;
        if (uniqueRegions) uniqueRegions.textContent = data.summary_stats.unique_regions;
        if (uniquePipeSizes) uniquePipeSizes.textContent = data.summary_stats.unique_pipe_sizes;
        if (dateRange) {
            dateRange.textContent = 
                `${data.summary_stats.date_range.start} to ${data.summary_stats.date_range.end}`;
        }

        // Populate officer dropdown
        this.populateOfficerDropdown(Object.keys(data.grouped_data));

        // Render charts
        this.renderCharts(data);
    }

    populateOfficerDropdown(officers) {
        const select = document.getElementById('officerSelect');
        if (!select) return;

        select.innerHTML = '<option value="">Choose an officer...</option>';
        officers.forEach(officer => {
            const option = document.createElement('option');
            option.value = officer;
            option.textContent = officer;
            select.appendChild(option);
        });
    }

    renderCharts(data) {
        // Destroy existing charts to prevent canvas reuse issues
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};

        // Top Officers Chart
        const officerCanvas = document.getElementById('officerChart');
        if (officerCanvas) {
            const officerCtx = officerCanvas.getContext('2d');
            const topOfficers = Object.entries(data.grouped_data)
                .sort((a, b) => b[1].count - a[1].count)
                .slice(0, 10);
            
            this.charts.officer = new Chart(officerCtx, {
                type: 'bar',
                data: {
                    labels: topOfficers.map(item => item[0]),
                    datasets: [{
                        label: 'Bursts Fixed',
                        data: topOfficers.map(item => item[1].count),
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Regional Distribution Chart
        const regionCanvas = document.getElementById('regionalChart');
        if (regionCanvas) {
            const regionCtx = regionCanvas.getContext('2d');
            const regions = Object.entries(data.region_summary);
            
            this.charts.region = new Chart(regionCtx, {
                type: 'pie',
                data: {
                    labels: regions.map(item => item[0]),
                    datasets: [{
                        data: regions.map(item => item[1].count),
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.6)',
                            'rgba(54, 162, 235, 0.6)',
                            'rgba(255, 206, 86, 0.6)',
                            'rgba(75, 192, 192, 0.6)',
                            'rgba(153, 102, 255, 0.6)',
                            'rgba(255, 159, 64, 0.6)',
                            'rgba(199, 199, 199, 0.6)',
                            'rgba(83, 102, 255, 0.6)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false
                }
            });
        }

        // Pipe Size Chart
        const pipeCanvas = document.getElementById('pipeSizeChart');
        if (pipeCanvas) {
            const pipeCtx = pipeCanvas.getContext('2d');
            const pipes = Object.entries(data.pipe_size_summary);
            
            this.charts.pipe = new Chart(pipeCtx, {
                type: 'bar',
                data: {
                    labels: pipes.map(item => `${item[0]}mm`),
                    datasets: [{
                        label: 'Burst Count',
                        data: pipes.map(item => item[1].count),
                        backgroundColor: 'rgba(75, 192, 192, 0.6)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        // Monthly Trends Chart
        const trendCanvas = document.getElementById('monthlyTrendsChart');
        if (trendCanvas) {
            const trendCtx = trendCanvas.getContext('2d');
            const monthlyData = data.monthly_trends;
            const months = Object.keys(monthlyData).sort();
            
            this.charts.trend = new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: months,
                    datasets: [{
                        label: 'Bursts per Month',
                        data: months.map(month => monthlyData[month]),
                        fill: false,
                        borderColor: 'rgba(153, 102, 255, 1)',
                        backgroundColor: 'rgba(153, 102, 255, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }

    handleOfficerSelect(event) {
        const officerName = event.target.value;
        const officerDetails = document.getElementById('officerDetails');
        
        if (!officerName) {
            if (officerDetails) officerDetails.classList.add('hidden');
            return;
        }

        if (!this.processedData || !this.processedData.grouped_data[officerName]) {
            this.showError('Officer data not available');
            return;
        }

        const officerData = this.processedData.grouped_data[officerName];
        
        // Update officer details
        const officerTotalBursts = document.getElementById('officerTotalBursts');
        const officerRegions = document.getElementById('officerRegions');
        const officerCommonPipe = document.getElementById('officerCommonPipe');

        if (officerTotalBursts) officerTotalBursts.textContent = officerData.count;
        if (officerRegions) officerRegions.textContent = officerData.unique_regions;
        if (officerCommonPipe) {
            officerCommonPipe.textContent = 
                `${officerData.most_common_pipe_size}mm (${officerData.pipe_size_counts[officerData.most_common_pipe_size]} bursts)`;
        }
        
        if (officerDetails) officerDetails.classList.remove('hidden');
    }

    showTable(type) {
        const container = document.getElementById('dataTableContainer');
        if (!container || !this.processedData) return;

        let tableHTML = '';
        let headers = [];
        let rows = [];

        switch(type) {
            case 'officers':
                headers = ['Officer', 'Total Bursts', 'Regions Worked', 'Most Common Pipe'];
                rows = Object.entries(this.processedData.grouped_data).map(([officer, data]) => [
                    officer,
                    data.count,
                    data.unique_regions,
                    `${data.most_common_pipe_size}mm`
                ]);
                break;
                
            case 'regions':
                headers = ['Region', 'Total Bursts', 'Top Officer', 'Most Common Pipe'];
                rows = Object.entries(this.processedData.region_summary).map(([region, data]) => [
                    region,
                    data.count,
                    data.top_officer,
                    `${data.most_common_pipe_size}mm`
                ]);
                break;
                
            case 'pipes':
                headers = ['Pipe Size (mm)', 'Total Bursts', 'Top Region', 'Top Officer'];
                rows = Object.entries(this.processedData.pipe_size_summary).map(([size, data]) => [
                    size,
                    data.count,
                    data.top_region,
                    data.top_officer
                ]);
                break;
                
            case 'raw':
                headers = Object.keys(this.processedData.raw_data[0]);
                rows = this.processedData.raw_data.map(row => 
                    headers.map(header => row[header] || '')
                );
                break;
        }

        // Generate table HTML
        tableHTML = `
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            ${headers.map(header => `<th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${header}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                        ${rows.map(row => `
                            <tr>
                                ${row.map(cell => `<td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${cell}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = tableHTML;
    }

    exportToExcel() {
        if (!this.processedData) {
            this.showError('No data to export');
            return;
        }

        // Check if XLSX library is available
        if (typeof XLSX === 'undefined') {
            this.showError('Excel export library not loaded');
            return;
        }

        try {
            const ws = XLSX.utils.json_to_sheet(this.processedData.raw_data);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "Burst Data");
            XLSX.writeFile(wb, `burst_analysis_${new Date().toISOString().slice(0, 10)}.xlsx`);
        } catch (error) {
            this.showError('Error exporting to Excel: ' + error.message);
        }
    }

    exportToCSV() {
        if (!this.processedData) {
            this.showError('No data to export');
            return;
        }

        try {
            const csvContent = [
                Object.keys(this.processedData.raw_data[0]).join(','),
                ...this.processedData.raw_data.map(row => 
                    Object.values(row).map(value => 
                        `"${String(value).replace(/"/g, '""')}"`
                    ).join(',')
                )
            ].join('\n');

            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            link.setAttribute('href', url);
            link.setAttribute('download', `burst_analysis_${new Date().toISOString().slice(0, 10)}.csv`);
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            // Clean up
            URL.revokeObjectURL(url);
        } catch (error) {
            this.showError('Error exporting to CSV: ' + error.message);
        }
    }

    async generateSelectedReport() {
        if (!this.processedData) {
            this.showError('No data to generate report');
            return;
        }

        const reportType = document.getElementById('reportType');
        if (!reportType) {
            this.showError('Report type selection not available');
            return;
        }

        try {
            const response = await fetch('/generate-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    data: this.processedData,
                    report_type: reportType.value
                })
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                // Download the report
                if (result.download_url) {
                    window.location.href = result.download_url;
                } else {
                    this.showError('Report generated but download URL not provided');
                }
            } else {
                this.showError('Error generating report: ' + result.message);
            }
        } catch (error) {
            this.showError('Error generating report: ' + error.message);
        }
    }

    showError(message) {
        const errorMessage = document.getElementById('errorMessage');
        if (!errorMessage) {
            console.error('Error:', message);
            return;
        }
        
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorMessage.classList.add('hidden');
        }, 5000);
    }

    // Cleanup method for destroying charts
    cleanup() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
        this.charts = {};
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the Burst Analyzer
    const app = new BurstAnalyzer();
    
    // Make app globally accessible for debugging
    window.burstAnalyzer = app;
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        if (window.burstAnalyzer) {
            window.burstAnalyzer.cleanup();
        }
    });
});

// Export for module usage if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BurstAnalyzer;
}