// Admin Panel JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Load statistics
    loadStatistics();
    
    // Initialize usage chart
    initializeUsageChart();
    
    // Set up event listeners
    setupEventListeners();
    
    // Refresh data every 30 seconds
    setInterval(loadStatistics, 30000);
});

function loadStatistics() {
    fetch('/admin/stats')
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                document.getElementById('requestsToday').textContent = data.total_requests_today.toLocaleString();
                document.getElementById('totalKeys').textContent = data.total_api_keys.toLocaleString();
                document.getElementById('errorRate').textContent = data.error_rate + '%';
            }
        })
        .catch(error => {
            console.error('Error loading statistics:', error);
        });
}

function initializeUsageChart() {
    const ctx = document.getElementById('usageChart').getContext('2d');
    
    // Sample data - replace with real data from API
    const chartData = {
        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        datasets: [{
            label: 'API Requests',
            data: [1200, 1900, 3000, 5000, 2000, 3000, 4500],
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
            fill: true
        }]
    };
    
    new Chart(ctx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Weekly API Usage'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

function setupEventListeners() {
    // Create API Key button
    document.getElementById('createKeyBtn').addEventListener('click', createApiKey);
    
    // Copy key buttons
    document.querySelectorAll('.copy-key-btn').forEach(button => {
        button.addEventListener('click', function() {
            copyToClipboard(this.dataset.key);
            showToast('API key copied to clipboard!', 'success');
        });
    });
    
    // Revoke key buttons
    document.querySelectorAll('.revoke-key-btn').forEach(button => {
        button.addEventListener('click', function() {
            revokeApiKey(this.dataset.key);
        });
    });
    
    // Copy new API key button
    document.getElementById('copyNewKey').addEventListener('click', function() {
        const apiKey = document.getElementById('newApiKey').value;
        copyToClipboard(apiKey);
        showToast('API key copied to clipboard!', 'success');
    });
    
    // Admin checkbox handler
    document.getElementById('isAdmin').addEventListener('change', function() {
        const dailyLimitInput = document.getElementById('dailyLimit');
        if (this.checked) {
            dailyLimitInput.value = 10000000;
        } else {
            dailyLimitInput.value = 1000;
        }
    });
}

function createApiKey() {
    const owner = document.getElementById('owner').value;
    const dailyLimit = parseInt(document.getElementById('dailyLimit').value);
    const expiryDays = parseInt(document.getElementById('expiryDays').value);
    const isAdmin = document.getElementById('isAdmin').checked;
    
    if (!owner) {
        showToast('Owner name is required!', 'error');
        return;
    }
    
    const data = {
        owner: owner,
        daily_limit: dailyLimit,
        expiry_days: expiryDays,
        is_admin: isAdmin
    };
    
    fetch('/admin/create_key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Hide create modal
            const createModal = bootstrap.Modal.getInstance(document.getElementById('createKeyModal'));
            createModal.hide();
            
            // Show success modal with API key
            document.getElementById('newApiKey').value = data.api_key;
            const successModal = new bootstrap.Modal(document.getElementById('successModal'));
            successModal.show();
            
            // Reset form
            document.getElementById('createKeyForm').reset();
            
            // Reload page after modal is closed
            document.getElementById('successModal').addEventListener('hidden.bs.modal', function() {
                location.reload();
            }, { once: true });
            
        } else {
            showToast(data.error || 'Failed to create API key', 'error');
        }
    })
    .catch(error => {
        console.error('Error creating API key:', error);
        showToast('Failed to create API key', 'error');
    });
}

function revokeApiKey(apiKey) {
    if (!confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) {
        return;
    }
    
    fetch('/admin/revoke_key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ api_key: apiKey })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('API key revoked successfully', 'success');
            location.reload();
        } else {
            showToast(data.error || 'Failed to revoke API key', 'error');
        }
    })
    .catch(error => {
        console.error('Error revoking API key:', error);
        showToast('Failed to revoke API key', 'error');
    });
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Success handled by caller
    }, function(err) {
        console.error('Could not copy text: ', err);
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
    });
}

function showToast(message, type = 'info') {
    // Create toast element
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type === 'error' ? 'danger' : type}" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.innerHTML += toastHtml;
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

// Auto-refresh page data
function refreshData() {
    loadStatistics();
    // Add other data refresh functions here
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Handle API key display toggle
document.querySelectorAll('.api-key-display').forEach(element => {
    element.addEventListener('click', function() {
        const isHidden = this.textContent.includes('...');
        if (isHidden) {
            this.textContent = this.dataset.fullKey;
        } else {
            const key = this.dataset.fullKey;
            this.textContent = key.substring(0, 8) + '...' + key.substring(key.length - 4);
        }
    });
});
