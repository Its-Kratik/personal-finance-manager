/**
 * Personal Finance Manager Pro - Main Application JavaScript
 * =========================================================
 * 
 * Main application logic handling:
 * - Navigation and page management
 * - Authentication flows
 * - API communication
 * - Modal management
 * - Form handling
 * - Real-time updates
 * 
 * Version: 1.0.0
 */

import { formatCurrency, formatDate, debounce, showToast, validateEmail, validatePassword } from './utils.js';
import { initCharts, updateDashboardCharts, renderChart } from './charts.js';

class FinanceApp {
    constructor() {
        this.currentPage = 'landing';
        this.currentUser = null;
        this.apiBase = '';
        this.charts = {};
        this.modals = {};
        this.searchDebounce = debounce(this.performSearch.bind(this), 300);
        
        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            this.setupEventListeners();
            this.initModals();
            this.checkAuthStatus();
            this.setupServiceWorker();
            this.setupTheme();
            this.initOnboarding();
            
            console.log('Finance Manager Pro initialized successfully');
        } catch (error) {
            console.error('Failed to initialize application:', error);
            this.showError('Failed to initialize application');
        }
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Navigation
        document.addEventListener('click', this.handleNavigation.bind(this));
        
        // Authentication forms
        const loginForm = document.getElementById('login-form');
        const registerForm = document.getElementById('register-form');
        
        if (loginForm) {
            loginForm.addEventListener('submit', this.handleLogin.bind(this));
        }
        
        if (registerForm) {
            registerForm.addEventListener('submit', this.handleRegister.bind(this));
        }

        // Quick actions
        document.addEventListener('click', this.handleQuickActions.bind(this));
        
        // Search functionality
        const globalSearch = document.getElementById('global-search');
        if (globalSearch) {
            globalSearch.addEventListener('input', (e) => {
                this.searchDebounce(e.target.value);
            });
        }

        // Theme toggle
        const themeToggle = document.getElementById('theme-toggle-btn');
        if (themeToggle) {
            themeToggle.addEventListener('click', this.toggleTheme.bind(this));
        }

        // Mobile navigation
        const navToggle = document.getElementById('nav-toggle');
        if (navToggle) {
            navToggle.addEventListener('click', this.toggleMobileNav.bind(this));
        }

        // Form validation
        document.addEventListener('input', this.handleFormValidation.bind(this));
        document.addEventListener('change', this.handleFormValidation.bind(this));

        // Password toggles
        document.addEventListener('click', this.handlePasswordToggle.bind(this));

        // Scroll events
        window.addEventListener('scroll', this.handleScroll.bind(this));

        // FAB menu
        const fab = document.getElementById('fab');
        if (fab) {
            fab.addEventListener('click', this.toggleFAB.bind(this));
        }

