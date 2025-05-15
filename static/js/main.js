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
    if (mobileMenu) {
        mobileMenu.classList.toggle('hidden');
    }
}

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