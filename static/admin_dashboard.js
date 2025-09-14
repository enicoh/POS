// Admin Dashboard JavaScript
let authToken = localStorage.getItem('authToken');
let currentUser = null;
let redirectAttempted = false;

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're already on the login page to prevent infinite redirects
    if (window.location.pathname === '/login.html' || window.location.pathname === '/') {
        console.log('On login page, not initializing dashboard');
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
    console.log('Auth token found, initializing dashboard...');
    
    loadUserInfo();
    loadDashboard();
    
    // Reset product modal when it's hidden (only if not in edit mode)
    const productModal = document.getElementById('addProductModal');
    if (productModal) {
        productModal.addEventListener('hidden.bs.modal', function() {
            // Only reset if we're not in edit mode (check if button text is "Add Product")
            const buttonEl = document.getElementById('product-submit-btn');
            if (buttonEl && buttonEl.textContent === 'Add Product') {
                resetProductModal();
            }
        });
    }
    
    // Set up initial product submit button
    const productSubmitBtn = document.getElementById('product-submit-btn');
    if (productSubmitBtn) {
        productSubmitBtn.onclick = addProduct;
    }
    
    // Reset category modal when it's hidden
    const categoryModal = document.getElementById('addCategoryModal');
    if (categoryModal) {
        categoryModal.addEventListener('hidden.bs.modal', function() {
            resetCategoryModal();
        });
    }
    
    // Set up initial category submit button
    const categorySubmitBtn = document.getElementById('category-submit-btn');
    if (categorySubmitBtn) {
        categorySubmitBtn.onclick = addCategory;
    }
});

// Authentication functions
function loadUserInfo() {
    const tokenPayload = JSON.parse(atob(authToken.split('.')[1]));
    currentUser = tokenPayload;
    document.getElementById('admin-name').textContent = currentUser.username;
}

function logout() {
    localStorage.removeItem('authToken');
    window.location.href = '/login.html';
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
        console.error('API Error details:', error.message, error.stack);
        throw error;
    }
}

async function apiCallDirect(endpoint, method = 'GET', data = null) {
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
        const response = await fetch(endpoint, config);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'API call failed');
        }
        
        return result;
    } catch (error) {
        console.error('API Error:', error);
        console.error('API Error details:', error.message, error.stack);
        throw error;
    }
}

// Navigation functions
function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.style.display = 'none';
    });
    
    // Remove active class from all nav links
    document.querySelectorAll('.nav-link-admin').forEach(link => {
        link.classList.remove('active');
    });
    
    // Show selected section
    document.getElementById(`${sectionName}-section`).style.display = 'block';
    
    // Add active class to clicked nav link
    event.target.classList.add('active');
    
    // Update page title
    const titles = {
        'dashboard': 'Dashboard',
        'inventory': 'Inventory Management',
        'products': 'Product Management',
        'categories': 'Category Management',
        'sales': 'Sales Analytics',
        'users': 'User Management',
        'sizes': 'Product Sizes Management',
        'modifiers': 'Product Modifiers Management'
    };
    document.getElementById('page-title').textContent = titles[sectionName];
    
    // Load section data
    switch(sectionName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'inventory':
            loadInventory();
            break;
        case 'products':
            loadProducts();
            break;
        case 'categories':
            loadCategories();
            break;
        case 'sales':
            loadSalesAnalytics();
            break;
        case 'users':
            loadUsers();
            break;
    }
}

// Dashboard functions
async function loadDashboard() {
    try {
        console.log('Loading dashboard...');
        // Load dashboard statistics
        const stats = await apiCallDirect('/api/dashboard/stats');
        console.log('Dashboard stats received:', stats);
        
        // Update stats
        const totalProductsEl = document.getElementById('total-products');
        const lowStockEl = document.getElementById('low-stock-count');
        const todaySalesEl = document.getElementById('today-sales');
        const totalOrdersEl = document.getElementById('total-orders');
        
        if (totalProductsEl) {
            totalProductsEl.textContent = stats.total_products;
            console.log('Updated total products:', stats.total_products);
        }
        if (lowStockEl) {
            lowStockEl.textContent = stats.low_stock_count;
            console.log('Updated low stock:', stats.low_stock_count);
        }
        if (todaySalesEl) {
            todaySalesEl.textContent = `DZD ${stats.today_sales.toFixed(2)}`;
            console.log('Updated today sales:', stats.today_sales);
        }
        if (totalOrdersEl) {
            totalOrdersEl.textContent = stats.today_orders;
            console.log('Updated total orders:', stats.today_orders);
        }
        
        // Load inventory for low stock products
        try {
            const inventory = await apiCall('/admin/inventory');
            console.log('Inventory received:', inventory);
            
            // Load low stock products
            const lowStockList = document.getElementById('low-stock-list');
            if (inventory.low_stock_products.length === 0) {
                lowStockList.innerHTML = '<p class="text-muted">No low stock products</p>';
            } else {
                lowStockList.innerHTML = inventory.low_stock_products.map(product => `
                    <div class="alert alert-warning d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${product.name}</strong> - ${product.stock} remaining
                            <br><small class="text-muted">Threshold: ${product.low_stock_threshold}</small>
                        </div>
                        <button class="btn btn-sm btn-outline-warning" onclick="updateStockForProduct(${product.id}, '${product.name}', ${product.stock})">
                            Update Stock
                        </button>
                    </div>
                `).join('');
            }
        } catch (inventoryError) {
            console.error('Error loading inventory:', inventoryError);
            const lowStockList = document.getElementById('low-stock-list');
            lowStockList.innerHTML = '<p class="text-danger">Error loading inventory</p>';
        }
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        console.error('Dashboard error details:', error.message, error.stack);
        
        // Fallback to show 0 values for all stats
        const totalProductsEl = document.getElementById('total-products');
        const lowStockEl = document.getElementById('low-stock-count');
        const todaySalesEl = document.getElementById('today-sales');
        const totalOrdersEl = document.getElementById('total-orders');
        
        if (totalProductsEl) totalProductsEl.textContent = '0';
        if (lowStockEl) lowStockEl.textContent = '0';
        if (todaySalesEl) todaySalesEl.textContent = 'DZD 0.00';
        if (totalOrdersEl) totalOrdersEl.textContent = '0';
        
        // Show error message to user
        alert('Error loading dashboard data. Please check console for details.');
    }
}

