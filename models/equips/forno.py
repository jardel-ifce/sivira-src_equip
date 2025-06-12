from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_coccao import TipoCoccao
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logger_factory import setup_logger

logger = setup_logger('Forno')


class Forno(Equipamento):
    """
    🔥 Forno com controle de:
    - 🗂️ Ocupação por níveis
    - 🌡️ Temperatura
    - 💨 Vaporização (se aplicável)
    - 🚀 Velocidade (se aplicável)
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        nivel_tela_min: int,
        nivel_tela_max: int,
        faixa_temperatura_min: int,
        faixa_temperatura_max: int,
        setup_min: int,
        tipo_coccao: TipoCoccao,
        vaporizacao_seg_min: Optional[int] = None,
        vaporizacao_seg_max: Optional[int] = None,
        velocidade_mps_min: Optional[int] = None,
        velocidade_mps_max: Optional[int] = None,
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.FORNOS,
            setor=setor,
            numero_operadores=0,
            status_ativo=True,
        )

        # 🗂️ Ocupação por níveis
        self.nivel_tela_min = nivel_tela_min
        self.nivel_tela_max = nivel_tela_max
        self.capacidade_niveis_tela = nivel_tela_max
        self.ocupacao_niveis: List[Tuple[int, int, int, datetime, datetime]] = []  # (ordem_id, atividade_id, quantidade, início, fim)

        # 🌡️ Controle de temperatura
        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.temperatura_atual: Optional[int] = None

        # 💨 Controle de vaporização
        self.tem_vaporizacao = vaporizacao_seg_min is not None and vaporizacao_seg_max is not None
        self.faixa_vaporizacao_min = vaporizacao_seg_min
        self.faixa_vaporizacao_max = vaporizacao_seg_max
        self.vaporizacao_atual: Optional[int] = None

        # 🚀 Controle de velocidade
        self.tem_velocidade = velocidade_mps_min is not None and velocidade_mps_max is not None
        self.faixa_velocidade_min = velocidade_mps_min
        self.faixa_velocidade_max = velocidade_mps_max
        self.velocidade_atual: Optional[int] = None

        # 🔧 Configurações gerais
        self.setup_min = setup_min
        self.tipo_coccao = tipo_coccao

        # 🧾 Históricos de parâmetros aplicados por atividade
        self.historico_temperatura: List[Tuple[int, int, int, datetime, datetime, Optional[int]]] = []
        self.historico_vaporizacao: List[Tuple[int, int, int, datetime, datetime, Optional[int]]] = []
        self.historico_velocidade: List[Tuple[int, int, int, datetime, datetime, Optional[int]]] = []

    # ==========================================================
    # 🌡️ Temperatura
    # ==========================================================
    def selecionar_temperatura(self, temperatura: int) -> bool:
        if not self.faixa_temperatura_min <= temperatura <= self.faixa_temperatura_max:
            logger.warning(f"❌ Temperatura {temperatura}°C fora dos limites do forno {self.nome}.")
            return False
        self.temperatura_atual = temperatura
        return True

    def verificar_compatibilidade_temperatura(self, inicio: datetime, fim: datetime, temperatura: int) -> bool:
        conflitos = [temp for (_, _, _, ini, f, temp) in self.historico_temperatura if not (fim <= ini or inicio >= f)]
        return all(temp == temperatura for temp in conflitos) if conflitos else True

    # ==========================================================
    # 💨 Vaporização
    # ==========================================================
    def selecionar_vaporizacao(self, vaporizacao: Optional[int], atividade_exige: bool) -> bool:
        if not self.tem_vaporizacao or not atividade_exige:
            return True
        if vaporizacao is None:
            logger.warning(f"❌ Vaporização não definida para o forno {self.nome}, mas é obrigatória.")
            return False
        if not self.faixa_vaporizacao_min <= vaporizacao <= self.faixa_vaporizacao_max:
            logger.warning(f"❌ Vaporização {vaporizacao}s fora dos limites.")
            return False
        self.vaporizacao_atual = vaporizacao
        return True

    def verificar_compatibilidade_vaporizacao(self, inicio: datetime, fim: datetime, vaporizacao: Optional[int]) -> bool:
        if not self.tem_vaporizacao:
            return True
        conflitos = [vap for (_, _, _, ini, f, vap) in self.historico_vaporizacao if not (fim <= ini or inicio >= f)]
        return all(vap == vaporizacao for vap in conflitos) if conflitos else True

    # ==========================================================
    # 🚀 Velocidade
    # ==========================================================
    def selecionar_velocidade(self, velocidade: Optional[int], atividade_exige: bool) -> bool:
        if not self.tem_velocidade or not atividade_exige:
            return True
        if velocidade is None:
            logger.warning(f"❌ Velocidade não definida, mas é obrigatória.")
            return False
        if not self.faixa_velocidade_min <= velocidade <= self.faixa_velocidade_max:
            logger.warning(f"❌ Velocidade {velocidade} m/s fora dos limites.")
            return False
        self.velocidade_atual = velocidade
        return True

    def verificar_compatibilidade_velocidade(self, inicio: datetime, fim: datetime, velocidade: Optional[int]) -> bool:
        if not self.tem_velocidade:
            return True
        conflitos = [vel for (_, _, _, ini, f, vel) in self.historico_velocidade if not (fim <= ini or inicio >= f)]
        return all(vel == velocidade for vel in conflitos) if conflitos else True

    # ==========================================================
    # 🗂️ Ocupação
    # ==========================================================
    def verificar_espaco_niveis(self, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        ocupados = sum(qtd for (_, _, qtd, ini, f) in self.ocupacao_niveis if not (fim <= ini or inicio >= f))
        return (ocupados + quantidade) <= self.capacidade_niveis_tela

    def ocupar_niveis(self, ordem_id: int, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        if not self.verificar_espaco_niveis(quantidade, inicio, fim):
            return False
        self.ocupacao_niveis.append((ordem_id, atividade_id, quantidade, inicio, fim))
        self.historico_temperatura.append((ordem_id, atividade_id, quantidade, inicio, fim, self.temperatura_atual))
        if self.tem_vaporizacao:
            self.historico_vaporizacao.append((ordem_id, atividade_id, quantidade, inicio, fim, self.vaporizacao_atual))
        if self.tem_velocidade:
            self.historico_velocidade.append((ordem_id, atividade_id, quantidade, inicio, fim, self.velocidade_atual))
        
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_ordem(self, ordem_id: int):
        """
        ❌ Libera todas as ocupações relacionadas à ordem especificada.
        """
        antes = len(self.ocupacao_niveis)

        self.ocupacao_niveis = [
            (oid, aid, qtd, ini, fim)
            for (oid, aid, qtd, ini, fim) in self.ocupacao_niveis
            if oid != ordem_id
        ]
        self.historico_temperatura = [
            (oid, aid, qtd, ini, fim, t)
            for (oid, aid, qtd, ini, fim, t) in self.historico_temperatura
            if oid != ordem_id
        ]
        self.historico_vaporizacao = [
            (oid, aid, qtd, ini, fim, v)
            for (oid, aid, qtd, ini, fim, v) in self.historico_vaporizacao
            if oid != ordem_id
        ]
        self.historico_velocidade = [
            (oid, aid, qtd, ini, fim, v)
            for (oid, aid, qtd, ini, fim, v) in self.historico_velocidade
            if oid != ordem_id
        ]

        depois = len(self.ocupacao_niveis)
        if antes != depois:
            logger.info(f"🧼 Ocupações da ordem {ordem_id} removidas do forno {self.nome}.")
        self._resetar_se_vazio()

    def liberar_por_atividade(self, atividade_id: int, ordem_id: int):
        """
        ❌ Libera ocupações específicas de uma atividade dentro de uma ordem.
        """
        antes = len(self.ocupacao_niveis)

        self.ocupacao_niveis = [
            (oid, aid, qtd, ini, fim)
            for (oid, aid, qtd, ini, fim) in self.ocupacao_niveis
            if not (oid == ordem_id and aid == atividade_id)
        ]
        self.historico_temperatura = [
            (oid, aid, qtd, ini, fim, t)
            for (oid, aid, qtd, ini, fim, t) in self.historico_temperatura
            if not (oid == ordem_id and aid == atividade_id)
        ]
        self.historico_vaporizacao = [
            (oid, aid, qtd, ini, fim, v)
            for (oid, aid, qtd, ini, fim, v) in self.historico_vaporizacao
            if not (oid == ordem_id and aid == atividade_id)
        ]
        self.historico_velocidade = [
            (oid, aid, qtd, ini, fim, v)
            for (oid, aid, qtd, ini, fim, v) in self.historico_velocidade
            if not (oid == ordem_id and aid == atividade_id)
        ]

        depois = len(self.ocupacao_niveis)
        if antes != depois:
            logger.info(f"🧼 Ocupações da atividade {atividade_id} da ordem {ordem_id} removidas do forno {self.nome}.")
        self._resetar_se_vazio()

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        self.ocupacao_niveis = [(oid, aid, qtd, ini, fim) for (oid, aid, qtd, ini, fim) in self.ocupacao_niveis if fim > horario_atual]
        self.historico_temperatura = [(oid, aid, qtd, ini, fim, t) for (oid, aid, qtd, ini, fim, t) in self.historico_temperatura if fim > horario_atual]
        self.historico_vaporizacao = [(oid, aid, qtd, ini, fim, v) for (oid, aid, qtd, ini, fim, v) in self.historico_vaporizacao if fim > horario_atual]
        self.historico_velocidade = [(oid, aid, qtd, ini, fim, v) for (oid, aid, qtd, ini, fim, v) in self.historico_velocidade if fim > horario_atual]
        self._resetar_se_vazio()

    def liberar_todas_ocupacoes(self):
        self.ocupacao_niveis.clear()
        self.historico_temperatura.clear()
        self.historico_vaporizacao.clear()
        self.historico_velocidade.clear()
        self._resetar_parametros()

    def _resetar_se_vazio(self):
        if not self.ocupacao_niveis:
            self._resetar_parametros()

    def _resetar_parametros(self):
        self.temperatura_atual = None
        self.vaporizacao_atual = None
        self.velocidade_atual = None

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda do Forno {self.nome}")
        logger.info("==============================================")

        if not self.ocupacao_niveis:
            logger.info("🔹 Nenhuma ocupação.")
            return

        for (ordem_id, atividade_id, quantidade, inicio, fim) in self.ocupacao_niveis:
            temp = next((t for (oid, aid, qtd, ini, f, t) in self.historico_temperatura
                         if aid == atividade_id and ini == inicio and f == fim and oid == ordem_id), None)
            vap = next((v for (oid, aid, qtd, ini, f, v) in self.historico_vaporizacao
                        if aid == atividade_id and ini == inicio and f == fim and oid == ordem_id), None) if self.tem_vaporizacao else None
            vel = next((v for (oid, aid, qtd, ini, f, v) in self.historico_velocidade
                        if aid == atividade_id and ini == inicio and f == fim and oid == ordem_id), None) if self.tem_velocidade else None

            logger.info(
                f"🔥 Atividade {atividade_id} | Ordem {ordem_id} | {quantidade} níveis | "
                f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | "
                f"🌡️ {temp if temp is not None else '---'}°C | "
                f"💨 {vap if vap is not None else '---'}s | "
                f"🚀 {vel if vel is not None else '---'} m/s"
            )
