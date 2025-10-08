/**
 * Reddit F1 Streaming Demo - Main JavaScript
 * Common functions and alert management
 */

// ====================================================================
// Alert Management
// ====================================================================

let userAlerts = [];

// Load alerts khi modal mở
document.addEventListener('DOMContentLoaded', function() {
    const alertModal = document.getElementById('alertModal');
    
    if (alertModal) {
        alertModal.addEventListener('show.bs.modal', function() {
            loadUserAlerts();
        });
    }
    
    // Setup alert form
    const alertForm = document.getElementById('alertForm');
    if (alertForm) {
        alertForm.addEventListener('submit', function(e) {
            e.preventDefault();
            createAlert();
        });
    }
    
    // Check for new alerts periodically
    setInterval(checkForNewAlerts, 60000); // Every 60 seconds
});

async function loadUserAlerts() {
    try {
        const response = await fetch('/api/alerts?user_id=demo_user');
        const result = await response.json();
        
        const alertList = document.getElementById('alertList');
        
        if (result.success && result.data.length > 0) {
            userAlerts = result.data;
            
            alertList.innerHTML = result.data.map(alert => `
                <div class="alert alert-secondary mb-2">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${escapeHtml(alert.keyword)}</strong>
                            <br>
                            <small class="text-muted">
                                Min score: ${alert.min_score} | 
                                ${alert.enabled ? '<span class="badge bg-success">Active</span>' : '<span class="badge bg-secondary">Inactive</span>'}
                            </small>
                        </div>
                        <button class="btn btn-sm btn-danger" onclick="deleteAlert('${alert.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            alertList.innerHTML = '<div class="text-muted">Chưa có alerts nào.</div>';
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
        document.getElementById('alertList').innerHTML = 
            '<div class="alert alert-danger">Lỗi khi tải alerts</div>';
    }
}

async function createAlert() {
    const keyword = document.getElementById('keyword').value.trim();
    const minScore = parseInt(document.getElementById('minScore').value) || 10;
    
    if (!keyword) {
        alert('Vui lòng nhập từ khóa!');
        return;
    }
    
    try {
        const response = await fetch('/api/alerts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: 'demo_user',
                keyword: keyword,
                min_score: minScore
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert('✓ Alert đã được tạo!');
            document.getElementById('alertForm').reset();
            loadUserAlerts();
        } else {
            alert('✗ Lỗi: ' + result.error);
        }
    } catch (error) {
        alert('✗ Lỗi: ' + error.message);
    }
}

async function deleteAlert(alertId) {
    if (!confirm('Bạn có chắc muốn xóa alert này?')) {
        return;
    }
    
    // TODO: Implement delete endpoint
    alert('Tính năng xóa sẽ được triển khai sau.');
}

async function checkForNewAlerts() {
    // TODO: Implement alert checking logic
    // This would check for posts matching user's keywords
    // and show notifications
}

// ====================================================================
// Utility Functions
// ====================================================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function getTimeAgo(date) {
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Vừa xong';
    if (diffMins < 60) return `${diffMins} phút trước`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} giờ trước`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 30) return `${diffDays} ngày trước`;
    
    const diffMonths = Math.floor(diffDays / 30);
    return `${diffMonths} tháng trước`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('vi-VN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showNotification(message, type = 'info') {
    // Simple notification using Bootstrap toast
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Create toast container if not exists
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Add and show toast
    const toastElement = document.createElement('div');
    toastElement.innerHTML = toastHtml;
    toastContainer.appendChild(toastElement.firstElementChild);
    
    const toast = new bootstrap.Toast(toastElement.firstElementChild);
    toast.show();
}

// ====================================================================
// Export functions for use in other scripts
// ====================================================================

window.AppUtils = {
    escapeHtml,
    formatNumber,
    getTimeAgo,
    formatDate,
    showNotification
};
