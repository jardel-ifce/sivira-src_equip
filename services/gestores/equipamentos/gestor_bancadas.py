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
    # 🔧 Métodos utilitários
    # ==========================================================
    def _calcular_fracoes_disponiveis(self, bancada: Bancada, inicio: datetime, fim: datetime) -> int:
        """
        Calcula quantas frações estão disponíveis em uma bancada para o período especificado.

        Args:
            bancada: A bancada a ser verificada
            inicio: Início do período
            fim: Fim do período

        Returns:
            int: Número de frações livres
        """
        fracoes_disponiveis = 0
        for i in range(bancada.numero_fracoes):
            fracao_livre = True
            for ocupacao in bancada.fracoes_ocupacoes[i]:
                ocupacao_inicio = ocupacao[4]
                ocupacao_fim = ocupacao[5]
                if bancada._tem_sobreposicao_temporal(inicio, fim, ocupacao_inicio, ocupacao_fim):
                    fracao_livre = False
                    break
            if fracao_livre:
                fracoes_disponiveis += 1
        return fracoes_disponiveis

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
    
    def _tentar_alocacao_integral(
        self,
        atividade: "AtividadeModular",
        equipamentos_ordenados: List[Bancada],
        horario_inicio_tentativa: datetime,
        horario_final_tentativa: datetime
    ) -> Tuple[bool, Optional[List[Bancada]], Optional[datetime], Optional[datetime]]:
        """Tenta alocar a atividade integralmente em uma única bancada."""
        for bancada in equipamentos_ordenados:
            fracoes_necessarias = self._obter_fracoes_necessarias(atividade, bancada)
            fracoes_disponiveis = self._calcular_fracoes_disponiveis(bancada, horario_inicio_tentativa, horario_final_tentativa)

            if fracoes_disponiveis >= fracoes_necessarias:
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
                    atividade.equipamento_alocado = bancada
                    atividade.equipamentos_selecionados = [bancada]
                    atividade.alocada = True

                    logger.info(
                        f"✅ Atividade {atividade.id_atividade} alocada INTEIRAMENTE na {bancada.nome} "
                        f"({fracoes_necessarias} frações) "
                        f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                    )
                    return True, [bancada], horario_inicio_tentativa, horario_final_tentativa

        return False, None, None, None

    def _tentar_alocacao_dividida(
        self,
        atividade: "AtividadeModular",
        equipamentos_ordenados: List[Bancada],
        horario_inicio_tentativa: datetime,
        horario_final_tentativa: datetime
    ) -> Tuple[bool, Optional[List[Bancada]], Optional[datetime], Optional[datetime]]:
        """Tenta dividir a atividade entre múltiplas bancadas."""
        fracoes_total_necessarias = None
        fracoes_acumuladas = 0
        bancadas_utilizadas = set()

        for bancada in equipamentos_ordenados:
            fracoes_disponiveis = self._calcular_fracoes_disponiveis(bancada, horario_inicio_tentativa, horario_final_tentativa)

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
                    bancadas_utilizadas.add(bancada)
                    fracoes_acumuladas += usar_fracoes

                if fracoes_acumuladas >= fracoes_total_necessarias:
                    bancadas_lista = list(bancadas_utilizadas)
                    atividade.equipamento_alocado = bancadas_lista[0]
                    atividade.equipamentos_selecionados = bancadas_lista
                    atividade.alocada = True

                    logger.info(
                        f"🧩 Atividade {atividade.id_atividade} dividida entre "
                        f"{', '.join(b.nome for b in bancadas_lista)} "
                        f"({fracoes_acumuladas} frações total) "
                        f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}."
                    )
                    return True, bancadas_lista, horario_inicio_tentativa, horario_final_tentativa

        return False, None, None, None

    # ==========================================================
    # 🎯 Alocação 
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        
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

            # 1️⃣ Tenta alocar integralmente em uma bancada
            sucesso, bancadas, inicio_real, fim_real = self._tentar_alocacao_integral(
                atividade, equipamentos_ordenados, horario_inicio_tentativa, horario_final_tentativa
            )
            if sucesso:
                return sucesso, bancadas, inicio_real, fim_real

            # 2️⃣ Fallback: tenta dividir entre bancadas
            sucesso, bancadas, inicio_real, fim_real = self._tentar_alocacao_dividida(
                atividade, equipamentos_ordenados, horario_inicio_tentativa, horario_final_tentativa
            )
            if sucesso:
                return sucesso, bancadas, inicio_real, fim_real

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
            'total_fracoes': sum(b.numero_fracoes for b in self.bancadas),
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
            fracoes_disponiveis = self._calcular_fracoes_disponiveis(bancada, inicio, fim)

            if fracoes_disponiveis >= fracoes_necessarias:
                bancadas_disponiveis.append(bancada)
        return bancadas_disponiveis

    def obter_capacidade_total_disponivel(self, inicio: datetime, fim: datetime) -> int:
        """Retorna total de frações disponíveis em todas as bancadas."""
        return sum(
            self._calcular_fracoes_disponiveis(bancada, inicio, fim)
            for bancada in self.bancadas
        )

    # ==========================================================
    # 📊 Métodos para análise de alocações múltiplas
    # ==========================================================
    def _contar_fracoes_atividade(self, bancada: Bancada, id_ordem: int, id_pedido: int, id_atividade: int) -> int:
        """Conta quantas frações uma atividade usa em uma bancada específica."""
        fracoes_utilizadas = 0
        for fracao_index in range(bancada.numero_fracoes):
            ocupacoes_fracao = [
                oc for oc in bancada.fracoes_ocupacoes[fracao_index]
                if (oc[0] == id_ordem and oc[1] == id_pedido and oc[2] == id_atividade)
            ]
            if ocupacoes_fracao:
                fracoes_utilizadas += 1
        return fracoes_utilizadas

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
            fracoes_utilizadas = self._contar_fracoes_atividade(
                bancada, atividade.id_ordem, atividade.id_pedido, atividade.id_atividade
            )

            if fracoes_utilizadas > 0:
                detalhes['bancadas_utilizadas'].append({
                    'nome': bancada.nome,
                    'fracoes_utilizadas': fracoes_utilizadas,
                    'ocupacoes': fracoes_utilizadas  # Simplificado: 1 ocupação por fração
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
            for fracao_index in range(bancada.numero_fracoes):
                for ocupacao in bancada.fracoes_ocupacoes[fracao_index]:
                    id_ordem, id_pedido, id_atividade = ocupacao[0], ocupacao[1], ocupacao[2]
                    chave_atividade = (id_ordem, id_pedido, id_atividade)

                    if chave_atividade not in atividades_processadas:
                        # Usa o método utilitário para contar frações por bancada
                        bancadas_atividade = []
                        fracoes_total = 0

                        for b in self.bancadas:
                            fracoes_bancada = self._contar_fracoes_atividade(b, id_ordem, id_pedido, id_atividade)
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