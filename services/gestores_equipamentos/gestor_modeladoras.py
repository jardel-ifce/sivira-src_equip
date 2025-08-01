from datetime import datetime, timedelta
from typing import Union
from typing import List, Optional, Tuple, TYPE_CHECKING
from models.equipamentos.modeladora_de_paes import ModeladoraDePaes
from models.equipamentos.modeladora_de_salgados import ModeladoraDeSalgados
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular 
from utils.logs.logger_factory import setup_logger
import unicodedata

logger = setup_logger("GestorModeladoras")

ItensModelados = Union[ModeladoraDePaes, ModeladoraDeSalgados]

class GestorModeladoras:
    """
    🥖 Gestor responsável pela alocação e controle de Modeladoras de Pães.
    
    Funcionalidades:
    - Modeladoras sempre disponíveis (sem ocupação exclusiva)
    - Prioriza equipamentos com menor FIP
    - Registro simples para controle e histórico
    - Alocação direta no horário especificado
    """

    def __init__(self, modeladoras: List[ItensModelados]):
        self.modeladoras = modeladoras

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[ItensModelados]:
        """Ordena modeladoras por fator de importância de prioridade."""
        ordenadas = sorted(
            self.modeladoras,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        return ordenadas

    # ==========================================================
    # 🔍 Utilitários
    # ==========================================================
    def _obter_capacidade_unidade_por_minuto_explicita_do_json(self, atividade: "AtividadeModular") -> Optional[float]:
        """
        🔍 Verifica se há um valor explícito de 'capacidade_unidade_por_minuto' no JSON da atividade
        para alguma chave que contenha 'modeladora' no nome. Se houver, retorna esse valor.
        """
        try:
            config = atividade.configuracoes_equipamentos or {}
            for chave, conteudo in config.items():
                chave_normalizada = unicodedata.normalize("NFKD", chave).encode("ASCII", "ignore").decode("utf-8").lower()
                if "modeladora" in chave_normalizada:
                    capacidade_unidades = conteudo.get("capacidade_unidade_por_minuto")
                    if capacidade_unidades is not None:
                        logger.info(
                            f"📦 JSON da atividade {atividade.id_atividade} define capacidade_unidade_por_minuto = {capacidade_unidades} "
                            f"unidades/min para o equipamento '{chave}'"
                        )
                        return capacidade_unidades
            
            logger.debug(f"ℹ️ Nenhuma capacidade_unidade_por_minuto definida no JSON da atividade {atividade.id_atividade}.")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar capacidade_unidade_por_minuto no JSON da atividade: {e}")
            return None

    def _obter_ids_atividade(self, atividade: "AtividadeModular") -> Tuple[int, int, int, int]:
        """
        Extrai os IDs da atividade de forma consistente.
        Retorna: (id_ordem, id_pedido, id_atividade, id_item)
        """
        id_ordem = getattr(atividade, 'id_ordem', None) or getattr(atividade, 'ordem_id', 0)
        id_pedido = getattr(atividade, 'id_pedido', None) or getattr(atividade, 'pedido_id', 0)
        id_atividade = getattr(atividade, 'id_atividade', 0)
        id_item = getattr(atividade, 'id_item', 0)
        
        return id_ordem, id_pedido, id_atividade, id_item

    # ==========================================================
    # 🎯 Alocação Simples (Sempre Disponível)
    # ==========================================================    
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_unidades: int
    ) -> Tuple[bool, Optional[ItensModelados], Optional[datetime], Optional[datetime]]:
        """
        Aloca uma atividade nas modeladoras (sempre disponíveis).
        Usa ordenação por FIP mas não verifica disponibilidade.
        
        Args:
            inicio: Horário de início desejado
            fim: Horário de fim desejado
            atividade: Atividade a ser alocada
            quantidade_unidades: Quantidade de unidades a produzir
            
        Returns:
            Tuple[sucesso, modeladora_usada, inicio_real, fim_real]
        """
        modeladoras_ordenadas = self._ordenar_por_fip(atividade)
        
        # Obter IDs da atividade de forma consistente
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)

        if quantidade_unidades <= 0:
            logger.warning(f"❌ Quantidade inválida para atividade {id_atividade}: {quantidade_unidades}")
            return False, None, None, None

        if not modeladoras_ordenadas:
            logger.warning(f"❌ Nenhuma modeladora disponível para atividade {id_atividade}")
            return False, None, None, None

        # Usa a primeira modeladora na ordem de FIP (sempre disponível)
        modeladora_selecionada = modeladoras_ordenadas[0]
        
        sucesso = modeladora_selecionada.ocupar(
            id_ordem=id_ordem,
            id_pedido=id_pedido,
            id_atividade=id_atividade,
            id_item=id_item,
            quantidade=quantidade_unidades,
            inicio=inicio,
            fim=fim
        )

        if sucesso:
            atividade.equipamento_alocado = modeladora_selecionada
            atividade.equipamentos_selecionados = [modeladora_selecionada]
            atividade.alocada = True

            logger.info(
                f"✅ Atividade {id_atividade} (Item {id_item}) alocada na modeladora {modeladora_selecionada.nome} | "
                f"Quantidade {quantidade_unidades} unidades | "
                f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}"
            )
            return True, modeladora_selecionada, inicio, fim
        else:
            logger.error(f"❌ Falha inesperada ao registrar atividade {id_atividade} na modeladora {modeladora_selecionada.nome}")
            return False, None, None, None

    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Remove registros que já finalizaram em todas as modeladoras."""
        for modeladora in self.modeladoras:
            modeladora.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        """Remove registros específicos por atividade em todas as modeladoras."""
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for modeladora in self.modeladoras:
            modeladora.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        """Remove registros específicos por pedido em todas as modeladoras."""
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for modeladora in self.modeladoras:
            modeladora.liberar_por_pedido(id_ordem, id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        """Remove registros específicos por ordem em todas as modeladoras."""
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for modeladora in self.modeladoras:
            modeladora.liberar_por_ordem(id_ordem)

    def liberar_por_item(self, id_item: int):
        """Remove registros específicos por item em todas as modeladoras."""
        for modeladora in self.modeladoras:
            modeladora.liberar_por_item(id_item)

    def liberar_todas_ocupacoes(self):
        """Remove todos os registros de todas as modeladoras."""
        for modeladora in self.modeladoras:
            modeladora.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra histórico consolidado de todas as modeladoras."""
        logger.info("==============================================")
        logger.info("📅 Histórico das Modeladoras")
        logger.info("==============================================")
        for modeladora in self.modeladoras:
            modeladora.mostrar_agenda()

    def obter_status_modeladoras(self) -> dict:
        """Retorna o status atual de todas as modeladoras."""
        status = {}
        for modeladora in self.modeladoras:
            registros_ativos = [
                {
                    'id_ordem': oc[0],
                    'id_pedido': oc[1],
                    'id_atividade': oc[2],
                    'id_item': oc[3],
                    'quantidade': oc[4],
                    'inicio': oc[5].strftime('%H:%M'),
                    'fim': oc[6].strftime('%H:%M')
                }
                for oc in modeladora.ocupacoes
            ]
            
            status[modeladora.nome] = {
                'capacidade_min_unidades_por_minuto': modeladora.capacidade_min_unidades_por_minuto,
                'capacidade_max_unidades_por_minuto': modeladora.capacidade_max_unidades_por_minuto,
                'total_registros': len(modeladora.ocupacoes),
                'registros_ativos': registros_ativos,
                'sempre_disponivel': True
            }
        
        return status

    def obter_utilizacao_por_item(self, id_item: int) -> dict:
        """
        📊 Retorna informações de utilização de um item específico em todas as modeladoras.
        """
        utilizacao = {}
        
        for modeladora in self.modeladoras:
            registros_item = modeladora.obter_ocupacoes_item(id_item)
            
            if registros_item:
                quantidade_total = sum(oc[4] for oc in registros_item)
                periodo_inicio = min(oc[5] for oc in registros_item)
                periodo_fim = max(oc[6] for oc in registros_item)
                
                utilizacao[modeladora.nome] = {
                    'quantidade_total': quantidade_total,
                    'num_registros': len(registros_item),
                    'periodo_inicio': periodo_inicio.strftime('%H:%M'),
                    'periodo_fim': periodo_fim.strftime('%H:%M'),
                    'registros': [
                        {
                            'id_ordem': oc[0],
                            'id_pedido': oc[1],
                            'id_atividade': oc[2],
                            'quantidade': oc[4],
                            'inicio': oc[5].strftime('%H:%M'),
                            'fim': oc[6].strftime('%H:%M')
                        }
                        for oc in registros_item
                    ]
                }
        
        return utilizacao

    def obter_estatisticas_uso(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas de uso das modeladoras no período."""
        estatisticas = {
            'total_modeladoras': len(self.modeladoras),
            'modeladoras_utilizadas': 0,
            'total_unidades_produzidas': 0,
            'tempo_total_registrado': 0.0,
            'estatisticas_por_modeladora': {}
        }
        
        for modeladora in self.modeladoras:
            registros_periodo = modeladora.obter_ocupacoes_periodo(inicio, fim)
            
            if registros_periodo:
                estatisticas['modeladoras_utilizadas'] += 1
                
                # Calcular estatísticas da modeladora
                unidades_produzidas = sum(oc[4] for oc in registros_periodo)
                tempo_registrado = sum(
                    (oc[6] - oc[5]).total_seconds() / 60  # fim - inicio em minutos
                    for oc in registros_periodo
                )
                
                estatisticas['total_unidades_produzidas'] += unidades_produzidas
                estatisticas['tempo_total_registrado'] += tempo_registrado
                
                estatisticas['estatisticas_por_modeladora'][modeladora.nome] = {
                    'unidades_produzidas': unidades_produzidas,
                    'tempo_registrado_minutos': tempo_registrado,
                    'numero_registros': len(registros_periodo)
                }
        
        return estatisticas