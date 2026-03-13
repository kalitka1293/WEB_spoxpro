// spoXpro Admin Panel JavaScript

class AdminPanel {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeComponents();
        this.loadDashboardData();
    }

    setupEventListeners() {
        // Search functionality
        const searchInputs = document.querySelectorAll('.search-input');
        searchInputs.forEach(input => {
            input.addEventListener('input', this.debounce(this.handleSearch.bind(this), 300));
        });

        // Filter functionality
        const filterSelects = document.querySelectorAll('.filter-select');
        filterSelects.forEach(select => {
            select.addEventListener('change', this.handleFilter.bind(this));
        });

        // View mode toggle
        const viewModeButtons = document.querySelectorAll('.view-mode-btn');
        viewModeButtons.forEach(btn => {
            btn.addEventListener('click', this.handleViewModeChange.bind(this));
        });

        // Form validation
        const forms = document.querySelectorAll('.admin-form');
        forms.forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        });

        // Mobile sidebar toggle
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', this.toggleSidebar.bind(this));
        }

        // Confirmation dialogs
        const deleteButtons = document.querySelectorAll('.btn-delete');
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', this.handleDelete.bind(this));
        });
    }

    initializeComponents() {
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // Initialize charts if Chart.js is available
        if (typeof Chart !== 'undefined') {
            this.initializeCharts();
        }

        // Add loading states
        this.addLoadingStates();
    }

    loadDashboardData() {
        // Load real-time dashboard data
        if (window.location.pathname === '/admin/' || window.location.pathname === '/admin') {
            this.updateDashboardStats();
            // Update every 30 seconds
            setInterval(() => {
                this.updateDashboardStats();
            }, 30000);
        }
    }

    async updateDashboardStats() {
        try {
            const response = await fetch('/admin/api/dashboard-stats');
            if (response.ok) {
                const data = await response.json();
                this.updateStatsCards(data);
            }
        } catch (error) {
            console.error('Error updating dashboard stats:', error);
        }
    }

    updateStatsCards(data) {
        // Update stats cards with new data
        const statsCards = {
            'total-products': data.total_products,
            'total-users': data.total_users,
            'total-orders': data.total_orders,
            'total-revenue': this.formatCurrency(data.total_revenue)
        };

        Object.entries(statsCards).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                element.classList.add('updated');
                setTimeout(() => element.classList.remove('updated'), 1000);
            }
        });
    }

    handleSearch(event) {
        const query = event.target.value;
        const searchType = event.target.dataset.searchType || 'products';
        
        if (query.length >= 2) {
            this.performSearch(query, searchType);
        } else if (query.length === 0) {
            this.clearSearch();
        }
    }

    async performSearch(query, type) {
        try {
            this.showLoading();
            const response = await fetch(`/admin/api/${type}/search?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const results = await response.json();
                this.displaySearchResults(results, type);
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Поиск не удался. Пожалуйста, попробуйте еще раз.');
        } finally {
            this.hideLoading();
        }
    }

    displaySearchResults(results, type) {
        const container = document.querySelector('.search-results');
        if (!container) return;

        if (results.length === 0) {
            container.innerHTML = '<div class="alert alert-info">Результаты не найдены.</div>';
            return;
        }

        let html = '';
        results.forEach(item => {
            html += this.createResultItem(item, type);
        });

        container.innerHTML = html;
    }

    createResultItem(item, type) {
        switch (type) {
            case 'products':
                return `
                    <div class="result-item">
                        <h6>${item.name}</h6>
                        <p>Цена: ${this.formatCurrency(item.price)}</p>
                        <span class="badge ${item.is_active ? 'bg-success' : 'bg-secondary'}">
                            ${item.is_active ? 'Активен' : 'Неактивен'}
                        </span>
                    </div>
                `;
            default:
                return `<div class="result-item">${JSON.stringify(item)}</div>`;
        }
    }

    handleFilter(event) {
        const filterValue = event.target.value;
        const filterType = event.target.dataset.filterType;
        
        // Update URL with filter parameters
        const url = new URL(window.location);
        if (filterValue) {
            url.searchParams.set(filterType, filterValue);
        } else {
            url.searchParams.delete(filterType);
        }
        
        window.location.href = url.toString();
    }

    handleViewModeChange(event) {
        const viewMode = event.target.dataset.viewMode;
        const container = document.querySelector('.content-container');
        
        if (container) {
            container.className = container.className.replace(/view-\w+/, `view-${viewMode}`);
        }
        
        // Update active button
        document.querySelectorAll('.view-mode-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        event.target.classList.add('active');
        
        // Save preference
        localStorage.setItem('admin-view-mode', viewMode);
    }

    handleFormSubmit(event) {
        const form = event.target;
        const submitBtn = form.querySelector('button[type="submit"]');
        
        if (!this.validateForm(form)) {
            event.preventDefault();
            return false;
        }
        
        // Show loading state
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="loading-spinner"></span> Сохранение...';
        }
    }

    validateForm(form) {
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, 'Это поле обязательно для заполнения');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });
        
        // Custom validation rules
        const emailFields = form.querySelectorAll('input[type="email"]');
        emailFields.forEach(field => {
            if (field.value && !this.isValidEmail(field.value)) {
                this.showFieldError(field, 'Пожалуйста, введите действительный email адрес');
                isValid = false;
            }
        });
        
        const priceFields = form.querySelectorAll('.price-input');
        priceFields.forEach(field => {
            if (field.value && (isNaN(field.value) || parseFloat(field.value) < 0)) {
                this.showFieldError(field, 'Пожалуйста, введите действительную цену');
                isValid = false;
            }
        });
        
        return isValid;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('is-invalid');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = message;
        field.parentNode.appendChild(errorDiv);
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    handleDelete(event) {
        event.preventDefault();
        
        const itemName = event.target.dataset.itemName || 'this item';
        const deleteUrl = event.target.href;
        
        if (confirm(`Вы уверены, что хотите удалить ${itemName}? Это действие нельзя отменить.`)) {
            this.performDelete(deleteUrl);
        }
    }

    async performDelete(url) {
        try {
            this.showLoading();
            const response = await fetch(url, { method: 'DELETE' });
            
            if (response.ok) {
                this.showSuccess('Элемент успешно удален');
                // Reload page or remove item from DOM
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                throw new Error('Delete failed');
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showError('Не удалось удалить элемент. Пожалуйста, попробуйте еще раз.');
        } finally {
            this.hideLoading();
        }
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('show');
        }
    }

    initializeCharts() {
        // Sales chart
        const salesChartCanvas = document.getElementById('salesChart');
        if (salesChartCanvas) {
            this.createSalesChart(salesChartCanvas);
        }
        
        // Products chart
        const productsChartCanvas = document.getElementById('productsChart');
        if (productsChartCanvas) {
            this.createProductsChart(productsChartCanvas);
        }
    }

    createSalesChart(canvas) {
        new Chart(canvas, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                datasets: [{
                    label: 'Продажи',
                    data: [12, 19, 3, 5, 2, 3],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Ежемесячные продажи'
                    }
                }
            }
        });
    }

    createProductsChart(canvas) {
        new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: ['Активные', 'Неактивные'],
                datasets: [{
                    data: [75, 25],
                    backgroundColor: ['#28a745', '#dc3545']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Статус товаров'
                    }
                }
            }
        });
    }

    addLoadingStates() {
        // Add loading states to buttons and forms
        const buttons = document.querySelectorAll('.btn-loading');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                btn.disabled = true;
                btn.innerHTML = '<span class="loading-spinner"></span> Загрузка...';
            });
        });
    }

    showLoading() {
        const loader = document.querySelector('.page-loader');
        if (loader) {
            loader.style.display = 'block';
        }
    }

    hideLoading() {
        const loader = document.querySelector('.page-loader');
        if (loader) {
            loader.style.display = 'none';
        }
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'danger');
    }

    showAlert(message, type) {
        const alertContainer = document.querySelector('.alert-container') || document.body;
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.insertBefore(alert, alertContainer.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    // Utility functions
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    formatCurrency(amount) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB'
        }).format(amount);
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    clearSearch() {
        const container = document.querySelector('.search-results');
        if (container) {
            container.innerHTML = '';
        }
    }
}

// Initialize admin panel when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AdminPanel();
});

// Export for use in other scripts
window.AdminPanel = AdminPanel;