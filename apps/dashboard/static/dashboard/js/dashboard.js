// Dashboard JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard functionality
    initializeBulkSelection();
    initializeToasts();
    initializeFormValidation();
    initializeSearchDebounce();
});

// Bulk selection functionality
function initializeBulkSelection() {
    const selectAllCheckbox = document.getElementById('select-all');
    const bulkCheckboxes = document.querySelectorAll('.bulk-select');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            bulkCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActions();
        });
    }
    
    bulkCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectAllState();
            updateBulkActions();
        });
    });
}

function updateSelectAllState() {
    const selectAllCheckbox = document.getElementById('select-all');
    const bulkCheckboxes = document.querySelectorAll('.bulk-select');
    
    if (selectAllCheckbox && bulkCheckboxes.length > 0) {
        const checkedCount = document.querySelectorAll('.bulk-select:checked').length;
        
        if (checkedCount === 0) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = false;
        } else if (checkedCount === bulkCheckboxes.length) {
            selectAllCheckbox.indeterminate = false;
            selectAllCheckbox.checked = true;
        } else {
            selectAllCheckbox.indeterminate = true;
            selectAllCheckbox.checked = false;
        }
    }
}

function updateBulkActions() {
    const checkedCount = document.querySelectorAll('.bulk-select:checked').length;
    const bulkActionButtons = document.querySelectorAll('.bulk-action');
    
    bulkActionButtons.forEach(button => {
        button.disabled = checkedCount === 0;
        if (checkedCount > 0) {
            button.textContent = button.textContent.replace(/\(\d+\)/, `(${checkedCount})`);
        }
    });
}

// Toast notifications
function initializeToasts() {
    // Auto-show toasts
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(toast => {
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    });
}

function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    const toastTemplate = document.getElementById('toast-template');
    
    if (toastContainer && toastTemplate) {
        const toast = toastTemplate.cloneNode(true);
        toast.id = 'toast-' + Date.now();
        toast.style.display = 'block';
        
        const toastBody = toast.querySelector('.toast-body');
        toastBody.textContent = message;
        
        // Add appropriate classes based on type
        toast.classList.add('toast-' + type);
        if (type === 'success') {
            toast.classList.add('bg-success', 'text-white');
        } else if (type === 'error') {
            toast.classList.add('bg-danger', 'text-white');
        } else if (type === 'warning') {
            toast.classList.add('bg-warning');
        }
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[hx-post]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

// Search debounce
function initializeSearchDebounce() {
    const searchInputs = document.querySelectorAll('input[hx-trigger*="keyup"]');
    
    searchInputs.forEach(input => {
        let timeout;
        input.addEventListener('keyup', function() {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                htmx.trigger(input, 'keyup');
            }, 300);
        });
    });
}

// HTMX event handlers
document.addEventListener('htmx:beforeRequest', function(event) {
    // Show loading state
    const target = event.target;
    if (target.classList.contains('btn')) {
        target.disabled = true;
        const originalText = target.innerHTML;
        target.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        target.dataset.originalText = originalText;
    }
});

document.addEventListener('htmx:afterRequest', function(event) {
    // Hide loading state
    const target = event.target;
    if (target.classList.contains('btn') && target.dataset.originalText) {
        target.disabled = false;
        target.innerHTML = target.dataset.originalText;
        delete target.dataset.originalText;
    }
    
    // Handle response
    if (event.detail.xhr.status >= 200 && event.detail.xhr.status < 300) {
        try {
            const response = JSON.parse(event.detail.xhr.responseText);
            if (response.message) {
                showToast(response.message, response.success ? 'success' : 'error');
            }
        } catch (e) {
            // Response is not JSON, probably HTML
        }
    }
});

document.addEventListener('htmx:responseError', function(event) {
    showToast('An error occurred. Please try again.', 'error');
});

document.addEventListener('htmx:afterSwap', function(event) {
    // Reinitialize components after HTMX swap
    initializeBulkSelection();
    initializeFormValidation();
    
    // Update page title if needed
    const newTitle = event.detail.target.dataset.title;
    if (newTitle) {
        document.title = newTitle;
    }
});

// Utility functions
function confirmDelete(message = 'Are you sure you want to delete this item?') {
    return confirm(message);
}

function getSelectedItems() {
    const checkboxes = document.querySelectorAll('.bulk-select:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

// Export functions for global use
window.dashboard = {
    showToast,
    confirmDelete,
    getSelectedItems,
    updateBulkActions
};