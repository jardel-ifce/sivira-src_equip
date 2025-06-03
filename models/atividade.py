from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enums.tipo_atividade import TipoAtividade
from enums.tipo_profissional import TipoProfissional
from enums.tipo_equipamento import TipoEquipamento


class Atividade(ABC):
    """
    🧱 Classe base para representar uma atividade de produção.
    Deve ser herdada e especializada conforme o tipo de tarefa.
    """

    def __init__(
        self,
        id: str,
        quantidade_produto: int,
        tipo_atividade: TipoAtividade,
        tipos_profissionais_permitidos: list[TipoProfissional],
        quantidade_funcionarios: int,
        equipamentos_elegiveis: dict[TipoEquipamento, int]
    ):
        self.id = id
        self.quantidade_produto = quantidade_produto
        self.tipo_atividade = tipo_atividade
        self.tipos_profissionais_permitidos = tipos_profissionais_permitidos
        self.quantidade_funcionarios = quantidade_funcionarios
        self.equipamentos_elegiveis = equipamentos_elegiveis

        self.duracao: timedelta | None = None
        self.inicio_real: datetime | None = None
        self.fim_real: datetime | None = None
        self.alocada: bool = False
        self.equipamentos_selecionados = []
        self.equipamento_alocado = None  # pode ser sobrescrito com lista
        self.tipo_ocupacao = None

    @property
    @abstractmethod
    def quantidade_por_tipo_equipamento(self) -> dict[TipoEquipamento, int]:
        """
        Define a quantidade de equipamentos necessários por tipo.
        Obrigatório implementar nas subclasses.
        """
        pass

    @abstractmethod
    def calcular_duracao(self):
        """
        Calcula a duração da atividade com base na quantidade de produto ou lógica interna.
        Obrigatório implementar nas subclasses.
        """
        pass

    def iniciar(self):
        if not self.alocada:
            raise Exception(f"❌ Atividade ID {self.id} não alocada ainda.")
        print(f"🚀 Atividade {self.id} iniciada às {self.inicio_real.strftime('%H:%M')}.")
