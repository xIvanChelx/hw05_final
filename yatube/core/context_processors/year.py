from datetime import date

today = date.today()


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': today.year,
    }
