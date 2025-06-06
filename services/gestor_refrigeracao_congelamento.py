from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union
from models.equips.camara_refrigerada import CamaraRefrigerada
from models.equips.freezer import Freezer
from models.atividade_base import Atividade
from utils.conversores_ocupacao import gramas_para_caixas, gramas_para_niveis_tela
from utils.logger_factory import setup_logger
import unicodedata

# ❄️ Logger específico
logger = setup_logger('GestorRefrigeracaoCongelamento')

RefrigeradoresCongeladores = Union[CamaraRefrigerada, Freezer]

class GestorRefrigeracaoCongelamento:
    """
    ❄️ Gestor especializado no controle de câmaras de refrigeração/congelamento.
    Retorno padrão: (sucesso: bool, equipamento, inicio, fim)
    """

    def __init__(self, equipamentos: List[RefrigeradoresCongeladores]):
        self.equipamentos = equipamentos

    def _ordenar_por_fip(self, atividade: Atividade) -> List[RefrigeradoresCongeladores]:
        ordenadas = sorted(
            self.equipamentos,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        logger.info("📊 Ordem dos refrigeradores/congeladores por FIP (prioridade):")
        for m in ordenadas:
            fip = atividade.fips_equipamentos.get(m, 999)
            logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenadas

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        quantidade_produto: int
    ) -> Tuple[bool, Optional[RefrigeradoresCongeladores], Optional[datetime], Optional[datetime]]:
        """
        ❄️ Faz a alocação utilizando backward scheduling.
        Retorna (True, equipamento, inicio_real, fim_real) se sucesso.
        Caso contrário: (False, None, None, None)
        """
        duracao = atividade.duracao
        atividade.quantidade_produto = quantidade_produto

        equipamentos_ordenados = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for equipamento in equipamentos_ordenados:
                temperatura_desejada = self._obter_faixa_temperatura(atividade, equipamento)
                tipo_armazenamento = self._obter_tipo_armazenamento(atividade, equipamento)

                logger.info(
                    f"🌟 Tentando alocar Atividade {atividade.id} em {equipamento.nome} "
                    f"({quantidade_produto}g | {duracao}) entre "
                    f"{horario_inicio_tentativa.strftime('%H:%M')} e {horario_final_tentativa.strftime('%H:%M')} "
                    f"| Temp: {temperatura_desejada if temperatura_desejada is not None else 'N/A'}°C"
                )

                if tipo_armazenamento not in {"CAIXAS", "NIVEIS_TELA"}:
                    logger.warning(
                        f"⚠️ Tipo de armazenamento inválido ou ausente para {equipamento.nome}: {tipo_armazenamento}"
                    )
                    continue

                if tipo_armazenamento == "CAIXAS":
                    quantidade_ocupacao = gramas_para_caixas(quantidade_produto)
                    metodo_verificacao = "verificar_espaco_caixas"
                    metodo_ocupar = "ocupar_caixas"
                else:  # tipo_armazenamento == "NIVEIS_TELA"
                    quantidade_ocupacao = gramas_para_niveis_tela(quantidade_produto)
                    metodo_verificacao = "verificar_espaco_niveis"
                    metodo_ocupar = "ocupar_niveis"

                if temperatura_desejada is None:
                    logger.warning(f"⚠️ Temperatura desejada não definida para {equipamento.nome}.")
                    continue

                if not equipamento.verificar_compatibilidade_de_temperatura(
                    horario_inicio_tentativa, horario_final_tentativa, temperatura_desejada
                ):
                    continue

                if not equipamento.selecionar_faixa_temperatura(temperatura_desejada):
                    continue

                if not getattr(equipamento, metodo_verificacao)(
                    quantidade_ocupacao, horario_inicio_tentativa, horario_final_tentativa
                ):
                    continue

                sucesso = getattr(equipamento, metodo_ocupar)(
                    atividade_id=atividade.id,
                    quantidade=quantidade_ocupacao,
                    inicio=horario_inicio_tentativa,
                    fim=horario_final_tentativa
                )

                if sucesso:
                    atividade.equipamento_alocado = equipamento
                    atividade.equipamentos_selecionados = [equipamento]
                    atividade.alocada = True

                    logger.info(
                        f"✅ Atividade {atividade.id} alocada na {equipamento.nome} "
                        f"| {horario_inicio_tentativa.strftime('%H:%M')} → {horario_final_tentativa.strftime('%H:%M')} "
                        f"| Temp: {temperatura_desejada}°C"
                    )
                    return True, equipamento, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Nenhuma câmara pôde ser alocada para atividade {atividade.id} "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None



    def _obter_faixa_temperatura(self, atividade: Atividade, equipamento) -> Optional[int]:
        """
        🌡️ Busca no JSON a faixa de temperatura configurada para o equipamento específico.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = equipamento.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                
                logger.debug(f"🔎 Procurando faixa de temperatura para: '{nome_chave}'")
                logger.debug(f"🗂️ Chaves disponíveis: {list(atividade.configuracoes_equipamentos.keys())}")

                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "faixa_temperatura" in config:
                    faixa_temp = int(config["faixa_temperatura"])
                    logger.debug(f"✅ Faixa de temperatura encontrada para {nome_chave}: {faixa_temp}")
                    return faixa_temp
                else:
                    logger.debug(f"❌ Nenhuma faixa de temperatura definida para: '{nome_chave}'")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter faixa de temperatura para {equipamento.nome}: {e}")
        return None

    def _obter_tipo_armazenamento(self, atividade: Atividade, equipamento) -> Optional[str]:
        """
        📦 Busca no JSON o tipo de armazenamento (CAIXAS, NIVEIS_TELA, etc.) para o equipamento específico.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = equipamento.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                
                logger.debug(f"🔎 Procurando tipo de armazenamento para: '{nome_chave}'")
                logger.debug(f"🗂️ Chaves disponíveis: {list(atividade.configuracoes_equipamentos.keys())}")

                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "tipo_de_armazenamento" in config:
                    tipo = str(config["tipo_de_armazenamento"]).upper()
                    logger.debug(f"✅ Tipo de armazenamento encontrado para {nome_chave}: {tipo}")
                    return tipo
                else:
                    logger.debug(f"❌ Nenhum tipo de armazenamento definido para: '{nome_chave}'")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter tipo de armazenamento para {equipamento.nome}: {e}")
        return None


    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        for equipamento in self.equipamentos:
            equipamento.liberar_por_atividade(atividade_id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for equipamento in self.equipamentos:
            equipamento.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for equipamento in self.equipamentos:
            equipamento.liberar_todas_ocupacoes()

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        for equipamento in self.equipamentos:
            equipamento.liberar_intervalo(inicio, fim)

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Câmaras de Refrigeração/Congelamento")
        logger.info("==============================================")
        for equipamento in self.equipamentos:
            equipamento.mostrar_agenda()