// Inventory functions
async function loadInventory() {
    try {
        const inventory = await apiCall('/admin/inventory');
        const tableBody = document.getElementById('inventory-table');
        
        tableBody.innerHTML = inventory.inventory.map(product => {
            let statusClass = '';
            let statusText = '';
            
            if (product.stock === 0) {
                statusClass = 'out-of-stock';
                statusText = 'Out of Stock';
            } else if (product.low_stock_alert) {
                statusClass = 'low-stock';
                statusText = 'Low Stock';
            } else {
                statusClass = '';
                statusText = 'In Stock';
            }
            
            return `
                <tr class="${statusClass}">
                    <td>
                        <img src="${product.image_url || '/static/placeholder-coffee.jpg'}" 
                             class="product-image" alt="${product.name}">
                    </td>
                    <td>${product.name}</td>
                    <td>${product.category_name}</td>
                    <td>${product.stock}</td>
                    <td>${product.low_stock_threshold}</td>
                    <td><span class="badge bg-${product.stock === 0 ? 'danger' : product.low_stock_alert ? 'warning' : 'success'}">${statusText}</span></td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="updateStockForProduct(${product.id}, '${product.name}', ${product.stock})">
                            <i class="fas fa-edit"></i> Update Stock
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading inventory:', error);
    }
}

function refreshInventory() {
    loadInventory();
}

function updateStockForProduct(productId, productName, currentStock) {
    document.getElementById('update-product-id').value = productId;
    document.getElementById('update-product-name').value = productName;
    document.getElementById('update-stock-quantity').value = currentStock;
    
    const modal = new bootstrap.Modal(document.getElementById('updateStockModal'));
    modal.show();
}

async function updateStock() {
    try {
        const productId = document.getElementById('update-product-id').value;
        const newStock = document.getElementById('update-stock-quantity').value;
        
        await apiCall(`/admin/inventory/${productId}/stock`, 'PUT', {
            stock: parseInt(newStock)
        });
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('updateStockModal'));
        modal.hide();
        
        loadInventory();
        loadDashboard();
        
        alert('Stock updated successfully!');
    } catch (error) {
        console.error('Error updating stock:', error);
    }
}

// Product functions
async function loadProducts() {
    try {
        const inventory = await apiCall('/admin/inventory');
        const tableBody = document.getElementById('products-table');
        
        tableBody.innerHTML = inventory.inventory.map(product => `
            <tr class="product-row">
                <td>
                    <img src="${product.image_url || '/static/placeholder-coffee.svg'}" 
                         class="product-image" alt="${product.name}">
                </td>
                <td>
                    <i class="fas fa-chevron-right me-2 text-muted"></i>${product.name}
                </td>
                <td>${product.category_name}</td>
                <td>DZD ${product.price.toFixed(2)}</td>
                <td>${product.stock}</td>
                <td>
                    <span class="badge bg-${product.is_active ? 'success' : 'secondary'}">
                        ${product.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editProduct(${product.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteProduct(${product.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
            <tr id="product-details-${product.id}" class="product-details-row" style="display: none;">
                <td colspan="7">
                    <div class="product-details-card">
                        <div class="card-body">
                            <div class="row">
                                <div class="col-md-6">
                                    <h6><i class="fas fa-ruler me-2"></i>Sizes</h6>
                                    <div id="sizes-${product.id}">
                                        <div class="text-center text-muted">
                                            <i class="fas fa-spinner fa-spin"></i> Loading...
                                        </div>
                                    </div>
                                    <button class="btn btn-sm btn-outline-success mt-2" onclick="showAddSizeModal(${product.id})">
                                        <i class="fas fa-plus me-1"></i>Add Size
                                    </button>
                                </div>
                                <div class="col-md-6">
                                    <h6><i class="fas fa-plus-circle me-2"></i>Modifiers</h6>
                                    <div id="modifiers-${product.id}">
                                        <div class="text-center text-muted">
                                            <i class="fas fa-spinner fa-spin"></i> Loading...
                                        </div>
                                    </div>
                                    <button class="btn btn-sm btn-outline-success mt-2" onclick="showAddModifierModal(${product.id})">
                                        <i class="fas fa-plus me-1"></i>Add Modifier
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `).join('');
        
        // Add click handlers for expand/collapse
        tableBody.querySelectorAll('tr').forEach((row, index) => {
            if (index % 2 === 0) { // Only for product rows, not detail rows
                const productId = inventory.inventory[Math.floor(index / 2)]?.id;
                if (productId) {
                    row.addEventListener('click', () => toggleProductDetails(productId));
                    row.style.cursor = 'pointer';
                }
            }
        });
        
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

function showAddProductModal() {
    loadCategoriesForSelect();
    resetProductModal(); // This will reset the modal to add mode
    const modal = new bootstrap.Modal(document.getElementById('addProductModal'));
    modal.show();
}

async function loadCategoriesForSelect() {
    try {
        const categories = await apiCall('/categories');
        const select = document.getElementById('product-category');
        
        console.log('Loading categories for select:', categories);
        
        select.innerHTML = categories.map(category => 
            `<option value="${category.id}">${category.name}</option>`
        ).join('');
        
        console.log('Category options set:', Array.from(select.options).map(opt => ({ value: opt.value, text: opt.text })));
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function addProduct() {
    try {
        const productData = {
            name: document.getElementById('product-name').value,
            category_id: parseInt(document.getElementById('product-category').value),
            price: parseInt(document.getElementById('product-price').value),
            stock: parseInt(document.getElementById('product-stock').value),
            description: document.getElementById('product-description').value,
            image_url: document.getElementById('product-image-url').value,
            low_stock_threshold: parseInt(document.getElementById('product-low-stock').value)
        };
        
        await apiCall('/admin/products', 'POST', productData);
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('addProductModal'));
        modal.hide();
        
        document.getElementById('addProductForm').reset();
        loadProducts();
        loadDashboard();
        
        alert('Product added successfully!');
    } catch (error) {
        console.error('Error adding product:', error);
    }
}

// Category functions
async function loadCategories() {
    try {
        const categories = await apiCallDirect('/api/categories');
        const tableBody = document.getElementById('categories-table');
        
        tableBody.innerHTML = categories.map(category => `
            <tr>
                <td>${category.name}</td>
                <td>${category.description || 'No description'}</td>
                <td>${category.product_count || 0}</td>
                <td>
                    <span class="badge bg-${category.is_active ? 'success' : 'secondary'}">
                        ${category.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editCategory(${category.id})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteCategory(${category.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function showAddCategoryModal() {
    resetCategoryModal(); // This will reset the modal to add mode
    const modal = new bootstrap.Modal(document.getElementById('addCategoryModal'));
    modal.show();
}

async function addCategory() {
    try {
        const categoryData = {
            name: document.getElementById('category-name').value,
            description: document.getElementById('category-description').value
        };
        
        await apiCallDirect('/api/categories', 'POST', categoryData);
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('addCategoryModal'));
        modal.hide();
        
        document.getElementById('addCategoryForm').reset();
        loadCategories();
        
        alert('Category added successfully!');
    } catch (error) {
        console.error('Error adding category:', error);
    }
}

// User functions
async function loadUsers() {
    try {
        const users = await apiCall('/users');
        const tableBody = document.getElementById('users-table');
        
        tableBody.innerHTML = users.map(user => `
            <tr>
                <td>${user.username}</td>
                <td>
                    <span class="badge bg-${user.role === 'admin' ? 'primary' : 'info'}">
                        ${user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                    </span>
                </td>
                <td>
                    <span class="badge bg-${user.is_active ? 'success' : 'secondary'}">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>${new Date(user.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteUser(${user.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
        
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

function showAddUserModal() {
    const modal = new bootstrap.Modal(document.getElementById('addUserModal'));
    modal.show();
}

async function addUser() {
    try {
        const userData = {
            username: document.getElementById('user-username').value,
            password: document.getElementById('user-password').value,
            role: document.getElementById('user-role').value
        };
        
        await apiCall('/users', 'POST', userData);
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('addUserModal'));
        modal.hide();
        
        document.getElementById('addUserForm').reset();
        loadUsers();
        
        alert('User added successfully!');
    } catch (error) {
        console.error('Error adding user:', error);
    }
}

// Sales Analytics functions
async function loadSalesAnalytics() {
    try {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        let endpoint = '/analytics/sales';
        if (startDate && endDate) {
            endpoint += `?start_date=${startDate}&end_date=${endDate}`;
        }
        
        const analytics = await apiCall(endpoint);
        const content = document.getElementById('sales-analytics-content');
        
        content.innerHTML = `
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3 class="text-primary">DZD ${analytics.total_sales.toFixed(2)}</h3>
                            <p class="mb-0">Total Sales</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3 class="text-success">${analytics.total_orders}</h3>
                            <p class="mb-0">Total Orders</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card text-center">
                        <div class="card-body">
                            <h3 class="text-warning">${Object.keys(analytics.product_sales).length}</h3>
                            <p class="mb-0">Products Sold</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Top Selling Products</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Product</th>
                                    <th>Quantity Sold</th>
                                    <th>Revenue</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${Object.entries(analytics.product_sales)
                                    .sort((a, b) => b[1].revenue - a[1].revenue)
                                    .map(([product, data]) => `
                                        <tr>
                                            <td>${product}</td>
                                            <td>${data.quantity}</td>
                                            <td>DZD ${data.revenue.toFixed(2)}</td>
                                        </tr>
                                    `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        // Check scheduler status
        checkSchedulerStatus();
        
    } catch (error) {
        console.error('Error loading sales analytics:', error);
    }
}

// Generate PDF report
async function generateSalesReportPDF() {
    try {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        let url = '/api/pos/analytics/sales/pdf';
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);
        
        if (params.toString()) {
            url += '?' + params.toString();
        }
        
        // Create a temporary link to download the PDF
        const link = document.createElement('a');
        link.href = url;
        link.download = `sales_report_${startDate || 'all'}_${endDate || 'present'}.pdf`;
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
    } catch (error) {
        console.error('Error generating PDF report:', error);
        alert('Error generating PDF report: ' + error.message);
    }
}

// Reset daily analytics function
async function resetDailyAnalytics() {
    if (!confirm('Are you sure you want to reset daily analytics? This will clear today\'s data from the analytics view but preserve it for PDF reports.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/pos/analytics/reset', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Daily analytics reset successfully!');
            // Reload the analytics to show the reset state
            loadSalesAnalytics();
            // Update scheduler status
            checkSchedulerStatus();
        } else {
            throw new Error(result.error || 'Reset failed');
        }
    } catch (error) {
        console.error('Error resetting daily analytics:', error);
        alert('Error resetting daily analytics: ' + error.message);
    }
}

// Check scheduler status function
async function checkSchedulerStatus() {
    try {
        const response = await fetch('/api/pos/analytics/scheduler/status', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            const messageElement = document.getElementById('scheduler-message');
            if (result.scheduler_active) {
                if (result.next_reset) {
                    const nextReset = new Date(result.next_reset);
                    const now = new Date();
                    const timeDiff = nextReset - now;
                    const hours = Math.floor(timeDiff / (1000 * 60 * 60));
                    const minutes = Math.floor((timeDiff % (1000 * 60 * 60)) / (1000 * 60));
                    
                    if (timeDiff > 0) {
                        messageElement.textContent = `Next automatic reset: ${nextReset.toLocaleString()} (in ${hours}h ${minutes}m)`;
                    } else {
                        messageElement.textContent = 'Next automatic reset: Tonight at 00:00';
                    }
                } else {
                    messageElement.textContent = 'Automatic reset scheduled for 00:00 every day';
                }
            } else {
                messageElement.textContent = 'Scheduler not active';
            }
        } else {
            document.getElementById('scheduler-message').textContent = 'Unable to load scheduler status';
        }
    } catch (error) {
        console.error('Error checking scheduler status:', error);
        document.getElementById('scheduler-message').textContent = 'Error loading scheduler status';
    }
}

// ---------- PRODUCT SIZES & MODIFIERS MANAGEMENT ----------

let currentProductId = null;

// Toggle product details (sizes and modifiers)
function toggleProductDetails(productId) {
    const detailsRow = document.getElementById(`product-details-${productId}`);
    const productRow = detailsRow.previousElementSibling;
    const arrow = productRow.querySelector('.fa-chevron-right');
    
    if (detailsRow.style.display === 'none') {
        detailsRow.style.display = 'table-row';
        arrow.classList.remove('fa-chevron-right');
        arrow.classList.add('fa-chevron-down');
        // Load sizes and modifiers when expanding
        loadProductSizesInline(productId);
        loadProductModifiersInline(productId);
    } else {
        detailsRow.style.display = 'none';
        arrow.classList.remove('fa-chevron-down');
        arrow.classList.add('fa-chevron-right');
    }
}

// Load sizes for inline display
async function loadProductSizesInline(productId) {
    try {
        const response = await apiCall(`/admin/products/${productId}/sizes`);
        const sizes = response.sizes;
        
        const container = document.getElementById(`sizes-${productId}`);
        if (sizes.length === 0) {
            container.innerHTML = `
                <div class="text-muted small">
                    <i class="fas fa-ruler me-1"></i>No sizes defined
                </div>
            `;
            return;
        }
        
        container.innerHTML = sizes.map(size => `
            <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded size-modifier-item">
                <div>
                    <strong>${size.name}</strong>
                    <span class="text-muted ms-2">DZD ${size.price_modifier.toFixed(2)}</span>
                </div>
                <div>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editSizeInline(${size.id}, '${size.name}', ${size.price_modifier}, ${productId})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteSizeInline(${size.id}, ${productId})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading product sizes:', error);
        document.getElementById(`sizes-${productId}`).innerHTML = `
            <div class="text-danger small">
                <i class="fas fa-exclamation-triangle me-1"></i>Error loading sizes
            </div>
        `;
    }
}

// Load modifiers for inline display
async function loadProductModifiersInline(productId) {
    try {
        const response = await apiCall(`/admin/products/${productId}/modifiers`);
        const modifiers = response.modifiers;
        
        const container = document.getElementById(`modifiers-${productId}`);
        if (modifiers.length === 0) {
            container.innerHTML = `
                <div class="text-muted small">
                    <i class="fas fa-plus-circle me-1"></i>No modifiers defined
                </div>
            `;
            return;
        }
        
        container.innerHTML = modifiers.map(modifier => `
            <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded size-modifier-item">
                <div>
                    <strong>${modifier.name}</strong>
                    <span class="text-muted ms-2">DZD ${modifier.price_modifier.toFixed(2)}</span>
                </div>
                <div>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editModifierInline(${modifier.id}, '${modifier.name}', ${modifier.price_modifier}, ${productId})">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteModifierInline(${modifier.id}, ${productId})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading product modifiers:', error);
        document.getElementById(`modifiers-${productId}`).innerHTML = `
            <div class="text-danger small">
                <i class="fas fa-exclamation-triangle me-1"></i>Error loading modifiers
            </div>
        `;
    }
}

// Show add size modal for specific product
function showAddSizeModal(productId) {
    currentProductId = productId;
    const name = prompt('Enter size name:');
    if (!name) return;
    
    const priceModifier = prompt('Enter price modifier (DZD):', '0');
    if (priceModifier === null) return;
    
    const modifier = parseFloat(priceModifier);
    if (isNaN(modifier)) {
        alert('Invalid price modifier');
        return;
    }
    
    saveSizeInline(productId, name, modifier);
}

// Show add modifier modal for specific product
function showAddModifierModal(productId) {
    currentProductId = productId;
    const name = prompt('Enter modifier name:');
    if (!name) return;
    
    const priceModifier = prompt('Enter price modifier (DZD):', '0');
    if (priceModifier === null) return;
    
    const modifier = parseFloat(priceModifier);
    if (isNaN(modifier)) {
        alert('Invalid price modifier');
        return;
    }
    
    saveModifierInline(productId, name, modifier);
}

// Save size inline
async function saveSizeInline(productId, name, priceModifier) {
    try {
        const response = await fetch(`/api/pos/admin/products/${productId}/sizes`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, price_modifier: priceModifier })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            loadProductSizesInline(productId);
        } else {
            throw new Error(result.error || 'Failed to save size');
        }
        
    } catch (error) {
        console.error('Error saving size:', error);
        alert('Error saving size: ' + error.message);
    }
}

// Save modifier inline
async function saveModifierInline(productId, name, priceModifier) {
    try {
        const response = await fetch(`/api/pos/admin/products/${productId}/modifiers`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, price_modifier: priceModifier })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            loadProductModifiersInline(productId);
        } else {
            throw new Error(result.error || 'Failed to save modifier');
        }
        
    } catch (error) {
        console.error('Error saving modifier:', error);
        alert('Error saving modifier: ' + error.message);
    }
}

// Edit size inline
function editSizeInline(sizeId, currentName, currentPrice, productId) {
    const newName = prompt('Enter new size name:', currentName);
    if (newName === null) return;
    
    const newPrice = prompt('Enter new price modifier (DZD):', currentPrice.toString());
    if (newPrice === null) return;
    
    const modifier = parseFloat(newPrice);
    if (isNaN(modifier)) {
        alert('Invalid price modifier');
        return;
    }
    
    updateSizeInline(sizeId, newName, modifier, productId);
}

// Edit modifier inline
function editModifierInline(modifierId, currentName, currentPrice, productId) {
    const newName = prompt('Enter new modifier name:', currentName);
    if (newName === null) return;
    
    const newPrice = prompt('Enter new price modifier (DZD):', currentPrice.toString());
    if (newPrice === null) return;
    
    const modifier = parseFloat(newPrice);
    if (isNaN(modifier)) {
        alert('Invalid price modifier');
        return;
    }
    
    updateModifierInline(modifierId, newName, modifier, productId);
}

// Update size inline
async function updateSizeInline(sizeId, name, priceModifier, productId) {
    try {
        const response = await fetch(`/api/pos/admin/sizes/${sizeId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, price_modifier: priceModifier })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            loadProductSizesInline(productId);
        } else {
            throw new Error(result.error || 'Failed to update size');
        }
        
    } catch (error) {
        console.error('Error updating size:', error);
        alert('Error updating size: ' + error.message);
    }
}

// Update modifier inline
async function updateModifierInline(modifierId, name, priceModifier, productId) {
    try {
        const response = await fetch(`/api/pos/admin/modifiers/${modifierId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, price_modifier: priceModifier })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            loadProductModifiersInline(productId);
        } else {
            throw new Error(result.error || 'Failed to update modifier');
        }
        
    } catch (error) {
        console.error('Error updating modifier:', error);
        alert('Error updating modifier: ' + error.message);
    }
}

// Delete size inline
async function deleteSizeInline(sizeId, productId) {
    if (!confirm('Are you sure you want to delete this size?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/pos/admin/sizes/${sizeId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            loadProductSizesInline(productId);
        } else {
            throw new Error(result.error || 'Failed to delete size');
        }
        
    } catch (error) {
        console.error('Error deleting size:', error);
        alert('Error deleting size: ' + error.message);
    }
}

// Delete modifier inline
async function deleteModifierInline(modifierId, productId) {
    if (!confirm('Are you sure you want to delete this modifier?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/pos/admin/modifiers/${modifierId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            loadProductModifiersInline(productId);
        } else {
            throw new Error(result.error || 'Failed to delete modifier');
        }
        
    } catch (error) {
        console.error('Error deleting modifier:', error);
        alert('Error deleting modifier: ' + error.message);
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
    
    Object.keys(defaultSettings).forEach(key => {
        const element = document.getElementById(key);
        if (element) {
            element.value = defaultSettings[key];
            if (element.type === 'color') {
                const textElement = document.getElementById(key + '-text');
                if (textElement) {
                    textElement.value = defaultSettings[key];
                }
            }
        }
    });
    
    setupColorPickers();
    setupBackgroundTypeListener();
}

// Setup color picker event listeners
function setupColorPickers() {
    const colorInputs = ['primary-color', 'secondary-color', 'accent-color', 'background-color'];
    
    colorInputs.forEach(colorId => {
        const colorInput = document.getElementById(colorId);
        const textInput = document.getElementById(colorId + '-text');
        
        if (colorInput && textInput) {
            colorInput.addEventListener('input', function() {
                textInput.value = this.value;
                previewSettings();
            });
            
            textInput.addEventListener('input', function() {
                if (this.value.match(/^#[0-9A-F]{6}$/i)) {
                    colorInput.value = this.value;
                    previewSettings();
                }
            });
        }
    });
}

// Setup background type change listener
function setupBackgroundTypeListener() {
    const backgroundType = document.getElementById('background-type');
    const colorGroup = document.getElementById('background-color-group');
    const imageGroup = document.getElementById('background-image-group');
    
    if (backgroundType) {
        backgroundType.addEventListener('change', function() {
            if (this.value === 'image') {
                colorGroup.style.display = 'none';
                imageGroup.style.display = 'block';
            } else {
                colorGroup.style.display = 'block';
                imageGroup.style.display = 'none';
            }
            previewSettings();
        });
    }
}

// Preview settings changes
function previewSettings() {
    const primaryColor = document.getElementById('primary-color').value;
    const secondaryColor = document.getElementById('secondary-color').value;
    const accentColor = document.getElementById('accent-color').value;
    const backgroundColor = document.getElementById('background-color').value;
    const backgroundType = document.getElementById('background-type').value;
    const cardStyle = document.getElementById('card-style').value;
    const fontFamily = document.getElementById('font-family').value;
    const fontSize = document.getElementById('font-size').value;
    const themeMode = document.getElementById('theme-mode').value;
    
    // Apply CSS variables for preview
    const root = document.documentElement;
    root.style.setProperty('--primary-color', primaryColor);
    root.style.setProperty('--secondary-color', secondaryColor);
    root.style.setProperty('--accent-color', accentColor);
    
    // Apply background
    if (backgroundType === 'solid') {
        document.body.style.background = backgroundColor;
    } else if (backgroundType === 'gradient') {
        document.body.style.background = `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})`;
    }
    
    // Apply card styles
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.className = 'card';
        if (cardStyle === 'rounded') {
            card.classList.add('rounded-4');
        } else if (cardStyle === 'shadow') {
            card.classList.add('shadow-lg');
        } else if (cardStyle === 'bordered') {
            card.classList.add('border-2');
        }
    });
    
    // Apply font family
    if (fontFamily !== 'default') {
        document.body.style.fontFamily = getFontFamily(fontFamily);
    } else {
        document.body.style.fontFamily = '';
    }
    
    // Apply font size
    const sizeMap = { small: '0.875rem', medium: '1rem', large: '1.125rem' };
    document.body.style.fontSize = sizeMap[fontSize] || '1rem';
    
    // Apply theme mode
    if (themeMode === 'dark') {
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

// Save settings
async function saveSettings() {
    try {
        const settings = {
            'shop-name': document.getElementById('shop-name').value,
            'shop-slogan': document.getElementById('shop-slogan').value,
            'currency-symbol': document.getElementById('currency-symbol').value,
            'primary-color': document.getElementById('primary-color').value,
            'secondary-color': document.getElementById('secondary-color').value,
            'accent-color': document.getElementById('accent-color').value,
            'background-type': document.getElementById('background-type').value,
            'background-color': document.getElementById('background-color').value,
            'card-style': document.getElementById('card-style').value,
            'font-family': document.getElementById('font-family').value,
            'font-size': document.getElementById('font-size').value,
            'theme-mode': document.getElementById('theme-mode').value
        };
        
        const response = await fetch('/api/pos/admin/settings', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });
        
        const result = await response.json();
        
        if (response.ok) {
            alert('Settings saved successfully!');
            // Apply settings immediately
            applySettings(settings);
        } else {
            throw new Error(result.error || 'Failed to save settings');
        }
        
    } catch (error) {
        console.error('Error saving settings:', error);
        alert('Error saving settings: ' + error.message);
    }
}

// Apply settings to the interface
function applySettings(settings) {
    // Update page title
    if (settings['shop-name']) {
        document.title = settings['shop-name'] + ' - POS System';
        const titleElement = document.querySelector('.navbar-brand');
        if (titleElement) {
            titleElement.textContent = settings['shop-name'];
        }
    }
    
    // Update currency symbol throughout the interface
    if (settings['currency-symbol']) {
        // This would need to be implemented to update all currency displays
        console.log('Currency symbol updated to:', settings['currency-symbol']);
    }
    
    // Apply visual settings
    previewSettings();
}

// Reset settings to default
function resetSettings() {
    if (confirm('Are you sure you want to reset all settings to default?')) {
        loadDefaultSettings();
        previewSettings();
    }
}


// Product edit and delete functions
async function editProduct(productId) {
    try {
        clearProductForm();
        
        // Load categories first
        await loadCategoriesForSelect();
        
        const inventory = await apiCall('/admin/inventory');
        console.log('Inventory data:', inventory);
        console.log('Looking for product ID:', productId, 'Type:', typeof productId);
        
        if (!inventory || !inventory.inventory) {
            console.error('Invalid inventory data structure:', inventory);
            alert('Invalid inventory data structure');
            return;
        }
        
        console.log('Available products:', inventory.inventory.map(p => ({ id: p.id, name: p.name, type: typeof p.id })));
        
        // Try multiple comparison methods
        let product = inventory.inventory.find(p => p.id === parseInt(productId));
        if (!product) {
            product = inventory.inventory.find(p => p.id == productId);
        }
        if (!product) {
            product = inventory.inventory.find(p => String(p.id) === String(productId));
        }
        
        if (!product) {
            console.log('Product not found. Searched for ID:', productId);
            alert('Product not found');
            return;
        }
        
        // Show modal first (don't reset form for editing)
        const modal = new bootstrap.Modal(document.getElementById('addProductModal'));
        modal.show();
        
        // Wait for modal to be shown, then fill the form
        setTimeout(() => {
            const nameEl = document.getElementById('product-name');
            const categoryEl = document.getElementById('product-category');
            const priceEl = document.getElementById('product-price');
            const stockEl = document.getElementById('product-stock');
            const descEl = document.getElementById('product-description');
            const imageEl = document.getElementById('product-image-url');
            const lowStockEl = document.getElementById('product-low-stock');
            
            console.log('Setting form values:', {
                name: product.name,
                category_id: product.category_id,
                price: product.price,
                stock: product.stock,
                description: product.description,
                image_url: product.image_url,
                low_stock_threshold: product.low_stock_threshold
            });
            
            if (nameEl) {
                nameEl.value = product.name;
                console.log('Name set to:', nameEl.value);
            }
            if (priceEl) {
                priceEl.value = product.price;
                console.log('Price set to:', priceEl.value);
            }
            if (stockEl) {
                stockEl.value = product.stock;
                console.log('Stock set to:', stockEl.value);
            }
            if (descEl) {
                descEl.value = product.description || '';
                console.log('Description set to:', descEl.value);
            }
            if (imageEl) {
                imageEl.value = product.image_url || '';
                console.log('Image URL set to:', imageEl.value);
            }
            if (lowStockEl) {
                lowStockEl.value = product.low_stock_threshold;
                console.log('Low stock threshold set to:', lowStockEl.value);
            }
            
            // Set category value after ensuring dropdown is populated
            if (categoryEl) {
                console.log('Available category options:', Array.from(categoryEl.options).map(opt => ({ value: opt.value, text: opt.text })));
                console.log('Trying to set category to:', product.category_id, 'Type:', typeof product.category_id);
                
                // Try different value formats
                let categoryValue = product.category_id;
                if (typeof categoryValue === 'string') {
                    categoryValue = parseInt(categoryValue);
                }
                
                categoryEl.value = categoryValue;
                console.log('Category set to:', categoryEl.value, 'Type:', typeof categoryEl.value);
                
                // If the value didn't set, try with string value
                if (categoryEl.value != categoryValue) {
                    categoryEl.value = String(product.category_id);
                    console.log('Category retry with string:', categoryEl.value);
                }
                
                // Final check and retry
                if (categoryEl.value != product.category_id && categoryEl.value != String(product.category_id)) {
                    setTimeout(() => {
                        categoryEl.value = product.category_id;
                        console.log('Category final retry set to:', categoryEl.value);
                    }, 100);
                }
            }
            
            // Show image preview if there's an image URL
            if (product.image_url) {
                showImagePreview(product.image_url, false);
            }
        }, 200);
        
        // Change modal title and button
        const titleEl = document.querySelector('#addProductModal .modal-title');
        const buttonEl = document.getElementById('product-submit-btn');
        
        if (titleEl) {
            titleEl.textContent = 'Edit Product';
            console.log('Modal title changed to: Edit Product');
        }
        if (buttonEl) {
            buttonEl.textContent = 'Update Product';
            buttonEl.onclick = () => updateProduct(productId);
            console.log('Button text changed to: Update Product, onclick set to updateProduct');
        }
        
    } catch (error) {
        console.error('Error loading product for edit:', error);
        console.error('Error details:', error.message, error.stack);
        alert('Error loading product data: ' + error.message);
    }
}

async function updateProduct(productId) {
    try {
        const productData = {
            name: document.getElementById('product-name').value,
            category_id: parseInt(document.getElementById('product-category').value),
            price: parseInt(document.getElementById('product-price').value),
            stock: parseInt(document.getElementById('product-stock').value),
            description: document.getElementById('product-description').value,
            image_url: document.getElementById('product-image-url').value,
            low_stock_threshold: parseInt(document.getElementById('product-low-stock').value)
        };
        
        await apiCall(`/admin/products/${productId}`, 'PUT', productData);
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('addProductModal'));
        modal.hide();
        
        // Reset modal
        resetProductModal();
        
        loadProducts();
        loadDashboard();
        
        alert('Product updated successfully!');
    } catch (error) {
        console.error('Error updating product:', error);
    }
}

async function deleteProduct(productId) {
    if (confirm('Are you sure you want to delete this product?')) {
        try {
            await apiCall(`/admin/products/${productId}`, 'DELETE');
            loadProducts();
            loadDashboard();
            alert('Product deleted successfully!');
        } catch (error) {
            console.error('Error deleting product:', error);
            alert('Error deleting product: ' + error.message);
        }
    }
}

async function editCategory(categoryId) {
    try {
        const categories = await apiCallDirect('/api/categories');
        console.log('Categories data:', categories);
        console.log('Looking for category ID:', categoryId, 'Type:', typeof categoryId);
        
        if (!Array.isArray(categories)) {
            console.error('Invalid categories data structure:', categories);
            alert('Invalid categories data structure');
            return;
        }
        
        console.log('Available categories:', categories.map(c => ({ id: c.id, name: c.name, type: typeof c.id })));
        
        // Try multiple comparison methods
        let category = categories.find(c => c.id === parseInt(categoryId));
        if (!category) {
            category = categories.find(c => c.id == categoryId);
        }
        if (!category) {
            category = categories.find(c => String(c.id) === String(categoryId));
        }
        
        if (!category) {
            console.log('Category not found. Searched for ID:', categoryId);
            alert('Category not found');
            return;
        }
        
        // Show modal first
        const modal = new bootstrap.Modal(document.getElementById('addCategoryModal'));
        modal.show();
        
        // Wait for modal to be shown, then fill the form
        setTimeout(() => {
            const nameEl = document.getElementById('category-name');
            const descEl = document.getElementById('category-description');
            
            if (nameEl) nameEl.value = category.name;
            if (descEl) descEl.value = category.description || '';
        }, 100);
        
        // Change modal title and button
        const titleEl = document.querySelector('#addCategoryModal .modal-title');
        const buttonEl = document.getElementById('category-submit-btn');
        
        if (titleEl) titleEl.textContent = 'Edit Category';
        if (buttonEl) {
            buttonEl.textContent = 'Update Category';
            buttonEl.onclick = () => updateCategory(categoryId);
        }
        
    } catch (error) {
        console.error('Error loading category for edit:', error);
        console.error('Error details:', error.message, error.stack);
        alert('Error loading category data: ' + error.message);
    }
}

async function updateCategory(categoryId) {
    try {
        const categoryData = {
            name: document.getElementById('category-name').value,
            description: document.getElementById('category-description').value
        };
        
        await apiCallDirect(`/api/categories/${categoryId}`, 'PUT', categoryData);
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('addCategoryModal'));
        modal.hide();
        
        // Reset modal
        resetCategoryModal();
        
        loadCategories();
        
        alert('Category updated successfully!');
    } catch (error) {
        console.error('Error updating category:', error);
    }
}

async function deleteCategory(categoryId) {
    if (confirm('Are you sure you want to delete this category?')) {
        try {
            await apiCall(`/categories/${categoryId}`, 'DELETE');
            loadCategories();
            alert('Category deleted successfully!');
        } catch (error) {
            console.error('Error deleting category:', error);
            alert('Error deleting category: ' + error.message);
        }
    }
}

async function deleteUser(userId) {
    if (confirm('Are you sure you want to delete this user?')) {
        try {
            await apiCall(`/users/${userId}`, 'DELETE');
            loadUsers();
            alert('User deleted successfully!');
        } catch (error) {
            console.error('Error deleting user:', error);
            alert('Error deleting user: ' + error.message);
        }
    }
}

// Image upload functions
async function handleImageUpload() {
    const fileInput = document.getElementById('product-image-file');
    const file = fileInput.files[0];
    
    if (!file) {
        hideImagePreview();
        return;
    }
    
    // Check file size (16MB max)
    if (file.size > 16 * 1024 * 1024) {
        alert('File size too large. Maximum size is 16MB.');
        fileInput.value = '';
        return;
    }
    
    // Check file type
    const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
        alert('Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WEBP.');
        fileInput.value = '';
        return;
    }
    
    try {
        // Show loading state
        showImagePreview('/static/placeholder-coffee.svg', true);
        
        // Upload file
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/pos/upload/image', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Set the image URL in the URL input
            document.getElementById('product-image-url').value = result.image_url;
            showImagePreview(result.image_url, false);
        } else {
            throw new Error(result.error || 'Upload failed');
        }
    } catch (error) {
        console.error('Error uploading image:', error);
        alert('Error uploading image: ' + error.message);
        fileInput.value = '';
        hideImagePreview();
    }
}

function showImagePreview(imageUrl, isLoading = false) {
    const previewDiv = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');
    
    if (isLoading) {
        previewImg.src = imageUrl;
        previewImg.alt = 'Uploading...';
        previewDiv.style.display = 'block';
    } else {
        previewImg.src = imageUrl;
        previewImg.alt = 'Image Preview';
        previewDiv.style.display = 'block';
    }
}

function hideImagePreview() {
    const previewDiv = document.getElementById('image-preview');
    previewDiv.style.display = 'none';
}

// Clear image preview when modal is closed
function clearProductForm() {
    document.getElementById('product-image-file').value = '';
    document.getElementById('product-image-url').value = '';
    hideImagePreview();
}

function resetProductModal() {
    // Reset modal title and button to add mode
    const titleEl = document.querySelector('#addProductModal .modal-title');
    const buttonEl = document.getElementById('product-submit-btn');
    
    if (titleEl) titleEl.textContent = 'Add New Product';
    if (buttonEl) {
        buttonEl.textContent = 'Add Product';
        buttonEl.onclick = addProduct;
    }
    
    // Clear form
    document.getElementById('addProductForm').reset();
    clearProductForm();
}

function resetCategoryModal() {
    // Reset modal title and button to add mode
    const titleEl = document.querySelector('#addCategoryModal .modal-title');
    const buttonEl = document.getElementById('category-submit-btn');
    
    if (titleEl) titleEl.textContent = 'Add New Category';
    if (buttonEl) {
        buttonEl.textContent = 'Add Category';
        buttonEl.onclick = addCategory;
    }
    
    // Clear form
    document.getElementById('addCategoryForm').reset();
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
