from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, TYPE_CHECKING
from models.equipamentos.fritadeira import Fritadeira
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logs.logger_factory import setup_logger
import unicodedata
import math

# 🍟 Logger exclusivo para o gestor de fritadeiras
logger = setup_logger('GestorFritadeiras')


class GestorFritadeiras:
    """
    🍟 Gestor especializado no controle de fritadeiras.
    Utiliza backward scheduling e FIP (Fatores de Importância de Prioridade).
    Implementa verificação dinâmica de intervalos e priorização por fritadeira.
    ✅ CORRIGIDO: Frações tratadas como espaços físicos independentes
    ✅ MELHORADO: Validação de temperatura em ocupações simultâneas
    ❌ REMOVIDO: Tentativas inadequadas de sobreposição por id_item
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

    def _obter_quantidade_gramas(self, atividade: "AtividadeModular", fritadeira: Fritadeira) -> Optional[int]:
        """Obtém a quantidade em gramas necessária para a atividade."""
        try:
            chave = self._normalizar_nome(fritadeira.nome)
            config = atividade.configuracoes_equipamentos.get(chave, {})
            return int(config.get("quantidade_gramas", atividade.quantidade_produto or 0))
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter quantidade em gramas para {fritadeira.nome}: {e}")
            return None

    def _obter_temperatura(self, atividade: "AtividadeModular", fritadeira: Fritadeira) -> Optional[int]:
        try:
            chave = self._normalizar_nome(fritadeira.nome)
            config = atividade.configuracoes_equipamentos.get(chave, {})
            return int(config.get("temperatura", 0))
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter temperatura para {fritadeira.nome}: {e}")
            return None

    def _obter_fracoes_necessarias(self, atividade: "AtividadeModular", fritadeira: Fritadeira) -> Optional[int]:
        """Obtém o número de frações necessárias para a atividade."""
        try:
            chave = self._normalizar_nome(fritadeira.nome)
            config = atividade.configuracoes_equipamentos.get(chave, {})
            return int(config.get("fracoes_necessarias", 1))
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter frações necessárias para {fritadeira.nome}: {e}")
            return None

    # ==========================================================
    # 🆕 VERIFICAÇÃO DINÂMICA DE INTERVALOS COM MELHORIA DE TEMPERATURA
    # ==========================================================
    def _calcular_quantidade_maxima_fritadeira_periodo(
        self, 
        fritadeira: Fritadeira, 
        inicio: datetime, 
        fim: datetime
    ) -> int:
        """
        🔍 Calcula a quantidade máxima ocupada simultaneamente na fritadeira durante o período.
        Analisa todos os pontos temporais para detectar picos de ocupação.
        """
        # Coleta todos os pontos temporais relevantes
        pontos_temporais = set()
        ocupacoes_periodo = []
        
        for fracao_index in range(fritadeira.numero_fracoes):
            for ocupacao in fritadeira.ocupacoes_por_fracao[fracao_index]:
                # Acesso por índices: (id_ordem, id_pedido, id_atividade, id_item, quantidade, temperatura, setup_minutos, inicio, fim)
                inicio_ocup = ocupacao[7]  # início
                fim_ocup = ocupacao[8]     # fim
                quantidade = ocupacao[4]  # quantidade
                
                if not (fim <= inicio_ocup or inicio >= fim_ocup):  # há sobreposição temporal
                    ocupacoes_periodo.append(ocupacao)
                    pontos_temporais.add(inicio_ocup)
                    pontos_temporais.add(fim_ocup)
        
        # Adiciona pontos do período de interesse
        pontos_temporais.add(inicio)
        pontos_temporais.add(fim)
        
        # Ordena pontos temporais
        pontos_ordenados = sorted(pontos_temporais)
        
        quantidade_maxima = 0
        
        # Verifica quantidade em cada intervalo
        for i in range(len(pontos_ordenados) - 1):
            momento_inicio = pontos_ordenados[i]
            momento_fim = pontos_ordenados[i + 1]
            momento_meio = momento_inicio + (momento_fim - momento_inicio) / 2
            
            # Soma quantidade de todas as ocupações ativas neste momento
            quantidade_momento = 0
            for ocupacao in ocupacoes_periodo:
                inicio_ocup = ocupacao[7]
                fim_ocup = ocupacao[8]
                quantidade = ocupacao[4]
                
                if inicio_ocup <= momento_meio < fim_ocup:  # ocupação ativa neste momento
                    quantidade_momento += quantidade
            
            quantidade_maxima = max(quantidade_maxima, quantidade_momento)
        
        return quantidade_maxima

    def _validar_nova_ocupacao_fritadeira(
        self, 
        fritadeira: Fritadeira, 
        quantidade_nova: int, 
        temperatura: int,
        fracoes_necessarias: int,
        inicio: datetime, 
        fim: datetime
    ) -> bool:
        """
        🔍 MELHORADO: Valida se uma nova ocupação pode ser adicionada à fritadeira sem exceder limites.
        Considera capacidade total, temperatura individual, temperatura simultânea e número de frações.
        """
        # Validação 1: Temperatura da fritadeira
        if not fritadeira.validar_temperatura(temperatura):
            return False
        
        # 🆕 Validação 2: Temperatura em ocupações simultâneas
        if not fritadeira.validar_temperatura_simultanea(temperatura, inicio, fim):
            return False
        
        # Validação 3: Frações disponíveis
        fracoes_disponiveis = fritadeira.fracoes_disponiveis_periodo(inicio, fim)
        if len(fracoes_disponiveis) < fracoes_necessarias:
            logger.debug(f"❌ {fritadeira.nome}: apenas {len(fracoes_disponiveis)} frações disponíveis, necessárias {fracoes_necessarias}")
            return False
        
        # Validação 4: Capacidade total da fritadeira
        quantidade_atual_maxima = self._calcular_quantidade_maxima_fritadeira_periodo(fritadeira, inicio, fim)
        quantidade_final = quantidade_atual_maxima + quantidade_nova
        
        if quantidade_final < fritadeira.capacidade_min:
            logger.debug(f"❌ {fritadeira.nome}: quantidade total {quantidade_final} ficará abaixo do mínimo {fritadeira.capacidade_min}")
            return False
        
        if quantidade_final > fritadeira.capacidade_max:
            logger.debug(f"❌ {fritadeira.nome}: quantidade total {quantidade_final} excederá máximo {fritadeira.capacidade_max}")
            return False
        
        return True

    def _verificar_compatibilidade_fritadeira(
        self, 
        fritadeira: Fritadeira, 
        quantidade: int, 
        temperatura: int,
        fracoes_necessarias: int,
        inicio: datetime, 
        fim: datetime
    ) -> Tuple[bool, int]:
        """
        🔍 MELHORADO: Verifica se uma fritadeira pode receber uma ocupação e retorna capacidade disponível.
        Inclui validação de temperatura simultânea.
        Retorna (pode_alocar, capacidade_disponivel)
        """
        if not self._validar_nova_ocupacao_fritadeira(fritadeira, quantidade, temperatura, fracoes_necessarias, inicio, fim):
            return False, 0
        
        # Calcula capacidade disponível
        quantidade_atual_maxima = self._calcular_quantidade_maxima_fritadeira_periodo(fritadeira, inicio, fim)
        capacidade_disponivel = fritadeira.capacidade_max - quantidade_atual_maxima
        
        return True, max(0, capacidade_disponivel)

    # ==========================================================
    # 🧮 Análise de Capacidade Total com Verificação Dinâmica
    # ==========================================================
    def _verificar_capacidade_total_sistema(
        self, 
        quantidade_necessaria: int, 
        temperatura: int, 
        fracoes_necessarias: int,
        inicio: datetime, 
        fim: datetime
    ) -> bool:
        """Verifica se o sistema de fritadeiras como um todo pode atender a demanda com verificação dinâmica."""
        capacidade_total_disponivel = 0
        
        for fritadeira in self.fritadeiras:
            compativel, capacidade_disponivel = self._verificar_compatibilidade_fritadeira(
                fritadeira, 0, temperatura, fracoes_necessarias, inicio, fim
            )
            
            if compativel:
                capacidade_total_disponivel += capacidade_disponivel
        
        resultado = capacidade_total_disponivel >= quantidade_necessaria
        logger.info(
            f"🧮 Capacidade total do sistema: {capacidade_total_disponivel}g | "
            f"Necessário: {quantidade_necessaria}g | Atendível: {'✅' if resultado else '❌'}"
        )
        return resultado

    # ==========================================================
    # 🎯 Estratégias de Alocação Priorizadas (CORRIGIDAS)
    # ==========================================================
    def _tentar_alocacao_fritadeira_individual(
        self, 
        atividade: "AtividadeModular", 
        inicio: datetime, 
        fim: datetime
    ) -> Tuple[bool, Optional[Fritadeira], Optional[datetime], Optional[datetime]]:
        """
        Tenta alocar em uma única fritadeira por ordem de FIP.
        Prioriza fritadeiras que podem acomodar toda a demanda.
        ✅ MANTIDO: Funciona corretamente com frações independentes.
        """
        equipamentos_ordenados = self._ordenar_por_fip(atividade)
        
        for fritadeira in equipamentos_ordenados:
            temperatura = self._obter_temperatura(atividade, fritadeira)
            quantidade_gramas = self._obter_quantidade_gramas(atividade, fritadeira)
            fracoes_necessarias = self._obter_fracoes_necessarias(atividade, fritadeira)

            if not temperatura or not quantidade_gramas or not fracoes_necessarias:
                continue

            logger.debug(f"🔍 Testando {fritadeira.nome}: {quantidade_gramas}g, {fracoes_necessarias} frações, {temperatura}°C")

            # Verifica compatibilidade com verificação dinâmica melhorada
            compativel, capacidade_disponivel = self._verificar_compatibilidade_fritadeira(
                fritadeira, quantidade_gramas, temperatura, fracoes_necessarias, inicio, fim
            )

            if compativel and capacidade_disponivel >= quantidade_gramas:
                # Tenta ocupar as frações necessárias
                fracoes_disponiveis = fritadeira.fracoes_disponiveis_periodo(inicio, fim)
                fracoes_para_ocupar = fracoes_disponiveis[:fracoes_necessarias]
                
                sucesso_total = True
                fracoes_ocupadas = []
                
                for fracao_index in fracoes_para_ocupar:
                    sucesso = fritadeira.adicionar_ocupacao_fracao(
                        fracao_index=fracao_index,
                        id_ordem=atividade.id_ordem,
                        id_pedido=atividade.id_pedido,
                        id_atividade=atividade.id_atividade,
                        id_item=atividade.id_item,
                        quantidade=quantidade_gramas // fracoes_necessarias,  # Distribui igualmente
                        temperatura=temperatura,
                        setup_minutos=fritadeira.setup_minutos,
                        inicio=inicio,
                        fim=fim
                    )
                    
                    if sucesso:
                        fracoes_ocupadas.append(fracao_index)
                    else:
                        sucesso_total = False
                        logger.warning(f"❌ Falha ao ocupar fração {fracao_index} da {fritadeira.nome}")
                        break
                
                if sucesso_total:
                    logger.info(
                        f"✅ Alocação individual: {fritadeira.nome} para Atividade {atividade.id_atividade} | "
                        f"Quantidade: {quantidade_gramas}g | Frações: {fracoes_necessarias} | Temp: {temperatura}°C"
                    )
                    return True, fritadeira, inicio, fim
                else:
                    # Rollback das frações já ocupadas
                    for fracao_index in fracoes_ocupadas:
                        fritadeira.liberar_fracao_especifica(fracao_index, atividade.id_ordem, atividade.id_pedido, atividade.id_atividade)

        return False, None, None, None

    def _tentar_alocacao_priorizada_por_fritadeira(
        self, 
        atividade: "AtividadeModular", 
        inicio: datetime, 
        fim: datetime
    ) -> Tuple[bool, List[Fritadeira], Optional[datetime], Optional[datetime]]:
        """
        Tenta alocar priorizando uso de fritadeiras completas antes de dividir.
        Verifica cada fritadeira individualmente antes de partir para distribuição.
        ✅ MANTIDO: Funciona corretamente com frações independentes.
        """
        temperatura = self._obter_temperatura(atividade, self.fritadeiras[0])
        quantidade_gramas = self._obter_quantidade_gramas(atividade, self.fritadeiras[0])
        fracoes_necessarias = self._obter_fracoes_necessarias(atividade, self.fritadeiras[0])
        
        if not temperatura or not quantidade_gramas or not fracoes_necessarias:
            return False, [], None, None

        equipamentos_ordenados = self._ordenar_por_fip(atividade)
        
        # ETAPA 1: Tenta alocar em fritadeiras individuais completas
        for fritadeira in equipamentos_ordenados:
            compativel, capacidade_disponivel = self._verificar_compatibilidade_fritadeira(
                fritadeira, quantidade_gramas, temperatura, fracoes_necessarias, inicio, fim
            )
            
            if compativel and capacidade_disponivel >= quantidade_gramas:
                fracoes_disponiveis = fritadeira.fracoes_disponiveis_periodo(inicio, fim)
                
                if len(fracoes_disponiveis) >= fracoes_necessarias:
                    logger.info(f"🎯 Tentando alocar completamente em {fritadeira.nome}")
                    
                    # Tenta alocar todas as frações necessárias nesta fritadeira
                    fracoes_para_ocupar = fracoes_disponiveis[:fracoes_necessarias]
                    sucesso_total = True
                    fracoes_ocupadas = []
                    
                    for fracao_index in fracoes_para_ocupar:
                        sucesso = fritadeira.adicionar_ocupacao_fracao(
                            fracao_index=fracao_index,
                            id_ordem=atividade.id_ordem,
                            id_pedido=atividade.id_pedido,
                            id_atividade=atividade.id_atividade,
                            id_item=atividade.id_item,
                            quantidade=quantidade_gramas // fracoes_necessarias,
                            temperatura=temperatura,
                            setup_minutos=fritadeira.setup_minutos,
                            inicio=inicio,
                            fim=fim
                        )
                        
                        if sucesso:
                            fracoes_ocupadas.append(fracao_index)
                        else:
                            sucesso_total = False
                            break
                    
                    if sucesso_total:
                        logger.info(
                            f"✅ Alocação priorizada: {fritadeira.nome} completa para Atividade {atividade.id_atividade} | "
                            f"Quantidade: {quantidade_gramas}g | Frações: {fracoes_necessarias}"
                        )
                        return True, [fritadeira], inicio, fim
                    else:
                        # Rollback
                        for fracao_index in fracoes_ocupadas:
                            fritadeira.liberar_fracao_especifica(fracao_index, atividade.id_ordem, atividade.id_pedido, atividade.id_atividade)

        return False, [], None, None

    def _tentar_alocacao_distribuida_ultima_opcao(
        self, 
        atividade: "AtividadeModular", 
        inicio: datetime, 
        fim: datetime
    ) -> Tuple[bool, List[Fritadeira], Optional[datetime], Optional[datetime]]:
        """
        Última opção: distribui entre múltiplas fritadeiras quando não consegue alocar em uma só.
        ✅ MANTIDO: Funciona corretamente com frações independentes.
        """
        temperatura = self._obter_temperatura(atividade, self.fritadeiras[0])
        quantidade_gramas = self._obter_quantidade_gramas(atividade, self.fritadeiras[0])
        fracoes_necessarias = self._obter_fracoes_necessarias(atividade, self.fritadeiras[0])
        
        if not temperatura or not quantidade_gramas or not fracoes_necessarias:
            return False, [], None, None

        logger.info(f"🔄 Tentando distribuição entre múltiplas fritadeiras (última opção)")
        
        equipamentos_ordenados = self._ordenar_por_fip(atividade)
        fritadeiras_utilizadas = []
        fracoes_restantes = fracoes_necessarias
        quantidade_restante = quantidade_gramas
        alocacoes_realizadas = []  # Para rollback se necessário
        
        for fritadeira in equipamentos_ordenados:
            if fracoes_restantes <= 0:
                break
            
            compativel, capacidade_disponivel = self._verificar_compatibilidade_fritadeira(
                fritadeira, 0, temperatura, 1, inicio, fim  # Verifica pelo menos 1 fração
            )
            
            if compativel:
                fracoes_disponiveis = fritadeira.fracoes_disponiveis_periodo(inicio, fim)
                fracoes_a_usar = min(len(fracoes_disponiveis), fracoes_restantes)
                
                if fracoes_a_usar > 0:
                    quantidade_por_fracao = quantidade_restante // fracoes_restantes
                    fracoes_ocupadas_fritadeira = []
                    
                    for i in range(fracoes_a_usar):
                        fracao_index = fracoes_disponiveis[i]
                        sucesso = fritadeira.adicionar_ocupacao_fracao(
                            fracao_index=fracao_index,
                            id_ordem=atividade.id_ordem,
                            id_pedido=atividade.id_pedido,
                            id_atividade=atividade.id_atividade,
                            id_item=atividade.id_item,
                            quantidade=quantidade_por_fracao,
                            temperatura=temperatura,
                            setup_minutos=fritadeira.setup_minutos,
                            inicio=inicio,
                            fim=fim
                        )
                        
                        if sucesso:
                            fracoes_ocupadas_fritadeira.append(fracao_index)
                            fracoes_restantes -= 1
                            quantidade_restante -= quantidade_por_fracao
                        else:
                            # Falha - fazer rollback desta fritadeira
                            for fracao_rollback in fracoes_ocupadas_fritadeira:
                                fritadeira.liberar_fracao_especifica(fracao_rollback, atividade.id_ordem, atividade.id_pedido, atividade.id_atividade)
                            break
                    
                    if fracoes_ocupadas_fritadeira:  # Se conseguiu ocupar pelo menos uma fração
                        fritadeiras_utilizadas.append(fritadeira)
                        alocacoes_realizadas.append((fritadeira, fracoes_ocupadas_fritadeira))
                        logger.info(f"🔄 Distribuição: {fritadeira.nome} recebeu {fracoes_a_usar} frações")

        # Verifica se conseguiu alocar tudo
        if fracoes_restantes == 0:
            logger.info(
                f"✅ Alocação distribuída: {len(fritadeiras_utilizadas)} fritadeiras para Atividade {atividade.id_atividade} | "
                f"Total: {quantidade_gramas}g | Frações: {fracoes_necessarias} | Temp: {temperatura}°C"
            )
            return True, fritadeiras_utilizadas, inicio, fim
        else:
            # Rollback completo - não conseguiu alocar tudo
            logger.warning(f"❌ Distribuição falhou - fazendo rollback completo")
            for fritadeira, fracoes_ocupadas in alocacoes_realizadas:
                for fracao_index in fracoes_ocupadas:
                    fritadeira.liberar_fracao_especifica(fracao_index, atividade.id_ordem, atividade.id_pedido, atividade.id_atividade)
            
            return False, [], None, None

    # ==========================================================
    # 🎯 Alocação Principal com Priorização CORRIGIDA
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular"
    ) -> Tuple[bool, Optional[List[Fritadeira]], Optional[datetime], Optional[datetime]]:
        """
        Aloca fritadeiras seguindo a estratégia corrigida:
        1. Verifica capacidade total do sistema
        2. Tenta alocação individual por FIP (fritadeira completa)
        3. ❌ REMOVIDO: Sobreposição inadequada por id_item
        4. Tenta alocação priorizada por fritadeira completa
        5. Em último caso, distribui entre múltiplas fritadeiras
        
        ✅ CORRIGIDO: Frações tratadas como espaços físicos independentes
        ✅ MELHORADO: Validação de temperatura simultânea
        """
        duracao = atividade.duracao
        horario_final_tentativa = fim
        
        # Obter parâmetros básicos
        temperatura = self._obter_temperatura(atividade, self.fritadeiras[0])
        quantidade_gramas = self._obter_quantidade_gramas(atividade, self.fritadeiras[0])
        fracoes_necessarias = self._obter_fracoes_necessarias(atividade, self.fritadeiras[0])
        
        if not temperatura or not quantidade_gramas or not fracoes_necessarias:
            logger.error(f"❌ Parâmetros inválidos para atividade {atividade.id_atividade}")
            return False, None, None, None

        logger.info(
            f"🎯 Iniciando alocação (FRAÇÕES FÍSICAS INDEPENDENTES): "
            f"{quantidade_gramas}g, {fracoes_necessarias} frações, {temperatura}°C"
        )

        while horario_final_tentativa - duracao >= inicio:
            horario_inicial_tentativa = horario_final_tentativa - duracao

            # 1. Verificar capacidade total do sistema com verificação dinâmica
            if not self._verificar_capacidade_total_sistema(
                quantidade_gramas, temperatura, fracoes_necessarias, 
                horario_inicial_tentativa, horario_final_tentativa
            ):
                horario_final_tentativa -= timedelta(minutes=1)
                continue

            # 2. Tentar alocação individual (fritadeira completa)
            sucesso, fritadeira, ini, fim_exec = self._tentar_alocacao_fritadeira_individual(
                atividade, horario_inicial_tentativa, horario_final_tentativa
            )
            if sucesso:
                atividade.equipamento_alocado = fritadeira
                atividade.equipamentos_selecionados = [fritadeira]
                atividade.alocada = True
                return True, [fritadeira], ini, fim_exec

            # 3. ❌ REMOVIDO: Sobreposição inadequada por id_item
            # Motivo: Frações são espaços físicos independentes que não podem ser compartilhados

            # 4. Tentar alocação priorizada por fritadeira
            sucesso, fritadeiras, ini, fim_exec = self._tentar_alocacao_priorizada_por_fritadeira(
                atividade, horario_inicial_tentativa, horario_final_tentativa
            )
            if sucesso:
                atividade.equipamento_alocado = fritadeiras[0]  # Principal
                atividade.equipamentos_selecionados = fritadeiras
                atividade.alocada = True
                return True, fritadeiras, ini, fim_exec

            # 5. Última opção: distribuição entre múltiplas fritadeiras
            sucesso, fritadeiras, ini, fim_exec = self._tentar_alocacao_distribuida_ultima_opcao(
                atividade, horario_inicial_tentativa, horario_final_tentativa
            )
            if sucesso:
                atividade.equipamento_alocado = fritadeiras[0]  # Principal
                atividade.equipamentos_selecionados = fritadeiras
                atividade.alocada = True
                logger.info(f"⚠️ Usando distribuição como última opção para Atividade {atividade.id_atividade}")
                return True, fritadeiras, ini, fim_exec

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Nenhuma estratégia de alocação funcionou para atividade {atividade.id_atividade} "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')} "
            f"(FRAÇÕES TRATADAS COMO RECURSOS FÍSICOS INDEPENDENTES)."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        for fritadeira in self.fritadeiras:
            fritadeira.liberar_por_atividade(
                id_ordem=atividade.id_ordem, 
                id_pedido=atividade.id_pedido, 
                id_atividade=atividade.id_atividade
            )
                
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for fritadeira in self.fritadeiras:
            fritadeira.liberar_por_pedido(
                id_ordem=atividade.id_ordem, 
                id_pedido=atividade.id_pedido
            )

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for fritadeira in self.fritadeiras:
            fritadeira.liberar_por_ordem(id_ordem=atividade.id_ordem)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for fritadeira in self.fritadeiras:
            fritadeira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for fritadeira in self.fritadeiras:
            fritadeira.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Fritadeiras")
        logger.info("==============================================")
        for fritadeira in self.fritadeiras:
            fritadeira.mostrar_agenda()

    def obter_estatisticas_sistema(self, inicio: datetime, fim: datetime) -> Dict:
        """Retorna estatísticas consolidadas do sistema de fritadeiras."""
        estatisticas_sistema = {
            'fritadeiras_total': len(self.fritadeiras),
            'fritadeiras_utilizadas': 0,
            'capacidade_total_sistema': 0,
            'capacidade_utilizada_sistema': 0,
            'fracoes_totais': 0,
            'fracoes_utilizadas': 0,
            'taxa_utilizacao_capacidade': 0.0,
            'taxa_utilizacao_fracoes': 0.0,
            'temperaturas_utilizadas': set(),
            'estatisticas_por_fritadeira': {}
        }
        
        for fritadeira in self.fritadeiras:
            stats = fritadeira.obter_estatisticas_uso(inicio, fim)
            estatisticas_sistema['estatisticas_por_fritadeira'][fritadeira.nome] = stats
            
            estatisticas_sistema['capacidade_total_sistema'] += fritadeira.capacidade_max
            estatisticas_sistema['fracoes_totais'] += fritadeira.numero_fracoes
            
            if stats['fracoes_utilizadas'] > 0:
                estatisticas_sistema['fritadeiras_utilizadas'] += 1
                estatisticas_sistema['capacidade_utilizada_sistema'] += stats['quantidade_maxima_simultanea']
                estatisticas_sistema['fracoes_utilizadas'] += stats['fracoes_utilizadas']
                estatisticas_sistema['temperaturas_utilizadas'].update(stats['temperaturas_utilizadas'])
        
        # Calcular taxas
        if estatisticas_sistema['capacidade_total_sistema'] > 0:
            estatisticas_sistema['taxa_utilizacao_capacidade'] = (
                estatisticas_sistema['capacidade_utilizada_sistema'] / 
                estatisticas_sistema['capacidade_total_sistema'] * 100
            )
        
        if estatisticas_sistema['fracoes_totais'] > 0:
            estatisticas_sistema['taxa_utilizacao_fracoes'] = (
                estatisticas_sistema['fracoes_utilizadas'] / 
                estatisticas_sistema['fracoes_totais'] * 100
            )
        
        estatisticas_sistema['temperaturas_utilizadas'] = list(estatisticas_sistema['temperaturas_utilizadas'])
        
        return estatisticas_sistema

    # ==========================================================
    # 📋 DOCUMENTAÇÃO DAS CORREÇÕES IMPLEMENTADAS
    # ==========================================================
    def obter_relatorio_correcoes_implementadas(self) -> Dict[str, any]:
        """
        📋 Documenta as correções implementadas no gestor.
        """
        return {
            "correcoes_principais": {
                "1_remocao_sobreposicao_inadequada": {
                    "problema_original": "Método _tentar_alocacao_com_sobreposicao_item tentava sobrepor ocupações do mesmo id_item",
                    "solucao_implementada": "Método removido completamente da estratégia de alocação",
                    "justificativa": "Frações são espaços físicos independentes que requerem operadores humanos dedicados",
                    "impacto": "2 pedidos mesmo item com 2 frações cada = 4 frações ocupadas (comportamento correto)"
                },
                "2_validacao_temperatura_simultanea": {
                    "problema_original": "Não validava temperatura em ocupações simultâneas",
                    "solucao_implementada": "Integração com fritadeira.validar_temperatura_simultanea()",
                    "justificativa": "Ocupações simultâneas devem ter mesma temperatura, independente do item",
                    "impacto": "Previne conflitos de temperatura em ocupações simultâneas"
                },
                "3_melhoria_verificacao_compatibilidade": {
                    "problema_original": "Verificação de compatibilidade não incluía temperatura simultânea",
                    "solucao_implementada": "Atualização do método _verificar_compatibilidade_fritadeira",
                    "justificativa": "Validação completa deve incluir todos os aspectos de compatibilidade",
                    "impacto": "Detecção precoce de incompatibilidades de temperatura"
                }
            },
            "estrategia_alocacao_corrigida": {
                "ordem_tentativas": [
                    "1. Verificar capacidade total do sistema",
                    "2. Tentar alocação individual por FIP",
                    "3. ❌ REMOVIDO: Sobreposição por id_item",
                    "4. Tentar alocação priorizada por fritadeira",
                    "5. Distribuir entre múltiplas fritadeiras (último recurso)"
                ],
                "principios_aplicados": [
                    "Frações como espaços físicos independentes",
                    "Validação de temperatura simultânea obrigatória",
                    "Priorização por FIP mantida",
                    "Rollback em caso de falha parcial"
                ]
            },
            "comportamento_esperado": {
                "cenario_exemplo": {
                    "pedido_1": "id_item=100, fracoes_necessarias=2, temperatura=180°C",
                    "pedido_2": "id_item=100, fracoes_necessarias=2, temperatura=180°C",
                    "resultado_antes": "Tentaria sobrepor (incorreto)",
                    "resultado_depois": "4 frações ocupadas independentemente (correto)",
                    "validacao_temperatura": "Ambos 180°C - compatível para ocupações simultâneas"
                },
                "regras_validacao": [
                    "Cada fração = 1 operador humano = espaço físico único",
                    "Ocupações simultâneas = mesma temperatura obrigatória",
                    "Capacidade total = soma de todas as frações ativas",
                    "Não há compartilhamento entre atividades diferentes"
                ]
            }
        }

    def diagnosticar_problemas_alocacao(self, inicio: datetime, fim: datetime) -> Dict[str, any]:
        """
        🔍 Diagnostica problemas potenciais na alocação atual.
        ✅ ATUALIZADO: Inclui diagnóstico de conflitos de temperatura.
        """
        diagnostico = {
            "fragmentacao_detectada": [],
            "subutilizacao_detectada": [],
            "conflitos_temperatura": [],
            "distribuicoes_desnecessarias": [],
            "validacao_temperatura_simultanea": []
        }
        
        for fritadeira in self.fritadeiras:
            # Detecta fragmentação
            fracoes_ocupadas = 0
            capacidade_utilizada = self._calcular_quantidade_maxima_fritadeira_periodo(fritadeira, inicio, fim)
            
            for fracao_index in range(fritadeira.numero_fracoes):
                if fritadeira.ocupacoes_por_fracao[fracao_index]:
                    fracoes_ocupadas += 1
            
            # Fragmentação: poucas frações ocupadas mas baixa utilização de capacidade
            if fracoes_ocupadas > 0 and capacidade_utilizada < fritadeira.capacidade_min:
                diagnostico["fragmentacao_detectada"].append({
                    "fritadeira": fritadeira.nome,
                    "fracoes_ocupadas": fracoes_ocupadas,
                    "capacidade_utilizada": capacidade_utilizada,
                    "capacidade_minima": fritadeira.capacidade_min
                })
            
            # Subutilização: muitas frações livres mas equipamento usado
            if fracoes_ocupadas > 0 and fracoes_ocupadas < fritadeira.numero_fracoes // 2:
                diagnostico["subutilizacao_detectada"].append({
                    "fritadeira": fritadeira.nome,
                    "fracoes_ocupadas": fracoes_ocupadas,
                    "fracoes_totais": fritadeira.numero_fracoes,
                    "taxa_utilizacao": (fracoes_ocupadas / fritadeira.numero_fracoes) * 100
                })
            
            # 🆕 Verificar conflitos de temperatura simultânea
            inconsistencias_temp = fritadeira.validar_consistencia_ocupacoes()
            conflitos_temp = [inc for inc in inconsistencias_temp if "temperatura" in inc.lower()]
            if conflitos_temp:
                diagnostico["validacao_temperatura_simultanea"].append({
                    "fritadeira": fritadeira.nome,
                    "conflitos": conflitos_temp
                })
        
        return diagnostico

    # ==========================================================
    # 📊 LIMITAÇÕES DA ABORDAGEM CORRIGIDA
    # ==========================================================
    def obter_limitacoes_abordagem_corrigida(self) -> Dict[str, str]:
        """
        📋 Documenta as limitações da abordagem corrigida.
        """
        return {
            "1_maior_consumo_fracoes": (
                "Com a correção, o sistema consome mais frações pois não há "
                "compartilhamento inadequado. Isso pode reduzir a capacidade "
                "total de atendimento simultâneo do sistema."
            ),
            "2_possivel_reducao_eficiencia": (
                "A remoção da sobreposição pode resultar em menor eficiência "
                "aparente, mas reflete o comportamento real operacional "
                "onde cada fração precisa de operador dedicado."
            ),
            "3_validacao_temperatura_mais_restritiva": (
                "A validação de temperatura simultânea pode rejeitar mais "
                "alocações, exigindo sequenciamento temporal para diferentes "
                "temperaturas do mesmo equipamento."
            ),
            "4_complexidade_operacional_realista": (
                "O sistema agora reflete melhor a complexidade operacional "
                "real, mas pode parecer menos otimizado em comparação "
                "com abordagens que ignoram limitações físicas."
            ),
            "5_necessidade_planejamento_temperatura": (
                "Operadores precisarão planejar melhor o sequenciamento "
                "de temperaturas para maximizar utilização, já que mudanças "
                "de temperatura podem exigir tempos de setup."
            )
        }

    def obter_metricas_impacto_correcoes(self, inicio: datetime, fim: datetime) -> Dict[str, any]:
        """
        📊 Calcula métricas do impacto das correções implementadas.
        """
        stats_sistema = self.obter_estatisticas_sistema(inicio, fim)
        diagnostico = self.diagnosticar_problemas_alocacao(inicio, fim)
        
        return {
            "metricas_utilizacao": {
                "taxa_utilizacao_fracoes": stats_sistema['taxa_utilizacao_fracoes'],
                "taxa_utilizacao_capacidade": stats_sistema['taxa_utilizacao_capacidade'],
                "fritadeiras_ativas": stats_sistema['fritadeiras_utilizadas'],
                "fritadeiras_total": stats_sistema['fritadeiras_total']
            },
            "qualidade_alocacao": {
                "fragmentacao_detectada": len(diagnostico['fragmentacao_detectada']),
                "subutilizacao_detectada": len(diagnostico['subutilizacao_detectada']),
                "conflitos_temperatura": len(diagnostico['validacao_temperatura_simultanea']),
                "consistencia_geral": "OK" if not diagnostico['validacao_temperatura_simultanea'] else "PROBLEMAS"
            },
            "comportamento_corrigido": {
                "sobreposicao_inadequada": "REMOVIDA",
                "validacao_temperatura_simultanea": "IMPLEMENTADA",
                "fracoes_como_espacos_fisicos": "CORRIGIDO",
                "operadores_dedicados_por_fracao": "RESPEITADO"
            },
            "recomendacoes": [
                "Planejar sequenciamento de temperaturas para otimizar utilização",
                "Considerar aumentar número de frações se utilização alta",
                "Monitorar fragmentação e ajustar estratégias se necessário",
                "Validar consistência de ocupações periodicamente"
            ]
        }