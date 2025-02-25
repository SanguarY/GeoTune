// Allgemeine JavaScript-Funktionen für GeoTune
document.addEventListener('DOMContentLoaded', function() {
    // Auto-Close für Bootstrap-Alerts nach 5 Sekunden
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});