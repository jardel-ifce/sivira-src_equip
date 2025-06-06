from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from models.equips.forno import Forno
from models.atividade_base import Atividade
from utils.conversores_ocupacao import gramas_para_niveis_tela
from utils.logger_factory import setup_logger
import unicodedata

# 🔥 Logger específico para o gestor de fornos
logger = setup_logger('GestorFornos')


class GestorFornos:
    """
    🔥 Gestor especializado no controle de fornos.
    ✔️ Utiliza Backward Scheduling com FIP.
    ✔️ Verifica ocupação, temperatura, vaporização e velocidade.
    ✔️ Lê os parâmetros via JSON.
    """

    def __init__(self, fornos: List[Forno]):
        self.fornos = fornos

    # ==========================================================
    # 🔥 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        quantidade_gramas: int
    ) -> Tuple[bool, Optional[Forno], Optional[datetime], Optional[datetime]]:
        """
        🔥 Faz a alocação backward considerando parâmetros técnicos e quantidade em gramas.

        Retorna:
        (sucesso, forno, inicio_real, fim_real)
        """

        duracao = atividade.duracao
        quantidade_niveis = self._obter_quantidade_niveis(quantidade_gramas)

        equipamentos_ordenados = sorted(
            self.fornos,
            key=lambda forno: atividade.fips_equipamentos.get(forno, 999)
        )

        horario_final_tentativa = fim

        while horario_final_tentativa - duracao >= inicio:
            horario_inicial_tentativa = horario_final_tentativa - duracao

            for forno in equipamentos_ordenados:
                temperatura = self._obter_temperatura_desejada(atividade, forno)
                vaporizacao = self._obter_vaporizacao_desejada(atividade, forno)
                velocidade = self._obter_velocidade_desejada(atividade, forno)

                if not forno.verificar_espaco_niveis(quantidade_niveis, horario_inicial_tentativa, horario_final_tentativa):
                    continue
                if not forno.verificar_compatibilidade_temperatura(horario_inicial_tentativa, horario_final_tentativa, temperatura):
                    continue
                if not forno.verificar_compatibilidade_vaporizacao(horario_inicial_tentativa, horario_final_tentativa, vaporizacao):
                    continue
                if not forno.verificar_compatibilidade_velocidade(horario_inicial_tentativa, horario_final_tentativa, velocidade):
                    continue

                forno.selecionar_temperatura(temperatura)
                forno.selecionar_vaporizacao(vaporizacao, forno.tem_vaporizacao)
                forno.selecionar_velocidade(velocidade, forno.tem_velocidade)

                sucesso = forno.ocupar_niveis(
                    atividade_id=atividade.id,
                    quantidade=quantidade_niveis,
                    inicio=horario_inicial_tentativa,
                    fim=horario_final_tentativa
                )

                if sucesso:
                    atividade.equipamento_alocado = forno
                    atividade.equipamentos_selecionados = [forno]
                    atividade.alocada = True

                    logger.info(
                        f"✅ Forno {forno.nome} alocado para Atividade {atividade.id} "
                        f"de {horario_inicial_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')} | "
                        f"Temp: {temperatura}°C | "
                        f"Vapor: {vaporizacao if vaporizacao is not None else '---'}s | "
                        f"Velocidade: {velocidade if velocidade is not None else '---'} m/s"
                    )
                    return True, forno, horario_inicial_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=5)

        logger.warning(
            f"❌ Nenhum forno disponível para alocar a atividade {atividade.id} "
            f"dentro da janela {inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    def _normalizar_nome(self, nome: str) -> str:
        nome_bruto = nome.lower().replace(" ", "_")
        return unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")

    def _obter_temperatura_desejada(self, atividade: Atividade, forno: Forno) -> Optional[int]:
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "faixa_temperatura" in config:
                return int(config["faixa_temperatura"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter temperatura para {forno.nome}: {e}")
        return None

    def _obter_vaporizacao_desejada(self, atividade: Atividade, forno: Forno) -> Optional[int]:
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "vaporizacao" in config:
                return int(config["vaporizacao"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter vaporização para {forno.nome}: {e}")
        return None

    def _obter_velocidade_desejada(self, atividade: Atividade, forno: Forno) -> Optional[int]:
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "velocidade_mps" in config:
                return int(config["velocidade_mps"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter velocidade para {forno.nome}: {e}")
        return None

    def _obter_quantidade_niveis(self, quantidade_gramas: int) -> int:
        """
        🔢 Converte a quantidade do produto (g) para níveis de tela.
        """
        return gramas_para_niveis_tela(quantidade_gramas)

    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        for forno in self.fornos:
            forno.liberar_por_atividade(atividade_id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for forno in self.fornos:
            forno.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for forno in self.fornos:
            forno.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda dos Fornos")
        logger.info("==============================================")
        for forno in self.fornos:
            forno.mostrar_agenda()
