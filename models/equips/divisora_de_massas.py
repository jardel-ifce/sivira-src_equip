from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_atividade import TipoAtividade
from typing import List, Tuple
from datetime import datetime


class DivisoraDeMassas(Equipamento):
    """
    Classe que representa uma divisora de massas com ou sem boleadora.
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self, 
        id: int, 
        nome: str, 
        setor: TipoSetor, 
        numero_operadores: int, 
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
        boleadora: bool,
        capacidade_divisao_unidades_por_segundo: int,
        capacidade_boleamento_unidades_por_segundo: int
    ):
        super().__init__(
            id=id, 
            nome=nome, 
            setor=setor, 
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.DIVISORAS_BOLEADORAS,
            status_ativo=True
        )

        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.boleadora = boleadora
        self.capacidade_divisao_unidades_por_segundo = capacidade_divisao_unidades_por_segundo
        self.capacidade_boleamento_unidades_por_segundo = capacidade_boleamento_unidades_por_segundo

        # Ocupações temporais
        self.ocupacao: List[Tuple[datetime, datetime, TipoAtividade]] = []

    # ============================================
    # 🏗️ Validação de Capacidade de Lote
    # ============================================
    def validar_capacidade(self, gramas: int) -> bool:
        """
        Verifica se a quantidade de gramas está dentro dos limites operacionais.
        """
        if gramas < self.capacidade_gramas_min:
            print(
                f"❌ Quantidade {gramas}g abaixo da capacidade mínima ({self.capacidade_gramas_min}g) da divisora {self.nome}."
            )
            return False

        if gramas > self.capacidade_gramas_max:
            print(
                f"❌ Quantidade {gramas}g excede a capacidade máxima ({self.capacidade_gramas_max}g) da divisora {self.nome}."
            )
            return False

        return True

    # ============================================
    # 🕑 Ocupação Temporal
    # ============================================
    def registrar_ocupacao(
        self, inicio: datetime, fim: datetime, atividade: TipoAtividade
    ):
        """
        Registra ocupação no intervalo de tempo especificado.
        """
        self.ocupacao.append((inicio, fim, atividade))
        print(
            f"🕑 {self.nome} | Ocupada de {inicio} até {fim} para {atividade.name}."
        )

    def liberar_ocupacoes_anteriores_a(self, momento: datetime):
        """
        Remove ocupações que terminaram antes do momento indicado.
        """
        ocupacoes_ativas = [
            (ini, fim, atv) for (ini, fim, atv) in self.ocupacao if fim > momento
        ]
        ocupacoes_liberadas = len(self.ocupacao) - len(ocupacoes_ativas)
        self.ocupacao = ocupacoes_ativas
        if ocupacoes_liberadas > 0:
            print(
                f"🟩 {self.nome} | Liberou {ocupacoes_liberadas} ocupações anteriores a {momento}."
            )

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        """
        Verifica se a divisora está disponível no intervalo de tempo.
        """
        for ocup_inicio, ocup_fim, _ in self.ocupacao:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                return False
        return True

    # ============================================
    # 🔍 Visualização e Status
    # ============================================
    def __str__(self):
        return (
            super().__str__() +
            f"\n🧠 Capacidade por lote: {self.capacidade_gramas_min}g até {self.capacidade_gramas_max}g"
            f"\n⚙️ Velocidade de divisão: {self.capacidade_divisao_unidades_por_segundo} unidades/segundo"
            f"\n⚙️ Velocidade de boleamento: {self.capacidade_boleamento_unidades_por_segundo} unidades/segundo"
            f"\n🔗 Possui boleadora: {'Sim' if self.boleadora else 'Não'}"
            f"\n🗂️ Ocupações registradas: {len(self.ocupacao)}"
        )
