// Cashier POS JavaScript
let authToken = localStorage.getItem('authToken');
let currentUser = null;
let products = [];
let categories = [];
let currentOrder = [];
let currentOrderId = null; // Track if we're working with a loaded pending order
let selectedProduct = null;
let selectedSize = null;
let selectedModifiers = [];
let modalQuantity = 1;
let redirectAttempted = false;

// Initialize the POS
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're already on the login page to prevent infinite redirects
    if (window.location.pathname === '/login.html' || window.location.pathname === '/') {
        console.log('On login page, not initializing POS');
        return;
    }
    
    // Check if we have a valid token
    if (!authToken) {
        // Only redirect if we haven't already attempted it and we're not already on login
        if (!redirectAttempted && window.location.pathname !== '/login.html') {
            redirectAttempted = true;
            console.log('No auth token found, redirecting to login...');
            // Clear any existing cookies
            document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
            window.location.href = '/login.html';
        }
        return;
    }
    
    // If we have a token, proceed with initialization
    console.log('Auth token found, initializing POS...');
    
    loadUserInfo();
    loadProducts();
    loadCategories();
    ensureCashRegisterSession();
    loadSettings();
    
    // Listen for settings changes from admin panel
    window.addEventListener('storage', function(e) {
        if (e.key === 'posSettings') {
            const settings = JSON.parse(e.newValue || '{}');
            applySettings(settings);
        }
    });
});

// Load and apply settings
async function loadSettings() {
    try {
        // First try to load from localStorage (set by admin)
        const savedSettings = localStorage.getItem('posSettings');
        if (savedSettings) {
            const settings = JSON.parse(savedSettings);
            applySettings(settings);
            return;
        }
        
        // If no saved settings, try to load from public POS settings API
        const response = await fetch('/api/pos/settings', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const settingsMap = await response.json();
            
            // Save to localStorage for future use
            localStorage.setItem('posSettings', JSON.stringify(settingsMap));
            
            // Apply settings
            applySettings(settingsMap);
        }
    } catch (error) {
        console.error('Error loading settings:', error);
        // Load default settings if nothing works
        loadDefaultSettings();
    }
}

// Load default settings
function loadDefaultSettings() {
    const defaultSettings = {
        'shop-name': 'My Coffee Shop',
        'shop-slogan': 'Brewing Happiness',
        'currency-symbol': 'DZD',
        'primary-color': '#007bff',
        'secondary-color': '#6c757d',
        'accent-color': '#28a745',
        'background-type': 'solid',
        'background-color': '#f8f9fa',
        'card-style': 'default',
        'font-family': 'default',
        'font-size': 'medium',
        'theme-mode': 'light'
    };
    
    applySettings(defaultSettings);
}

