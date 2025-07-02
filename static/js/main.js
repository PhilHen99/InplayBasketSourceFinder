// Main JavaScript file for Basketball Teams Dashboard

// Enable tooltips everywhere
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable enter key on search fields
    const searchFields = document.querySelectorAll('input[type="text"]');
    searchFields.forEach(field => {
        field.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const applyButton = document.getElementById('apply-filters');
                if (applyButton) {
                    applyButton.click();
                }
            }
        });
    });
});

// Function to generate a shareable URL
function generateShareableUrl(teamName) {
    const baseUrl = window.location.origin;
    return `${baseUrl}/team/${encodeURIComponent(teamName)}`;
}

// Function to copy text to clipboard
function copyToClipboard(text) {
    // Create a temporary input element
    const tempInput = document.createElement('input');
    tempInput.value = text;
    document.body.appendChild(tempInput);
    
    // Select the text
    tempInput.select();
    tempInput.setSelectionRange(0, 99999); // For mobile devices
    
    // Copy the text
    document.execCommand('copy');
    
    // Remove the temporary element
    document.body.removeChild(tempInput);
    
    return true;
}

// Export function to create CSV of filtered teams
function exportToCSV(data, filename) {
    // Column headers
    const headers = Object.keys(data[0]);
    
    // Convert data to CSV format
    let csvContent = headers.join(',') + '\n';
    
    data.forEach(item => {
        const row = headers.map(header => {
            // Handle values that might contain commas or quotes
            let value = item[header] || '';
            value = value.toString().replace(/"/g, '""'); // Escape quotes
            
            // Wrap in quotes if contains comma, newline or quote
            if (value.includes(',') || value.includes('\n') || value.includes('"')) {
                value = `"${value}"`;
            }
            
            return value;
        });
        
        csvContent += row.join(',') + '\n';
    });
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
} 