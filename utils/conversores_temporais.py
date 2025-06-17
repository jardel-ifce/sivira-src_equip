from datetime import timedelta

def converter_para_timedelta(texto: str) -> timedelta:
    """
    Converte string "HH:MM" ou "HH:MM:SS" para timedelta.
    """
    partes = texto.strip().split(":")
    horas, minutos, segundos = 0, 0, 0

    if len(partes) == 2:
        horas, minutos = map(int, partes)
    elif len(partes) == 3:
        horas, minutos, segundos = map(int, partes)
    else:
        raise ValueError(f"Formato inválido para tempo: '{texto}'")

    return timedelta(hours=horas, minutes=minutos, seconds=segundos)