// Apply settings to the interface
function applySettings(settings) {
    let settingsMap = {};
    
    // Handle both array format (from API) and object format (from localStorage)
    if (Array.isArray(settings)) {
        settings.forEach(setting => {
            settingsMap[setting.key] = setting.value;
        });
    } else {
        settingsMap = settings;
    }
    
    // Update shop name in header
    if (settingsMap['shop-name']) {
        const titleElement = document.querySelector('.pos-header h1');
        if (titleElement) {
            titleElement.textContent = settingsMap['shop-name'];
        }
        document.title = settingsMap['shop-name'] + ' - POS System';
    }
    
    // Apply color theme
    if (settingsMap['primary-color']) {
        document.documentElement.style.setProperty('--primary-color', settingsMap['primary-color']);
    }
    if (settingsMap['secondary-color']) {
        document.documentElement.style.setProperty('--secondary-color', settingsMap['secondary-color']);
    }
    if (settingsMap['accent-color']) {
        document.documentElement.style.setProperty('--accent-color', settingsMap['accent-color']);
    }
    
    // Apply background
    if (settingsMap['background-type'] === 'solid' && settingsMap['background-color']) {
        document.querySelector('.pos-container').style.background = settingsMap['background-color'];
    } else if (settingsMap['background-type'] === 'gradient' && settingsMap['primary-color'] && settingsMap['secondary-color']) {
        document.querySelector('.pos-container').style.background = `linear-gradient(135deg, ${settingsMap['primary-color']}, ${settingsMap['secondary-color']})`;
    }
    
    // Apply font family
    if (settingsMap['font-family'] && settingsMap['font-family'] !== 'default') {
        const fontFamily = getFontFamily(settingsMap['font-family']);
        document.body.style.fontFamily = fontFamily;
    }
    
    // Apply font size
    if (settingsMap['font-size']) {
        const sizeMap = { small: '0.875rem', medium: '1rem', large: '1.125rem' };
        document.body.style.fontSize = sizeMap[settingsMap['font-size']] || '1rem';
    }
    
    // Apply theme mode
    if (settingsMap['theme-mode'] === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
}

// Get font family CSS
function getFontFamily(fontName) {
    const fonts = {
        'roboto': '"Roboto", sans-serif',
        'opensans': '"Open Sans", sans-serif',
        'lato': '"Lato", sans-serif',
        'montserrat': '"Montserrat", sans-serif'
    };
    return fonts[fontName] || 'inherit';
}

// Authentication functions
function loadUserInfo() {
    const tokenPayload = JSON.parse(atob(authToken.split('.')[1]));
    currentUser = tokenPayload;
    document.getElementById('cashier-name').textContent = currentUser.username;
}

// Single logout definition (moved to the bottom of file). Duplicate removed.

// Cash register session management
async function ensureCashRegisterSession() {
    try {
        // Try to get existing open session
        const response = await fetch('/api/cash-register-sessions', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const sessions = await response.json();
            const openSession = sessions.find(s => s.status === 'open');
            if (openSession) {
                console.log('Open cash register session found');
                return;
            }
        }
        
        // No open session found, create one
        console.log('Creating new cash register session');
        await fetch('/api/cash-register-sessions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                starting_cash: 0
            })
        });
        
    } catch (error) {
        console.error('Error managing cash register session:', error);
        // Continue anyway - the error will be shown when trying to create an order
    }
}

// API helper functions
async function apiCall(endpoint, method = 'GET', data = null) {
    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        }
    };
    
    if (data) {
        config.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(`/api/pos${endpoint}`, config);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'API call failed');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        alert('Error: ' + error.message);
        throw error;
    }
}

