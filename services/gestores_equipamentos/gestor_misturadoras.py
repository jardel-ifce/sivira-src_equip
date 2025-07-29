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
    """
    🥣 Gestor especializado para controle de masseiras,
    utilizando Backward Scheduling minuto a minuto com FIPs (Fatores de Importância de Prioridade).
    
    Funcionalidades:
    - Prioriza uso de uma masseira, múltiplas se necessário
    - Respeita capacidade mínima na divisão de pedidos
    - Permite sobreposição do mesmo id_item com intervalos flexíveis
    - Validação dinâmica de capacidade considerando picos de sobreposição
    - Ordenação por FIP para priorização
    """

    def __init__(self, masseiras: List[Masseira]):
        """
        Inicializa o gestor com uma lista de masseiras disponíveis.
        """
        self.masseiras = masseiras

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Masseira]:
        """
        Ordena as masseiras com base no FIP da atividade.
        Equipamentos com menor FIP são priorizados.
        """
        return sorted(
            self.masseiras, 
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )

    # ==========================================================
    # 🔧 Obtenção de Configurações
    # ==========================================================
    def _obter_velocidades_para_masseira(self, atividade: "AtividadeModular", masseira: Masseira) -> List[TipoVelocidade]:
        """Obtém as velocidades configuradas para uma masseira específica."""
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                chave = self._normalizar_nome(masseira.nome)
                config = atividade.configuracoes_equipamentos.get(chave, {})
                velocidades_raw = config.get("velocidade", [])
                
                if isinstance(velocidades_raw, str):
                    velocidades_raw = [velocidades_raw]
                
                velocidades = []
                for v in velocidades_raw:
                    try:
                        velocidades.append(TipoVelocidade[v.strip().upper()])
                    except (KeyError, AttributeError):
                        logger.warning(f"⚠️ Velocidade inválida: '{v}' para masseira {masseira.nome}")
                
                if not velocidades:
                    logger.debug(f"⚠️ Nenhuma velocidade definida para masseira {masseira.nome}")
                
                return velocidades
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter velocidades para {masseira.nome}: {e}")
        
        return []

    def _obter_tipo_mistura_para_masseira(self, atividade: "AtividadeModular", masseira: Masseira) -> Optional[TipoMistura]:
        """Obtém o tipo de mistura configurado para uma masseira específica."""
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                chave = self._normalizar_nome(masseira.nome)
                config = atividade.configuracoes_equipamentos.get(chave, {})
                raw = config.get("tipo_mistura")
                
                if raw is None:
                    logger.debug(f"⚠️ Tipo de mistura não definido para masseira {masseira.nome}")
                    return None
                
                if isinstance(raw, list):
                    raw = raw[0] if raw else None
                
                if raw is None:
                    return None
                
                try:
                    return TipoMistura[raw.strip().upper()]
                except (KeyError, AttributeError):
                    logger.warning(f"⚠️ Tipo de mistura inválido: '{raw}' para masseira {masseira.nome}")
                    return None
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter tipo de mistura para {masseira.nome}: {e}")
        
        return None

    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        """Normaliza nome do equipamento para busca em configurações."""
        return (
            unicodedata.normalize("NFKD", nome.lower())
            .encode("ASCII", "ignore")
            .decode()
            .replace(" ", "_")
        )

    def _obter_ids_atividade(self, atividade: "AtividadeModular") -> Tuple[int, int, int, int]:
        """
        Extrai os IDs da atividade de forma consistente.
        Retorna: (id_ordem, id_pedido, id_atividade, id_item)
        """
        # Tenta diferentes atributos para compatibilidade
        id_ordem = getattr(atividade, 'id_ordem', None) or getattr(atividade, 'ordem_id', 0)
        id_pedido = getattr(atividade, 'id_pedido', None) or getattr(atividade, 'pedido_id', 0)
        id_atividade = getattr(atividade, 'id_atividade', 0)
        id_item = getattr(atividade, 'id_item', 0)
        
        return id_ordem, id_pedido, id_atividade, id_item

    # ==========================================================
    # 🎯 Alocação com Backward Scheduling e Intervalos Flexíveis
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_alocada: float,
        **kwargs
    ) -> Tuple[bool, Optional[List[Masseira]], Optional[datetime], Optional[datetime]]:
        """
        Aloca uma atividade nas masseiras disponíveis usando Backward Scheduling.
        
        Regras implementadas:
        1. Prioriza uso de uma masseira, múltiplas se necessário
        2. Respeita capacidade mínima na divisão
        3. Permite sobreposição do mesmo id_item
        4. Ordenação por FIP
        """
        duracao = atividade.duracao
        masseiras_ordenadas = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim

        # Obter IDs da atividade de forma consistente
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)

        if quantidade_alocada <= 0:
            logger.warning(f"❌ Quantidade inválida para atividade {id_atividade}: {quantidade_alocada}")
            return False, None, None, None

        logger.info(f"🎯 Iniciando alocação atividade {id_atividade}: {quantidade_alocada:.2f}g do item {id_item}")
        logger.debug(f"📅 Janela: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} (duração: {duracao})")

        # ==========================================================
        # 🔄 BACKWARD SCHEDULING - MINUTO A MINUTO
        # ==========================================================
        tentativas = 0
        while horario_final_tentativa - duracao >= inicio:
            tentativas += 1
            horario_inicio_tentativa = horario_final_tentativa - duracao
            
            logger.debug(f"⏰ Tentativa {tentativas}: {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}")

            # 1️⃣ PRIMEIRA ESTRATÉGIA: Tenta alocação integral em uma masseira
            sucesso_individual = self._tentar_alocacao_individual(
                horario_inicio_tentativa, horario_final_tentativa,
                atividade, quantidade_alocada, masseiras_ordenadas,
                id_ordem, id_pedido, id_atividade, id_item
            )
            
            if sucesso_individual:
                masseira_usada, inicio_real, fim_real = sucesso_individual
                atividade.equipamento_alocado = masseira_usada
                atividade.equipamentos_selecionados = [masseira_usada]
                atividade.alocada = True
                
                minutos_retrocedidos = int((fim - fim_real).total_seconds() / 60)
                logger.info(
                    f"✅ Atividade {id_atividade} (Item {id_item}) alocada INTEIRAMENTE na {masseira_usada.nome} "
                    f"({quantidade_alocada:.2f}g) de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                    f"(retrocedeu {minutos_retrocedidos} minutos)"
                )
                return True, [masseira_usada], inicio_real, fim_real

            # 2️⃣ SEGUNDA ESTRATÉGIA: Tenta alocação distribuída entre múltiplas masseiras
            sucesso_distribuido = self._tentar_alocacao_distribuida(
                horario_inicio_tentativa, horario_final_tentativa,
                atividade, quantidade_alocada, masseiras_ordenadas,
                id_ordem, id_pedido, id_atividade, id_item
            )
            
            if sucesso_distribuido:
                masseiras_usadas, inicio_real, fim_real = sucesso_distribuido
                atividade.equipamento_alocado = None  # Múltiplas masseiras
                atividade.equipamentos_selecionados = masseiras_usadas
                atividade.alocada = True
                
                minutos_retrocedidos = int((fim - fim_real).total_seconds() / 60)
                logger.info(
                    f"🧩 Atividade {id_atividade} (Item {id_item}) DIVIDIDA entre "
                    f"{', '.join(m.nome for m in masseiras_usadas)} "
                    f"({quantidade_alocada:.2f}g total) de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                    f"(retrocedeu {minutos_retrocedidos} minutos)"
                )
                return True, masseiras_usadas, inicio_real, fim_real

            # 3️⃣ Falhou nesta janela: RETROCEDE 1 MINUTO
            horario_final_tentativa -= timedelta(minutes=1)
            
            # Log ocasional para evitar spam
            if tentativas % 10 == 0:
                logger.debug(f"⏪ Tentativa {tentativas}: retrocedendo para {horario_final_tentativa.strftime('%H:%M')}")

        # Não conseguiu alocar em nenhuma janela válida
        minutos_total_retrocedidos = int((fim - (inicio + duracao)).total_seconds() / 60)
        logger.warning(
            f"❌ Atividade {id_atividade} (Item {id_item}) não pôde ser alocada após {tentativas} tentativas "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}. "
            f"Quantidade necessária: {quantidade_alocada:.2f}g "
            f"(retrocedeu até o limite de {minutos_total_retrocedidos} minutos)"
        )
        return False, None, None, None

    def _tentar_alocacao_individual(
        self, 
        inicio_tentativa: datetime, 
        fim_tentativa: datetime,
        atividade: "AtividadeModular",
        quantidade_alocada: float,
        masseiras_ordenadas: List[Masseira],
        id_ordem: int, id_pedido: int, id_atividade: int, id_item: int
    ) -> Optional[Tuple[Masseira, datetime, datetime]]:
        """
        Tenta alocar toda a quantidade em uma única masseira.
        Permite sobreposição do mesmo id_item com validação dinâmica de capacidade.
        """
        for masseira in masseiras_ordenadas:
            # Obter configurações técnicas
            velocidades = self._obter_velocidades_para_masseira(atividade, masseira)
            tipo_mistura = self._obter_tipo_mistura_para_masseira(atividade, masseira)
            
            # Verifica disponibilidade básica (parâmetros técnicos)
            if not masseira.verificar_disponibilidade(quantidade_alocada, velocidades, tipo_mistura):
                logger.debug(f"❌ {masseira.nome}: não atende requisitos técnicos")
                continue
            
            # Verifica se pode alocar considerando mesmo item (intervalos flexíveis)
            if not masseira.esta_disponivel_para_item(inicio_tentativa, fim_tentativa, id_item):
                logger.debug(f"❌ {masseira.nome}: ocupada por item diferente")
                continue
            
            # Verifica se quantidade individual está nos limites da masseira
            if not (masseira.capacidade_gramas_min <= quantidade_alocada <= masseira.capacidade_gramas_max):
                logger.debug(f"❌ {masseira.nome}: quantidade {quantidade_alocada:.2f}g fora dos limites [{masseira.capacidade_gramas_min}-{masseira.capacidade_gramas_max}]g")
                continue
            
            # Tenta adicionar a ocupação (validação dinâmica de capacidade interna)
            sucesso = masseira.adicionar_ocupacao(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade_alocada=quantidade_alocada,
                velocidades=velocidades,
                tipo_mistura=tipo_mistura,
                inicio=inicio_tentativa,
                fim=fim_tentativa
            )
            
            if sucesso:
                logger.debug(f"✅ {masseira.nome}: alocação individual bem-sucedida")
                return masseira, inicio_tentativa, fim_tentativa
            else:
                logger.debug(f"❌ {masseira.nome}: falha na validação de capacidade dinâmica")
        
        return None

    def _tentar_alocacao_distribuida(
        self, 
        inicio_tentativa: datetime, 
        fim_tentativa: datetime,
        atividade: "AtividadeModular",
        quantidade_alocada: float,
        masseiras_ordenadas: List[Masseira],
        id_ordem: int, id_pedido: int, id_atividade: int, id_item: int
    ) -> Optional[Tuple[List[Masseira], datetime, datetime]]:
        """
        Tenta alocar a quantidade distribuindo entre múltiplas masseiras.
        Garante que cada parte respeite a capacidade mínima das masseiras.
        """
        # Coleta masseiras com capacidade disponível
        masseiras_com_capacidade = []
        
        for masseira in masseiras_ordenadas:
            velocidades = self._obter_velocidades_para_masseira(atividade, masseira)
            tipo_mistura = self._obter_tipo_mistura_para_masseira(atividade, masseira)
            
            # Verifica disponibilidade para o item específico
            if not masseira.esta_disponivel_para_item(inicio_tentativa, fim_tentativa, id_item):
                logger.debug(f"❌ {masseira.nome}: ocupada por item diferente")
                continue
            
            # Verifica compatibilidade técnica com quantidade mínima
            if not masseira.verificar_disponibilidade(masseira.capacidade_gramas_min, velocidades, tipo_mistura):
                logger.debug(f"❌ {masseira.nome}: não atende requisitos técnicos mínimos")
                continue
                
            # Calcula capacidade disponível para o item específico
            capacidade_disponivel = masseira.obter_capacidade_disponivel_item(
                id_item, inicio_tentativa, fim_tentativa
            )
            
            # Deve ter pelo menos capacidade mínima disponível
            if capacidade_disponivel >= masseira.capacidade_gramas_min:
                masseiras_com_capacidade.append((masseira, capacidade_disponivel, velocidades, tipo_mistura))
                logger.debug(f"🔍 {masseira.nome}: {capacidade_disponivel:.2f}g disponível para item {id_item}")

        if not masseiras_com_capacidade:
            logger.debug("❌ Nenhuma masseira com capacidade mínima disponível")
            return None

        # Tenta distribuir a quantidade respeitando capacidades mínimas
        quantidade_restante = quantidade_alocada
        masseiras_selecionadas = []
        alocacoes_temporarias = []

        for masseira, capacidade_disponivel, velocidades, tipo_mistura in masseiras_com_capacidade:
            if quantidade_restante <= 0:
                break

            # Calcula quanto alocar nesta masseira
            quantidade_para_alocar = min(
                quantidade_restante, 
                capacidade_disponivel, 
                masseira.capacidade_gramas_max
            )
            
            # REGRA CRÍTICA: Garante que cada parte respeite capacidade mínima
            # Se for a última masseira, pode pegar o resto (mesmo que seja menor que o mínimo)
            # Senão, deve respeitar o mínimo E garantir que sobre pelo menos o mínimo para próximas
            eh_ultima_masseira = (masseiras_com_capacidade.index((masseira, capacidade_disponivel, velocidades, tipo_mistura)) == len(masseiras_com_capacidade) - 1)
            
            if not eh_ultima_masseira:
                # Não é a última: deve deixar pelo menos capacidade_minima para próximas masseiras
                masseiras_restantes = len(masseiras_com_capacidade) - len(alocacoes_temporarias) - 1
                capacidade_minima_necessaria_para_restantes = masseiras_restantes * min(
                    m[0].capacidade_gramas_min for m in masseiras_com_capacidade[len(alocacoes_temporarias)+1:]
                ) if masseiras_restantes > 0 else 0
                
                quantidade_maxima_permitida = quantidade_restante - capacidade_minima_necessaria_para_restantes
                quantidade_para_alocar = min(quantidade_para_alocar, quantidade_maxima_permitida)
            
            # Verifica se a quantidade final respeita o mínimo da masseira atual
            if quantidade_para_alocar < masseira.capacidade_gramas_min and not eh_ultima_masseira:
                logger.debug(f"❌ {masseira.nome}: quantidade {quantidade_para_alocar:.2f}g abaixo do mínimo {masseira.capacidade_gramas_min}g")
                continue
            
            # Última validação: quantidade deve ser positiva
            if quantidade_para_alocar <= 0:
                logger.debug(f"❌ {masseira.nome}: quantidade calculada inválida: {quantidade_para_alocar:.2f}g")
                continue
                
            # Tenta adicionar a ocupação
            sucesso = masseira.adicionar_ocupacao(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade_alocada=quantidade_para_alocar,
                velocidades=velocidades,
                tipo_mistura=tipo_mistura,
                inicio=inicio_tentativa,
                fim=fim_tentativa
            )
            
            if sucesso:
                masseiras_selecionadas.append(masseira)
                alocacoes_temporarias.append((masseira, quantidade_para_alocar))
                quantidade_restante -= quantidade_para_alocar
                logger.debug(f"✅ {masseira.nome}: alocados {quantidade_para_alocar:.2f}g do item {id_item}, restam {quantidade_restante:.2f}g")
            else:
                logger.debug(f"❌ {masseira.nome}: falha na validação de capacidade dinâmica para {quantidade_para_alocar:.2f}g")

        # Verifica se conseguiu alocar toda a quantidade
        if quantidade_restante <= 0:
            logger.debug(f"✅ Alocação distribuída bem-sucedida: {len(masseiras_selecionadas)} masseiras para item {id_item}")
            return masseiras_selecionadas, inicio_tentativa, fim_tentativa
        else:
            # Rollback: remove alocações parciais que não completaram
            logger.debug(f"🔄 Rollback: não conseguiu alocar {quantidade_restante:.2f}g restantes do item {id_item}")
            for masseira, _ in alocacoes_temporarias:
                masseira.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
            return None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular") -> None:
        """Libera ocupações específicas por atividade em todas as masseiras."""
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for masseira in self.masseiras:
            masseira.liberar_por_atividade(
                id_ordem=id_ordem, 
                id_pedido=id_pedido, 
                id_atividade=id_atividade
            )

    def liberar_por_pedido(self, atividade: "AtividadeModular") -> None:
        """Libera ocupações específicas por pedido em todas as masseiras."""
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for masseira in self.masseiras:
            masseira.liberar_por_pedido(
                id_ordem=id_ordem, 
                id_pedido=id_pedido
            )

    def liberar_por_ordem(self, atividade: "AtividadeModular") -> None:
        """Libera ocupações específicas por ordem em todas as masseiras."""
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for masseira in self.masseiras:
            masseira.liberar_por_ordem(id_ordem)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime) -> None:
        """Libera ocupações que já finalizaram em todas as masseiras."""
        for masseira in self.masseiras:
            masseira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self) -> None:
        """Libera todas as ocupações de todas as masseiras."""
        for masseira in self.masseiras:
            masseira.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self) -> None:
        """Mostra agenda de todas as masseiras."""
        logger.info("==============================================")
        logger.info("📅 Agenda das Masseiras")
        logger.info("==============================================")
        for masseira in self.masseiras:
            masseira.mostrar_agenda()

    def obter_status_masseiras(self) -> dict:
        """Retorna o status atual de todas as masseiras."""
        status = {}
        for masseira in self.masseiras:
            ocupacoes_ativas = [
                {
                    'id_ordem': oc[0],
                    'id_pedido': oc[1],
                    'id_atividade': oc[2],
                    'id_item': oc[3],
                    'quantidade': oc[4],
                    'velocidades': [v.name for v in oc[5]],
                    'tipo_mistura': oc[6].name if oc[6] else None,
                    'inicio': oc[7].strftime('%H:%M'),
                    'fim': oc[8].strftime('%H:%M')
                }
                for oc in masseira.ocupacoes
            ]
            
            status[masseira.nome] = {
                'capacidade_minima': masseira.capacidade_gramas_min,
                'capacidade_maxima': masseira.capacidade_gramas_max,
                'total_ocupacoes': len(masseira.ocupacoes),
                'ocupacoes_ativas': ocupacoes_ativas
            }
        
        return status

    def verificar_disponibilidade(
        self,
        inicio: datetime,
        fim: datetime,
        id_item: Optional[int] = None,
        quantidade: Optional[float] = None
    ) -> List[Masseira]:
        """
        Verifica quais masseiras estão disponíveis no período para um item específico.
        """
        disponiveis = []
        
        for masseira in self.masseiras:
            if id_item is not None:
                if masseira.esta_disponivel_para_item(inicio, fim, id_item):
                    if quantidade is None:
                        disponiveis.append(masseira)
                    else:
                        # Verifica se pode adicionar a quantidade especificada
                        if masseira.validar_nova_ocupacao_item(id_item, quantidade, inicio, fim):
                            disponiveis.append(masseira)
            else:
                # Comportamento original para compatibilidade
                if masseira.esta_disponivel(inicio, fim):
                    if quantidade is None or masseira.validar_capacidade_individual(quantidade):
                        disponiveis.append(masseira)
        
        return disponiveis

    def obter_utilizacao_por_item(self, id_item: int) -> dict:
        """
        📊 Retorna informações de utilização de um item específico em todas as masseiras.
        """
        utilizacao = {}
        
        for masseira in self.masseiras:
            ocupacoes_item = [
                oc for oc in masseira.ocupacoes if oc[3] == id_item
            ]
            
            if ocupacoes_item:
                quantidade_total = sum(oc[4] for oc in ocupacoes_item)
                periodo_inicio = min(oc[7] for oc in ocupacoes_item)
                periodo_fim = max(oc[8] for oc in ocupacoes_item)
                
                utilizacao[masseira.nome] = {
                    'quantidade_total': quantidade_total,
                    'num_ocupacoes': len(ocupacoes_item),
                    'periodo_inicio': periodo_inicio.strftime('%H:%M'),
                    'periodo_fim': periodo_fim.strftime('%H:%M'),
                    'ocupacoes': [
                        {
                            'id_ordem': oc[0],
                            'id_pedido': oc[1],
                            'quantidade': oc[4],
                            'inicio': oc[7].strftime('%H:%M'),
                            'fim': oc[8].strftime('%H:%M')
                        }
                        for oc in ocupacoes_item
                    ]
                }
        
        return utilizacao

    def calcular_pico_utilizacao_item(self, id_item: int) -> dict:
        """
        📈 Calcula o pico de utilização de um item específico em cada masseira.
        """
        picos = {}
        
        for masseira in self.masseiras:
            ocupacoes_item = [oc for oc in masseira.ocupacoes if oc[3] == id_item]
            
            if not ocupacoes_item:
                continue
                
            # Usa método da própria masseira para calcular pico
            periodo_inicio = min(oc[7] for oc in ocupacoes_item)
            periodo_fim = max(oc[8] for oc in ocupacoes_item)
            
            pico_quantidade = masseira.obter_quantidade_maxima_item_periodo(
                id_item, periodo_inicio, periodo_fim
            )
            
            if pico_quantidade > 0:
                picos[masseira.nome] = {
                    'pico_quantidade': pico_quantidade,
                    'periodo_analise': f"{periodo_inicio.strftime('%H:%M')} - {periodo_fim.strftime('%H:%M')}",
                    'percentual_capacidade': (pico_quantidade / masseira.capacidade_gramas_max) * 100
                }
        
        return picos