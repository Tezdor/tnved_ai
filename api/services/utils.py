def normalize_confidence(value):
    """
    Приводит уверенность всех моделей к процентам 0-100.
    """

    if value is None:
        return 0

    try:
        value = float(value)
    except (ValueError, TypeError):
        return 0

    # если модель вернула вероятность 0..1
    if 0 <= value <= 1:
        value *= 100

    return round(value)