from datetime import timedelta
from typing import List, Tuple, Optional

class FaixaTempo:
    def __init__(self, faixas: List[Tuple[int, int, int]]):
        self.faixas = sorted(faixas, key=lambda f: f[0])

    def tempo_para(self, peso_gramas: int) -> Optional[timedelta]:
        for peso_min, peso_max, tempo_minutos in self.faixas:
            if peso_min <= peso_gramas <= peso_max:
                return timedelta(minutes=tempo_minutos)
        return None
