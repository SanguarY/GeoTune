def verbindungsanfragen(request):
    """Kontext-Prozessor für Verbindungsanfragen"""
    anzahl = 0
    if request.user.is_authenticated:
        anzahl = request.user.erhaltene_verbindungen.filter(status='angefragt').count()
    return {'anzahl_verbindungsanfragen': anzahl}