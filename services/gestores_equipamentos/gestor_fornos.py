from datetime import datetime, timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING
from models.equipamentos.forno import Forno
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.producao.conversores_ocupacao import gramas_para_niveis_tela, unidades_para_niveis_tela
from utils.logs.logger_factory import setup_logger
from enums.producao.tipo_item import TipoItem
import unicodedata

# 🔥 Logger específico para o gestor de fornos
logger = setup_logger('GestorFornos')


class GestorFornos:
    """
    🔥 Gestor especializado no controle de fornos.
    Utiliza backward scheduling e FIP (Fatores de Importância de Prioridade).
    """

    def __init__(self, fornos: List[Forno]):
        self.fornos = fornos

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================    
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Forno]:
        ordenados = sorted(
            self.fornos,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        # logger.info("📊 Ordem dos fornos por FIP (prioridade):")
        # for m in ordenados:
        #     fip = atividade.fips_equipamentos.get(m, 999)
        #     logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenados    
    
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    def _normalizar_nome(self, nome: str) -> str:
        nome_bruto = nome.lower().replace(" ", "_")
        return unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")

    def _obter_temperatura_desejada(self, atividade: "AtividadeModular", forno: Forno) -> Optional[int]:
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "faixa_temperatura" in config:
                return int(config["faixa_temperatura"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter temperatura para {forno.nome}: {e}")
        return None

    def _obter_vaporizacao_desejada(self, atividade: "AtividadeModular", forno: Forno) -> Optional[int]:
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "vaporizacao" in config:
                return int(config["vaporizacao"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter vaporizacao para {forno.nome}: {e}")
        return None

    def _obter_velocidade_desejada(self, atividade: "AtividadeModular", forno: Forno) -> Optional[int]:
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "velocidade_mps" in config:
                return int(config["velocidade_mps"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter velocidade para {forno.nome}: {e}")
        return None

    def _obter_unidades_por_nivel(self, atividade: "AtividadeModular", forno: Forno) -> int:
        """
        Obtém a quantidade de unidades por nível do forno a partir da atividade.
        """
        try:
            chave = self._normalizar_nome(forno.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            if config and "unidades_por_nivel" in config:
                return int(config["unidades_por_nivel"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter unidades por nível para {forno.nome}: {e}")
        return None
    
    
    def _obter_quantidade_niveis(self, atividade: "AtividadeModular", quantidade: int, unidades_por_nivel: int) -> int:
        if atividade.tipo_item is TipoItem.SUBPRODUTO:
            quantidade_niveis = gramas_para_niveis_tela(quantidade)
        elif atividade.tipo_item is TipoItem.PRODUTO:
            quantidade_niveis = unidades_para_niveis_tela(quantidade, unidades_por_nivel)
        return quantidade_niveis
    
    # ==========================================================
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade: int
    ) -> Tuple[bool, Optional[Forno], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao

        fornos_ordenados = self._ordenar_por_fip(atividade)

        horario_final_tentativa = fim

        while horario_final_tentativa - duracao >= inicio:
            horario_inicial_tentativa = horario_final_tentativa - duracao

            for forno in fornos_ordenados:
                temperatura = self._obter_temperatura_desejada(atividade, forno)
                vaporizacao = self._obter_vaporizacao_desejada(atividade, forno)
                velocidade = self._obter_velocidade_desejada(atividade, forno)

                unidades_por_nivel = self._obter_unidades_por_nivel(atividade, forno)

                quantidade_niveis = self._obter_quantidade_niveis(atividade, quantidade, unidades_por_nivel)

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
                    ordem_id=atividade.ordem_id,
                    pedido_id=atividade.pedido_id,
                    atividade_id=atividade.id_atividade,
                    quantidade_niveis=quantidade_niveis,
                    inicio=horario_inicial_tentativa,
                    fim=horario_final_tentativa
                )

                if sucesso:
                    atividade.equipamento_alocado = forno
                    atividade.equipamentos_selecionados = [forno]
                    atividade.alocada = True

                    logger.info(
                        f"✅  {forno.nome} alocado para Atividade {atividade.id_atividade} | Níveis: {quantidade_niveis} | "
                        f"de {horario_inicial_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')} | "
                        f"Temp: {temperatura}°C | "
                        f"Vaporização segundos: {vaporizacao if vaporizacao is not None else '---'}s | "
                        f"Velocidade mps: {velocidade if velocidade is not None else '---'} m/s"
                    )
                    return True, forno, horario_inicial_tentativa, horario_final_tentativa
  
            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Nenhum forno disponível para alocar a atividade {atividade.id_atividade} para {quantidade_niveis}"
            f"dentro da janela {inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}."
        )
        return False, None, None, None


    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        for forno in self.fornos:
            forno.liberar_por_atividade(atividade_id=atividade.id_atividade, pedido_id=atividade.pedido_id, ordem_id=atividade.ordem_id)

    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for forno in self.fornos:
            forno.liberar_por_pedido(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for forno in self.fornos:
            forno.liberar_por_ordem(ordem_id=atividade.ordem_id)

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
