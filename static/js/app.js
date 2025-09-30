/**
 * Personal Finance Manager Pro - Simple & Attractive
 * ================================================
 * 
 * Clean, modern JavaScript with smooth animations
 * and beautiful user interactions.
 */

class FinanceApp {
    constructor() {
        this.currentPage = 'landing';
        this.currentUser = null;
        this.isLoading = false;
        
        this.init();
    }

    /**
     * Initialize the application with smooth startup
     */
    init() {
        this.showWelcomeAnimation();
        this.setupEventListeners();
        this.setupTheme();
        this.setupAnimations();
        
        console.log('💰 Finance Manager Pro - Ready to transform your finances!');
    }

    /**
     * Welcome animation on page load
     */
    showWelcomeAnimation() {
        const hero = document.querySelector('.hero-section');
        if (hero) {
            hero.style.opacity = '0';
            hero.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                hero.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                hero.style.opacity = '1';
                hero.style.transform = 'translateY(0)';
            }, 100);
        }
    }

    /**
     * Setup all event listeners with modern interactions
     */
    setupEventListeners() {
        // Primary CTA buttons
        this.setupButton('#get-started-btn', () => this.navigateToPage('register'), '🚀 Let\'s get started!');
        this.setupButton('#login-link', () => this.navigateToPage('login'), '👋 Welcome back!');
        
        // Navigation buttons  
        this.setupButton('[data-page="dashboard"]', () => this.navigateToPage('dashboard'));
        this.setupButton('[data-page="transactions"]', () => this.navigateToPage('transactions'));
        this.setupButton('[data-page="budgets"]', () => this.navigateToPage('budgets'));
        this.setupButton('[data-page="reports"]', () => this.navigateToPage('reports'));
        this.setupButton('[data-page="settings"]', () => this.navigateToPage('settings'));

        // Auth form handlers
        this.setupForm('#login-form', this.handleLogin.bind(this));
        this.setupForm('#register-form', this.handleRegister.bind(this));
        
        // Theme toggle
        this.setupButton('#theme-toggle', this.toggleTheme.bind(this));
        
        // Back buttons
        this.setupButton('.back-btn', this.goBack.bind(this));
        
        // Smooth scrolling for anchor links
        this.setupSmoothScroll();
    }

    /**
     * Setup button with attractive interactions
     */
    setupButton(selector, callback, successMessage = null) {
        const buttons = document.querySelectorAll(selector);
        
        buttons.forEach(button => {
            if (!button) return;
            
            // Add ripple effect
            this.addRippleEffect(button);
            
            // Click handler
            button.addEventListener('click', async (e) => {
                e.preventDefault();
                
                if (this.isLoading) return;
                
                // Button press animation
                this.animateButtonPress(button);
                
                // Show success message if provided
                if (successMessage) {
                    this.showToast(successMessage, 'info');
                }
                
                // Execute callback
                if (callback) await callback(e);
            });
            
            // Hover effects
            button.addEventListener('mouseenter', () => {
                button.style.transform = 'translateY(-2px)';
                button.style.boxShadow = '0 8px 25px rgba(79, 138, 139, 0.3)';
            });
            
            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translateY(0)';
                button.style.boxShadow = 'none';
            });
        });
    }

    /**
     * Add beautiful ripple effect to buttons
     */
    addRippleEffect(button) {
        button.style.position = 'relative';
        button.style.overflow = 'hidden';
        
        button.addEventListener('click', (e) => {
            const ripple = document.createElement('span');
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            // Add ripple keyframes if not exists
            if (!document.getElementById('ripple-styles')) {
                const style = document.createElement('style');
                style.id = 'ripple-styles';
                style.textContent = `
                    @keyframes ripple {
                        to { transform: scale(4); opacity: 0; }
                    }
                `;
                document.head.appendChild(style);
            }
            
            button.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        });
    }

    /**
     * Animate button press
     */
    animateButtonPress(button) {
        button.style.transform = 'scale(0.95)';
        setTimeout(() => {
            button.style.transform = 'scale(1)';
        }, 150);
    }

    /**
     * Setup form with loading states
     */
    setupForm(selector, handler) {
        const form = document.querySelector(selector);
        if (!form) return;
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = form.querySelector('[type="submit"]');
            if (!submitBtn) return;
            
            // Show loading state
            const originalText = submitBtn.textContent;
            this.setButtonLoading(submitBtn, true);
            
            try {
                await handler(e);
            } catch (error) {
                this.showToast('Oops! Something went wrong. Please try again.', 'error');
            } finally {
                // Reset button
                this.setButtonLoading(submitBtn, false, originalText);
            }
        });
    }

    /**
     * Beautiful page navigation with smooth transitions
     */
    async navigateToPage(page) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        
        // Show loading animation
        this.showPageTransition();
        
        try {
            // Hide current page with fade out
            await this.hideCurrentPage();
            
            // Show new page with fade in
            await this.showPage(page);
            
            this.currentPage = page;
            
            // Update URL
            if (history.pushState) {
                history.pushState(null, null, `#${page}`);
            }
            
            // Load page data if needed
            await this.loadPageData(page);
            
        } catch (error) {
            console.error('Navigation error:', error);
            this.showToast('Navigation failed. Please try again.', 'error');
        } finally {
            this.hidePageTransition();
            this.isLoading = false;
        }
    }

    /**
     * Hide current page with smooth animation
     */
    hideCurrentPage() {
        return new Promise(resolve => {
            const currentPage = document.querySelector('.page.active');
            if (!currentPage) {
                resolve();
                return;
            }
            
            currentPage.style.transition = 'all 0.3s ease-out';
            currentPage.style.opacity = '0';
            currentPage.style.transform = 'translateX(-20px)';
            
            setTimeout(() => {
                currentPage.classList.remove('active');
                currentPage.style.display = 'none';
                resolve();
            }, 300);
        });
    }

    /**
     * Show new page with smooth animation
     */
    showPage(page) {
        return new Promise(resolve => {
            const targetPage = document.getElementById(`${page}-page`);
            if (!targetPage) {
                console.warn(`Page ${page} not found`);
                resolve();
                return;
            }
            
            // Prepare page for animation
            targetPage.style.display = 'block';
            targetPage.style.opacity = '0';
            targetPage.style.transform = 'translateX(20px)';
            targetPage.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            
            // Trigger animation
            setTimeout(() => {
                targetPage.style.opacity = '1';
                targetPage.style.transform = 'translateX(0)';
                targetPage.classList.add('active');
                resolve();
            }, 50);
        });
    }

    /**
     * Show page transition loading
     */
    showPageTransition() {
        const loader = this.createLoader();
        document.body.appendChild(loader);
        
        setTimeout(() => {
            loader.style.opacity = '1';
        }, 10);
    }

    /**
     * Hide page transition loading
     */
    hidePageTransition() {
        const loader = document.getElementById('page-loader');
        if (loader) {
            loader.style.opacity = '0';
            setTimeout(() => loader.remove(), 300);
        }
    }

    /**
     * Create beautiful loading spinner
     */
    createLoader() {
        const loader = document.createElement('div');
        loader.id = 'page-loader';
        loader.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(103, 126, 234, 0.1);
            backdrop-filter: blur(10px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        loader.innerHTML = `
            <div style="
                width: 50px;
                height: 50px;
                border: 3px solid rgba(79, 138, 139, 0.3);
                border-top: 3px solid #4F8A8B;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            "></div>
        `;
        
        // Add spinner keyframes
        if (!document.getElementById('spinner-styles')) {
            const style = document.createElement('style');
            style.id = 'spinner-styles';
            style.textContent = `
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
        }
        
        return loader;
    }

    /**
     * Handle login with beautiful UX
     */
    async handleLogin(e) {
        const form = e.target;
        const formData = new FormData(form);
        
        const username = formData.get('username')?.trim();
        const password = formData.get('password');
        
        if (!username || !password) {
            this.showToast('Please fill in all fields', 'warning');
            return;
        }
        
        // Simulate API call
        await this.delay(1500);
        
        // For demo - accept any credentials
        this.showToast('Welcome back! 🎉', 'success');
        await this.delay(800);
        await this.navigateToPage('dashboard');
    }

    /**
     * Handle registration with beautiful UX
     */
    async handleRegister(e) {
        const form = e.target;
        const formData = new FormData(form);
        
        const username = formData.get('username')?.trim();
        const email = formData.get('email')?.trim();
        const password = formData.get('password');
        
        if (!username || !email || !password) {
            this.showToast('Please fill in all fields', 'warning');
            return;
        }
        
        if (!this.isValidEmail(email)) {
            this.showToast('Please enter a valid email address', 'error');
            return;
        }
        
        // Simulate API call
        await this.delay(2000);
        
        this.showToast('Account created successfully! 🚀', 'success');
        await this.delay(800);
        await this.navigateToPage('dashboard');
    }

    /**
     * Load page-specific data
     */
    async loadPageData(page) {
        switch (page) {
            case 'dashboard':
                await this.loadDashboard();
                break;
            case 'transactions':
                await this.loadTransactions();
                break;
            default:
                break;
        }
    }

    /**
     * Load dashboard with demo data
     */
    async loadDashboard() {
        console.log('📊 Loading dashboard...');
        
        // Animate dashboard cards
        const cards = document.querySelectorAll('.stat-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    /**
     * Show beautiful toast notifications
     */
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        
        const icons = {
            success: '✅',
            error: '❌', 
            warning: '⚠️',
            info: 'ℹ️'
        };
        
        const colors = {
            success: '#38B27B',
            error: '#FA7373',
            warning: '#FFB600',
            info: '#4F8A8B'
        };
        
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${colors[type]};
            color: white;
            padding: 16px 24px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
            z-index: 10000;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 12px;
            transform: translateX(100%);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            max-width: 350px;
        `;
        
        toast.innerHTML = `
            <span style="font-size: 18px;">${icons[type]}</span>
            <span>${message}</span>
        `;
        
        document.body.appendChild(toast);
        
        // Show animation
        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 100);
        
        // Hide animation
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    /**
     * Set button loading state
     */
    setButtonLoading(button, loading, originalText = null) {
        if (loading) {
            button.disabled = true;
            button.style.opacity = '0.7';
            button.innerHTML = `
                <span style="display: inline-flex; align-items: center; gap: 8px;">
                    <span style="width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.3); border-top: 2px solid white; border-radius: 50%; animation: spin 1s linear infinite;"></span>
                    Loading...
                </span>
            `;
        } else {
            button.disabled = false;
            button.style.opacity = '1';
            button.textContent = originalText || button.textContent;
        }
    }

    /**
     * Setup theme toggle
     */
    setupTheme() {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        document.documentElement.setAttribute('data-theme', savedTheme);
    }

    /**
     * Toggle theme with smooth transition
     */
    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        this.showToast(`Switched to ${newTheme} mode`, 'info');
    }

    /**
     * Go back to previous page
     */
    async goBack() {
        const previousPages = {
            login: 'landing',
            register: 'landing', 
            dashboard: 'landing',
            transactions: 'dashboard',
            budgets: 'dashboard',
            reports: 'dashboard',
            settings: 'dashboard'
        };
        
        const prevPage = previousPages[this.currentPage] || 'landing';
        await this.navigateToPage(prevPage);
    }

    /**
     * Setup smooth scrolling
     */
    setupSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    /**
     * Setup entrance animations
     */
    setupAnimations() {
        // Animate elements on scroll
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        });
        
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(30px)';
            el.style.transition = 'all 0.6s ease';
            observer.observe(el);
        });
    }

    // Utility functions
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new FinanceApp();
    console.log('🎉 Personal Finance Manager Pro is ready!');
});

// Export for module usage (if needed)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FinanceApp;
}
