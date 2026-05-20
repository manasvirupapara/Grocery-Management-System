// Dark Mode Theme Management
(function() {
    // Load saved theme preference
    function loadTheme() {
        const savedTheme = localStorage.getItem('radhi-theme') || 'light';
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-mode');
            updateThemeIcon(true);
        } else {
            document.body.classList.remove('dark-mode');
            updateThemeIcon(false);
        }
    }
    
    // Update theme icon
    function updateThemeIcon(isDark) {
        const icon = document.getElementById('themeIcon');
        if (icon) {
            icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
    
    // Toggle theme function
    window.toggleTheme = function() {
        const isDark = document.body.classList.toggle('dark-mode');
        localStorage.setItem('radhi-theme', isDark ? 'dark' : 'light');
        updateThemeIcon(isDark);
    };
    
    // Load theme on page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', loadTheme);
    } else {
        loadTheme();
    }
})();
