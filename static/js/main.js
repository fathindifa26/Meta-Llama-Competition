class FaceRecognitionUI {
    constructor() {
        this.purchaseInput = document.getElementById('purchase-input');
        this.purchaseBtn = document.getElementById('purchase-btn');
        this.statusIndicator = document.getElementById('status-indicator');
        this.logBox = document.getElementById('log-box');
        this.clearLogsBtn = document.getElementById('clear-logs');
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.startLogFetching();
        this.checkVideoConnection();
    }
    
    setupEventListeners() {
        // Enter key untuk purchase
        this.purchaseInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                this.handlePurchase();
            }
        });
        
        // Click button untuk purchase
        this.purchaseBtn.addEventListener('click', () => {
            this.handlePurchase();
        });
        
        // Clear logs
        this.clearLogsBtn.addEventListener('click', () => {
            this.clearLogs();
        });
        
        // Auto-enable/disable purchase button
        this.purchaseInput.addEventListener('input', (e) => {
            const hasText = e.target.value.trim().length > 0;
            this.purchaseBtn.disabled = !hasText;
        });
    }
    
    async handlePurchase() {
        const value = this.purchaseInput.value.trim();
        if (!value) return;
        
        try {
            // Show loading
            const originalText = this.purchaseBtn.innerHTML;
            this.purchaseBtn.innerHTML = '<div class="loading"></div> Processing...';
            this.purchaseBtn.disabled = true;
            
            const response = await fetch('/purchase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ purchase: value })
            });
            
            if (response.ok) {
                this.purchaseInput.value = '';
                this.showNotification('Purchase recorded successfully!', 'success');
            } else {
                const error = await response.json();
                this.showNotification(error.error || 'Purchase failed', 'error');
            }
        } catch (error) {
            console.error('Purchase error:', error);
            this.showNotification('Network error occurred', 'error');
        } finally {
            // Reset button
            this.purchaseBtn.innerHTML = '<i class="fas fa-shopping-cart"></i> Beli';
            this.purchaseBtn.disabled = this.purchaseInput.value.trim().length === 0;
        }
    }
    
    async fetchLogs() {
        try {
            const response = await fetch('/logs');
            const logs = await response.json();
            
            this.logBox.innerHTML = logs.map(log => {
                const logType = this.getLogType(log);
                return `<div class="log-entry ${logType}">${this.escapeHtml(log)}</div>`;
            }).join('');
            
            // Auto-scroll to bottom
            this.logBox.scrollTop = this.logBox.scrollHeight;
            
            // Update status based on logs
            this.updateStatus(logs);
            
        } catch (error) {
            console.error('Error fetching logs:', error);
        }
    }
    
    getLogType(log) {
        if (log.includes('Error') || log.includes('❌')) return 'error';
        if (log.includes('⚠️') || log.includes('Warning')) return 'warning';
        if (log.includes('✅') || log.includes('Selamat')) return 'success';
        return 'info';
    }
    
    updateStatus(logs) {
        const latestLog = logs[logs.length - 1] || '';
        const statusIcon = this.statusIndicator.querySelector('i');
        const statusText = this.statusIndicator.querySelector('span');
        
        // Reset classes
        this.statusIndicator.className = 'status-indicator';
        
        if (latestLog.includes('Selamat datang kembali') || latestLog.includes('customer baru')) {
            this.statusIndicator.classList.add('customer-recognized');
            statusIcon.className = 'fas fa-user-check';
            statusText.textContent = 'Customer teridentifikasi';
            this.purchaseBtn.disabled = this.purchaseInput.value.trim().length === 0;
        } else if (latestLog.includes('Wajah terdeteksi') || latestLog.includes('recognition')) {
            this.statusIndicator.classList.add('customer-detected');
            statusIcon.className = 'fas fa-user-clock';
            statusText.textContent = 'Mengenali customer...';
            this.purchaseBtn.disabled = true;
        } else {
            this.statusIndicator.classList.add('no-customer');
            statusIcon.className = 'fas fa-user-slash';
            statusText.textContent = 'Tidak ada customer terdeteksi';
            this.purchaseBtn.disabled = true;
        }
    }
    
    clearLogs() {
        if (confirm('Are you sure you want to clear all logs?')) {
            this.logBox.innerHTML = '<div class="log-entry info">Logs cleared by user</div>';
        }
    }
    
    showNotification(message, type = 'info') {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
    
    checkVideoConnection() {
        const videoStream = document.getElementById('video-stream');
        const connectionStatus = document.getElementById('connection-status');
        
        videoStream.onerror = () => {
            connectionStatus.innerHTML = '<i class="fas fa-circle" style="color: #dc3545;"></i> Disconnected';
        };
        
        videoStream.onload = () => {
            connectionStatus.innerHTML = '<i class="fas fa-circle"></i> Live';
        };
    }
    
    startLogFetching() {
        this.fetchLogs();
        setInterval(() => this.fetchLogs(), 1000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FaceRecognitionUI();
});