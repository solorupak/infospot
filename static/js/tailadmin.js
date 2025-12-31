// TailAdmin JavaScript Integration
// This file handles TailAdmin component interactions and HTMX integration

class TailAdminComponents {
    constructor() {
        this.initializeComponents();
        this.setupHTMXIntegration();
        this.setupThemeToggle();
    }
    
    initializeComponents() {
        console.log('TailAdmin components initialized');
        
        // Initialize any components that need JS
        this.initializeModals();
        this.initializeDropdowns();
    }
    
    initializeModals() {
        // Modal functionality will be handled by Alpine.js
        // This is a placeholder for any additional modal logic
    }
    
    initializeDropdowns() {
        // Dropdown functionality will be handled by Alpine.js
        // This is a placeholder for any additional dropdown logic
    }
    
    setupHTMXIntegration() {
        // Show loading indicators for HTMX requests
        document.body.addEventListener('htmx:beforeRequest', (event) => {
            const indicator = event.target.querySelector('.htmx-indicator');
            if (indicator) {
                indicator.classList.remove('hidden');
            }
        });
        
        document.body.addEventListener('htmx:afterRequest', (event) => {
            const indicator = event.target.querySelector('.htmx-indicator');
            if (indicator) {
                indicator.classList.add('hidden');
            }
            
            // Reinitialize components after HTMX content swap
            this.initializeComponents();
        });
        
        // Handle HTMX errors
        document.body.addEventListener('htmx:responseError', (event) => {
            console.error('HTMX Error:', event.detail);
            this.showToast('An error occurred. Please try again.', 'error');
        });
    }
    
    setupThemeToggle() {
        // Initialize theme from localStorage or system preference
        const savedTheme = localStorage.getItem('theme');
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        const theme = savedTheme || systemTheme;
        
        this.setTheme(theme);
        
        // Listen for theme toggle clicks
        document.addEventListener('click', (event) => {
            if (event.target.matches('[data-theme-toggle]') || event.target.closest('[data-theme-toggle]')) {
                this.toggleTheme();
            }
        });
    }
    
    setTheme(theme) {
        const html = document.documentElement;
        
        if (theme === 'dark') {
            html.classList.add('dark');
        } else {
            html.classList.remove('dark');
        }
        
        localStorage.setItem('theme', theme);
    }
    
    toggleTheme() {
        const html = document.documentElement;
        const isDark = html.classList.contains('dark');
        
        this.setTheme(isDark ? 'light' : 'dark');
    }
    
    showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 p-4 rounded-lg text-white z-50 ${
            type === 'error' ? 'bg-red-500' : 
            type === 'success' ? 'bg-green-500' : 
            'bg-blue-500'
        }`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Alpine.js data functions for sidebar functionality
function sidebarData() {
    return {
        isExpanded: localStorage.getItem('sidebar_expanded') !== 'false',
        isHovered: false,
        isMobileOpen: false,
        
        get sidebarClasses() {
            const classes = [];
            
            if (this.isExpanded || this.isHovered) {
                classes.push('lg:ml-[290px]');
            } else {
                classes.push('lg:ml-[90px]');
            }
            
            if (this.isMobileOpen) {
                classes.push('ml-0');
            }
            
            return classes.join(' ');
        },
        
        get logoAlignment() {
            if (!this.isExpanded && !this.isHovered) {
                return 'lg:justify-center';
            }
            return 'justify-start';
        },
        
        toggleSidebar() {
            if (window.innerWidth >= 991) {
                this.isExpanded = !this.isExpanded;
                localStorage.setItem('sidebar_expanded', this.isExpanded);
            } else {
                this.isMobileOpen = !this.isMobileOpen;
            }
        },
        
        toggleMobileSidebar() {
            this.isMobileOpen = !this.isMobileOpen;
        },
        
        setHovered(hovered) {
            this.isHovered = hovered;
        }
    };
}

// Initialize TailAdmin components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.tailAdmin = new TailAdminComponents();
});

// Make sidebarData available globally for Alpine.js
window.sidebarData = sidebarData;