from datetime import datetime, timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING
from models.equipamentos.bancada import Bancada
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logs.logger_factory import setup_logger

# 🪕 Logger específico para o gestor de bancadas
logger = setup_logger('GestorBancadas')


class GestorBancadas:
    """
    🪕 Gestor especializado para controle de bancadas,
    utilizando Backward Scheduling com FIPs (Fatores de Importância de Prioridade).
    
    ✅ CORRIGIDO: Retorna todas as bancadas utilizadas para registro adequado no AtividadeModular
    """

    def __init__(self, bancadas: List[Bancada]):
        """
        Inicializa o gestor com uma lista de bancadas disponíveis.
        """
        self.bancadas = bancadas

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Bancada]:
        """
        Ordena as bancadas com base no FIP da atividade.
        Equipamentos com menor FIP são priorizados.
        """
        ordenadas = sorted(
            self.bancadas,
            key=lambda b: atividade.fips_equipamentos.get(b, 999)
        )
        return ordenadas
    
    # ==========================================================
    # 🔁 Obter frações necessárias 
    # ==========================================================
    def _obter_fracoes_necessarias(self, atividade: "AtividadeModular", bancada: Bancada) -> int:
        """
        Consulta no dicionário `configuracoes_equipamentos` da atividade
        quantas frações são necessárias para essa bancada específica.

        Se não houver configuração específica, assume 1 fração.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_chave = bancada.nome.lower().replace(" ", "_")
                logger.debug(f"🔎 Procurando config para: '{nome_chave}'")
                logger.debug(f"🗂️ Chaves disponíveis: {list(atividade.configuracoes_equipamentos.keys())}")
                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config:
                    fracoes = config.get("fracoes_necessarias", 1)
                    logger.debug(f"✅ Encontrado: {fracoes} frações para {nome_chave}")
                    return fracoes
                else:
                    logger.debug(f"❌ Nenhuma configuração encontrada para: '{nome_chave}'")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter frações para {bancada.nome}: {e}")
        return 1
    
    # ==========================================================
    # 🎯 Alocação - CORRIGIDA PARA RETORNAR TODAS AS BANCADAS
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular"
    ) -> Tuple[bool, Optional[List[Bancada]], Optional[datetime], Optional[datetime]]:
        """
        ✅ CORRIGIDO: Retorna sempre lista de bancadas para garantir processamento adequado.
        Isso força o AtividadeModular a reconhecer alocações múltiplas e consolidar o registro.
        
        Returns:
            Tuple[bool, Optional[List[Bancada]], Optional[datetime], Optional[datetime]]
            - bool: Sucesso da alocação
            - List[Bancada]: SEMPRE lista (mesmo com 1 bancada) para consistência
            - datetime: Início real da alocação
            - datetime: Fim real da alocação
        """

        duracao = atividade.duracao
        equipamentos_ordenados = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            # 1️⃣ Tenta alocar integralmente em uma bancada (prioridade por FIP)
            for bancada in equipamentos_ordenados:
                fracoes_necessarias = self._obter_fracoes_necessarias(atividade, bancada)

                if bancada.quantidade_fracoes_disponiveis(horario_inicio_tentativa, horario_final_tentativa) >= fracoes_necessarias:
                    sucesso = bancada.ocupar_fracoes(
                        id_ordem=atividade.id_ordem,
                        id_pedido=atividade.id_pedido,
                        id_atividade=atividade.id_atividade,
                        id_item=atividade.id_item if hasattr(atividade, 'id_item') else 0,
                        quantidade_fracoes=fracoes_necessarias,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa
                    )
                    if sucesso:
                        # ✅ COMPATIBILIDADE: Configura adequadamente a atividade
                        atividade.equipamento_alocado = bancada
                        atividade.equipamentos_selecionados = [bancada]
                        atividade.alocada = True
                        
                        logger.info(
                            f"✅ Atividade {atividade.id_atividade} alocada INTEIRAMENTE na {bancada.nome} "
                            f"({fracoes_necessarias} frações) "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )
                        # ✅ CORREÇÃO CRÍTICA: Retorna lista mesmo para bancada única (consistência)
                        return True, [bancada], horario_inicio_tentativa, horario_final_tentativa

            # 2️⃣ Fallback: tenta dividir a carga entre bancadas
            fracoes_total_necessarias = None
            fracoes_acumuladas = 0
            bancadas_utilizadas = set()  # ← NOVO: Set para rastrear bancadas únicas

            for bancada in equipamentos_ordenados:
                fracoes_disponiveis = bancada.quantidade_fracoes_disponiveis(horario_inicio_tentativa, horario_final_tentativa)

                if fracoes_disponiveis > 0:
                    if fracoes_total_necessarias is None:
                        fracoes_total_necessarias = self._obter_fracoes_necessarias(atividade, bancada)

                    usar_fracoes = min(fracoes_total_necessarias - fracoes_acumuladas, fracoes_disponiveis)

                    sucesso = bancada.ocupar_fracoes(
                        id_ordem=atividade.id_ordem,
                        id_pedido=atividade.id_pedido,
                        id_atividade=atividade.id_atividade,
                        id_item=atividade.id_item if hasattr(atividade, 'id_item') else 0,
                        quantidade_fracoes=usar_fracoes,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa
                    )

                    if sucesso:
                        bancadas_utilizadas.add(bancada)  # ← MODIFICAÇÃO: Adiciona ao set
                        fracoes_acumuladas += usar_fracoes

                    if fracoes_acumuladas >= fracoes_total_necessarias:
                        # ✅ CORREÇÃO: Para múltiplas bancadas, configura adequadamente
                        bancadas_lista = list(bancadas_utilizadas)
                        atividade.equipamento_alocado = bancadas_lista[0]  # Primeira como principal
                        atividade.equipamentos_selecionados = bancadas_lista
                        atividade.alocada = True
                        
                        logger.info(
                            f"🧩 Atividade {atividade.id_atividade} dividida entre "
                            f"{', '.join(b.nome for b in bancadas_lista)} "
                            f"({fracoes_acumuladas} frações total) "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                        )
                        # ✅ CORREÇÃO CRÍTICA: Retorna lista de bancadas únicas
                        return True, bancadas_lista, horario_inicio_tentativa, horario_final_tentativa

            # Nenhuma alocação possível nesta janela → tenta retroceder
            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {atividade.id_atividade} não pôde ser alocada "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular") -> None:
        """Libera ocupações específicas por atividade em todas as bancadas."""
        for bancada in self.bancadas:
            bancada.liberar_por_atividade(
                id_ordem=atividade.id_ordem, 
                id_pedido=atividade.id_pedido, 
                id_atividade=atividade.id_atividade
            )

    def liberar_por_pedido(self, atividade: "AtividadeModular") -> None:
        """Libera ocupações específicas por pedido em todas as bancadas."""
        for bancada in self.bancadas:
            bancada.liberar_por_pedido(
                id_ordem=atividade.id_ordem, 
                id_pedido=atividade.id_pedido
            )

    def liberar_por_ordem(self, atividade: "AtividadeModular") -> None:
        """Libera ocupações específicas por ordem em todas as bancadas."""
        for bancada in self.bancadas:
            bancada.liberar_por_ordem(id_ordem=atividade.id_ordem)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime) -> None:
        """Libera ocupações que já finalizaram em todas as bancadas."""
        for bancada in self.bancadas:
            bancada.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self) -> None:
        """Libera todas as ocupações de todas as bancadas."""
        for bancada in self.bancadas:
            bancada.liberar_todas_ocupacoes()

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime) -> None:
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        for bancada in self.bancadas:
            bancada.liberar_por_intervalo(inicio, fim)

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self) -> None:
        """Mostra agenda consolidada de todas as bancadas."""
        logger.info("==============================================")
        logger.info("📅 Agenda das Bancadas")
        logger.info("==============================================")
        for bancada in self.bancadas:
            bancada.mostrar_agenda()

    # ==========================================================
    # 📊 Estatísticas e Relatórios
    # ==========================================================
    def obter_estatisticas_globais(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas consolidadas de todas as bancadas."""
        estatisticas = {
            'total_bancadas': len(self.bancadas),
            'total_fracoes': sum(b.qtd_fracoes for b in self.bancadas),
            'fracoes_utilizadas': 0,
            'total_ocupacoes': 0,
            'bancadas_utilizadas': 0,
            'detalhes_por_bancada': {}
        }

        for bancada in self.bancadas:
            stats_bancada = bancada.obter_estatisticas_uso(inicio, fim)
            estatisticas['detalhes_por_bancada'][bancada.nome] = stats_bancada
            
            if stats_bancada['fracoes_utilizadas'] > 0:
                estatisticas['bancadas_utilizadas'] += 1
            
            estatisticas['fracoes_utilizadas'] += stats_bancada['fracoes_utilizadas']
            estatisticas['total_ocupacoes'] += stats_bancada['total_ocupacoes']

        # Calcula taxa de utilização global
        if estatisticas['total_fracoes'] > 0:
            estatisticas['taxa_utilizacao_global'] = (
                estatisticas['fracoes_utilizadas'] / estatisticas['total_fracoes'] * 100
            )
        else:
            estatisticas['taxa_utilizacao_global'] = 0.0

        return estatisticas

    def obter_bancadas_disponiveis(self, inicio: datetime, fim: datetime, fracoes_necessarias: int = 1) -> List[Bancada]:
        """Retorna lista de bancadas que têm frações suficientes disponíveis."""
        bancadas_disponiveis = []
        for bancada in self.bancadas:
            if bancada.verificar_espaco_fracoes(fracoes_necessarias, inicio, fim):
                bancadas_disponiveis.append(bancada)
        return bancadas_disponiveis

    def obter_capacidade_total_disponivel(self, inicio: datetime, fim: datetime) -> int:
        """Retorna total de frações disponíveis em todas as bancadas."""
        return sum(
            bancada.quantidade_fracoes_disponiveis(inicio, fim) 
            for bancada in self.bancadas
        )

    # ==========================================================
    # 📊 Métodos para análise de alocações múltiplas
    # ==========================================================
    def obter_detalhes_alocacao_atividade(self, atividade: "AtividadeModular") -> dict:
        """
        🔍 Retorna detalhes completos da alocação de uma atividade,
        incluindo informações de múltiplas bancadas se aplicável.
        """
        detalhes = {
            'id_atividade': atividade.id_atividade,
            'id_item': getattr(atividade, 'id_item', 0),
            'alocacao_multipla': len(atividade.equipamentos_selecionados) > 1 if hasattr(atividade, 'equipamentos_selecionados') else False,
            'bancadas_utilizadas': [],
            'fracoes_total': 0
        }
        
        # Coleta informações de todas as bancadas que processam esta atividade
        for bancada in self.bancadas:
            fracoes_utilizadas = 0
            ocupacoes_atividade = []
            
            for fracao_index in range(bancada.qtd_fracoes):
                ocupacoes_fracao = [
                    oc for oc in bancada.ocupacoes_por_fracao[fracao_index]
                    if (oc[0] == atividade.id_ordem and 
                        oc[1] == atividade.id_pedido and 
                        oc[2] == atividade.id_atividade)
                ]
                
                if ocupacoes_fracao:
                    fracoes_utilizadas += 1
                    ocupacoes_atividade.extend(ocupacoes_fracao)
            
            if fracoes_utilizadas > 0:
                detalhes['bancadas_utilizadas'].append({
                    'nome': bancada.nome,
                    'fracoes_utilizadas': fracoes_utilizadas,
                    'ocupacoes': len(ocupacoes_atividade)
                })
                detalhes['fracoes_total'] += fracoes_utilizadas
        
        return detalhes

    def listar_alocacoes_multiplas(self) -> List[dict]:
        """
        📊 Lista todas as atividades que utilizaram múltiplas bancadas.
        """
        alocacoes_multiplas = []
        atividades_processadas = set()
        
        for bancada in self.bancadas:
            for fracao_index in range(bancada.qtd_fracoes):
                for ocupacao in bancada.ocupacoes_por_fracao[fracao_index]:
                    id_ordem, id_pedido, id_atividade = ocupacao[0], ocupacao[1], ocupacao[2]
                    chave_atividade = (id_ordem, id_pedido, id_atividade)
                    
                    if chave_atividade not in atividades_processadas:
                        # Conta quantas bancadas diferentes processam esta atividade
                        bancadas_atividade = []
                        fracoes_total = 0
                        
                        for b in self.bancadas:
                            fracoes_bancada = 0
                            for fi in range(b.qtd_fracoes):
                                ocupacoes_atividade = [
                                    oc for oc in b.ocupacoes_por_fracao[fi]
                                    if (oc[0] == id_ordem and oc[1] == id_pedido and oc[2] == id_atividade)
                                ]
                                if ocupacoes_atividade:
                                    fracoes_bancada += 1
                            
                            if fracoes_bancada > 0:
                                bancadas_atividade.append({
                                    'nome': b.nome,
                                    'fracoes_utilizadas': fracoes_bancada
                                })
                                fracoes_total += fracoes_bancada
                        
                        if len(bancadas_atividade) > 1:
                            alocacoes_multiplas.append({
                                'id_ordem': id_ordem,
                                'id_pedido': id_pedido,
                                'id_atividade': id_atividade,
                                'id_item': ocupacao[3],
                                'fracoes_total': fracoes_total,
                                'num_bancadas': len(bancadas_atividade),
                                'bancadas': bancadas_atividade,
                                'inicio': ocupacao[4].strftime('%H:%M [%d/%m]'),
                                'fim': ocupacao[5].strftime('%H:%M [%d/%m]')
                            })
                        
                        atividades_processadas.add(chave_atividade)
        
        return alocacoes_multiplas