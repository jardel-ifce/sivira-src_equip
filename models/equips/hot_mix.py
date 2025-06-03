from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_velocidade import TipoVelocidade
from enums.tipo_pressao_chama import TipoPressaoChama
from enums.tipo_setor import TipoSetor
from enums.tipo_chama import TipoChama
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logger_factory import setup_logger


# 🔥 Logger
logger = setup_logger('HotMix')


class HotMix(Equipamento):
    """
    🍳 Equipamento HotMix — Misturadora com Cocção.
    ✔️ Ocupação exclusiva por atividade.
    ✔️ Controle de velocidade, chamas múltiplas e pressão de chama.
    ✔️ Registro de históricos por atividade.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
        velocidades_suportadas: List[TipoVelocidade],
        chamas_suportadas: List[TipoChama],
        pressao_chamas_suportadas: List[TipoPressaoChama]
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.MISTURADORAS_COM_COCCAO,
            setor=setor,
            numero_operadores=numero_operadores,
            status_ativo=True,
        )

        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.velocidades_suportadas = velocidades_suportadas
        self.chamas_suportadas = chamas_suportadas
        self.pressao_chamas_suportadas = pressao_chamas_suportadas

        self.velocidade_atual: Optional[TipoVelocidade] = None
        self.chama_atual: Optional[List[TipoChama]] = None
        self.pressao_chama_atual: Optional[List[TipoPressaoChama]] = None

        self.ocupacoes: List[Tuple[int, int, int, datetime, datetime]] = []
        self.historico_chama: List[Tuple[int, datetime, datetime, List[TipoChama]]] = []
        self.historico_velocidade: List[Tuple[int, datetime, datetime, TipoVelocidade]] = []
        self.historico_pressao_chama: List[Tuple[int, datetime, datetime, List[TipoPressaoChama]]] = []

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def validar_capacidade(self, quantidade: int) -> bool:
        return self.capacidade_gramas_min <= quantidade <= self.capacidade_gramas_max

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for _, _, _, ocup_ini, ocup_fim in self.ocupacoes:
            if not (fim <= ocup_ini or inicio >= ocup_fim):
                return False
        return True

    # ==========================================================
    # ⚙️ Configuração de Parâmetros
    # ==========================================================
    def configurar_velocidade(self, velocidade: TipoVelocidade) -> bool:
        if velocidade in self.velocidades_suportadas:
            self.velocidade_atual = velocidade
            logger.info(f"⚙️ {self.nome} | Velocidade ajustada para {velocidade.name}.")
            return True
        logger.error(f"❌ Velocidade {velocidade.name} não suportada.")
        return False

    def verificar_chamas_suportadas(self, chamas: List[TipoChama]) -> bool:
        return all(c in self.chamas_suportadas for c in chamas)

    def verificar_pressoes_suportadas(self, pressoes: List[TipoPressaoChama]) -> bool:
        return all(p in self.pressao_chamas_suportadas for p in pressoes)

    # ==========================================================
    # 🏗️ Ocupação
    # ==========================================================
    def ocupar(
        self,
        ocupacao_id: int,
        atividade_id: int,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
        chamas: List[TipoChama],
        pressao_chamas: List[TipoPressaoChama]
    ) -> bool:
        if not self.validar_capacidade(quantidade):
            logger.error(f"❌ {self.nome} | {quantidade}g fora dos limites.")
            return False
        if not self.esta_disponivel(inicio, fim):
            logger.warning(f"❌ {self.nome} | Ocupada de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}.")
            return False
        if not self.verificar_chamas_suportadas(chamas):
            logger.error(f"❌ Algumas chamas não são suportadas por {self.nome}.")
            return False
        if not self.verificar_pressoes_suportadas(pressao_chamas):
            logger.error(f"❌ Algumas pressões de chama não são suportadas por {self.nome}.")
            return False
        if self.velocidade_atual is None:
            logger.error(f"❌ Velocidade não configurada antes da ocupação.")
            return False

        self.chama_atual = chamas
        self.pressao_chama_atual = pressao_chamas

        self.ocupacoes.append((ocupacao_id, atividade_id, quantidade, inicio, fim))
        self.historico_chama.append((atividade_id, inicio, fim, chamas))
        self.historico_velocidade.append((atividade_id, inicio, fim, self.velocidade_atual))
        self.historico_pressao_chama.append((atividade_id, inicio, fim, pressao_chamas))

        logger.info(
            f"🍳 {self.nome} | Ocupada por atividade {atividade_id} com {quantidade}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        self.ocupacoes = [o for o in self.ocupacoes if o[4] > horario_atual]
        self.historico_chama = [h for h in self.historico_chama if h[2] > horario_atual]
        self.historico_velocidade = [h for h in self.historico_velocidade if h[2] > horario_atual]
        self.historico_pressao_chama = [h for h in self.historico_pressao_chama if h[2] > horario_atual]
        if not self.ocupacoes:
            self.velocidade_atual = None
            self.chama_atual = None
            self.pressao_chama_atual = None

    def liberar_por_atividade(self, atividade_id: int):
        self.ocupacoes = [o for o in self.ocupacoes if o[1] != atividade_id]
        self.historico_chama = [h for h in self.historico_chama if h[0] != atividade_id]
        self.historico_velocidade = [h for h in self.historico_velocidade if h[0] != atividade_id]
        self.historico_pressao_chama = [h for h in self.historico_pressao_chama if h[0] != atividade_id]
        if not self.ocupacoes:
            self.velocidade_atual = None
            self.chama_atual = None
            self.pressao_chama_atual = None

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda da HotMix {self.nome}")
        logger.info("==============================================")
        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return
        for (oid, aid, qtd, ini, fim) in self.ocupacoes:
            logger.info(
                f"🔸 Ocupação {oid}: Atividade {aid} | {qtd}g | "
                f"Início: {ini.strftime('%H:%M')} | Fim: {fim.strftime('%H:%M')} | "
                f"Velocidade: {self.velocidade_atual.name if self.velocidade_atual else 'Não definida'} | "
                f"Chamas: {[c.name for c in self.chama_atual] if self.chama_atual else 'Não definida'} | "
                f"Pressões: {[p.name for p in self.pressao_chama_atual] if self.pressao_chama_atual else 'Não definida'}"
            )

    # ==========================================================
    # 🔄 Reset Total
    # ==========================================================
    def resetar(self):
        self.velocidade_atual = None
        self.chama_atual = None
        self.pressao_chama_atual = None
        self.ocupacoes.clear()
        self.historico_chama.clear()
        self.historico_velocidade.clear()
        self.historico_pressao_chama.clear()
        logger.info(f"🔄 {self.nome} resetada completamente.")

    # ==========================================================
    # 📜 Representação
    # ==========================================================
    def __str__(self):
        return (
            super().__str__() +
            f"\n📦 Capacidade: {self.capacidade_gramas_min}g a {self.capacidade_gramas_max}g" +
            f"\n⚙️ Velocidade atual: {self.velocidade_atual.name if self.velocidade_atual else 'Não definida'}" +
            f"\n📅 Ocupações: {len(self.ocupacoes)} registradas."
        )