        // Window events
        window.addEventListener('resize', this.handleResize.bind(this));
        window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));

        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
    }

    /**
     * Handle navigation clicks
     */
    handleNavigation(event) {
        const target = event.target.closest('[data-page]');
        if (target) {
            event.preventDefault();
            const page = target.dataset.page;
            this.navigateToPage(page);
        }

        // Handle auth links
        if (event.target.matches('#get-started-btn, #register-link')) {
            event.preventDefault();
            this.navigateToPage('register');
        }

        if (event.target.matches('#login-link, #login-link-from-register')) {
            event.preventDefault();
            this.navigateToPage('login');
        }

        if (event.target.matches('#logout-btn')) {
            event.preventDefault();
            this.logout();
        }
    }

    /**
     * Navigate to a specific page
     */
    navigateToPage(page) {
        // Hide all pages
        const pages = document.querySelectorAll('.page');
        pages.forEach(p => {
            p.classList.remove('active');
            p.style.display = 'none';
        });

        // Show target page
        const targetPage = document.getElementById(`${page}-page`);
        if (targetPage) {
            targetPage.style.display = 'block';
            setTimeout(() => {
                targetPage.classList.add('active');
            }, 50);
        }

        // Update navigation
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => link.classList.remove('active'));
        
        const activeNavLink = document.querySelector(`[data-page="${page}"]`);
        if (activeNavLink) {
            activeNavLink.classList.add('active');
        }

        // Show/hide navbar
        const navbar = document.getElementById('navbar');
        if (navbar) {
            if (['dashboard', 'transactions', 'budgets', 'reports', 'settings'].includes(page)) {
                navbar.style.display = 'block';
                document.getElementById('fab')?.style.setProperty('display', 'flex');
            } else {
                navbar.style.display = 'none';
                document.getElementById('fab')?.style.setProperty('display', 'none');
            }
        }

        this.currentPage = page;
        
        // Load page-specific data
        this.loadPageData(page);
        
        // Update URL without reload
        if (history.pushState) {
            history.pushState(null, null, `#${page}`);
        }
    }

    /**
     * Load page-specific data
     */
    async loadPageData(page) {
        try {
            switch (page) {
                case 'dashboard':
                    await this.loadDashboardData();
                    break;
                case 'transactions':
                    await this.loadTransactions();
                    break;
                case 'budgets':
                    await this.loadBudgets();
                    break;
                case 'reports':
                    await this.loadReports();
                    break;
                case 'settings':
                    await this.loadSettings();
                    break;
            }
        } catch (error) {
            console.error(`Failed to load ${page} data:`, error);
            this.showError(`Failed to load ${page} data`);
        }
    }

    /**
     * Handle login form submission
     */
    async handleLogin(event) {
        event.preventDefault();
        
        const form = event.target;
        const submitBtn = form.querySelector('[type="submit"]');
        const spinner = submitBtn.querySelector('.btn-spinner');
        const btnText = submitBtn.querySelector('.btn-text');
        
        // Show loading state
        submitBtn.disabled = true;
        spinner.style.display = 'inline-block';
        btnText.textContent = 'Signing In...';
        
        try {
            const formData = new FormData(form);
            const data = {
                username: formData.get('username'),
                password: formData.get('password')
            };
            
            const response = await this.apiRequest('/login', {
                method: 'POST',
                body: JSON.stringify(data),
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.success) {
                this.currentUser = response.user;
                showToast('Login successful!', 'success');
                this.navigateToPage('dashboard');
                this.startTour();
            } else {
                throw new Error(response.error || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showError(error.message || 'Login failed');
        } finally {
            // Reset loading state
            submitBtn.disabled = false;
            spinner.style.display = 'none';
            btnText.textContent = 'Sign In';
        }
    }

    /**
     * Handle register form submission
     */
    async handleRegister(event) {
        event.preventDefault();
        
        const form = event.target;
        const submitBtn = form.querySelector('[type="submit"]');
        const spinner = submitBtn.querySelector('.btn-spinner');
        const btnText = submitBtn.querySelector('.btn-text');
        
        // Show loading state
        submitBtn.disabled = true;
        spinner.style.display = 'inline-block';
        btnText.textContent = 'Creating Account...';
        
        try {
            const formData = new FormData(form);
            const data = {
                username: formData.get('username'),
                email: formData.get('email'),
                password: formData.get('password')
            };
            
            // Validation
            if (!validateEmail(data.email)) {
                throw new Error('Please enter a valid email address');
            }
            
            if (!validatePassword(data.password)) {
                throw new Error('Password must be at least 8 characters with letters and numbers');
            }
            
            const response = await this.apiRequest('/register', {
                method: 'POST',
                body: JSON.stringify(data),
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.success) {
                this.currentUser = response.user;
                showToast('Account created successfully!', 'success');
                this.navigateToPage('dashboard');
                this.startTour();
            } else {
                throw new Error(response.error || 'Registration failed');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showError(error.message || 'Registration failed');
        } finally {
            // Reset loading state
            submitBtn.disabled = false;
            spinner.style.display = 'none';
            btnText.textContent = 'Create Account';
        }
    }

    /**
     * Handle logout
     */
    async logout() {
        try {
            await this.apiRequest('/logout');
            this.currentUser = null;
            showToast('Logged out successfully', 'info');
            this.navigateToPage('landing');
        } catch (error) {
            console.error('Logout error:', error);
        }
    }

    /**
     * Check authentication status
     */
    async checkAuthStatus() {
        try {
            const response = await this.apiRequest('/api/user');
            if (response.user) {
                this.currentUser = response.user;
                // If we're on landing page and user is authenticated, go to dashboard
                if (this.currentPage === 'landing') {
                    this.navigateToPage('dashboard');
                }
            }
        } catch (error) {
            console.log('User not authenticated');
        }
    }

    /**
     * Load dashboard data
     */
    async loadDashboardData() {
        try {
            this.showLoading('loading-dashboard');
            
            // Load financial summary
            const summaryResponse = await this.apiRequest('/api/dashboard/summary');
            this.updateDashboardSummary(summaryResponse);
            
            // Load chart data
            const chartResponse = await this.apiRequest('/api/chart-data');
            await updateDashboardCharts(chartResponse);
            
            // Load recent transactions
            const transactionsResponse = await this.apiRequest('/transactions?limit=5');
            this.updateRecentTransactions(transactionsResponse.transactions);
            
            // Load top categories
            const categoriesResponse = await this.apiRequest('/api/insights');
            this.updateTopCategories(categoriesResponse.insights.top_categories);
            
            // Check onboarding status
            await this.checkOnboardingStatus();
            
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
            this.showError('Failed to load dashboard data');
        } finally {
            this.hideLoading('loading-dashboard');
        }
    }

    /**
     * Update dashboard summary cards
     */
    updateDashboardSummary(data) {
        const elements = {
            totalIncome: document.getElementById('total-income'),
            totalExpense: document.getElementById('total-expense'),
            netBalance: document.getElementById('net-balance'),
            savingsRate: document.getElementById('savings-rate'),
            avgDailySpending: document.getElementById('avg-daily-spending'),
            largestTransaction: document.getElementById('largest-transaction')
        };

        if (elements.totalIncome) {
            this.animateCounter(elements.totalIncome, data.total_income || 0);
        }
        if (elements.totalExpense) {
            this.animateCounter(elements.totalExpense, data.total_expense || 0);
        }
        if (elements.netBalance) {
            this.animateCounter(elements.netBalance, data.net_balance || 0);
        }
        if (elements.savingsRate) {
            elements.savingsRate.textContent = `${data.savings_rate || 0}%`;
        }
        if (elements.avgDailySpending) {
            this.animateCounter(elements.avgDailySpending, data.avg_daily_spending || 0);
        }
        if (elements.largestTransaction) {
            elements.largestTransaction.textContent = formatCurrency(data.largest_transaction || 0);
        }

        // Update change indicators
        this.updateChangeIndicators(data);
    }

    /**
     * Update change indicators with comparison to previous period
     */
    updateChangeIndicators(data) {
        const indicators = [
            { element: 'income-change', value: data.income_change || 0, type: 'income' },
            { element: 'expense-change', value: data.expense_change || 0, type: 'expense' },
            { element: 'balance-change', value: data.balance_change || 0, type: 'balance' }
        ];

        indicators.forEach(({ element, value, type }) => {
            const el = document.getElementById(element);
            if (el) {
                const isPositive = value > 0;
                const changeIcon = el.querySelector('.change-icon');
                const changeText = el.querySelector('.change-text');
                
                if (changeIcon) {
                    changeIcon.textContent = isPositive ? '↗' : '↘';
                }
                
                if (changeText) {
                    const sign = isPositive ? '+' : '';
                    changeText.textContent = `${sign}${value.toFixed(1)}% from last period`;
                }
                
                // Add appropriate classes for styling
                el.className = `stat-change ${isPositive ? 'positive' : 'negative'}`;
            }
        });
    }

    /**
     * Update recent transactions list
     */
    updateRecentTransactions(transactions) {
        const container = document.getElementById('recent-transactions-list');
        if (!container) return;

        if (!transactions || transactions.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No recent transactions</p>
                    <button class="btn btn-primary btn-sm" onclick="app.openAddTransactionModal()">
                        Add Transaction
                    </button>
                </div>
            `;
            return;
        }

        const transactionHTML = transactions.map(transaction => `
            <div class="transaction-item" data-id="${transaction.id}">
                <div class="transaction-icon" style="background: ${transaction.category_color || '#4F8A8B'}">
                    ${transaction.category_icon || '💳'}
                </div>
                <div class="transaction-details">
                    <div class="transaction-description">${transaction.description || 'No description'}</div>
                    <div class="transaction-category">${transaction.category_name}</div>
                </div>
                <div class="transaction-amount ${transaction.type}">
                    ${transaction.type === 'income' ? '+' : '-'}${formatCurrency(transaction.amount)}
                </div>
                <div class="transaction-date">
                    ${formatDate(transaction.date)}
                </div>
            </div>
        `).join('');

        container.innerHTML = transactionHTML;
    }

    /**
     * Update top categories list
     */
    updateTopCategories(categories) {
        const container = document.getElementById('top-categories-list');
        if (!container || !categories) return;

        if (categories.length === 0) {
            container.innerHTML = '<p class="text-center">No spending data available</p>';
            return;
        }

        const categoriesHTML = categories.map(category => `
            <div class="category-item">
                <div class="category-icon" style="background: ${category.color || '#4F8A8B'}">
                    ${category.icon || '📊'}
                </div>
                <div class="category-info">
                    <div class="category-name">${category.name}</div>
                    <div class="category-count">${category.transaction_count || 0} transactions</div>
                </div>
                <div class="category-amount">
                    ${formatCurrency(category.total_amount || 0)}
                </div>
            </div>
        `).join('');

        container.innerHTML = categoriesHTML;
    }

    /**
     * Handle quick actions
     */
    handleQuickActions(event) {
        const action = event.target.closest('[data-action]')?.dataset.action;
        
        switch (action) {
            case 'income':
            case 'expense':
                this.openAddTransactionModal(action);
                break;
            case 'budget':
                this.openCreateBudgetModal();
                break;
            case 'export':
                this.exportData();
                break;
        }
    }

    /**
     * Open add transaction modal
     */
    openAddTransactionModal(type = null) {
        const modal = this.modals.addTransaction;
        if (!modal) return;

        // Reset form
        const form = document.getElementById('add-transaction-form');
        if (form) {
            form.reset();
            
            // Set transaction type if provided
            if (type) {
                const typeRadio = form.querySelector(`input[value="${type}"]`);
                if (typeRadio) {
                    typeRadio.checked = true;
                    this.updateTransactionCategories(type);
                }
            }
            
            // Set today's date as default
            const dateInput = form.querySelector('input[name="date"]');
            if (dateInput) {
                dateInput.value = new Date().toISOString().split('T')[0];
            }
        }

        this.showModal('addTransaction');
        this.initTransactionForm();
    }

    /**
     * Initialize transaction form
     */
    initTransactionForm() {
        const form = document.getElementById('add-transaction-form');
        if (!form) return;

        // Handle step navigation
        this.setupFormSteps();
        
        // Handle type selection
        const typeRadios = form.querySelectorAll('input[name="transaction_type"]');
        typeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.updateTransactionCategories(e.target.value);
            });
        });

        // Handle amount formatting
        const amountInput = form.querySelector('input[name="amount"]');
        if (amountInput) {
            amountInput.addEventListener('input', this.formatAmountInput.bind(this));
        }

        // Handle description character count
        const descInput = form.querySelector('input[name="description"]');
        const countElement = document.getElementById('description-count');
        if (descInput && countElement) {
            descInput.addEventListener('input', (e) => {
                countElement.textContent = e.target.value.length;
            });
        }

        // Load categories
        this.loadCategories();
    }

    /**
     * Setup form steps navigation
     */
    setupFormSteps() {
        const steps = document.querySelectorAll('.form-step');
        const nextBtn = document.getElementById('modal-next');
        const prevBtn = document.getElementById('modal-prev');
        const saveBtn = document.getElementById('modal-save');
        const dots = document.querySelectorAll('.step-dot');
        
        let currentStep = 1;
        const totalSteps = steps.length;

        const updateStep = () => {
            // Update steps visibility
            steps.forEach((step, index) => {
                step.classList.toggle('active', index === currentStep - 1);
            });

            // Update dots
            dots.forEach((dot, index) => {
                dot.classList.toggle('active', index < currentStep);
            });

            // Update buttons
            prevBtn.style.display = currentStep > 1 ? 'inline-flex' : 'none';
            nextBtn.style.display = currentStep < totalSteps ? 'inline-flex' : 'none';
            saveBtn.style.display = currentStep === totalSteps ? 'inline-flex' : 'none';

            // Update review if on last step
            if (currentStep === totalSteps) {
                this.updateTransactionReview();
            }
        };

        nextBtn.addEventListener('click', () => {
            if (this.validateCurrentStep(currentStep)) {
                currentStep = Math.min(currentStep + 1, totalSteps);
                updateStep();
            }
        });

        prevBtn.addEventListener('click', () => {
            currentStep = Math.max(currentStep - 1, 1);
            updateStep();
        });

        updateStep();
    }

    /**
     * Validate current form step
     */
    validateCurrentStep(step) {
        const form = document.getElementById('add-transaction-form');
        let isValid = true;

        if (step === 1) {
            // Validate transaction type
            const typeChecked = form.querySelector('input[name="transaction_type"]:checked');
            if (!typeChecked) {
                this.showError('Please select a transaction type');
                isValid = false;
            }
        } else if (step === 2) {
            // Validate amount and category
            const amount = form.querySelector('input[name="amount"]').value;
            const category = form.querySelector('select[name="category_id"]').value;

            if (!amount || parseFloat(amount) <= 0) {
                this.showError('Please enter a valid amount');
                isValid = false;
            }

            if (!category) {
                this.showError('Please select a category');
                isValid = false;
            }
        }

        return isValid;
    }

    /**
     * Update transaction review
     */
    updateTransactionReview() {
        const form = document.getElementById('add-transaction-form');
        const formData = new FormData(form);
        
        const type = formData.get('transaction_type');
        const amount = formData.get('amount');
        const categoryId = formData.get('category_id');
        const date = formData.get('date');
        const description = formData.get('description');

        // Get category name
        const categorySelect = form.querySelector('select[name="category_id"]');
        const categoryName = categorySelect.options[categorySelect.selectedIndex]?.text || '';

        // Update review elements
        document.getElementById('review-type').textContent = type ? type.charAt(0).toUpperCase() + type.slice(1) : '';
        document.getElementById('review-amount').textContent = formatCurrency(parseFloat(amount) || 0);
        document.getElementById('review-category').textContent = categoryName;
        document.getElementById('review-date').textContent = formatDate(date);
        document.getElementById('review-description').textContent = description || 'No description';
        
        // Update icon
        const iconElement = document.getElementById('review-icon');
        if (iconElement) {
            iconElement.textContent = type === 'income' ? '💰' : '💸';
        }
    }

    /**
     * Update categories based on transaction type
     */
    async updateTransactionCategories(type) {
        try {
            const response = await this.apiRequest(`/api/categories?type=${type}`);
            const categorySelect = document.querySelector('select[name="category_id"]');
            
            if (categorySelect && response.categories) {
                categorySelect.innerHTML = '<option value="">Select a category</option>' +
                    response.categories.map(cat => 
                        `<option value="${cat.id}">${cat.icon} ${cat.name}</option>`
                    ).join('');
            }
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }

    /**
     * Load all categories
     */
    async loadCategories() {
        try {
            const response = await this.apiRequest('/api/categories');
            this.categories = response.categories || [];
        } catch (error) {
            console.error('Failed to load categories:', error);
        }
    }

    /**
     * Handle transaction form submission
     */
    async handleTransactionSubmit(event) {
        event.preventDefault();
        
        const form = event.target;
        const submitBtn = form.querySelector('[type="submit"]');
        const spinner = submitBtn.querySelector('.btn-spinner');
        
        submitBtn.disabled = true;
        spinner.style.display = 'inline-block';
        
        try {
            const formData = new FormData(form);
            const data = {
                type: formData.get('transaction_type'),
                amount: parseFloat(formData.get('amount')),
                category_id: parseInt(formData.get('category_id')),
                date: formData.get('date'),
                description: formData.get('description')
            };
            
            const response = await this.apiRequest('/transactions', {
                method: 'POST',
                body: JSON.stringify(data),
                headers: { 'Content-Type': 'application/json' }
            });
            
            if (response.success) {
                showToast('Transaction added successfully!', 'success');
                this.hideModal('addTransaction');
                
                // Refresh data if we're on relevant pages
                if (this.currentPage === 'dashboard') {
                    await this.loadDashboardData();
                } else if (this.currentPage === 'transactions') {
                    await this.loadTransactions();
                }
                
                // Update onboarding
                this.updateOnboardingProgress({ first_transaction_added: true });
            }
        } catch (error) {
            console.error('Transaction submission error:', error);
            this.showError(error.message || 'Failed to add transaction');
        } finally {
            submitBtn.disabled = false;
            spinner.style.display = 'none';
        }
    }

    /**
     * Initialize modals
     */
    initModals() {
        const modalElements = {
            addTransaction: document.getElementById('add-transaction-modal'),
            createBudget: document.getElementById('create-budget-modal'),
            confirmation: document.getElementById('confirmation-modal')
        };

        Object.keys(modalElements).forEach(key => {
            const modal = modalElements[key];
            if (modal) {
                this.modals[key] = modal;
                this.setupModalEvents(modal, key);
            }
        });
    }

    /**
     * Setup modal events
     */
    setupModalEvents(modal, modalKey) {
        // Close button
        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hideModal(modalKey));
        }

        // Overlay click
        const overlay = document.getElementById('modal-overlay');
        if (overlay) {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    this.hideModal(modalKey);
                }
            });
        }

        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideModal(modalKey);
            }
        });

        // Form submission
        const form = modal.querySelector('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                if (modalKey === 'addTransaction') {
                    this.handleTransactionSubmit(e);
                } else if (modalKey === 'createBudget') {
                    this.handleBudgetSubmit(e);
                }
            });
        }
    }

    /**
     * Show modal
     */
    showModal(modalKey) {
        const modal = this.modals[modalKey];
        const overlay = document.getElementById('modal-overlay');
        
        if (modal && overlay) {
            overlay.classList.add('active');
            modal.classList.add('active');
            overlay.style.display = 'flex';
            modal.style.display = 'block';
            
            // Focus first input
            const firstInput = modal.querySelector('input, select, textarea');
            if (firstInput) {
                setTimeout(() => firstInput.focus(), 100);
            }
        }
    }

    /**
     * Hide modal
     */
    hideModal(modalKey) {
        const modal = this.modals[modalKey];
        const overlay = document.getElementById('modal-overlay');
        
        if (modal && overlay) {
            overlay.classList.remove('active');
            modal.classList.remove('active');
            
            setTimeout(() => {
                overlay.style.display = 'none';
                modal.style.display = 'none';
            }, 300);
        }
    }

    /**
     * Perform search
     */
    async performSearch(query) {
        if (!query || query.length < 2) {
            this.hideSearchResults();
            return;
        }

        try {
            const response = await this.apiRequest(`/api/search/transactions?q=${encodeURIComponent(query)}`);
            this.showSearchResults(response.transactions || []);
        } catch (error) {
            console.error('Search error:', error);
        }
    }

    /**
     * Show search results
     */
    showSearchResults(transactions) {
        const resultsContainer = document.getElementById('global-search-results');
        if (!resultsContainer) return;

        if (transactions.length === 0) {
            resultsContainer.innerHTML = '<div class="search-no-results">No transactions found</div>';
        } else {
            const resultsHTML = transactions.slice(0, 5).map(transaction => `
                <div class="search-result-item" data-id="${transaction.id}">
                    <div class="search-result-icon">${transaction.category_icon || '💳'}</div>
                    <div class="search-result-content">
                        <div class="search-result-description">${transaction.description || 'No description'}</div>
                        <div class="search-result-meta">
                            ${transaction.category_name} • ${formatDate(transaction.date)}
                        </div>
                    </div>
                    <div class="search-result-amount ${transaction.type}">
                        ${formatCurrency(transaction.amount)}
                    </div>
                </div>
            `).join('');
            
            resultsContainer.innerHTML = resultsHTML;
        }

        resultsContainer.style.display = 'block';
    }

    /**
     * Hide search results
     */
    hideSearchResults() {
        const resultsContainer = document.getElementById('global-search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }
    }

    /**
     * Animate counter
     */
    animateCounter(element, targetValue) {
        const duration = 1000;
        const startValue = 0;
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            const currentValue = startValue + (targetValue - startValue) * easeOutQuart;
            
            element.textContent = formatCurrency(currentValue);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    /**
     * Setup theme management
     */
    setupTheme() {
        // Get saved theme or default to auto
        const savedTheme = localStorage.getItem('theme') || 'auto';
        this.applyTheme(savedTheme);
        
        // Update theme icon
        this.updateThemeIcon(savedTheme);
    }

    /**
     * Toggle theme
     */
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'auto';
        const themes = ['auto', 'light', 'dark'];
        const currentIndex = themes.indexOf(currentTheme);
        const nextTheme = themes[(currentIndex + 1) % themes.length];
        
        this.applyTheme(nextTheme);
        localStorage.setItem('theme', nextTheme);
    }

    /**
     * Apply theme
     */
    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.updateThemeIcon(theme);
    }

    /**
     * Update theme icon
     */
    updateThemeIcon(theme) {
        const themeIcon = document.getElementById('theme-icon');
        if (themeIcon) {
            const icons = {
                auto: '🌓',
                light: '☀️',
                dark: '🌙'
            };
            themeIcon.textContent = icons[theme] || icons.auto;
        }
    }

    /**
     * Handle form validation
     */
    handleFormValidation(event) {
        const input = event.target;
        
        if (input.type === 'email') {
            this.validateEmailInput(input);
        } else if (input.type === 'password') {
            this.validatePasswordInput(input);
        } else if (input.name === 'username') {
            this.validateUsernameInput(input);
        }
    }

    /**
     * Validate email input
     */
    validateEmailInput(input) {
        const isValid = validateEmail(input.value);
        const errorElement = document.getElementById(input.id + '-error');
        
        if (input.value && !isValid) {
            input.classList.add('invalid');
            if (errorElement) {
                errorElement.textContent = 'Please enter a valid email address';
            }
        } else {
            input.classList.remove('invalid');
            if (errorElement) {
                errorElement.textContent = '';
            }
        }
    }

    /**
     * Validate password input
     */
    validatePasswordInput(input) {
        const password = input.value;
        const isValid = validatePassword(password);
        const errorElement = document.getElementById(input.id + '-error');
        
        // Show strength indicator for register password
        if (input.id === 'register-password') {
            this.updatePasswordStrength(password);
        }
        
        if (password && !isValid) {
            input.classList.add('invalid');
            if (errorElement) {
                errorElement.textContent = 'Password must be at least 8 characters with letters and numbers';
            }
        } else {
            input.classList.remove('invalid');
            if (errorElement) {
                errorElement.textContent = '';
            }
        }
    }

    /**
     * Update password strength indicator
     */
    updatePasswordStrength(password) {
        const strengthElement = document.getElementById('password-strength');
        const fillElement = document.getElementById('strength-fill');
        const textElement = document.getElementById('strength-text');
        
        if (!strengthElement || !password) {
            strengthElement?.style.setProperty('display', 'none');
            return;
        }
        
        strengthElement.style.display = 'block';
        
        let strength = 0;
        let text = 'Weak';
        let color = '#FA7373';
        
        // Length check
        if (password.length >= 8) strength += 25;
        
        // Character variety checks
        if (/[a-z]/.test(password)) strength += 25;
        if (/[A-Z]/.test(password)) strength += 25;
        if (/[0-9]/.test(password)) strength += 25;
        
        // Determine text and color
        if (strength >= 75) {
            text = 'Strong';
            color = '#38B27B';
        } else if (strength >= 50) {
            text = 'Good';
            color = '#FFB600';
        } else if (strength >= 25) {
            text = 'Fair';
            color = '#ff9800';
        }
        
        if (fillElement) {
            fillElement.style.width = `${strength}%`;
            fillElement.style.background = color;
        }
        
        if (textElement) {
            textElement.textContent = text;
            textElement.style.color = color;
        }
    }

    /**
     * Handle password toggle
     */
    handlePasswordToggle(event) {
        const toggle = event.target.closest('.password-toggle');
        if (!toggle) return;
        
        const targetId = toggle.getAttribute('data-target') || 
                        toggle.parentElement.querySelector('input[type="password"], input[type="text"]')?.id;
        
        if (!targetId) return;
        
        const input = document.getElementById(targetId);
        if (!input) return;
        
        const isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        
        const icon = toggle.querySelector('.toggle-icon');
        if (icon) {
            icon.textContent = isPassword ? '🙈' : '👁️';
        }
    }

    /**
     * Handle scroll events
     */
    handleScroll() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollToTopBtn = document.getElementById('scroll-to-top');
        
        // Show/hide scroll to top button
        if (scrollToTopBtn) {
            if (scrollTop > 500) {
                scrollToTopBtn.classList.add('show');
            } else {
                scrollToTopBtn.classList.remove('show');
            }
            
            scrollToTopBtn.addEventListener('click', () => {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }
        
        // Add shadow to navbar on scroll
        const navbar = document.getElementById('navbar');
        if (navbar) {
            if (scrollTop > 0) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
    }

    /**
     * Initialize onboarding
     */
    async initOnboarding() {
        if (!this.currentUser) return;
        
        try {
            const response = await this.apiRequest('/api/onboarding');
            this.onboardingData = response.onboarding || {};
            
            // Show checklist if user hasn't completed onboarding
            if (!this.onboardingData.checklist_completed) {
                this.showOnboardingChecklist();
            }
        } catch (error) {
            console.error('Failed to load onboarding data:', error);
        }
    }

    /**
     * Show onboarding checklist
     */
    showOnboardingChecklist() {
        const checklist = document.getElementById('onboarding-checklist');
        if (checklist) {
            checklist.style.display = 'block';
            this.updateChecklistProgress();
        }
    }

    /**
     * Update checklist progress
     */
    updateChecklistProgress() {
        const items = [
            'tour_completed',
            'first_transaction_added',
            'first_budget_set',
            'export_used',
            'sample_data_added'
        ];
        
        let completedCount = 0;
        
        items.forEach(item => {
            const checkbox = document.getElementById(`check-${item.split('_')[1]}`);
            if (checkbox && this.onboardingData[item]) {
                checkbox.checked = true;
                completedCount++;
            }
        });
        
        const progressFill = document.getElementById('checklist-progress');
        const progressText = document.getElementById('checklist-text');
        const completionReward = document.getElementById('completion-reward');
        
        const percentage = (completedCount / items.length) * 100;
        
        if (progressFill) {
            progressFill.style.width = `${percentage}%`;
        }
        
        if (progressText) {
            progressText.textContent = `${completedCount} of ${items.length} completed`;
        }
        
        // Show completion reward
        if (completedCount === items.length && completionReward) {
            completionReward.style.display = 'flex';
            setTimeout(() => {
                this.hideOnboardingChecklist();
                this.updateOnboardingProgress({ checklist_completed: true });
            }, 3000);
        }
    }

    /**
     * Update onboarding progress
     */
    async updateOnboardingProgress(updates) {
        try {
            await this.apiRequest('/api/onboarding', {
                method: 'PUT',
                body: JSON.stringify(updates),
                headers: { 'Content-Type': 'application/json' }
            });
            
            // Update local data
            Object.assign(this.onboardingData, updates);
            this.updateChecklistProgress();
        } catch (error) {
            console.error('Failed to update onboarding progress:', error);
        }
    }

    /**
     * Start welcome tour
     */
    startTour() {
        if (this.onboardingData?.tour_completed) return;
        
        const tourOverlay = document.getElementById('tour-overlay');
        if (!tourOverlay) return;
        
        tourOverlay.style.display = 'flex';
        this.currentTourStep = 1;
        this.totalTourSteps = 5;
        
        this.setupTourEvents();
        this.showTourStep(1);
    }

    /**
     * Setup tour events
     */
    setupTourEvents() {
        const nextBtn = document.getElementById('tour-next');
        const prevBtn = document.getElementById('tour-prev');
        const skipBtn = document.getElementById('tour-skip');
        const finishBtn = document.getElementById('tour-finish');
        
        nextBtn?.addEventListener('click', () => this.nextTourStep());
        prevBtn?.addEventListener('click', () => this.prevTourStep());
        skipBtn?.addEventListener('click', () => this.endTour());
        finishBtn?.addEventListener('click', () => this.endTour());
    }

    /**
     * Show tour step
     */
    showTourStep(step) {
        const tourTitle = document.getElementById('tour-title');
        const tourDescription = document.getElementById('tour-description');
        const tourProgressBar = document.getElementById('tour-progress-bar');
        const tourStepCounter = document.getElementById('tour-step-counter');
        
        const steps = {
            1: {
                title: 'Welcome to your Dashboard!',
                description: 'Here you can see your financial overview, including income, expenses, and savings.'
            },
            2: {
                title: 'Financial Summary Cards',
                description: 'These cards show your key financial metrics with comparisons to previous periods.'
            },
            3: {
                title: 'Quick Actions',
                description: 'Use these buttons to quickly add transactions, set budgets, and export data.'
            },
            4: {
                title: 'Interactive Charts',
                description: 'Visualize your spending patterns and trends with these interactive charts.'
            },
            5: {
                title: 'Recent Activity',
                description: 'Keep track of your latest transactions and top spending categories.'
            }
        };
        
        const stepData = steps[step];
        if (stepData) {
            tourTitle.textContent = stepData.title;
            tourDescription.textContent = stepData.description;
        }
        
        // Update progress
        const progress = (step / this.totalTourSteps) * 100;
        tourProgressBar.style.width = `${progress}%`;
        tourStepCounter.textContent = `${step} of ${this.totalTourSteps}`;
        
        // Update buttons
        const prevBtn = document.getElementById('tour-prev');
        const nextBtn = document.getElementById('tour-next');
        const finishBtn = document.getElementById('tour-finish');
        
        prevBtn.style.display = step > 1 ? 'inline-flex' : 'none';
        nextBtn.style.display = step < this.totalTourSteps ? 'inline-flex' : 'none';
        finishBtn.style.display = step === this.totalTourSteps ? 'inline-flex' : 'none';
        
        // Highlight tour target
        this.highlightTourTarget(step);
    }

    /**
     * Highlight tour target element
     */
    highlightTourTarget(step) {
        // Remove previous highlights
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });
        
        // Add highlight to current target
        const targets = {
            1: '[data-tour-step="1"]',
            2: '[data-tour-step="2"]',
            3: '[data-tour-step="3"]',
            4: '[data-tour-step="4"]',
            5: '[data-tour-step="5"]'
        };
        
        const target = document.querySelector(targets[step]);
        if (target) {
            target.classList.add('tour-highlight');
            
            // Scroll target into view
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    }

    /**
     * Next tour step
     */
    nextTourStep() {
        if (this.currentTourStep < this.totalTourSteps) {
            this.currentTourStep++;
            this.showTourStep(this.currentTourStep);
        }
    }

    /**
     * Previous tour step
     */
    prevTourStep() {
        if (this.currentTourStep > 1) {
            this.currentTourStep--;
            this.showTourStep(this.currentTourStep);
        }
    }

    /**
     * End tour
     */
    endTour() {
        const tourOverlay = document.getElementById('tour-overlay');
        if (tourOverlay) {
            tourOverlay.style.display = 'none';
        }
        
        // Remove highlights
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });
        
        // Update onboarding progress
        this.updateOnboardingProgress({ tour_completed: true });
        
        showToast('Welcome tour completed!', 'success');
    }

    /**
     * Toggle FAB menu
     */
    toggleFAB() {
        const fab = document.getElementById('fab');
        if (fab) {
            fab.classList.toggle('active');
        }
    }

    /**
     * Format amount input
     */
    formatAmountInput(event) {
        let value = event.target.value;
        
        // Remove non-numeric characters except decimal point
        value = value.replace(/[^0-9.]/g, '');
        
        // Ensure only one decimal point
        const parts = value.split('.');
        if (parts.length > 2) {
            value = parts[0] + '.' + parts.slice(1).join('');
        }
        
        // Limit decimal places to 2
        if (parts[1] && parts[1].length > 2) {
            value = parts[0] + '.' + parts[1].substring(0, 2);
        }
        
        event.target.value = value;
    }

    /**
     * Show loading state
     */
    showLoading(elementId) {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }
    }

    /**
     * Hide loading state
     */
    hideLoading(elementId) {
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        showToast(message, 'error');
    }

    /**
     * API request helper
     */
    async apiRequest(endpoint, options = {}) {
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * Setup service worker for PWA
     */
    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('ServiceWorker registration successful');
                })
                .catch(err => {
                    console.log('ServiceWorker registration failed: ', err);
                });
        }
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(event) {
        if (event.ctrlKey || event.metaKey) {
            switch (event.key) {
                case 'k':
                    event.preventDefault();
                    document.getElementById('global-search')?.focus();
                    break;
                case 'n':
                    event.preventDefault();
                    this.openAddTransactionModal();
                    break;
                case 'd':
                    event.preventDefault();
                    this.navigateToPage('dashboard');
                    break;
                case 't':
                    event.preventDefault();
                    this.navigateToPage('transactions');
                    break;
            }
        }
    }

    /**
     * Handle mobile navigation toggle
     */
    toggleMobileNav() {
        const navToggle = document.getElementById('nav-toggle');
        const navMenu = document.getElementById('nav-menu');
        
        if (navToggle && navMenu) {
            navToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
        }
    }

    /**
     * Handle window resize
     */
    handleResize() {
        // Close mobile nav on resize
        if (window.innerWidth > 768) {
            const navToggle = document.getElementById('nav-toggle');
            const navMenu = document.getElementById('nav-menu');
            
            navToggle?.classList.remove('active');
            navMenu?.classList.remove('active');
        }
        
        // Resize charts if they exist
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }

    /**
     * Handle before unload
     */
    handleBeforeUnload(event) {
        // Check if there are unsaved changes
        const forms = document.querySelectorAll('form');
        let hasUnsavedChanges = false;
        
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                if (input.value && input.defaultValue !== input.value) {
                    hasUnsavedChanges = true;
                }
            });
        });
        
        if (hasUnsavedChanges) {
            event.preventDefault();
            event.returnValue = '';
        }
    }

    /**
     * Load transactions page data
     */
    async loadTransactions(filters = {}) {
        try {
            this.showLoading('transactions-loading');
            
            // Load transactions with filters
            const params = new URLSearchParams();
            Object.keys(filters).forEach(key => {
                if (filters[key] && filters[key] !== 'all') {
                    params.append(key, filters[key]);
                }
            });
            
            const transactionsResponse = await this.apiRequest(`/transactions?${params.toString()}`);
            this.updateTransactionsTable(transactionsResponse.transactions || []);
            this.updateTransactionsSummary(transactionsResponse.summary || {});
            
            // Load categories for filter dropdown
            const categoriesResponse = await this.apiRequest('/api/categories');
            this.populateCategoryFilter(categoriesResponse.categories || []);
            
            // Update pagination if needed
            this.updateTransactionsPagination(transactionsResponse.pagination || {});
            
        } catch (error) {
            console.error('Failed to load transactions:', error);
            this.showError('Failed to load transactions');
            this.showTransactionsEmpty();
        } finally {
            this.hideLoading('transactions-loading');
        }
    }

    /**
     * Update transactions table
     */
    updateTransactionsTable(transactions) {
        const tbody = document.getElementById('transactions-tbody');
        const emptyState = document.getElementById('transactions-empty');
        
        if (!tbody) return;

        if (!transactions || transactions.length === 0) {
            tbody.innerHTML = '';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';

        const transactionRows = transactions.map(transaction => `
            <tr data-id="${transaction.id}">
                <td>${formatDate(transaction.date)}</td>
                <td>
                    <div class="category-cell">
                        <span class="category-icon" style="background: ${transaction.category_color || '#4F8A8B'}">
                            ${transaction.category_icon || '💳'}
                        </span>
                        ${transaction.category_name}
                    </div>
                </td>
                <td>${transaction.description || 'No description'}</td>
                <td>
                    <span class="transaction-type ${transaction.type}">
                        ${transaction.type.charAt(0).toUpperCase() + transaction.type.slice(1)}
                    </span>
                </td>
                <td class="amount ${transaction.type}">
                    ${transaction.type === 'income' ? '+' : '-'}${formatCurrency(transaction.amount)}
                </td>
                <td class="actions-col">
                    <div class="table-actions">
                        <button class="table-action-btn" onclick="app.editTransaction(${transaction.id})" 
                                aria-label="Edit transaction">
                            ✏️
                        </button>
                        <button class="table-action-btn" onclick="app.deleteTransaction(${transaction.id})" 
                                aria-label="Delete transaction">
                            🗑️
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        tbody.innerHTML = transactionRows;
    }

    /**
     * Update transactions summary
     */
    updateTransactionsSummary(summary) {
        const elements = {
            total: document.getElementById('transactions-total'),
            income: document.getElementById('transactions-income'),
            expense: document.getElementById('transactions-expense'),
            net: document.getElementById('transactions-net')
        };

        if (elements.total) {
            elements.total.textContent = `${summary.count || 0} transactions`;
        }
        if (elements.income) {
            elements.income.textContent = formatCurrency(summary.total_income || 0);
        }
        if (elements.expense) {
            elements.expense.textContent = formatCurrency(summary.total_expense || 0);
        }
        if (elements.net) {
            const net = (summary.total_income || 0) - (summary.total_expense || 0);
            elements.net.textContent = formatCurrency(net);
            elements.net.className = `summary-value ${net >= 0 ? 'income' : 'expense'}`;
        }
    }

    /**
     * Populate category filter dropdown
     */
    populateCategoryFilter(categories) {
        const categoryFilter = document.getElementById('transaction-category-filter');
        if (!categoryFilter) return;

        const options = categories.map(category => 
            `<option value="${category.id}">${category.icon} ${category.name}</option>`
        ).join('');

        categoryFilter.innerHTML = '<option value="all">All Categories</option>' + options;
    }

    /**
     * Load budgets page data
     */
    async loadBudgets() {
        try {
            this.showLoading('budgets-loading');
            
            // Load budgets
            const budgetsResponse = await this.apiRequest('/api/budgets');
            this.updateBudgetsGrid(budgetsResponse.budgets || []);
            
            // Load budget performance
            const performanceResponse = await this.apiRequest('/api/budgets/performance');
            this.updateBudgetOverview(performanceResponse.performance || []);
            
            // Load categories for budget creation
            const categoriesResponse = await this.apiRequest('/api/categories?type=expense');
            this.populateBudgetCategories(categoriesResponse.categories || []);
            
        } catch (error) {
            console.error('Failed to load budgets:', error);
            this.showError('Failed to load budgets');
            this.showBudgetsEmpty();
        } finally {
            this.hideLoading('budgets-loading');
        }
    }

    /**
     * Update budgets grid
     */
    updateBudgetsGrid(budgets) {
        const grid = document.getElementById('budgets-grid');
        const emptyState = document.getElementById('budgets-empty');
        
        if (!grid) return;

        if (!budgets || budgets.length === 0) {
            grid.innerHTML = '';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';

        const budgetCards = budgets.map(budget => {
            const spent = budget.actual_spent || 0;
            const percentage = budget.budget_amount > 0 ? (spent / budget.budget_amount) * 100 : 0;
            const remaining = budget.budget_amount - spent;
            
            let status = 'safe';
            if (percentage >= 100) status = 'danger';
            else if (percentage >= 80) status = 'warning';
            
            return `
                <div class="budget-card" data-id="${budget.id}">
                    <div class="budget-header">
                        <div class="budget-category">
                            <div class="budget-category-icon" style="background: ${budget.category_color || '#4F8A8B'}">
                                ${budget.category_icon || '🎯'}
                            </div>
                            <div>
                                <div class="budget-category-name">${budget.category_name}</div>
                                <div class="budget-period">${budget.period} budget</div>
                            </div>
                        </div>
                        <div class="budget-actions">
                            <button class="table-action-btn" onclick="app.editBudget(${budget.id})" 
                                    aria-label="Edit budget">
                                ✏️
                            </button>
                            <button class="table-action-btn" onclick="app.deleteBudget(${budget.id})" 
                                    aria-label="Delete budget">
                                🗑️
                            </button>
                        </div>
                    </div>
                    <div class="budget-amount">${formatCurrency(budget.budget_amount)}</div>
                    <div class="budget-progress">
                        <div class="budget-progress-bar">
                            <div class="budget-progress-fill ${status}" style="width: ${Math.min(percentage, 100)}%"></div>
                        </div>
                        <div class="budget-stats">
                            <span class="budget-spent">Spent: ${formatCurrency(spent)}</span>
                            <span class="budget-remaining ${status}">
                                ${remaining >= 0 ? 'Left: ' + formatCurrency(remaining) : 'Over: ' + formatCurrency(Math.abs(remaining))}
                            </span>
                        </div>
                    </div>
                    <div class="budget-details">
                        <div class="budget-detail-item">
                            <span class="budget-detail-label">Progress:</span>
                            <span class="budget-detail-value">${percentage.toFixed(1)}%</span>
                        </div>
                        <div class="budget-detail-item">
                            <span class="budget-detail-label">Status:</span>
                            <span class="budget-detail-value ${status}">${status.charAt(0).toUpperCase() + status.slice(1)}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        grid.innerHTML = budgetCards;
    }
    /**
     * Update budget overview cards
     */
    updateBudgetOverview(performance) {
        const totalBudgets = performance.length;
        const totalBudgetAmount = performance.reduce((sum, item) => sum + item.budget_amount, 0);
        const totalSpent = performance.reduce((sum, item) => sum + item.actual_spent, 0);
        const remainingBudget = totalBudgetAmount - totalSpent;

        const elements = {
            totalBudgets: document.getElementById('total-budgets'),
            totalBudgetAmount: document.getElementById('total-budget-amount'),
            totalSpent: document.getElementById('total-spent'),
            remainingBudget: document.getElementById('remaining-budget')
        };

        if (elements.totalBudgets) {
            this.animateCounter(elements.totalBudgets, totalBudgets);
        }
        if (elements.totalBudgetAmount) {
            elements.totalBudgetAmount.textContent = formatCurrency(totalBudgetAmount);
        }
        if (elements.totalSpent) {
            elements.totalSpent.textContent = formatCurrency(totalSpent);
        }
        if (elements.remainingBudget) {
            elements.remainingBudget.textContent = formatCurrency(remainingBudget);
            elements.remainingBudget.className = `card-value ${remainingBudget >= 0 ? 'positive' : 'negative'}`;
        }
    }

    /**
     * Load reports page data
     */
    async loadReports() {
        try {
            this.showLoading('reports-loading');
            
            // Get selected period
            const period = document.getElementById('reports-period')?.value || 'this_month';
            
            // Load insights data
            const insightsResponse = await this.apiRequest(`/api/insights?period=${period}`);
            this.updateReportsInsights(insightsResponse.insights || {});
            
            // Load chart data for reports
            const chartResponse = await this.apiRequest(`/api/chart-data?period=${period}`);
            await this.updateReportsCharts(chartResponse);
            
            // Load detailed analysis
            const analysisResponse = await this.apiRequest(`/api/analysis?period=${period}`);
            this.updateDetailedAnalysis(analysisResponse.analysis || {});
            
        } catch (error) {
            console.error('Failed to load reports:', error);
            this.showError('Failed to load reports');
        } finally {
            this.hideLoading('reports-loading');
        }
    }

    /**
     * Update reports insights
     */
    updateReportsInsights(insights) {
        // Update income vs expenses comparison
        const incomeElement = document.getElementById('insight-income');
        const expenseElement = document.getElementById('insight-expense');
        
        if (incomeElement && expenseElement) {
            incomeElement.textContent = formatCurrency(insights.total_income || 0);
            expenseElement.textContent = formatCurrency(insights.total_expense || 0);
            
            // Update comparison bars
            const maxAmount = Math.max(insights.total_income || 0, insights.total_expense || 0);
            if (maxAmount > 0) {
                const incomeFill = document.querySelector('.income-fill');
                const expenseFill = document.querySelector('.expense-fill');
                
                if (incomeFill) {
                    incomeFill.style.width = `${(insights.total_income / maxAmount) * 100}%`;
                }
                if (expenseFill) {
                    expenseFill.style.width = `${(insights.total_expense / maxAmount) * 100}%`;
                }
            }
        }

        // Update savings rate
        this.updateSavingsRate(insights.savings_rate || 0);
        
        // Update top spending category
        this.updateTopSpendingCategory(insights.top_category || {});
        
        // Update spending trend
        this.updateSpendingTrend(insights.spending_trend || {});
    }

    /**
     * Update savings rate circle
     */
    updateSavingsRate(savingsRate) {
        const savingsRatePath = document.getElementById('savings-rate-path');
        const savingsRateText = document.getElementById('savings-rate-text');
        const totalSaved = document.getElementById('total-saved');
        
        if (savingsRatePath) {
            const circumference = 100; // Based on stroke-dasharray total
            const offset = circumference - (savingsRate / 100) * circumference;
            savingsRatePath.style.strokeDasharray = `${savingsRate}, ${circumference}`;
        }
        
        if (savingsRateText) {
            savingsRateText.textContent = `${savingsRate.toFixed(0)}%`;
        }
        
        if (totalSaved) {
            // This would need to be calculated based on actual savings data
            totalSaved.textContent = formatCurrency(0);
        }
    }

    /**
     * Update reports charts
     */
    async updateReportsCharts(chartData) {
        if (chartData.monthly_trends) {
            await renderReportsTrendsChart(chartData.monthly_trends);
        }
        
        if (chartData.category_breakdown) {
            await renderCategoryChart(chartData.category_breakdown);
        }
    }

    /**
     * Load settings page data
     */
    async loadSettings() {
        try {
            this.showLoading('settings-loading');
            
            // Load user preferences
            const preferencesResponse = await this.apiRequest('/api/preferences');
            this.populateSettingsForm(preferencesResponse.preferences || {});
            
            // Load user profile data
            const profileResponse = await this.apiRequest('/api/profile');
            this.populateProfileForm(profileResponse.profile || {});
            
            // Load account activity data
            const activityResponse = await this.apiRequest('/api/account/activity');
            this.updateAccountActivity(activityResponse.activity || {});
            
        } catch (error) {
            console.error('Failed to load settings:', error);
            this.showError('Failed to load settings');
        } finally {
            this.hideLoading('settings-loading');
        }
    }

    /**
     * Populate settings form with current preferences
     */
    populateSettingsForm(preferences) {
        const formElements = {
            theme: document.getElementById('theme-select'),
            currency: document.getElementById('currency-select'),
            dateFormat: document.getElementById('date-format-select'),
            defaultView: document.getElementById('default-transaction-view'),
            transactionsPerPage: document.getElementById('transactions-per-page')
        };

        Object.keys(formElements).forEach(key => {
            const element = formElements[key];
            const prefKey = key.replace(/([A-Z])/g, '_$1').toLowerCase();
            
            if (element && preferences[prefKey]) {
                element.value = preferences[prefKey];
            }
        });

        // Handle checkboxes for notifications
        const notificationCheckboxes = [
            'budget-warnings',
            'budget-exceeded',
            'daily-summary',
            'weekly-report',
            'security-alerts',
            'feature-updates'
        ];

        notificationCheckboxes.forEach(id => {
            const checkbox = document.getElementById(id);
            const prefKey = id.replace(/-/g, '_');
            
            if (checkbox && preferences[prefKey] !== undefined) {
                checkbox.checked = preferences[prefKey];
            }
        });
    }

    /**
     * Populate profile form
     */
    populateProfileForm(profile) {
        const profileElements = {
            username: document.getElementById('profile-username'),
            email: document.getElementById('profile-email'),
            firstName: document.getElementById('profile-first-name'),
            lastName: document.getElementById('profile-last-name')
        };

        Object.keys(profileElements).forEach(key => {
            const element = profileElements[key];
            const profileKey = key.replace(/([A-Z])/g, '_$1').toLowerCase();
            
            if (element && profile[profileKey]) {
                element.value = profile[profileKey];
            }
        });
    }

    /**
     * Update account activity information
     */
    updateAccountActivity(activity) {
        const lastLogin = document.getElementById('last-login');
        const accountCreated = document.getElementById('account-created');
        
        if (lastLogin && activity.last_login) {
            lastLogin.textContent = formatDate(activity.last_login, 'medium');
        }
        
        if (accountCreated && activity.created_at) {
            accountCreated.textContent = formatDate(activity.created_at, 'medium');
        }
    }

    /**
     * Show empty state for transactions
     */
    showTransactionsEmpty() {
        const emptyState = document.getElementById('transactions-empty');
        if (emptyState) {
            emptyState.style.display = 'block';
        }
    }

    /**
     * Show empty state for budgets
     */
    showBudgetsEmpty() {
        const emptyState = document.getElementById('budgets-empty');
        if (emptyState) {
            emptyState.style.display = 'block';
        }
    }

    /**
     * Edit transaction
     */
    async editTransaction(transactionId) {
        try {
            const response = await this.apiRequest(`/api/transaction/${transactionId}`);
            if (response.transaction) {
                this.openEditTransactionModal(response.transaction);
            }
        } catch (error) {
            console.error('Failed to load transaction for editing:', error);
            this.showError('Failed to load transaction');
        }
    }

    /**
     * Delete transaction
     */
    async deleteTransaction(transactionId) {
        const confirmed = await showConfirmation(
            'Are you sure you want to delete this transaction? This action cannot be undone.',
            'Delete Transaction'
        );
        
        if (!confirmed) return;
        
        try {
            const response = await this.apiRequest(`/transactions/${transactionId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                showToast('Transaction deleted successfully', 'success');
                await this.loadTransactions(); // Reload transactions
            }
        } catch (error) {
            console.error('Failed to delete transaction:', error);
            this.showError('Failed to delete transaction');
        }
    }

    /**
     * Edit budget
     */
    async editBudget(budgetId) {
        // Implementation similar to editTransaction
        console.log('Edit budget:', budgetId);
        // You would implement this similar to the transaction editing
    }

    /**
     * Delete budget
     */
    async deleteBudget(budgetId) {
        const confirmed = await showConfirmation(
            'Are you sure you want to delete this budget?',
            'Delete Budget'
        );
        
        if (!confirmed) return;
        
        try {
            const response = await this.apiRequest(`/api/budgets/${budgetId}`, {
                method: 'DELETE'
            });
            
            if (response.success) {
                showToast('Budget deleted successfully', 'success');
                await this.loadBudgets(); // Reload budgets
            }
        } catch (error) {
            console.error('Failed to delete budget:', error);
            this.showError('Failed to delete budget');
        }
    }
    
// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new FinanceApp();
});

// Export for module usage
export default FinanceApp;
