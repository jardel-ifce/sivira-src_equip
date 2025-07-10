from datetime import datetime, timedelta
from typing import Optional, List
from models.equipamentos.equipamento import Equipamento  # Base comum dos equipamentos
from enums.funcionarios.tipo_profissional import TipoProfissional
from models.funcionarios.funcionario import Funcionario


class AtividadeSimulada:
    def __init__(
        self,
        id_atividade: int,
        nome: str,
        quantidade: float,
        duracao: timedelta,
        equipamentos_possiveis: List[Equipamento],
        tipos_profissionais: List[TipoProfissional],
        quantidade_funcionarios: int = 1,
        tempo_maximo_espera: timedelta = timedelta(0),
        predecessora: Optional[int] = None
    ):
        self.id_atividade = id_atividade
        self.nome = nome
        self.quantidade = quantidade
        self.duracao = duracao
        self.equipamentos_possiveis = equipamentos_possiveis
        self.tipos_profissionais = tipos_profissionais
        self.quantidade_funcionarios = quantidade_funcionarios
        self.tempo_maximo_espera = tempo_maximo_espera
        self.predecessora = predecessora

        # Campos de simulação
        self.equipamento_escolhido: Optional[Equipamento] = None
        self.inicio: Optional[datetime] = None
        self.fim: Optional[datetime] = None
        self.funcionarios: List[Funcionario] = []

    def alocar_equipamento(self, equipamento: Equipamento, inicio: datetime):
        self.equipamento_escolhido = equipamento
        self.inicio = inicio
        self.fim = inicio + self.duracao

    def definir_janela(self, inicio: datetime):
        self.inicio = inicio
        self.fim = inicio + self.duracao

    def resetar(self):
        self.equipamento_escolhido = None
        self.inicio = None
        self.fim = None
        self.funcionarios = []

    def to_dict(self):
        return {
            "id_atividade": self.id_atividade,
            "nome": self.nome,
            "quantidade": self.quantidade,
            "inicio": self.inicio.strftime('%H:%M') if self.inicio else None,
            "fim": self.fim.strftime('%H:%M') if self.fim else None,
            "equipamento": getattr(self.equipamento_escolhido, "nome", None),
            "funcionarios": [f.nome for f in self.funcionarios],
        }
