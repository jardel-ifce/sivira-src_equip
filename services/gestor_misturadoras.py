import unicodedata
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from models.equips.masseira import Masseira
from models.atividade_base import Atividade
from enums.tipo_velocidade import TipoVelocidade
from enums.tipo_mistura import TipoMistura
from utils.logger_factory import setup_logger

logger = setup_logger('GestorMisturadoras')


class GestorMisturadoras:
    def __init__(self, masseiras: List[Masseira]):
        self.masseiras = masseiras

    def _ordenar_por_fip(self, atividade: Atividade) -> List[Masseira]:
        ordenadas = sorted(
            self.masseiras,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        logger.info("📊 Ordem das masseiras por FIP (prioridade):")
        for m in ordenadas:
            fip = atividade.fips_equipamentos.get(m, 999)
            logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenadas

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        quantidade: float
    ) -> Tuple[bool, Optional[Masseira], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        horario_final_tentativa = fim

        logger.info(
            f"🎯 Tentando alocar atividade {atividade.id} "
            f"(duração: {duracao}, quantidade: {quantidade}g) "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

        masseiras_ordenadas = self._ordenar_por_fip(atividade)

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            # 🔁 Primeiro tenta dividir entre masseiras disponíveis
            masseiras_disponiveis = [
                m for m in masseiras_ordenadas
                if m.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa)
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
                        quantidade_gramas=alocar,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        atividade_id=atividade.id,
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
                            f"✅ Atividade {atividade.id} dividida em {len(equipamentos_usados)} masseira(s) "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}"
                        )
                        return True, equipamentos_usados[0], horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=5)

        logger.warning(
            f"❌ Atividade {atividade.id} não pôde ser alocada em nenhuma masseira "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

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

    def obter_masseira_por_id(self, id: int) -> Optional[Masseira]:
        for masseira in self.masseiras:
            if masseira.id == id:
                return masseira
        return None

    def _obter_velocidades_para_masseira(self, atividade: Atividade, masseira: Masseira) -> List[TipoVelocidade]:
        chave = self._normalizar_nome(masseira.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        velocidades_raw = config.get("velocidade", []) if config else []

        if isinstance(velocidades_raw, str):
            velocidades_raw = [velocidades_raw]

        velocidades = []
        for v in velocidades_raw:
            try:
                velocidades.append(TipoVelocidade[v])
            except Exception:
                logger.warning(f"⚠️ Velocidade inválida: '{v}' para masseira {chave}")

        if not velocidades:
            logger.warning(f"⚠️ Nenhuma velocidade definida para masseira {chave}")
        else:
            logger.info(f"⚙️ Velocidades para {masseira.nome}: {[v.name for v in velocidades]}")

        return velocidades

    def _obter_tipo_mistura_para_masseira(self, atividade: Atividade, masseira: Masseira) -> Optional[TipoMistura]:
        chave = self._normalizar_nome(masseira.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)

        if not config or not config.get("tipo_mistura"):
            logger.warning(f"⚠️ Tipo de mistura não definido para masseira {chave}")
            return None

        try:
            tipo = TipoMistura[config["tipo_mistura"]]
            logger.info(f"⚙️ Tipo de mistura para {masseira.nome}: {tipo.name}")
            return tipo
        except Exception:
            logger.warning(f"⚠️ Tipo de mistura inválido: '{config['tipo_mistura']}' para masseira {chave}")
            return None

    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        return unicodedata.normalize("NFKD", nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")
