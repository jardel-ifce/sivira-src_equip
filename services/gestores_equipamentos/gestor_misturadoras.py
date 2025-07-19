import unicodedata
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, TYPE_CHECKING
from models.equipamentos.masseira import Masseira
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from enums.equipamentos.tipo_mistura import TipoMistura
from utils.logs.logger_factory import setup_logger

logger = setup_logger('GestorMisturadoras')


class GestorMisturadoras:
    def __init__(self, masseiras: List[Masseira]):
        self.masseiras = masseiras

    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Masseira]:
        return sorted(self.masseiras, key=lambda m: atividade.fips_equipamentos.get(m, 999))

    def _obter_velocidades_para_masseira(self, atividade: "AtividadeModular", masseira: Masseira) -> List[TipoVelocidade]:
        chave = self._normalizar_nome(masseira.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave, {})
        velocidades_raw = config.get("velocidade", [])
        if isinstance(velocidades_raw, str):
            velocidades_raw = [velocidades_raw]
        velocidades = []
        for v in velocidades_raw:
            try:
                velocidades.append(TipoVelocidade[v.strip().upper()])
            except KeyError:
                logger.warning(f"⚠️ Velocidade inválida: '{v}' para masseira {masseira.nome}")
        if not velocidades:
            logger.warning(f"⚠️ Nenhuma velocidade definida para masseira {masseira.nome}")
        return velocidades

    def _obter_tipo_mistura_para_masseira(self, atividade: "AtividadeModular", masseira: Masseira) -> Optional[TipoMistura]:
        chave = self._normalizar_nome(masseira.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave, {})
        raw = config.get("tipo_mistura")
        if raw is None:
            logger.warning(f"⚠️ Tipo de mistura não definido para masseira {masseira.nome}")
            return None
        if isinstance(raw, list):
            raw = raw[0] if raw else None
        if raw is None:
            return None
        try:
            return TipoMistura[raw.strip().upper()]
        except KeyError:
            logger.warning(f"⚠️ Tipo de mistura inválido: '{raw}' para masseira {masseira.nome}")
            return None

    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        return (
            unicodedata.normalize("NFKD", nome.lower())
            .encode("ASCII", "ignore")
            .decode()
            .replace(" ", "_")
        )

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade: float,
        **kwargs
    ) -> Tuple[bool, Optional[Masseira], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        horario_final_tentativa = fim
        masseiras_ordenadas = self._ordenar_por_fip(atividade)

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            masseiras_disponiveis = [
                m for m in masseiras_ordenadas
                if m.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa, atividade_id=atividade.id_atividade)
            ]

            capacidade_total = sum(m.capacidade_gramas_max for m in masseiras_disponiveis)
            if capacidade_total >= quantidade:
                restante = quantidade
                equipamentos_usados = []

                for masseira in masseiras_disponiveis:
                    capacidade = masseira.capacidade_gramas_max
                    alocar = min(restante, capacidade)

                    velocidades = self._obter_velocidades_para_masseira(atividade, masseira)
                    tipo_mistura = self._obter_tipo_mistura_para_masseira(atividade, masseira)

                    sucesso = masseira.ocupar(
                        ordem_id=atividade.ordem_id,
                        pedido_id=atividade.pedido_id,
                        atividade_id=atividade.id_atividade,
                        quantidade_gramas=alocar,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        velocidades=velocidades,
                        tipo_mistura=tipo_mistura
                    )

                    if sucesso:
                        equipamentos_usados.append(masseira)
                        restante -= alocar

                    if restante <= 0:
                        atividade.equipamentos_selecionados.extend(equipamentos_usados)
                        atividade.inicio_planejado = horario_inicio_tentativa
                        atividade.fim_planejado = horario_final_tentativa
                        atividade.alocada = True
                        logger.info(
                            f"✅ Atividade {atividade.id_atividade} da ordem {atividade.ordem_id} alocada em "
                            f"{len(equipamentos_usados)} masseira(s) | Quantidade {quantidade} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}"
                        )
                        return True, equipamentos_usados[0], horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {atividade.id_atividade} da ordem {atividade.ordem_id} não pôde ser alocada "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        for masseira in self.masseiras:
            masseira.liberar_por_atividade(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id, atividade_id=atividade.id_atividade)

    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for masseira in self.masseiras:
            masseira.liberar_por_pedido(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for masseira in self.masseiras:
            masseira.liberar_por_ordem(ordem_id=atividade.ordem_id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for masseira in self.masseiras:
            masseira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for masseira in self.masseiras:
            masseira.ocupacoes.clear()

    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Masseiras")
        logger.info("==============================================")
        for masseira in self.masseiras:
            masseira.mostrar_agenda()