// Product loading functions
async function loadProducts() {
    try {
        products = await apiCall('/pos/products');
        displayProducts(products);
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

async function loadCategories() {
    try {
        categories = await apiCall('/categories');
        displayCategories();
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function displayProducts(productsToShow) {
    const productGrid = document.getElementById('product-grid');
    
    if (productsToShow.length === 0) {
        productGrid.innerHTML = '<div class="col-12 text-center text-white"><p>No products available</p></div>';
        return;
    }
    
    productGrid.innerHTML = productsToShow.map(product => `
        <div class="col-xl-2 col-lg-3 col-md-4 col-sm-6 col-6 mb-3">
            <div class="product-card ${product.stock === 0 ? 'out-of-stock' : ''}" 
                 onclick="${product.stock > 0 ? `showProductModal(${product.id})` : ''}">
                <img src="${product.image_url || '/static/placeholder-coffee.svg'}" 
                     class="product-image" alt="${product.name}">
                <div class="product-name">${product.name}</div>
                <div class="product-price">DZD ${product.price.toFixed(2)}</div>
                ${product.stock === 0 ? '<small class="text-danger">Out of Stock</small>' : ''}
            </div>
        </div>
    `).join('');
}

function displayCategories() {
    const categoryTabs = document.querySelector('.category-tabs .d-flex');
    
    // Add "All" category
    categoryTabs.innerHTML = `
        <button class="category-tab active" onclick="filterByCategory('all')">
            All
        </button>
    `;
    
    // Add other categories
    categories.forEach(category => {
        categoryTabs.innerHTML += `
            <button class="category-tab" onclick="filterByCategory(${category.id})">
                ${category.name}
            </button>
        `;
    });
}

// Product filtering and search
function filterByCategory(categoryId) {
    // Update active tab
    document.querySelectorAll('.category-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    event.target.classList.add('active');
    
    let filteredProducts = products;
    if (categoryId !== 'all') {
        filteredProducts = products.filter(product => product.category_id === categoryId);
    }
    
    displayProducts(filteredProducts);
}

function searchProducts() {
    const searchTerm = document.getElementById('product-search').value.toLowerCase();
    const filteredProducts = products.filter(product => 
        product.name.toLowerCase().includes(searchTerm) ||
        product.description.toLowerCase().includes(searchTerm)
    );
    
    displayProducts(filteredProducts);
}

// Product modal functions
function showProductModal(productId) {
    selectedProduct = products.find(p => p.id === productId);
    if (!selectedProduct) return;
    
    // Reset selections
    selectedSize = null;
    selectedModifiers = [];
    modalQuantity = 1;
    
    // Update modal content
    document.getElementById('modalProductImage').src = selectedProduct.image_url || '/static/placeholder-coffee.svg';
    document.getElementById('modalProductName').textContent = selectedProduct.name;
    document.getElementById('modalProductDescription').textContent = selectedProduct.description || 'No description available';
    document.getElementById('modalQuantity').textContent = modalQuantity;
    document.getElementById('modalStock').textContent = selectedProduct.stock || 0;
    document.getElementById('specialInstructions').value = '';
    
    // Update quantity buttons state
    updateQuantityButtons();
    
    // Show/hide size options
    const sizeOptions = document.getElementById('sizeOptions');
    const sizeButtons = document.getElementById('sizeButtons');
    if (selectedProduct.sizes && selectedProduct.sizes.length > 0) {
        sizeOptions.style.display = 'block';
        sizeButtons.innerHTML = selectedProduct.sizes.map(size => `
            <button class="size-btn" onclick="selectSize(${size.id})" data-size-id="${size.id}">
                ${size.name} ${size.price_modifier > 0 ? `+DZD${size.price_modifier.toFixed(2)}` : ''}
            </button>
        `).join('');
    } else {
        sizeOptions.style.display = 'none';
    }
    
    // Show/hide modifier options
    const modifierOptions = document.getElementById('modifierOptions');
    const modifierList = document.getElementById('modifierList');
    if (selectedProduct.modifiers && selectedProduct.modifiers.length > 0) {
        modifierOptions.style.display = 'block';
        modifierList.innerHTML = selectedProduct.modifiers.map(modifier => `
            <div class="modifier-option">
                <label>
                    <input type="checkbox" class="modifier-checkbox" value="${modifier.id}" 
                           onchange="toggleModifier(${modifier.id})">
                    ${modifier.name}
                </label>
                <span>${modifier.price_modifier > 0 ? `+DZD${modifier.price_modifier.toFixed(2)}` : 'Free'}</span>
            </div>
        `).join('');
    } else {
        modifierOptions.style.display = 'none';
    }
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('productModal'));
    modal.show();
}

function selectSize(sizeId) {
    // Update button states
    document.querySelectorAll('.size-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    selectedSize = sizeId;
}

function toggleModifier(modifierId) {
    const checkbox = event.target;
    if (checkbox.checked) {
        selectedModifiers.push(modifierId);
    } else {
        selectedModifiers = selectedModifiers.filter(id => id !== modifierId);
    }
}

function increaseQuantity() {
    if (selectedProduct && modalQuantity < selectedProduct.stock) {
        modalQuantity++;
        document.getElementById('modalQuantity').textContent = modalQuantity;
        updateQuantityButtons();
    }
}

function decreaseQuantity() {
    if (modalQuantity > 1) {
        modalQuantity--;
        document.getElementById('modalQuantity').textContent = modalQuantity;
        updateQuantityButtons();
    }
}

function updateQuantityButtons() {
    const increaseBtn = document.querySelector('.quantity-btn[onclick="increaseQuantity()"]');
    const decreaseBtn = document.querySelector('.quantity-btn[onclick="decreaseQuantity()"]');
    
    if (selectedProduct) {
        // Disable increase button if at stock limit
        if (increaseBtn) {
            increaseBtn.disabled = modalQuantity >= selectedProduct.stock;
        }
        
        // Disable decrease button if at minimum
        if (decreaseBtn) {
            decreaseBtn.disabled = modalQuantity <= 1;
        }
    }
}

function addToOrder() {
    if (!selectedProduct) return;
    
    // Reset current order ID when adding new items (starting fresh order)
    currentOrderId = null;
    
    // Calculate price
    let unitPrice = selectedProduct.price;
    
    // Add size modifier
    if (selectedSize) {
        const size = selectedProduct.sizes.find(s => s.id === selectedSize);
        if (size) {
            unitPrice += size.price_modifier;
        }
    }
    
    // Add modifier costs
    let modifierCost = 0;
    selectedModifiers.forEach(modifierId => {
        const modifier = selectedProduct.modifiers.find(m => m.id === modifierId);
        if (modifier) {
            modifierCost += modifier.price_modifier;
        }
    });
    
    unitPrice += modifierCost;
    
    // Check if same item already exists in order
    const specialInstructions = document.getElementById('specialInstructions').value;
    const existingItemIndex = currentOrder.findIndex(item => 
        item.product_id === selectedProduct.id &&
        item.size_id === selectedSize &&
        JSON.stringify(item.modifier_ids.sort()) === JSON.stringify([...selectedModifiers].sort()) &&
        item.special_instructions === specialInstructions
    );
    
    if (existingItemIndex !== -1) {
        // Item exists, just increase quantity
        currentOrder[existingItemIndex].quantity += modalQuantity;
        currentOrder[existingItemIndex].total_price = currentOrder[existingItemIndex].unit_price * currentOrder[existingItemIndex].quantity;
    } else {
        // Create new order item
        const orderItem = {
            product_id: selectedProduct.id,
            product_name: selectedProduct.name,
            size_id: selectedSize,
            size_name: selectedSize ? selectedProduct.sizes.find(s => s.id === selectedSize)?.name : null,
            modifier_ids: [...selectedModifiers],
            modifiers: selectedModifiers.map(id => {
                const modifier = selectedProduct.modifiers.find(m => m.id === id);
                return modifier ? { name: modifier.name, price_modifier: modifier.price_modifier } : null;
            }).filter(m => m),
            quantity: modalQuantity,
            unit_price: unitPrice,
            total_price: unitPrice * modalQuantity,
            special_instructions: specialInstructions
        };
        
        // Add to current order
        currentOrder.push(orderItem);
    }
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('productModal'));
    modal.hide();
    
    // Update order display
    updateOrderDisplay();
}

// Order management functions
function updateOrderDisplay() {
    const orderItems = document.getElementById('order-items');
    const orderSummary = document.getElementById('order-summary');
    
    if (currentOrder.length === 0) {
        orderItems.innerHTML = `
            <div class="empty-cart">
                <i class="fas fa-shopping-cart"></i>
                <p>No items in cart</p>
                <small>Click on products to add them to your order</small>
            </div>
        `;
        orderSummary.style.display = 'none';
        return;
    }
    
    // Display order items
    orderItems.innerHTML = currentOrder.map((item, index) => `
        <div class="order-item">
            <div class="order-item-header">
                <div>
                    <strong>${item.product_name}</strong>
                    ${item.size_name ? `<br><small class="text-muted">Size: ${item.size_name}</small>` : ''}
                    ${item.modifiers.length > 0 ? `<br><small class="text-muted">Modifiers: ${item.modifiers.map(m => m.name).join(', ')}</small>` : ''}
                    ${item.special_instructions ? `<br><small class="text-info">Note: ${item.special_instructions}</small>` : ''}
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="removeOrderItem(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="d-flex justify-content-between align-items-center">
                <div class="quantity-controls">
                    <button class="quantity-btn" onclick="updateOrderItemQuantity(${index}, -1)">-</button>
                    <span>${item.quantity}</span>
                    <button class="quantity-btn" onclick="updateOrderItemQuantity(${index}, 1)">+</button>
                </div>
                <div class="text-end">
                    <div>DZD ${item.unit_price.toFixed(2)} each</div>
                    <div><strong>DZD ${item.total_price.toFixed(2)}</strong></div>
                </div>
            </div>
        </div>
    `).join('');
    
    // Calculate totals (no tax)
    const subtotal = currentOrder.reduce((sum, item) => sum + item.total_price, 0);
    const total = subtotal; // No tax
    
    document.getElementById('subtotal').textContent = `DZD ${subtotal.toFixed(2)}`;
    document.getElementById('tax').textContent = `DZD 0.00`;
    document.getElementById('total').textContent = `DZD ${total.toFixed(2)}`;
    
    orderSummary.style.display = 'block';
}

function removeOrderItem(index) {
    currentOrder.splice(index, 1);
    updateOrderDisplay();
}

function updateOrderItemQuantity(index, change) {
    const item = currentOrder[index];
    const newQuantity = item.quantity + change;
    
    if (newQuantity <= 0) {
        removeOrderItem(index);
        return;
    }
    
    item.quantity = newQuantity;
    item.total_price = item.unit_price * newQuantity;
    updateOrderDisplay();
}

// Payment processing
async function processPayment(paymentMethod) {
    if (currentOrder.length === 0) {
        alert('No items in cart');
        return;
    }
    
    // Only cash payment is available
    showCashCalculator();
}

// Save pending order (for dine-in customers)
async function savePendingOrder() {
    if (currentOrder.length === 0) {
        alert('No items in cart');
        return;
    }
    
    const customerName = document.getElementById('customer-name').value;
    const customerPhone = document.getElementById('customer-phone').value;
    // Default to takeaway since we removed the order type selection
    
    try {
        const orderData = {
            items: currentOrder.map(item => ({
                product_id: item.product_id,
                size_id: item.size_id,
                modifier_ids: item.modifier_ids,
                quantity: item.quantity,
                special_instructions: item.special_instructions
            })),
            customer_name: customerName,
            customer_phone: customerPhone,
            order_type: 'takeaway',
            notes: ''
        };
        
        const order = await apiCall('/pos/orders', 'POST', orderData);
        
        alert(`Order saved successfully! Order #${order.id}`);
        
        // Clear current order
        currentOrder = [];
        updateOrderDisplay();
        document.getElementById('customer-name').value = '';
        document.getElementById('customer-phone').value = '';
        
        // Reload products to update stock
        loadProducts();
        
    } catch (error) {
        console.error('Error saving pending order:', error);
        alert('Error saving order: ' + error.message);
    }
}

// Show cash calculator modal
function showCashCalculator() {
    const total = currentOrder.reduce((sum, item) => sum + item.total_price, 0);
    
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'cashCalculatorModal';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Cash Payment Calculator</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row mb-3">
                        <div class="col-6">
                            <label class="form-label">Order Total:</label>
                            <div class="form-control-plaintext fw-bold fs-4 text-primary">DZD ${total.toFixed(2)}</div>
                        </div>
                        <div class="col-6">
                            <label class="form-label">Amount Received:</label>
                            <input type="number" class="form-control form-control-lg" id="amountReceived" 
                                   placeholder="0" min="0" step="0.01">
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-12">
                            <label class="form-label">Change to Give:</label>
                            <div class="form-control-plaintext fw-bold fs-3 text-success" id="changeAmount">DZD 0.00</div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-12">
                            <div class="btn-group w-100" role="group">
                                <button type="button" class="btn btn-outline-secondary" onclick="addToAmount(50)">+50</button>
                                <button type="button" class="btn btn-outline-secondary" onclick="addToAmount(100)">+100</button>
                                <button type="button" class="btn btn-outline-secondary" onclick="addToAmount(200)">+200</button>
                                <button type="button" class="btn btn-outline-secondary" onclick="addToAmount(500)">+500</button>
                                <button type="button" class="btn btn-outline-secondary" onclick="addToAmount(1000)">+1000</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-success" id="processCashPayment" disabled>Process Payment</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Add event listeners
    const amountInput = document.getElementById('amountReceived');
    const changeDisplay = document.getElementById('changeAmount');
    const processBtn = document.getElementById('processCashPayment');
    
    amountInput.addEventListener('input', function() {
        const received = parseFloat(this.value) || 0;
        const change = received - total;
        changeDisplay.textContent = `DZD ${change.toFixed(2)}`;
        
        if (change >= 0) {
            processBtn.disabled = false;
            changeDisplay.className = 'form-control-plaintext fw-bold fs-3 text-success';
        } else {
            processBtn.disabled = true;
            changeDisplay.className = 'form-control-plaintext fw-bold fs-3 text-danger';
        }
    });
    
    processBtn.addEventListener('click', function() {
        const received = parseFloat(amountInput.value) || 0;
        if (received >= total) {
            processCashPayment(received);
            bsModal.hide();
        }
    });
    
    // Focus on amount input
    setTimeout(() => amountInput.focus(), 500);
    
    // Clean up modal when hidden
    modal.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(modal);
    });
}

// Add amount to calculator
function addToAmount(amount) {
    const input = document.getElementById('amountReceived');
    const current = parseFloat(input.value) || 0;
    input.value = (current + amount).toFixed(2);
    input.dispatchEvent(new Event('input'));
}

// Process cash payment
async function processCashPayment(amountReceived) {
    const customerName = document.getElementById('customer-name').value;
    const customerPhone = document.getElementById('customer-phone').value;
    
    try {
        let orderId;
        
        if (currentOrderId) {
            // We're completing an existing pending order
            orderId = currentOrderId;
        } else {
            // Create new order
            const orderData = {
                items: currentOrder.map(item => ({
                    product_id: item.product_id,
                    size_id: item.size_id,
                    modifier_ids: item.modifier_ids,
                    quantity: item.quantity,
                    special_instructions: item.special_instructions
                })),
                customer_name: customerName,
                customer_phone: customerPhone,
                notes: ''
            };
            
            const order = await apiCall('/pos/orders', 'POST', orderData);
            orderId = order.id;
        }
        
        // Complete order with cash payment
        const paymentData = {
            payment_method: 'cash',
            transaction_id: '',
            amount_received: amountReceived
        };
        
        await apiCall(`/pos/orders/${orderId}/complete`, 'POST', paymentData);
        
        // Show success message with change
        const total = currentOrder.reduce((sum, item) => sum + item.total_price, 0);
        const change = amountReceived - total;
        alert(`Payment successful!\nAmount received: DZD ${amountReceived}\nChange: DZD ${change.toFixed(2)}`);
        
        // Clear order and reset order ID
        currentOrder = [];
        currentOrderId = null;
        updateOrderDisplay();
        document.getElementById('customer-name').value = '';
        document.getElementById('customer-phone').value = '';
        
        // Reload products to update stock
        loadProducts();
        
        // Refresh pending orders list to remove completed order
        loadPendingOrdersList();
        
    } catch (error) {
        console.error('Error processing cash payment:', error);
        alert('Error processing payment: ' + error.message);
    }
}


function generateTransactionId() {
    return 'TXN' + Date.now() + Math.random().toString(36).substr(2, 5).toUpperCase();
}

// Pending orders management
async function showPendingOrders() {
    try {
        await loadPendingOrdersList();
        const modal = new bootstrap.Modal(document.getElementById('pendingOrdersModal'));
        modal.show();
    } catch (error) {
        console.error('Error showing pending orders:', error);
        alert('Error loading pending orders: ' + error.message);
    }
}

async function loadPendingOrdersList() {
    try {
        const orders = await apiCall('/pos/orders/pending');
        const pendingList = document.getElementById('pending-orders-list');
        
        if (orders.length === 0) {
            pendingList.innerHTML = `
                <div class="text-center py-4">
                    <i class="fas fa-clock fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No pending orders</p>
                </div>
            `;
        } else {
            pendingList.innerHTML = `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th>Order #</th>
                                <th>Customer</th>
                                <th>Items</th>
                                <th>Total</th>
                                <th>Time</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${orders.map(order => `
                                <tr class="order-row" data-order-id="${order.id}" style="cursor: pointer;">
                                    <td><strong>#${order.id}</strong></td>
                                    <td>${order.customer_name || 'N/A'}</td>
                                    <td>
                                        <small class="text-muted">
                                            ${order.items ? order.items.length : 0} item(s)
                                        </small>
                                    </td>
                                    <td><strong>DZD ${order.total.toFixed(2)}</strong></td>
                                    <td>
                                        <small class="text-muted">
                                            ${new Date(order.created_at).toLocaleTimeString()}
                                        </small>
                                    </td>
                                    <td>
                                        <div class="btn-group btn-group-sm">
                                            <button class="btn btn-outline-primary btn-sm" onclick="event.stopPropagation(); loadPendingOrder(${order.id})" title="Load Order">
                                                <i class="fas fa-edit" style="font-size: 0.7rem;"></i>
                                            </button>
                                            <button class="btn btn-outline-success btn-sm" onclick="event.stopPropagation(); completePendingOrder(${order.id})" title="Complete">
                                                <i class="fas fa-check" style="font-size: 0.7rem;"></i>
                                            </button>
                                            <button class="btn btn-outline-danger btn-sm" onclick="event.stopPropagation(); cancelPendingOrder(${order.id})" title="Cancel">
                                                <i class="fas fa-times" style="font-size: 0.7rem;"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
            
            // Add double-click event listeners to table rows
            setTimeout(() => {
                document.querySelectorAll('.order-row').forEach(row => {
                    row.addEventListener('dblclick', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        const orderId = this.getAttribute('data-order-id');
                        console.log('Double-clicked order:', orderId);
                        loadPendingOrder(orderId);
                    });
                });
            }, 100);
        }
        
    } catch (error) {
        console.error('Error loading pending orders list:', error);
        throw error;
    }
}

function refreshPendingOrders() {
    loadPendingOrdersList();
}

async function loadPendingOrder(orderId) {
    try {
        const order = await apiCall(`/pos/orders/${orderId}`);
        
        // Set the current order ID to track this is a loaded pending order
        currentOrderId = orderId;
        
        // Load order into current order
        currentOrder = (order.items || []).map(item => ({
            product_id: item.product_id,
            size_id: item.size_id,
            modifier_ids: item.modifier_ids || [],
            quantity: item.quantity,
            unit_price: item.unit_price,
            total_price: item.total_price,
            special_instructions: item.special_instructions || '',
            product_name: item.product_name,
            size_name: item.size_name || '',
            modifiers: item.modifiers || []
        }));
        
        // Set customer info
        document.getElementById('customer-name').value = order.customer_name || '';
        document.getElementById('customer-phone').value = order.customer_phone || '';
        
        // Order type is no longer needed since we removed the selection
        
        updateOrderDisplay();
        
        // Show the order summary if it was hidden
        const orderSummary = document.getElementById('order-summary');
        if (orderSummary && currentOrder.length > 0) {
            orderSummary.style.display = 'block';
        }
        
        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('pendingOrdersModal'));
        if (modal) {
            modal.hide();
        }
        
        // Order loaded successfully (no popup needed)
        
    } catch (error) {
        console.error('Error loading pending order:', error);
        alert('Error loading order: ' + error.message);
    }
}

