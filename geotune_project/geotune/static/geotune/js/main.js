/**
 * GeoTune Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Navigation Toggle
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbar = document.querySelector('.navbar');
    
    if (navbarToggler && navbar) {
        navbarToggler.addEventListener('click', function() {
            navbar.classList.toggle('mobile-open');
        });
    }

    // Close dropdowns when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.dropdown')) {
            const dropdownMenus = document.querySelectorAll('.dropdown-menu');
            dropdownMenus.forEach(menu => {
                menu.parentElement.classList.remove('show');
                menu.classList.remove('show');
            });
        }
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]:not([href="#"])').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Add shadow to navbar on scroll
    window.addEventListener('scroll', function() {
        if (window.scrollY > 10) {
            navbar.classList.add('navbar-scrolled');
        } else {
            navbar.classList.remove('navbar-scrolled');
        }
    });

    // Initialize any interactive elements
    initializeTooltips();
    handleFormValidation();

    // Verbesserte Dropdown-Funktionalität für die Navigation
    const dropdowns = document.querySelectorAll('.navbar .dropdown');
    
    // Timeout für jedes Dropdown-Element speichern
    const dropdownTimeouts = new Map();
    
    // Verzögerung in Millisekunden
    const delay = 300;
    
    dropdowns.forEach(dropdown => {
        const menu = dropdown.querySelector('.dropdown-menu');
        if (!menu) return;
        
        // Bei Hover über dem Dropdown anzeigen
        dropdown.addEventListener('mouseenter', function() {
            // Wenn ein Timeout zum Verstecken existiert, diesen löschen
            if (dropdownTimeouts.has(dropdown)) {
                clearTimeout(dropdownTimeouts.get(dropdown));
                dropdownTimeouts.delete(dropdown);
            }
            
            // Dropdown einblenden
            menu.classList.add('show');
        });
        
        // Bei Verlassen des Dropdowns mit Verzögerung ausblenden
        dropdown.addEventListener('mouseleave', function() {
            // Neuen Timeout setzen
            const timeout = setTimeout(() => {
                menu.classList.remove('show');
                dropdownTimeouts.delete(dropdown);
            }, delay);
            
            // Timeout speichern
            dropdownTimeouts.set(dropdown, timeout);
        });
        
        // Verhindert, dass das Dropdown beim Klick auf einen Menüpunkt verschwindet
        menu.addEventListener('click', function(e) {
            // Stoppt die Ausbreitung des Klick-Events
            // e.stopPropagation();
        });
    });
});

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Handle custom form validation styling
 */
function handleFormValidation() {
    // Add validation classes to inputs on blur/change
    const formInputs = document.querySelectorAll('.form-control');
    
    formInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.checkValidity()) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            } else if (this.value !== '') {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            }
        });
    });

    // Custom file input display
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileNameDisplay = this.nextElementSibling;
            if (fileNameDisplay && this.files.length > 0) {
                fileNameDisplay.textContent = this.files[0].name;
            }
        });
    });
}