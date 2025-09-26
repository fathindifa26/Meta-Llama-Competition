class MenuSelectionApp {
    constructor() {
        this.menuGrid = document.getElementById('menu-grid');
        this.floatingCart = document.getElementById('floating-cart');
        this.cartCount = document.getElementById('cart-count');
        this.orderSummary = document.getElementById('order-summary');
        this.orderItems = document.getElementById('order-items');
        this.totalAmount = document.getElementById('total-amount');
        this.confirmOrderBtn = document.getElementById('confirm-order');
        this.clearOrderBtn = document.getElementById('clear-order');
        this.viewCartBtn = document.getElementById('view-cart');
        
        // Recommendation elements
        this.lastPurchaseSection = document.getElementById('last-purchase-section');
        this.popularSection = document.getElementById('popular-section');
        this.lastPurchaseCard = document.getElementById('last-purchase-card');
        this.popularCard = document.getElementById('popular-card');
        
        // ✅ Mood section elements
        this.moodSection = document.getElementById('moodSection');
        
        this.recommendations = null;
        this.cart = new Map(); // Map to store cart items
        this.menuItems = [];
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadMenu();
        this.addBackButton();
        
        // ✅ Initialize mood system after DOM is ready
        this.initializeMoodSystem();
    }
    
    // ✅ Initialize mood system integration
    initializeMoodSystem() {
        // Make addToCart method globally accessible for mood recommendations
        window.addToCart = (menuId) => {
            const menuItem = this.findMenuItemById(menuId);
            if (menuItem) {
                this.addToCartFromMood(menuItem);
            } else {
                console.warn('Menu item not found for mood recommendation:', menuId);
                this.showError('Menu item tidak ditemukan');
            }
        };
        
        // Also make it available as addToCartFromMood for specific calls
        window.addToCartFromMood = (menuId) => window.addToCart(menuId);
    }
    
    // ✅ Find menu item by ID
    findMenuItemById(menuId) {
        if (this.recommendations && this.recommendations.all_menu) {
            return this.recommendations.all_menu.find(item => item.id === menuId);
        }
        return null;
    }
    
    // ✅ Add to cart from mood recommendation with special handling
    addToCartFromMood(item) {
        // Add directly to cart with quantity 1 (similar to quickOrder)
        this.cart.set(item.id, {
            ...item,
            quantity: 1,
            totalPrice: item.price
        });
        
        // Update UI
        this.updateCartUI();
        this.showSuccessMessage(`🎭 ${item.name} dari rekomendasi mood ditambahkan ke cart!`);
        
        // Show floating cart briefly with special animation
        this.floatingCart.style.animation = 'bounce 0.6s ease, glow 1.5s ease';
        setTimeout(() => {
            this.floatingCart.style.animation = '';
        }, 1500);
        
        // Optional: Auto-hide mood result after successful add to cart
        setTimeout(() => {
            if (window.moodRecommendation) {
                const moodResult = document.getElementById('moodResult');
                if (moodResult && moodResult.style.display !== 'none') {
                    // Show a follow-up message
                    this.showFollowUpMessage();
                }
            }
        }, 2000);
    }
    
    // ✅ Show follow-up message after mood recommendation is added
    showFollowUpMessage() {
        const followUpDiv = document.createElement('div');
        followUpDiv.className = 'mood-followup-message';
        followUpDiv.innerHTML = `
            <div class="followup-content">
                <p>🎉 Perfect! Item sudah ditambahkan ke keranjang.</p>
                <p>Mau coba mood lain atau lanjut checkout?</p>
                <div class="followup-buttons">
                    <button onclick="window.moodRecommendation?.findAnotherMood()" class="btn-mood-again">
                        🔄 Cari Mood Lain
                    </button>
                    <button onclick="document.getElementById('view-cart').click()" class="btn-checkout-now">
                        🛒 Lihat Keranjang
                    </button>
                </div>
            </div>
        `;
        
        // Position it near the mood section
        const moodSection = document.getElementById('moodSection');
        if (moodSection) {
            moodSection.appendChild(followUpDiv);
            
            // Auto remove after 8 seconds
            setTimeout(() => {
                if (followUpDiv.parentNode) {
                    followUpDiv.style.animation = 'slideOut 0.3s ease-in';
                    setTimeout(() => followUpDiv.remove(), 300);
                }
            }, 8000);
        }
    }
    
    setupEventListeners() {
        // ✅ Check if elements exist before adding listeners
        if (this.viewCartBtn) {
            this.viewCartBtn.addEventListener('click', () => {
                this.showOrderSummary();
            });
        }
        
        if (this.confirmOrderBtn) {
            this.confirmOrderBtn.addEventListener('click', () => {
                this.confirmOrder();
            });
        }
        
        if (this.clearOrderBtn) {
            this.clearOrderBtn.addEventListener('click', () => {
                this.clearCart();
            });
        }
        
        // Close order summary when clicking outside
        if (this.orderSummary) {
            this.orderSummary.addEventListener('click', (e) => {
                if (e.target === this.orderSummary) {
                    this.hideOrderSummary();
                }
            });
        }
        
        // Handle escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideOrderSummary();
            }
        });
    }
    
    addBackButton() {
        const backButton = document.createElement('button');
        backButton.className = 'back-button';
        backButton.innerHTML = '<i class="fas fa-arrow-left"></i> Back to Camera';
        backButton.addEventListener('click', () => {
            window.location.href = '/';
        });
        document.body.appendChild(backButton);
    }
    
    async loadMenu() {
        try {
            console.log('🔄 Loading menu from API...');
            const response = await fetch('/api/menu');
            
            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            
            this.recommendations = await response.json();
            console.log('📋 Menu API Response:', this.recommendations);
            
            // Check if we have the required data
            if (!this.recommendations) {
                throw new Error('No data received from API');
            }
            
            if (!this.recommendations.all_menu || this.recommendations.all_menu.length === 0) {
                console.warn('⚠️ No menu items found!');
                this.showError('No menu items available');
                return;
            }
            
            console.log(`✅ Found ${this.recommendations.all_menu.length} menu items`);
            
            // ✅ Show mood section if mood features are available
            this.handleMoodFeatures();
            
            // Render recommendations first
            this.renderRecommendations();
            
            // Then render menu
            this.renderMenu();
            
        } catch (error) {
            console.error('❌ Error loading menu:', error);
            this.showError(`Failed to load menu: ${error.message}`);
            
            // Hide recommendation sections on error
            if (this.lastPurchaseSection) this.lastPurchaseSection.style.display = 'none';
            if (this.popularSection) this.popularSection.style.display = 'none';
            if (this.moodSection) this.moodSection.style.display = 'none';
        }
    }
    
    // ✅ Handle mood features availability
    handleMoodFeatures() {
        if (this.moodSection && this.recommendations.has_mood_features) {
            console.log('🎭 Mood features enabled - showing mood section');
            this.moodSection.style.display = 'block';
            
            // Add mood section to the flow with proper spacing
            this.moodSection.classList.add('mood-enabled');
            
            // Optionally show a brief intro animation
            setTimeout(() => {
                this.moodSection.style.animation = 'fadeInUp 0.6s ease-out';
            }, 500);
        } else {
            console.log('❌ Mood features not available');
            if (this.moodSection) {
                this.moodSection.style.display = 'none';
            }
        }
    }
    
    renderRecommendations() {
        console.log('🎯 Rendering recommendations:', this.recommendations);
        
        // Render Last Purchase Recommendation
        if (this.recommendations.last_purchase && this.lastPurchaseSection) {
            console.log('👑 Rendering last purchase:', this.recommendations.last_purchase.name);
            this.renderLastPurchase(this.recommendations.last_purchase);
            this.lastPurchaseSection.style.display = 'block';
        } else {
            console.log('👤 No last purchase - hiding section');
            if (this.lastPurchaseSection) this.lastPurchaseSection.style.display = 'none';
        }
        
        // Render Most Popular Recommendation
        if (this.recommendations.most_popular && this.popularSection) {
            console.log('🔥 Rendering most popular:', this.recommendations.most_popular.name);
            this.renderMostPopular(this.recommendations.most_popular);
            this.popularSection.style.display = 'block';
        } else {
            console.log('📊 No popular item - hiding section');
            if (this.popularSection) this.popularSection.style.display = 'none';
        }
    }
    
    renderLastPurchase(item) {
        if (!this.lastPurchaseCard) return;
        
        const lastPurchased = new Date(item.last_purchased);
        const timeAgo = this.getTimeAgo(lastPurchased);
        
        this.lastPurchaseCard.innerHTML = `
            <div class="recommendation-badge last-purchase">
                <i class="fas fa-crown"></i> Your Favorite
            </div>
            <div class="recommendation-content">
                <div class="recommendation-image">
                    <i class="${this.getMenuIcon(item.name)}"></i>
                </div>
                <div class="recommendation-details">
                    <div class="recommendation-name">${item.name}</div>
                    <div class="recommendation-description">${item.description}</div>
                    <div class="recommendation-meta">
                        <div class="recommendation-price">Rp ${this.formatPrice(item.price)}</div>
                        <div class="recommendation-stats">
                            Terakhir beli ${timeAgo} (${item.last_quantity}x)
                        </div>
                    </div>
                    <button class="quick-order" data-menu-id="${item.id}" data-recommendation="last-purchase">
                        <i class="fas fa-shopping-cart"></i>
                        Pesan Lagi
                    </button>
                </div>
            </div>
        `;
        
        // Add event listener
        const quickOrderBtn = this.lastPurchaseCard.querySelector('.quick-order');
        if (quickOrderBtn) {
            quickOrderBtn.addEventListener('click', () => {
                this.quickOrder(item);
            });
        }
    }
    
    renderMostPopular(item) {
        if (!item || !this.popularCard) {
            console.warn('⚠️ No popular item data or card element');
            return;
        }
        
        // Handle case where total_orders might be 0 or undefined
        const totalOrders = item.total_orders || 0;
        const statsText = totalOrders > 0 ? `${totalOrders} orang sudah pesan` : 'Menu favorit';
        
        this.popularCard.innerHTML = `
            <div class="recommendation-badge popular">
                <i class="fas fa-fire"></i> Most Popular
            </div>
            <div class="recommendation-content">
                <div class="recommendation-image">
                    <i class="${this.getMenuIcon(item.name)}"></i>
                </div>
                <div class="recommendation-details">
                    <div class="recommendation-name">${item.name}</div>
                    <div class="recommendation-description">${item.description || 'Delicious drink'}</div>
                    <div class="recommendation-meta">
                        <div class="recommendation-price">Rp ${this.formatPrice(item.price)}</div>
                        <div class="recommendation-stats">
                            ${statsText}
                        </div>
                    </div>
                    <button class="quick-order" data-menu-id="${item.id}" data-recommendation="popular">
                        <i class="fas fa-fire"></i>
                        Coba Sekarang
                    </button>
                </div>
            </div>
        `;
        
        // Add event listener with safety check
        const quickOrderBtn = this.popularCard.querySelector('.quick-order');
        if (quickOrderBtn) {
            quickOrderBtn.addEventListener('click', () => {
                this.quickOrder(item);
            });
        }
    }
        
    renderMenu() {
        console.log('📋 Rendering main menu...');
        
        if (!this.menuGrid) {
            console.error('❌ Menu grid element not found');
            return;
        }
        
        this.menuGrid.innerHTML = '';
        
        // Safety checks
        if (!this.recommendations) {
            console.error('❌ No recommendations data');
            this.showError('Menu data not available');
            return;
        }
        
        if (!this.recommendations.all_menu) {
            console.error('❌ No all_menu in recommendations');
            this.showError('Menu items not found');
            return;
        }
        
        if (this.recommendations.all_menu.length === 0) {
            console.warn('⚠️ Empty menu array');
            this.menuGrid.innerHTML = '<div class="empty-menu">No menu items available</div>';
            return;
        }
        
        // Render menu items
        console.log(`🍽️ Rendering ${this.recommendations.all_menu.length} menu items`);
        this.recommendations.all_menu.forEach((item, index) => {
            console.log(`   ${index + 1}. ${item.name} - Rp ${item.price}`);
            const menuCard = this.createMenuCard(item);
            this.menuGrid.appendChild(menuCard);
        });
        
        console.log('✅ Menu rendering completed');
    }
    
    createMenuCard(item) {
        const card = document.createElement('div');
        card.className = 'menu-item';
        card.dataset.menuId = item.id;
        
        // Get menu icon based on name
        const icon = this.getMenuIcon(item.name);
        
        card.innerHTML = `
            <div class="menu-image">
                <i class="${icon}"></i>
            </div>
            <div class="menu-details">
                <div class="menu-name">${item.name}</div>
                <div class="menu-description">${item.description}</div>
                <div class="menu-price">Rp ${this.formatPrice(item.price)}</div>
                <div class="quantity-controls">
                    <button class="qty-btn minus-btn" data-menu-id="${item.id}">-</button>
                    <span class="quantity-display" data-menu-id="${item.id}">0</span>
                    <button class="qty-btn plus-btn" data-menu-id="${item.id}">+</button>
                </div>
                <button class="add-to-cart" data-menu-id="${item.id}">
                    <i class="fas fa-cart-plus"></i>
                    Add to Cart
                </button>
            </div>
        `;
        
        // Add event listeners
        this.setupCardEventListeners(card, item);
        
        return card;
    }
    
    getMenuIcon(name) {
        const icons = {
            'Americano': 'fas fa-coffee',
            'Cappuccino': 'fas fa-coffee',
            'Latte': 'fas fa-mug-hot',
            'Cold Brew': 'fas fa-glass-whiskey',
            'Matcha Latte': 'fas fa-leaf'
        };
        return icons[name] || 'fas fa-coffee';
    }
    
    setupCardEventListeners(card, item) {
        const minusBtn = card.querySelector('.minus-btn');
        const plusBtn = card.querySelector('.plus-btn');
        const addToCartBtn = card.querySelector('.add-to-cart');
        
        if (minusBtn) {
            minusBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.updateQuantity(item.id, -1);
            });
        }
        
        if (plusBtn) {
            plusBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.updateQuantity(item.id, 1);
            });
        }
        
        if (addToCartBtn) {
            addToCartBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.addToCart(item);
            });
        }
    }
    
    updateQuantity(menuId, change) {
        const quantityDisplay = document.querySelector(`[data-menu-id="${menuId}"].quantity-display`);
        const minusBtn = document.querySelector(`[data-menu-id="${menuId}"].minus-btn`);
        const menuCard = document.querySelector(`[data-menu-id="${menuId}"]`);
        
        if (!quantityDisplay) return;
        
        let currentQty = parseInt(quantityDisplay.textContent);
        let newQty = Math.max(0, currentQty + change);
        
        quantityDisplay.textContent = newQty;
        
        if (minusBtn) {
            minusBtn.disabled = newQty === 0;
        }
        
        // Update card appearance
        if (menuCard) {
            if (newQty > 0) {
                menuCard.classList.add('selected');
            } else {
                menuCard.classList.remove('selected');
            }
        }
    }
    
    addToCart(item) {
        const quantityDisplay = document.querySelector(`[data-menu-id="${item.id}"].quantity-display`);
        
        if (!quantityDisplay) {
            console.warn('Quantity display not found for item:', item.id);
            return;
        }
        
        const quantity = parseInt(quantityDisplay.textContent);
        
        if (quantity === 0) {
            this.updateQuantity(item.id, 1);
            return;
        }
        
        // Add to cart
        this.cart.set(item.id, {
            ...item,
            quantity: quantity,
            totalPrice: item.price * quantity
        });
        
        // Update UI
        this.updateCartUI();
        this.showSuccessMessage(`${item.name} added to cart!`);
        
        // Reset quantity display
        quantityDisplay.textContent = '0';
        const menuCard = document.querySelector(`[data-menu-id="${item.id}"]`);
        if (menuCard) {
            menuCard.classList.remove('selected');
        }
    }
    
    quickOrder(item) {
        // Add directly to cart with quantity 1
        this.cart.set(item.id, {
            ...item,
            quantity: 1,
            totalPrice: item.price
        });
        
        // Update UI
        this.updateCartUI();
        this.showSuccessMessage(`${item.name} ditambahkan ke cart!`);
        
        // Show floating cart briefly
        if (this.floatingCart) {
            this.floatingCart.style.animation = 'bounce 0.6s ease';
            setTimeout(() => {
                this.floatingCart.style.animation = '';
            }, 600);
        }
    }
    
    updateCartUI() {
        const totalItems = Array.from(this.cart.values()).reduce((sum, item) => sum + item.quantity, 0);
        
        if (totalItems > 0) {
            if (this.floatingCart) this.floatingCart.classList.remove('hidden');
            if (this.cartCount) this.cartCount.textContent = totalItems;
        } else {
            if (this.floatingCart) this.floatingCart.classList.add('hidden');
        }
    }
    
    showOrderSummary() {
        if (this.cart.size === 0) {
            this.showError('Your cart is empty!');
            return;
        }
        
        this.renderOrderSummary();
        if (this.orderSummary) {
            this.orderSummary.classList.remove('hidden');
        }
    }
    
    hideOrderSummary() {
        if (this.orderSummary) {
            this.orderSummary.classList.add('hidden');
        }
    }
    
    renderOrderSummary() {
        if (!this.orderItems || !this.totalAmount) return;
        
        this.orderItems.innerHTML = '';
        let total = 0;
        
        Array.from(this.cart.values()).forEach(item => {
            total += item.totalPrice;
            
            const orderItem = document.createElement('div');
            orderItem.className = 'order-item';
            orderItem.innerHTML = `
                <div class="item-details">
                    <div class="item-name">${item.name}</div>
                    <div class="item-quantity">${item.quantity}x @ Rp ${this.formatPrice(item.price)}</div>
                </div>
                <div class="item-price">Rp ${this.formatPrice(item.totalPrice)}</div>
            `;
            
            this.orderItems.appendChild(orderItem);
        });
        
        this.totalAmount.textContent = `Rp ${this.formatPrice(total)}`;
    }
    
    async confirmOrder() {
        if (this.cart.size === 0) {
            this.showError('Your cart is empty!');
            return;
        }
        
        // Show loading state
        if (this.confirmOrderBtn) {
            this.confirmOrderBtn.classList.add('loading');
            this.confirmOrderBtn.disabled = true;
        }
        
        try {
            const orders = Array.from(this.cart.values()).map(item => ({
                menu_id: item.id,
                quantity: item.quantity
            }));
            
            const response = await fetch('/api/purchase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ orders })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showSuccessMessage(`Order confirmed! Total: Rp ${this.formatPrice(result.total)}`);
                this.clearCart();
                this.hideOrderSummary();
                
                // Show countdown redirect
                this.showCountdownRedirect();
            } else {
                throw new Error(result.error || 'Order failed');
            }
        } catch (error) {
            console.error('Order error:', error);
            this.showError('Failed to process order. Please try again.');
        } finally {
            if (this.confirmOrderBtn) {
                this.confirmOrderBtn.classList.remove('loading');
                this.confirmOrderBtn.disabled = false;
            }
        }
    }
    
    clearCart() {
        this.cart.clear();
        this.updateCartUI();
        this.hideOrderSummary();
        
        // Reset all quantity displays
        document.querySelectorAll('.quantity-display').forEach(display => {
            display.textContent = '0';
        });
        
        // Remove selected class from all cards
        document.querySelectorAll('.menu-item').forEach(card => {
            card.classList.remove('selected');
        });
    }
    
    showCountdownRedirect() {
        const countdownDiv = document.createElement('div');
        countdownDiv.className = 'countdown-redirect';
        countdownDiv.innerHTML = `
            <div class="countdown-content">
                <i class="fas fa-check-circle"></i>
                <h3>Order Berhasil!</h3>
                <p>Terima kasih atas pesanan Anda</p>
                <div class="countdown-timer">
                    Kembali ke camera dalam <span id="countdown">3</span> detik
                </div>
            </div>
        `;
        document.body.appendChild(countdownDiv);
        
        let countdown = 3;
        const countdownElement = document.getElementById('countdown');
        
        const interval = setInterval(() => {
            countdown--;
            if (countdownElement) {
                countdownElement.textContent = countdown;
            }
            
            if (countdown <= 0) {
                clearInterval(interval);
                window.location.href = '/';
            }
        }, 1000);
    }
    
    showSuccessMessage(message) {
        // Remove existing success message
        const existing = document.querySelector('.success-message');
        if (existing) {
            existing.remove();
        }
        
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
        document.body.appendChild(successDiv);
        
        // Show animation
        setTimeout(() => successDiv.classList.add('show'), 100);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            successDiv.classList.remove('show');
            setTimeout(() => {
                if (successDiv.parentNode) {
                    successDiv.remove();
                }
            }, 300);
        }, 3000);
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => errorDiv.classList.add('show'), 100);
        
        setTimeout(() => {
            errorDiv.classList.remove('show');
            setTimeout(() => {
                if (errorDiv.parentNode) {
                    errorDiv.remove();
                }
            }, 300);
        }, 3000);
    }
    
    getTimeAgo(date) {
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) {
            const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
            if (diffHours === 0) {
                const diffMinutes = Math.floor(diffTime / (1000 * 60));
                return `${diffMinutes} menit yang lalu`;
            }
            return `${diffHours} jam yang lalu`;
        } else if (diffDays === 1) {
            return 'kemarin';
        } else {
            return `${diffDays} hari yang lalu`;
        }
    }
    
    formatPrice(price) {
        return new Intl.NumberFormat('id-ID').format(price);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new MenuSelectionApp();
});