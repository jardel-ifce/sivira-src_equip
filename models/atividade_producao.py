from dataclasses import dataclass
from datetime import timedelta
from enums.tipo_equipamento import TipoEquipamento

@dataclass
class AtividadeProducao:
    """
    Representa uma atividade de produção que exige um equipamento específico
    e tem tempos de execução distintos conforme a quantidade produzida.
    """
    nome: str
    equipamento_necessario: TipoEquipamento
    tempos_por_faixa: dict[tuple[int, int], timedelta]

    def tempo_para_quantidade(self, quantidade: int) -> timedelta:
        """
        Retorna o tempo de execução da atividade conforme a faixa de quantidade.
        Exemplo: 30-240 unidades → 3 min
        """
        for (minimo, maximo), tempo in self.tempos_por_faixa.items():
            if minimo <= quantidade <= maximo:
                return tempo
        raise ValueError(
            f"Quantidade {quantidade} fora das faixas definidas para a atividade '{self.nome}'."
        )