async function completePendingOrder(orderId) {
    if (confirm('Are you sure you want to complete this order?')) {
        try {
            // Load the order first
            await loadPendingOrder(orderId);
            
            // Only cash payment is available
            showCashCalculator();
            
        } catch (error) {
            console.error('Error completing pending order:', error);
            alert('Error completing order: ' + error.message);
        }
    }
}

async function cancelPendingOrder(orderId) {
    if (confirm('Are you sure you want to cancel this order?')) {
        try {
            await apiCall(`/pos/orders/${orderId}/cancel`, 'POST');
            alert('Order cancelled successfully');
            await loadPendingOrdersList(); // Refresh the list
        } catch (error) {
            console.error('Error cancelling order:', error);
            alert('Error cancelling order: ' + error.message);
        }
    }
}

// Utility functions
function formatCurrency(amount) {
    return `DZD ${amount.toFixed(2)}`;
}

// Logout function
function logout() {
    // Clear localStorage
    localStorage.removeItem('authToken');
    
    // Clear cookie
    document.cookie = 'auth_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    
    // Redirect to login page
    window.location.href = '/login.html';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Set default dates for any date inputs
    const today = new Date().toISOString().split('T')[0];
    document.querySelectorAll('input[type="date"]').forEach(input => {
        if (!input.value) {
            input.value = today;
        }
    });
});
