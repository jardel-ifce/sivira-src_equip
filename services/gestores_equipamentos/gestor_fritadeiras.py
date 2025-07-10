from datetime import datetime, timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING
from models.equipamentos.fritadeira import Fritadeira
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logs.logger_factory import setup_logger
import unicodedata

# 🍟 Logger exclusivo para o gestor de fritadeiras
logger = setup_logger('GestorFritadeiras')


class GestorFritadeiras:
    """
    🍟 Gestor especializado no controle de fritadeiras.
    Utiliza backward scheduling e FIP (Fatores de Importância de Prioridade).
    Utiliza parâmetros de configuração via JSON para frações e temperatura.
    """

    def __init__(self, fritadeiras: List[Fritadeira]):
        self.fritadeiras = fritadeiras

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================  
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Fritadeira]:
        return sorted(
            self.fritadeiras,
            key=lambda f: atividade.fips_equipamentos.get(f, 999)
        )
    
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    def _normalizar_nome(self, nome: str) -> str:
        nome_bruto = nome.lower().replace(" ", "_")
        return unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")

    def _obter_fracoes_necessarias(self, atividade: "AtividadeModular", fritadeira: Fritadeira) -> Optional[int]:
        try:
            chave = self._normalizar_nome(fritadeira.nome)
            config = atividade.configuracoes_equipamentos.get(chave, {})
            return int(config.get("fracoes_necessarias", 0))
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter quantidade de frações para {fritadeira.nome}: {e}")
            return None

    def _obter_temperatura(self, atividade: "AtividadeModular", fritadeira: Fritadeira) -> Optional[int]:
        try:
            chave = self._normalizar_nome(fritadeira.nome)
            config = atividade.configuracoes_equipamentos.get(chave, {})
            return int(config.get("temperatura", 0))
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter temperatura para {fritadeira.nome}: {e}")
            return None

    # ==========================================================
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular"
    ) -> Tuple[bool, Optional[Fritadeira], Optional[datetime], Optional[datetime]]:
       
        duracao = atividade.duracao
        equipamentos_ordenados = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim

        while horario_final_tentativa - duracao >= inicio:
            horario_inicial_tentativa = horario_final_tentativa - duracao

            for fritadeira in equipamentos_ordenados:
                temperatura = self._obter_temperatura(atividade, fritadeira)
                quantidade_fracoes = self._obter_fracoes_necessarias(atividade, fritadeira)

                if not temperatura or not quantidade_fracoes:
                    continue

                sucesso = fritadeira.ocupar(
                    ordem_id=atividade.ordem_id,
                    pedido_id=atividade.pedido_id,
                    atividade_id=atividade.id,
                    quantidade_fracoes=quantidade_fracoes,
                    inicio=horario_inicial_tentativa,
                    fim=horario_final_tentativa,
                    temperatura=temperatura
                )
                if sucesso:
                    atividade.equipamento_alocado = fritadeira
                    atividade.equipamentos_selecionados = [fritadeira]
                    atividade.alocada = True

                    logger.info(
                        f"✅ Fritadeira {fritadeira.nome} alocada para Atividade {atividade.id} de "
                        f"{horario_inicial_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')} | "
                        f"Temp: {temperatura}°C | Frações: {quantidade_fracoes}"
                    )
                    return True, fritadeira, horario_inicial_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Nenhuma fritadeira disponível para a atividade {atividade.id} "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        for fritadeira in self.fritadeiras:
            fritadeira.liberar_por_atividade(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id, atividade_id=atividade.id)
                
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for fritadeira in self.fritadeiras:
            fritadeira.liberar_por_pedido(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for fritadeira in self.fritadeiras:
            fritadeira.liberar_por_ordem(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id, atividade_id=atividade.id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for fritadeira in self.fritadeiras:
            fritadeira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for fritadeira in self.fritadeiras:
            fritadeira.fracoes_ocupadas.clear()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Fritadeiras")
        logger.info("==============================================")
        for fritadeira in self.fritadeiras:
            fritadeira.mostrar_agenda()
