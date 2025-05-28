from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor  
from enums.tipo_embalagem import TipoEmbalagem
from enums.tipo_atividade import TipoAtividade
from typing import List, Tuple
from datetime import datetime


class Embaladora(Equipamento):
    """
    Classe que representa uma Embaladora.
    Operação baseada em lotes de peso dentro de capacidade máxima.
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_gramas: int,
        lista_tipo_embalagem: List[TipoEmbalagem],
        numero_operadores: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.EMBALADORAS,
            setor=setor,
            numero_operadores=numero_operadores,
            status_ativo=True
        )

        self.capacidade_gramas = capacidade_gramas
        self.lista_tipo_embalagem = lista_tipo_embalagem

        # Ocupação temporal
        self.ocupacao: List[Tuple[datetime, datetime, TipoAtividade]] = []

    # ============================================
    # 🏗️ Validação de Capacidade de Lote
    # ============================================
    def validar_capacidade(self, gramas: int) -> bool:
        """
        Verifica se o peso está dentro da capacidade operacional da embaladora.
        """
        if gramas > self.capacidade_gramas:
            print(
                f"❌ Quantidade {gramas}g excede a capacidade máxima ({self.capacidade_gramas}g) da embaladora {self.nome}."
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
        Verifica se a embaladora está disponível no intervalo de tempo.
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
            f"\n📦 Capacidade por ciclo: {self.capacidade_gramas}g"
            f"\n🎯 Tipos de embalagem suportados: {[emb.name for emb in self.lista_tipo_embalagem]}"
            f"\n🗂️ Ocupações registradas: {len(self.ocupacao)}"
        )
