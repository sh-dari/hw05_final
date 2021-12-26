from datetime import datetime


def year(request):
    today = datetime.today()
    return {
        'year': today.year,
    }
