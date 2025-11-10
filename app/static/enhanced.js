// Dark Mode Toggle and Theme Manager
class ThemeManager {
    constructor() {
        this.themeMode = localStorage.getItem('themeMode') || 'manual';
        this.theme = 'light';
        this.init();
    }

    init() {
        // Decide theme based on mode
        if (this.themeMode === 'auto') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.theme = prefersDark ? 'dark' : 'light';
        } else {
            // Default to auto mode if first visit
            if (!localStorage.getItem('theme') && !localStorage.getItem('themeMode')) {
                this.themeMode = 'auto';
                localStorage.setItem('themeMode', 'auto');
                const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                this.theme = prefersDark ? 'dark' : 'light';
            } else {
                this.theme = localStorage.getItem('theme') || 'light';
            }
        }
        // Apply theme
        this.applyTheme(this.theme);
        
        // Setup toggle button if exists
        this.setupToggleButton();
        
        // Listen for system theme changes
        this.watchSystemTheme();
    }

    setupToggleButton() {
        const toggleBtn = document.getElementById('themeToggle');
        if (toggleBtn) {
            // Update icon visibility based on current theme
            this.updateToggleIcon(toggleBtn);
            
            // Add click handler
            toggleBtn.onclick = () => this.toggle();
        }
    }

    updateToggleIcon(btn) {
        const lightIcon = btn.querySelector('.theme-icon-light');
        const darkIcon = btn.querySelector('.theme-icon-dark');
        
        if (lightIcon && darkIcon) {
            if (this.theme === 'dark') {
                lightIcon.style.display = 'block';
                darkIcon.style.display = 'none';
            } else {
                lightIcon.style.display = 'none';
                darkIcon.style.display = 'block';
            }
        }
    }

    toggle() {
        // Toggle forces manual mode
        this.themeMode = 'manual';
        localStorage.setItem('themeMode', 'manual');
        this.theme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.theme);
        localStorage.setItem('theme', this.theme);
        
        // Update button icon with animation
        const toggleBtn = document.getElementById('themeToggle');
        if (toggleBtn) {
            toggleBtn.style.transform = 'rotate(360deg)';
            setTimeout(() => {
                this.updateToggleIcon(toggleBtn);
                toggleBtn.style.transform = 'rotate(0deg)';
            }, 150);
        }
        
        // Show toast notification
        if (window.toast) {
            window.toast.show(`Đã chuyển sang ${this.theme === 'dark' ? 'chế độ tối' : 'chế độ sáng'}`, 'info');
        }
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        // Add transition class for smooth theme change
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
    }

    watchSystemTheme() {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            // Only react in auto mode
            if ((localStorage.getItem('themeMode') || this.themeMode) === 'auto') {
                this.theme = e.matches ? 'dark' : 'light';
                this.applyTheme(this.theme);
                const toggleBtn = document.getElementById('themeToggle');
                if (toggleBtn) this.updateToggleIcon(toggleBtn);
            }
        });
    }
}

// Toast Notification System
class ToastNotification {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 12px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        
        toast.innerHTML = `
            <span class="toast-icon">${icons[type]}</span>
            <span class="toast-message">${message}</span>
        `;
        
        toast.style.cssText = `
            background: var(--surface-elevated);
            color: var(--text);
            padding: 14px 20px;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            display: flex;
            align-items: center;
            gap: 12px;
            min-width: 280px;
            max-width: 400px;
            pointer-events: auto;
            animation: slideInRight 0.3s ease;
            border-left: 4px solid ${type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--danger)' : type === 'warning' ? 'var(--warning)' : 'var(--accent)'};
        `;
        
        this.container.appendChild(toast);
        
        // Auto remove
        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
        
        // Click to dismiss
        toast.onclick = () => {
            toast.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        };
    }
}

// Loading Overlay
class LoadingOverlay {
    constructor() {
        this.overlay = this.createOverlay();
    }

    createOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            backdrop-filter: blur(10px);
            z-index: 9999;
            display: none;
            align-items: center;
            justify-content: center;
        `;
        
        overlay.innerHTML = `
            <div style="text-align: center;">
                <div class="loading-spinner"></div>
                <p style="color: white; margin-top: 20px; font-weight: 600;" id="loading-text">Đang tải...</p>
            </div>
        `;
        
        document.body.appendChild(overlay);
        return overlay;
    }

    show(message = 'Đang tải...') {
        this.overlay.style.display = 'flex';
        document.getElementById('loading-text').textContent = message;
    }

    hide() {
        this.overlay.style.display = 'none';
    }
}

// Image Upload with Preview
class ImageUploader {
    constructor(inputId, previewId, options = {}) {
        this.input = document.getElementById(inputId);
        this.preview = document.getElementById(previewId);
        this.options = {
            maxSize: options.maxSize || 5 * 1024 * 1024, // 5MB
            allowedTypes: options.allowedTypes || ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'],
            ...options
        };
        this.init();
    }

    init() {
        if (!this.input) return;
        
        this.input.addEventListener('change', (e) => this.handleUpload(e));
        
        // Drag and drop
        if (this.preview) {
            this.preview.addEventListener('dragover', (e) => {
                e.preventDefault();
                this.preview.classList.add('dragover');
            });
            
            this.preview.addEventListener('dragleave', () => {
                this.preview.classList.remove('dragover');
            });
            
            this.preview.addEventListener('drop', (e) => {
                e.preventDefault();
                this.preview.classList.remove('dragover');
                const file = e.dataTransfer.files[0];
                if (file) {
                    this.processFile(file);
                }
            });
        }
    }

    handleUpload(event) {
        const file = event.target.files[0];
        if (file) {
            this.processFile(file);
        }
    }

    processFile(file) {
        // Validate file type
        if (!this.options.allowedTypes.includes(file.type)) {
            toast.show('Chỉ hỗ trợ file ảnh JPG, PNG, WEBP', 'error');
            return;
        }

        // Validate file size
        if (file.size > this.options.maxSize) {
            toast.show(`Kích thước file không được vượt quá ${this.options.maxSize / 1024 / 1024}MB`, 'error');
            return;
        }

        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            if (this.preview) {
                if (this.preview.tagName === 'IMG') {
                    this.preview.src = e.target.result;
                } else {
                    this.preview.style.backgroundImage = `url(${e.target.result})`;
                }
                this.preview.classList.add('has-image');
            }
            
            if (this.options.onPreview) {
                this.options.onPreview(e.target.result);
            }
        };
        reader.readAsDataURL(file);
    }
}

// Keyboard Shortcuts
class KeyboardShortcuts {
    constructor() {
        this.shortcuts = {
            'ctrl+k': () => this.focusSearch(),
            'ctrl+/': () => this.showShortcuts(),
            'esc': () => this.closeModals(),
            'n': () => this.newPost(),
        };
        this.init();
    }

    init() {
        document.addEventListener('keydown', (e) => {
            const key = [];
            if (e.ctrlKey) key.push('ctrl');
            if (e.shiftKey) key.push('shift');
            if (e.altKey) key.push('alt');
            key.push(e.key.toLowerCase());
            
            const shortcut = key.join('+');
            
            // Don't trigger if typing in input
            if (['input', 'textarea'].includes(e.target.tagName.toLowerCase())) {
                if (shortcut === 'esc') {
                    e.target.blur();
                }
                return;
            }
            
            if (this.shortcuts[shortcut]) {
                e.preventDefault();
                this.shortcuts[shortcut]();
            }
        });
    }

    focusSearch() {
        const searchInput = document.querySelector('.search-form input');
        if (searchInput) {
            searchInput.focus();
        }
    }

    showShortcuts() {
        toast.show('Ctrl+K: Tìm kiếm | N: Bài viết mới | Esc: Đóng', 'info', 5000);
    }

    closeModals() {
        const modals = document.querySelectorAll('.modal-overlay.active');
        modals.forEach(modal => modal.classList.remove('active'));
    }

    newPost() {
        if (typeof openCreatePostModal === 'function') {
            openCreatePostModal();
        }
    }
}

// Search with Debounce
function debounce(func, wait) {
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

// Initialize on page load
let themeManager, toast, loading, shortcuts;

document.addEventListener('DOMContentLoaded', () => {
    themeManager = new ThemeManager();
    toast = new ToastNotification();
    loading = new LoadingOverlay();
    shortcuts = new KeyboardShortcuts();
    
    // Make toast globally available
    window.toast = toast;
    window.loading = loading;
    
    console.log('✨ VocabApp Enhanced Features Loaded');
});

// Add animations CSS
const style = document.createElement('style');
style.textContent = `
@keyframes slideInRight {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOutRight {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(400px);
        opacity: 0;
    }
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.loading-spinner {
    width: 48px;
    height: 48px;
    border: 4px solid rgba(255, 255, 255, 0.2);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

.theme-toggle {
    width: 40px;
    height: 40px;
    border: none;
    background: transparent;
    color: var(--text);
    cursor: pointer;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
}

.theme-toggle:hover {
    background: var(--sidebar-hover);
    transform: scale(1.1);
}

.theme-toggle svg {
    transition: transform 0.3s ease;
}

.toast {
    font-size: 14px;
    font-weight: 500;
}

.toast-icon {
    font-size: 18px;
    font-weight: bold;
}

.toast:hover {
    transform: scale(1.02);
    cursor: pointer;
}

/* Smooth page transitions */
body.page-transition {
    opacity: 0;
    transition: opacity 0.2s ease;
}

/* Image upload preview states */
.has-image {
    border: 2px solid var(--success) !important;
}

.dragover {
    border: 2px dashed var(--primary) !important;
    background: var(--sidebar-hover) !important;
}
`;
document.head.appendChild(style);
