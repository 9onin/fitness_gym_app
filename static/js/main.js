/**
 * Main JavaScript file for Fitness Gym App
 */

// Auto-hiding flash messages after a delay
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.display = 'none';
        }, 5000); // Hide after 5 seconds
    });
});

// Confirmation for delete actions
function confirmDelete(message) {
    return confirm(message || 'Вы уверены, что хотите удалить этот элемент?');
}

// Format date for display
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', options);
}

// Format time for display
function formatTime(dateString) {
    const options = { hour: '2-digit', minute: '2-digit' };
    const date = new Date(dateString);
    return date.toLocaleTimeString('ru-RU', options);
}

// Toggle mobile menu
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobile-menu');
    const toggleButton = document.querySelector('[aria-controls="mobile-menu"]');
    if (mobileMenu) {
        mobileMenu.classList.toggle('hidden');
        if (toggleButton) {
            const expanded = !mobileMenu.classList.contains('hidden');
            toggleButton.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        }
    }
}

function toggleNotifications() {
    const panel = document.getElementById('header-notifications');
    const toggleButton = document.querySelector('[aria-controls="header-notifications"]');
    const badge = document.querySelector('[data-notification-badge]');

    if (!panel) {
        return;
    }

    panel.classList.toggle('hidden');
    const isOpen = !panel.classList.contains('hidden');

    if (toggleButton) {
        toggleButton.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    }

    if (isOpen) {
        fetch('/user/notifications/mark-read', {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).then(function(response) {
            if (!response.ok) {
                return null;
            }
            return response.json();
        }).then(function(payload) {
            if (!payload || !badge) {
                return;
            }
            badge.remove();
        }).catch(function() {
            // ignore notification read failures to avoid breaking the panel UX
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.querySelector('[data-mobile-menu-toggle]');
    const mobileMenu = document.getElementById('mobile-menu');

    if (!toggle || !mobileMenu) {
        return;
    }

    function closeMobileMenu() {
        mobileMenu.classList.add('hidden');
        toggle.setAttribute('aria-expanded', 'false');
    }

    toggle.addEventListener('click', function() {
        const isHidden = mobileMenu.classList.toggle('hidden');
        toggle.setAttribute('aria-expanded', String(!isHidden));
    });

    mobileMenu.querySelectorAll('a').forEach(function(link) {
        link.addEventListener('click', closeMobileMenu);
    });

    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            closeMobileMenu();
        }
    });

    document.addEventListener('click', function(event) {
        const clickedInsideMenu = mobileMenu.contains(event.target);
        const clickedToggle = toggle.contains(event.target);

        if (!clickedInsideMenu && !clickedToggle) {
            closeMobileMenu();
        }
    });
});

// Progressive web app install and offline shell
document.addEventListener('DOMContentLoaded', function() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/service-worker.js').catch(function(error) {
            console.warn('Service worker registration failed:', error);
        });
    }

    let installPrompt = null;
    const installButtons = document.querySelectorAll('[data-install-app]');

    function showInstallButtons() {
        installButtons.forEach(function(button) {
            button.hidden = false;
            button.classList.remove('hidden');
        });
    }

    function hideInstallButtons() {
        installButtons.forEach(function(button) {
            button.hidden = true;
            button.classList.add('hidden');
        });
    }

    window.addEventListener('beforeinstallprompt', function(event) {
        event.preventDefault();
        installPrompt = event;
        showInstallButtons();
    });

    installButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            if (!installPrompt) {
                return;
            }

            installPrompt.prompt();
            installPrompt.userChoice.finally(function() {
                installPrompt = null;
                hideInstallButtons();
            });
        });
    });

    window.addEventListener('appinstalled', hideInstallButtons);
});

// Initialize any datetime pickers
document.addEventListener('DOMContentLoaded', function() {
    const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    
    datetimeInputs.forEach(function(input) {
        // Set default value to current date/time if not already set
        if (!input.value) {
            const now = new Date();
            now.setMinutes(now.getMinutes() - now.getMinutes() % 15 + 15); // Round to next 15 minutes
            
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            
            input.value = `${year}-${month}-${day}T${hours}:${minutes}`;
        }
    });
});

// Toggle password visibility for auth forms
document.addEventListener('DOMContentLoaded', function() {
    const toggles = document.querySelectorAll('[data-toggle-password]');

    toggles.forEach(function(toggle) {
        toggle.addEventListener('change', function() {
            const targetId = toggle.getAttribute('data-toggle-password');
            const passwordInput = document.getElementById(targetId);

            if (!passwordInput) {
                return;
            }

            passwordInput.type = toggle.checked ? 'text' : 'password';
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuLinks = document.querySelectorAll('#mobile-menu a, #mobile-menu button');
    const mobileMenu = document.getElementById('mobile-menu');
    const toggleButton = document.querySelector('[aria-controls="mobile-menu"]');

    mobileMenuLinks.forEach(function(link) {
        link.addEventListener('click', function() {
            if (!mobileMenu) {
                return;
            }
            mobileMenu.classList.add('hidden');
            if (toggleButton) {
                toggleButton.setAttribute('aria-expanded', 'false');
            }
        });
    });
});

document.addEventListener('click', function(event) {
    const panel = document.getElementById('header-notifications');
    const toggleButton = document.querySelector('[aria-controls="header-notifications"]');

    if (!panel || !toggleButton || panel.classList.contains('hidden')) {
        return;
    }

    if (panel.contains(event.target) || toggleButton.contains(event.target)) {
        return;
    }

    panel.classList.add('hidden');
    toggleButton.setAttribute('aria-expanded', 'false');
});
