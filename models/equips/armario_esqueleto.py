from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_atividade import TipoAtividade
from typing import List, Tuple
from datetime import datetime
from utils.logger_factory import setup_logger


# 🏭 Logger específico para o Armário Esqueleto
logger = setup_logger('Armário Esqueleto')

class ArmarioEsqueleto(Equipamento):
    """
    Classe que representa um Armário Esqueleto.
    A ocupação é feita exclusivamente por níveis de tela.
    A conversão de peso (gramas) para níveis de tela deve ser feita na atividade.
    """

    # =============================================
    # 🔧 Inicialização
    # =============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        nivel_tela_min: int,
        nivel_tela_max: int,
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.ARMARIOS_PARA_FERMENTACAO,
            setor=setor,
            numero_operadores=0,
            status_ativo=True,
        )

        self.nivel_tela_max = nivel_tela_max
        self.nivel_tela_min = nivel_tela_min
        self.nivel_tela_atual = 0
        # 📦 Ocupações: (ocupacao_id, atividade_id, quantidade, inicio, fim)
        self.ocupacao_niveis: List[Tuple[int, int, int, datetime, datetime]] = []

     # ==========================================================
    # 🗂️ Ocupação por Níveis de Tela
    # ==========================================================
    def verificar_espaco_niveis(self, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        ocupadas = sum(
            qtd for (_, _, qtd, ini, f) in self.ocupacao_niveis
            if not (fim <= ini or inicio >= f)
        )
        return (ocupadas + quantidade) <= self.nivel_tela_max

    def ocupar_niveis(self, ocupacao_id: int, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        if not self.verificar_espaco_niveis(quantidade, inicio, fim):
            return False

        self.ocupacao_niveis.append((ocupacao_id, atividade_id, quantidade, inicio, fim))
        return True
     # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        self.ocupacao_niveis = [
            (oid, aid, qtd, ini, fim) for (oid, aid, qtd, ini, fim) in self.ocupacao_niveis if aid != atividade_id
        ]
        self.ocupacao_caixas = [
            (oid, aid, qtd, ini, fim) for (oid, aid, qtd, ini, fim) in self.ocupacao_caixas if aid != atividade_id
        ]

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        self.ocupacao_niveis = [
            (oid, aid, qtd, ini, fim) for (oid, aid, qtd, ini, fim) in self.ocupacao_niveis if fim > horario_atual
        ]
    
    def liberar_todas_ocupacoes(self):
        self.ocupacao_niveis.clear()
       

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        self.ocupacao_niveis = [
            (oid, aid, qtd, ini, f) for (oid, aid, qtd, ini, f) in self.ocupacao_niveis
            if not (ini >= inicio and f <= fim)
        ]

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info(f"==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info(f"==============================================")


        for (oid, aid, qtd, ini, fim) in self.ocupacao_niveis:
            logger.info(
                f"🗂️ Ocupação {oid}: Atividade {aid} | {qtd} níveis | "
                f"Início: {ini.strftime('%H:%M')} | Fim: {fim.strftime('%H:%M')}"
            )

    # =============================================
    # 🔍 Status e Visualização
    # =============================================
    def __str__(self):
        return (
            super().__str__() +
            f"\n🗂️ Níveis de Tela Ocupados: {self.nivel_tela_atual}/{self.nivel_tela_max}" +
            f"\n🧠 Níveis Disponíveis: {self.niveis_disponiveis()}" +
            f"\n🟦 Status: {'Ocupado' if self.nivel_tela_atual > 0 else 'Disponível'}"
        )
