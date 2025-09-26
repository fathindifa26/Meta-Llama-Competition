class MoodRecommendation {
    constructor() {
        this.isLoading = false;
        this.presets = {};
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }
    }
    
    setupEventListeners() {
        // Character counter for textarea
        const moodInput = document.getElementById('moodInput');
        const charCount = document.getElementById('charCount');
        
        if (moodInput && charCount) {
            moodInput.addEventListener('input', () => {
                const count = moodInput.value.length;
                charCount.textContent = count;
                
                // Change color when approaching limit
                if (count > 150) {
                    charCount.style.color = '#ff6b6b';
                } else {
                    charCount.style.color = '#666';
                }
            });
        }
        
        // Find mood match button
        const findButton = document.getElementById('findMoodMatch');
        if (findButton) {
            findButton.addEventListener('click', () => this.findMoodMatch());
        }
        
        // Enter key in textarea
        if (moodInput) {
            moodInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.findMoodMatch();
                }
            });
        }
        
        // Load mood presets
        this.loadMoodPresets();
    }
    
    async loadMoodPresets() {
        try {
            const response = await fetch('/api/mood-presets');
            const data = await response.json();
            
            if (data.success) {
                this.presets = data.presets;
                this.renderQuickMoods(data.presets);
            }
        } catch (error) {
            console.error('Error loading mood presets:', error);
            // Fallback presets
            this.renderFallbackMoods();
        }
    }
    
    renderQuickMoods(presets) {
        const quickMoodsContainer = document.getElementById('quickMoods');
        if (!quickMoodsContainer) return;
        
        const moodButtons = {
            'tired': '😴 Capek',
            'stress': '😰 Stress', 
            'hot': '🌡️ Kepanasan',
            'focus': '🎯 Butuh Fokus',
            'cozy': '🛋️ Pengen Nyaman',
            'creative': '🎨 Lagi Kreatif'
        };
        
        quickMoodsContainer.innerHTML = '';
        
        Object.keys(moodButtons).forEach(key => {
            if (presets[key]) {
                const button = document.createElement('button');
                button.className = 'mood-btn';
                button.textContent = moodButtons[key];
                button.onclick = () => this.selectMood(key);
                quickMoodsContainer.appendChild(button);
            }
        });
    }
    
    renderFallbackMoods() {
        const quickMoodsContainer = document.getElementById('quickMoods');
        if (!quickMoodsContainer) return;
        
        const fallbackMoods = [
            { key: 'tired', text: '😴 Capek', prompt: 'Hari ini capek banget, butuh energi' },
            { key: 'stress', text: '😰 Stress', prompt: 'Lagi stress, butuh yang menenangkan' },
            { key: 'hot', text: '🌡️ Kepanasan', prompt: 'Cuaca panas, pengen yang seger' },
            { key: 'focus', text: '🎯 Butuh Fokus', prompt: 'Butuh konsentrasi untuk kerja' },
            { key: 'cozy', text: '🛋️ Pengen Nyaman', prompt: 'Pengen suasana nyaman dan hangat' },
            { key: 'creative', text: '🎨 Lagi Kreatif', prompt: 'Mood kreatif, pengen yang unik' }
        ];
        
        quickMoodsContainer.innerHTML = '';
        
        fallbackMoods.forEach(mood => {
            const button = document.createElement('button');
            button.className = 'mood-btn';
            button.textContent = mood.text;
            button.onclick = () => this.selectFallbackMood(mood.prompt);
            quickMoodsContainer.appendChild(button);
        });
    }
    
    async selectMood(moodKey) {
        if (this.isLoading) return;
        
        try {
            this.setLoading(true, `Mencari rekomendasi untuk mood: ${moodKey}...`);
            
            const response = await fetch(`/api/mood-recommendation/preset/${moodKey}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            this.handleRecommendationResult(result);
            
        } catch (error) {
            console.error('Error getting preset recommendation:', error);
            this.showError('Gagal mendapatkan rekomendasi. Coba lagi.');
        } finally {
            this.setLoading(false);
        }
    }
    
    selectFallbackMood(promptText) {
        const moodInput = document.getElementById('moodInput');
        if (moodInput) {
            moodInput.value = promptText;
            // Update character counter
            const charCount = document.getElementById('charCount');
            if (charCount) {
                charCount.textContent = promptText.length;
            }
        }
        this.findMoodMatch();
    }
    
    async findMoodMatch() {
        if (this.isLoading) return;
        
        const moodInput = document.getElementById('moodInput');
        if (!moodInput) return;
        
        const userInput = moodInput.value.trim();
        if (!userInput) {
            alert('Ceritakan dulu perasaanmu hari ini! 😊');
            moodInput.focus();
            return;
        }
        
        if (userInput.length < 5) {
            alert('Cerita sedikit lebih detail ya supaya rekomendasinya lebih akurat! 😉');
            moodInput.focus();
            return;
        }
        
        try {
            this.setLoading(true, 'Menganalisis perasaanmu dan mencari rekomendasi terbaik...');
            
            const response = await fetch('/api/mood-recommendation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_input: userInput
                })
            });
            
            const result = await response.json();
            this.handleRecommendationResult(result);
            
        } catch (error) {
            console.error('Error getting mood recommendation:', error);
            this.showError('Gagal mendapatkan rekomendasi. Coba periksa koneksi internet dan coba lagi.');
        } finally {
            this.setLoading(false);
        }
    }
    
    handleRecommendationResult(result) {
        const resultContainer = document.getElementById('moodResult');
        if (!resultContainer) return;
        
        if (result.success) {
            const rec = result.recommendation;
            const menuItem = rec.menu_item;
            
            if (!menuItem) {
                this.showError('Menu item tidak ditemukan');
                return;
            }
            
            resultContainer.innerHTML = `
                <div class="mood-recommendation-card">
                    <div class="recommendation-header">
                        <h3>✨ Rekomendasi Untukmu</h3>
                        <span class="confidence-badge">${rec.confidence}% cocok</span>
                    </div>
                    
                    <div class="recommended-item">
                        <div class="item-image-placeholder">
                            <i class="fas fa-coffee"></i>
                        </div>
                        <div class="item-details">
                            <h4>${menuItem.name}</h4>
                            <p class="price">Rp ${parseInt(menuItem.price).toLocaleString('id-ID')}</p>
                            <p class="description">${menuItem.description}</p>
                        </div>
                    </div>
                    
                    <div class="recommendation-reason">
                        <h5>💭 Mengapa ini cocok untukmu:</h5>
                        <p>${rec.reason}</p>
                    </div>
                    
                    ${rec.alternative_item ? `
                        <div class="alternative-item">
                            <h5>🔄 Alternatif lain yang mungkin kamu suka:</h5>
                            <p><strong>${rec.alternative_item.name}</strong> - ${rec.alternative_item.description}</p>
                        </div>
                    ` : ''}
                    
                    <div class="action-buttons">
                        <button class="btn-primary" onclick="window.addToCart ? window.addToCart(${menuItem.id}) : alert('Menambahkan ${menuItem.name} ke keranjang...')">
                            🛒 Tambah ke Keranjang
                        </button>
                        <button class="btn-secondary" onclick="moodRecommendation.findAnotherMood()">
                            🔄 Cari Mood Lain
                        </button>
                    </div>
                    
                    ${rec.is_fallback ? '<p class="fallback-note">⚠️ Menggunakan sistem rekomendasi backup (AI sedang sibuk)</p>' : ''}
                </div>
            `;
            
            resultContainer.style.display = 'block';
            
            // Smooth scroll to result
            setTimeout(() => {
                resultContainer.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
            }, 100);
            
            // Track recommendation (optional analytics)
            this.trackRecommendation(rec);
            
        } else {
            this.showError(result.error || 'Gagal mendapatkan rekomendasi');
        }
    }
    
    setLoading(isLoading, message = '') {
        this.isLoading = isLoading;
        const findButton = document.getElementById('findMoodMatch');
        const resultContainer = document.getElementById('moodResult');
        const quickMoods = document.querySelectorAll('.mood-btn');
        
        if (isLoading) {
            // Disable controls
            if (findButton) {
                findButton.disabled = true;
                findButton.textContent = '🔄 Menganalisis...';
            }
            
            quickMoods.forEach(btn => btn.disabled = true);
            
            // Show loading state
            if (resultContainer) {
                resultContainer.innerHTML = `
                    <div class="loading-state">
                        <div class="spinner"></div>
                        <p>${message}</p>
                    </div>
                `;
                resultContainer.style.display = 'block';
            }
        } else {
            // Re-enable controls
            if (findButton) {
                findButton.disabled = false;
                findButton.textContent = '✨ Carikan Untukku';
            }
            
            quickMoods.forEach(btn => btn.disabled = false);
        }
    }
    
    showError(message) {
        const resultContainer = document.getElementById('moodResult');
        if (resultContainer) {
            resultContainer.innerHTML = `
                <div class="error-state">
                    <p>❌ ${message}</p>
                    <button onclick="moodRecommendation.findAnotherMood()">Coba Lagi</button>
                </div>
            `;
            resultContainer.style.display = 'block';
        }
    }
    
    findAnotherMood() {
        const moodInput = document.getElementById('moodInput');
        const resultContainer = document.getElementById('moodResult');
        
        if (moodInput) {
            moodInput.value = '';
            moodInput.focus();
        }
        
        if (resultContainer) {
            resultContainer.style.display = 'none';
        }
        
        // Reset character counter
        const charCount = document.getElementById('charCount');
        if (charCount) {
            charCount.textContent = '0';
            charCount.style.color = '#666';
        }
    }
    
    trackRecommendation(recommendation) {
        // Optional: Send analytics data
        console.log('Mood recommendation generated:', {
            item_id: recommendation.recommended_item_id,
            confidence: recommendation.confidence,
            timestamp: new Date().toISOString()
        });
    }
}

// Global functions untuk compatibility
function findAnotherMood() {
    if (window.moodRecommendation) {
        window.moodRecommendation.findAnotherMood();
    }
}

// Initialize mood recommendation system
let moodRecommendation;

// Initialize when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        moodRecommendation = new MoodRecommendation();
        window.moodRecommendation = moodRecommendation;
    });
} else {
    moodRecommendation = new MoodRecommendation();
    window.moodRecommendation = moodRecommendation;
}