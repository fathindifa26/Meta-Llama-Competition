// static/js/face_recognition.js
class FaceRecognitionApp {
    constructor() {
        this.recognitionStatus = document.getElementById('recognition-status');
        this.customerInfo = document.getElementById('customer-info');
        this.customerName = document.getElementById('customer-name');
        this.customerMessage = document.getElementById('customer-message');
        this.actionButtons = document.getElementById('action-buttons');
        this.proceedBtn = document.getElementById('proceed-to-menu');
        this.skipBtn = document.getElementById('skip-order');
        
        // ✅ Welcome section elements
        this.welcomeMessage = document.getElementById('welcome-message');
        this.dynamicWelcome = document.getElementById('dynamic-welcome');
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.startStatusPolling();
    }
    
    setupEventListeners() {
        this.proceedBtn.addEventListener('click', () => {
            window.location.href = '/menu';
        });
        
        this.skipBtn.addEventListener('click', () => {
            this.resetSession();
        });
    }
    
    async startStatusPolling() {
        setInterval(async () => {
            try {
                const response = await fetch('/api/recognition_status');
                const status = await response.json();
                this.updateUI(status);
            } catch (error) {
                console.error('Error fetching status:', error);
            }
        }, 1000);
    }
    
    updateUI(status) {
        if (status.customer_id && (status.status === 'recognized' || status.status === 'new_customer')) {
            // Customer identified
            this.recognitionStatus.className = `recognition-status ${status.status.replace('_', '-')}`;
            
            if (status.status === 'recognized') {
                this.recognitionStatus.innerHTML = '<i class="fas fa-user-check"></i><span>Welcome back!</span>';
                this.customerName.textContent = 'Welcome Back!';
                this.customerMessage.textContent = 'Great to see you again. Ready to order?';
                
                // ✅ Update welcome message untuk pelanggan lama
                this.updateWelcomeMessage(
                    '🎉 Selamat datang kembali! Kami senang Anda kembali ke cafe kami. Kami sudah menyiapkan rekomendasi berdasarkan pesanan favorit Anda sebelumnya.',
                    'recognized'
                );
            } else {
                this.recognitionStatus.innerHTML = '<i class="fas fa-user-plus"></i><span>New customer detected!</span>';
                this.customerName.textContent = 'Welcome!';
                this.customerMessage.textContent = 'Welcome to our cafe! Let\'s find your perfect drink.';
                
                // ✅ Update welcome message untuk pelanggan baru
                this.updateWelcomeMessage(
                    '👋 Selamat datang di cafe kami! Terima kasih telah memilih cafe kami. Mulai sekarang kami akan mengingat Anda dan memberikan pengalaman yang lebih personal di kunjungan selanjutnya.',
                    'new-customer'
                );
            }
            
            this.customerInfo.classList.remove('hidden');
            this.actionButtons.classList.remove('hidden');
        } else {
            // Scanning
            this.recognitionStatus.className = 'recognition-status scanning';
            this.recognitionStatus.innerHTML = '<i class="fas fa-search"></i><span>Scanning for face...</span>';
            this.customerInfo.classList.add('hidden');
            this.actionButtons.classList.add('hidden');
            
            // ✅ Default welcome message saat scanning
            this.updateWelcomeMessage(
                'Mohon tunggu sebentar sementara kami mengenali Anda... Pastikan wajah Anda terlihat jelas di kamera.',
                'scanning'
            );
        }
    }
    
    // ✅ NEW METHOD: Update welcome message
    updateWelcomeMessage(message, type) {
        if (this.welcomeMessage && this.dynamicWelcome) {
            // Remove existing type classes
            this.dynamicWelcome.classList.remove('recognized', 'new-customer', 'scanning');
            
            // Add new type class
            if (type !== 'scanning') {
                this.dynamicWelcome.classList.add(type);
            }
            
            // Update message with fade effect
            this.welcomeMessage.style.opacity = '0';
            
            setTimeout(() => {
                this.welcomeMessage.textContent = message;
                this.welcomeMessage.style.opacity = '1';
            }, 200);
        }
    }
    
    async resetSession() {
        try {
            await fetch('/api/reset_session', { method: 'POST' });
            this.customerInfo.classList.add('hidden');
            this.actionButtons.classList.add('hidden');
            
            // ✅ Reset welcome message
            this.updateWelcomeMessage(
                'Mohon tunggu sebentar sementara kami mengenali Anda...',
                'scanning'
            );
        } catch (error) {
            console.error('Error resetting session:', error);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new FaceRecognitionApp();
});