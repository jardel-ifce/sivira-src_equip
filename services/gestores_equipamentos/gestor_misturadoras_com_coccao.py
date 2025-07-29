import unicodedata
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, TYPE_CHECKING
from models.equipamentos.hot_mix import HotMix
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from enums.equipamentos.tipo_chama import TipoChama
from enums.equipamentos.tipo_pressao_chama import TipoPressaoChama
from utils.logs.logger_factory import setup_logger

logger = setup_logger("GestorMisturadorasComCoccao")


class GestorMisturadorasComCoccao:
    """
    🍳 Gestor especializado no controle de misturadoras com cocção (HotMix).
    
    Funcionalidades:
    - Permite sobreposição do mesmo id_item com intervalos flexíveis
    - Validação dinâmica de capacidade considerando picos de sobreposição
    - Prioriza uso de uma HotMix, múltiplas se necessário
    - Respeita capacidade mínima na divisão de pedidos
    - Ordenação por FIP para priorização
    """

    def __init__(self, hotmixes: List[HotMix]):
        self.hotmixes = hotmixes
    
    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================  
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[HotMix]:
        """Ordena HotMixes por fator de importância de prioridade."""
        ordenadas = sorted(
            self.hotmixes,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        return ordenadas
    
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        """Normaliza nome para busca no JSON de configurações."""
        return unicodedata.normalize("NFKD", nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")

    def _obter_ids_atividade(self, atividade: "AtividadeModular") -> Tuple[int, int, int, int]:
        """
        Extrai os IDs da atividade de forma consistente.
        Retorna: (id_ordem, id_pedido, id_atividade, id_item)
        """
        id_ordem = getattr(atividade, 'id_ordem', None) or getattr(atividade, 'ordem_id', 0)
        id_pedido = getattr(atividade, 'id_pedido', None) or getattr(atividade, 'pedido_id', 0)
        id_atividade = getattr(atividade, 'id_atividade', 0)
        # id_item é o produto/subproduto que está sendo produzido
        id_item = getattr(atividade, 'id_produto', 0)
        
        return id_ordem, id_pedido, id_atividade, id_item

    def _obter_velocidade(self, atividade: "AtividadeModular", hotmix: HotMix) -> Optional[TipoVelocidade]:
        """Obtém a velocidade necessária para a atividade."""
        chave = self._normalizar_nome(hotmix.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        valor = config.get("velocidade") if config else None
        try:
            return TipoVelocidade[valor] if valor else None
        except Exception:
            return None

    def _obter_chama(self, atividade: "AtividadeModular", hotmix: HotMix) -> Optional[TipoChama]:
        """Obtém o tipo de chama necessário para a atividade."""
        chave = self._normalizar_nome(hotmix.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        valor = config.get("tipo_chama") if config else None
        try:
            return TipoChama[valor] if valor else None
        except Exception:
            return None

    def _obter_pressoes(self, atividade: "AtividadeModular", hotmix: HotMix) -> List[TipoPressaoChama]:
        """Obtém as pressões de chama necessárias para a atividade."""
        chave = self._normalizar_nome(hotmix.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        valores = config.get("pressao_chama") if config else []
        pressoes = []
        for p in valores:
            try:
                pressoes.append(TipoPressaoChama[p])
            except Exception:
                continue
        return pressoes

    # ==========================================================
    # 🔄 Alocação Individual com Intervalos Flexíveis
    # ==========================================================
    def _tentar_alocacao_individual(
        self, 
        inicio_tentativa: datetime, 
        fim_tentativa: datetime,
        atividade: "AtividadeModular",
        quantidade_gramas: int,
        hotmixes_ordenados: List[HotMix],
        id_ordem: int, id_pedido: int, id_atividade: int, id_item: int
    ) -> Optional[Tuple[HotMix, datetime, datetime]]:
        """
        Tenta alocar toda a quantidade em uma única HotMix.
        Permite sobreposição do mesmo id_item com validação dinâmica de capacidade.
        """
        for hotmix in hotmixes_ordenados:
            # Obter configurações técnicas
            velocidade = self._obter_velocidade(atividade, hotmix)
            chama = self._obter_chama(atividade, hotmix)
            pressoes = self._obter_pressoes(atividade, hotmix)
            
            if velocidade is None or chama is None or not pressoes:
                logger.debug(f"❌ {hotmix.nome}: configurações incompletas")
                continue
            
            # Verifica se pode alocar considerando mesmo item (intervalos flexíveis)
            if not hotmix.esta_disponivel_para_item(inicio_tentativa, fim_tentativa, id_item):
                logger.debug(f"❌ {hotmix.nome}: ocupada por item diferente")
                continue
            
            # Verifica se quantidade individual está nos limites da HotMix
            if not hotmix.validar_capacidade(quantidade_gramas):
                logger.debug(f"❌ {hotmix.nome}: quantidade {quantidade_gramas}g fora dos limites")
                continue
            
            # Verifica compatibilidade de parâmetros com ocupações existentes do mesmo item
            if not self._verificar_compatibilidade_parametros(hotmix, id_item, velocidade, chama, pressoes, inicio_tentativa, fim_tentativa):
                logger.debug(f"❌ {hotmix.nome}: parâmetros incompatíveis com ocupações existentes do item {id_item}")
                continue
            
            # Tenta adicionar a ocupação (validação dinâmica de capacidade interna)
            sucesso = hotmix.ocupar(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade=quantidade_gramas,
                velocidade=velocidade,
                chama=chama,
                pressao_chamas=pressoes,
                inicio=inicio_tentativa,
                fim=fim_tentativa
            )
            
            if sucesso:
                logger.debug(f"✅ {hotmix.nome}: alocação individual bem-sucedida para item {id_item}")
                return hotmix, inicio_tentativa, fim_tentativa
            else:
                logger.debug(f"❌ {hotmix.nome}: falha na validação de capacidade dinâmica")
        
        return None

    def _tentar_alocacao_distribuida(
        self, 
        inicio_tentativa: datetime, 
        fim_tentativa: datetime,
        atividade: "AtividadeModular",
        quantidade_gramas: int,
        hotmixes_ordenados: List[HotMix],
        id_ordem: int, id_pedido: int, id_atividade: int, id_item: int
    ) -> Optional[Tuple[List[HotMix], datetime, datetime]]:
        """
        Tenta alocar a quantidade distribuindo entre múltiplas HotMixes.
        CORRIGIDO: Garante que cada parte respeite a capacidade mínima das HotMixes
        e considera corretamente a capacidade disponível real para o item específico.
        """
        # Coleta HotMixes com capacidade disponível para o item específico
        hotmixes_com_capacidade = []
        
        for hotmix in hotmixes_ordenados:
            # Verifica disponibilidade para o item específico
            if not hotmix.esta_disponivel_para_item(inicio_tentativa, fim_tentativa, id_item):
                logger.debug(f"❌ {hotmix.nome}: ocupada por item diferente")
                continue
            
            # Obter configurações técnicas
            velocidade = self._obter_velocidade(atividade, hotmix)
            chama = self._obter_chama(atividade, hotmix)
            pressoes = self._obter_pressoes(atividade, hotmix)
            
            if velocidade is None or chama is None or not pressoes:
                logger.debug(f"❌ {hotmix.nome}: configurações incompletas")
                continue
            
            # Verifica compatibilidade de parâmetros
            if not self._verificar_compatibilidade_parametros(hotmix, id_item, velocidade, chama, pressoes, inicio_tentativa, fim_tentativa):
                logger.debug(f"❌ {hotmix.nome}: parâmetros incompatíveis")
                continue
            
            # CORRIGIDO: Calcula capacidade disponível real para o item específico
            capacidade_disponivel = hotmix.obter_capacidade_disponivel_item(
                id_item, inicio_tentativa, fim_tentativa
            )
            
            # Deve ter pelo menos capacidade mínima disponível
            if capacidade_disponivel >= hotmix.capacidade_gramas_min:
                hotmixes_com_capacidade.append((hotmix, capacidade_disponivel, velocidade, chama, pressoes))
                logger.debug(f"🔍 {hotmix.nome}: {capacidade_disponivel}g disponível para item {id_item}")

        if not hotmixes_com_capacidade:
            logger.debug("❌ Nenhuma HotMix com capacidade mínima disponível")
            return None

        # CORRIGIDO: Ordenar por capacidade disponível (maior primeiro) para melhor distribuição
        hotmixes_com_capacidade.sort(key=lambda x: x[1], reverse=True)

        # Tenta distribuir a quantidade respeitando capacidades mínimas
        quantidade_restante = quantidade_gramas
        hotmixes_selecionadas = []
        alocacoes_temporarias = []

        for i, (hotmix, capacidade_disponivel, velocidade, chama, pressoes) in enumerate(hotmixes_com_capacidade):
            if quantidade_restante <= 0:
                break

            # Calcula quanto alocar nesta HotMix
            eh_ultima_hotmix = (i == len(hotmixes_com_capacidade) - 1)
            
            if eh_ultima_hotmix:
                # Última HotMix: aloca todo o restante (se couber)
                quantidade_para_alocar = min(quantidade_restante, capacidade_disponivel)
            else:
                # Não é a última: calcula considerando que as próximas precisam de pelo menos o mínimo
                hotmixes_restantes = len(hotmixes_com_capacidade) - i - 1
                if hotmixes_restantes > 0:
                    # Soma das capacidades mínimas das HotMixes restantes
                    capacidade_minima_restantes = sum(
                        hm[0].capacidade_gramas_min 
                        for hm in hotmixes_com_capacidade[i+1:]
                    )
                    # Não pode alocar mais que: restante - mínimo_necessário_para_outras
                    quantidade_maxima_permitida = quantidade_restante - capacidade_minima_restantes
                    quantidade_para_alocar = min(
                        capacidade_disponivel,
                        max(hotmix.capacidade_gramas_min, quantidade_maxima_permitida)
                    )
                else:
                    quantidade_para_alocar = min(quantidade_restante, capacidade_disponivel)
            
            # Verifica se a quantidade está dentro dos limites
            if quantidade_para_alocar < hotmix.capacidade_gramas_min:
                if eh_ultima_hotmix and quantidade_restante < hotmix.capacidade_gramas_min:
                    # Se é a última e o restante é menor que o mínimo, tenta mesmo assim
                    logger.debug(f"⚠️ {hotmix.nome}: tentando alocar {quantidade_restante}g (abaixo do mínimo) por ser última HotMix")
                    quantidade_para_alocar = quantidade_restante
                else:
                    logger.debug(f"❌ {hotmix.nome}: quantidade {quantidade_para_alocar}g abaixo do mínimo {hotmix.capacidade_gramas_min}g")
                    continue
            
            # Última validação: quantidade deve ser positiva e não exceder máximo
            if quantidade_para_alocar <= 0:
                logger.debug(f"❌ {hotmix.nome}: quantidade calculada inválida: {quantidade_para_alocar}g")
                continue
                
            quantidade_para_alocar = min(quantidade_para_alocar, hotmix.capacidade_gramas_max)
                
            # Tenta adicionar a ocupação
            sucesso = hotmix.ocupar(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade=quantidade_para_alocar,
                velocidade=velocidade,
                chama=chama,
                pressao_chamas=pressoes,
                inicio=inicio_tentativa,
                fim=fim_tentativa
            )
            
            if sucesso:
                hotmixes_selecionadas.append(hotmix)
                alocacoes_temporarias.append((hotmix, quantidade_para_alocar))
                quantidade_restante -= quantidade_para_alocar
                logger.debug(f"✅ {hotmix.nome}: alocados {quantidade_para_alocar}g do item {id_item}, restam {quantidade_restante}g")
            else:
                logger.debug(f"❌ {hotmix.nome}: falha na validação de capacidade dinâmica para {quantidade_para_alocar}g")

        # Verifica se conseguiu alocar toda a quantidade
        if quantidade_restante <= 0:
            logger.debug(f"✅ Alocação distribuída bem-sucedida: {len(hotmixes_selecionadas)} HotMixes para item {id_item}")
            return hotmixes_selecionadas, inicio_tentativa, fim_tentativa
        else:
            # Rollback: remove alocações parciais que não completaram
            logger.debug(f"🔄 Rollback: não conseguiu alocar {quantidade_restante}g restantes do item {id_item}")
            for hotmix, _ in alocacoes_temporarias:
                hotmix.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
            return None

    def _verificar_compatibilidade_parametros(self, hotmix: HotMix, id_item: int, velocidade: TipoVelocidade, chama: TipoChama, pressoes: List[TipoPressaoChama], inicio: datetime, fim: datetime) -> bool:
        """Verifica se os parâmetros são compatíveis com ocupações existentes do mesmo produto."""
        
        for ocupacao in hotmix.obter_ocupacoes_item_periodo(id_item, inicio, fim):
            # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade, velocidade, chama, pressoes, inicio, fim)
            vel_existente = ocupacao[5]
            chama_existente = ocupacao[6]
            press_existentes = ocupacao[7]
            
            # Verificar se velocidade é compatível
            if vel_existente != velocidade:
                logger.debug(f"❌ Velocidade incompatível: existente={vel_existente.name}, nova={velocidade.name}")
                return False
            
            # Verificar se chama é compatível
            if chama_existente != chama:
                logger.debug(f"❌ Chama incompatível: existente={chama_existente.name}, nova={chama.name}")
                return False
            
            # Verificar se pressões são compatíveis
            if set(press_existentes) != set(pressoes):
                logger.debug(f"❌ Pressões incompatíveis: existentes={[p.name for p in press_existentes]}, novas={[p.name for p in pressoes]}")
                return False
        
        return True

    # ==========================================================
    # 🎯 Alocação Principal com Backward Scheduling
    # ==========================================================    
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_gramas: int,
        **kwargs
    ) -> Tuple[bool, Optional[List[HotMix]], Optional[datetime], Optional[datetime]]:
        """
        Aloca HotMixes seguindo a estratégia otimizada com intervalos flexíveis:
        1. Tenta alocação individual por FIP (permite sobreposição mesmo item)
        2. Tenta distribuição de carga (respeitando capacidades mínimas)
        3. Usa backward scheduling minuto a minuto
        """
        duracao = atividade.duracao
        hotmixes_ordenados = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim
        
        # Obter IDs da atividade de forma consistente
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)

        if quantidade_gramas <= 0:
            logger.warning(f"❌ Quantidade inválida para atividade {id_atividade}: {quantidade_gramas}")
            return False, None, None, None

        logger.info(f"🎯 Iniciando alocação atividade {id_atividade}: {quantidade_gramas}g do item {id_item}")
        logger.debug(f"📅 Janela: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} (duração: {duracao})")

        # ==========================================================
        # 🔄 BACKWARD SCHEDULING - MINUTO A MINUTO
        # ==========================================================
        tentativas = 0
        while horario_final_tentativa - duracao >= inicio:
            tentativas += 1
            horario_inicio_tentativa = horario_final_tentativa - duracao
            
            logger.debug(f"⏰ Tentativa {tentativas}: {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}")

            # 1️⃣ PRIMEIRA ESTRATÉGIA: Tenta alocação integral em uma HotMix
            sucesso_individual = self._tentar_alocacao_individual(
                horario_inicio_tentativa, horario_final_tentativa,
                atividade, quantidade_gramas, hotmixes_ordenados,
                id_ordem, id_pedido, id_atividade, id_item
            )
            
            if sucesso_individual:
                hotmix_usada, inicio_real, fim_real = sucesso_individual
                atividade.equipamento_alocado = hotmix_usada
                atividade.equipamentos_selecionados = [hotmix_usada]
                atividade.alocada = True
                
                minutos_retrocedidos = int((fim - fim_real).total_seconds() / 60)
                logger.info(
                    f"✅ Atividade {id_atividade} (Item {id_item}) alocada INTEIRAMENTE na {hotmix_usada.nome} "
                    f"({quantidade_gramas}g) de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                    f"(retrocedeu {minutos_retrocedidos} minutos)"
                )
                return True, [hotmix_usada], inicio_real, fim_real

            # 2️⃣ SEGUNDA ESTRATÉGIA: Tenta alocação distribuída entre múltiplas HotMixes
            sucesso_distribuido = self._tentar_alocacao_distribuida(
                horario_inicio_tentativa, horario_final_tentativa,
                atividade, quantidade_gramas, hotmixes_ordenados,
                id_ordem, id_pedido, id_atividade, id_item
            )
            
            if sucesso_distribuido:
                hotmixes_usadas, inicio_real, fim_real = sucesso_distribuido
                atividade.equipamento_alocado = None  # Múltiplas HotMixes
                atividade.equipamentos_selecionados = hotmixes_usadas
                atividade.alocada = True
                
                minutos_retrocedidos = int((fim - fim_real).total_seconds() / 60)
                logger.info(
                    f"🧩 Atividade {id_atividade} (Item {id_item}) DIVIDIDA entre "
                    f"{', '.join(h.nome for h in hotmixes_usadas)} "
                    f"({quantidade_gramas}g total) de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                    f"(retrocedeu {minutos_retrocedidos} minutos)"
                )
                return True, hotmixes_usadas, inicio_real, fim_real

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
            f"Quantidade necessária: {quantidade_gramas}g "
            f"(retrocedeu até o limite de {minutos_total_retrocedidos} minutos)"
        )
        return False, None, None, None
    
    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por atividade."""
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for hotmix in self.hotmixes:
            hotmix.liberar_por_atividade(
                id_ordem=id_ordem, 
                id_pedido=id_pedido, 
                id_atividade=id_atividade
            )
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por pedido."""
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for hotmix in self.hotmixes:
            hotmix.liberar_por_pedido(
                id_ordem=id_ordem, 
                id_pedido=id_pedido
            )

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por ordem."""
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for hotmix in self.hotmixes:
            hotmix.liberar_por_ordem(id_ordem=id_ordem)
      
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        for hotmix in self.hotmixes:
            hotmix.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações de todas as HotMixes."""
        for hotmix in self.hotmixes:
            hotmix.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda consolidada de todas as HotMixes."""
        logger.info("==============================================")
        logger.info("📅 Agenda das Misturadoras com Cocção (HotMix)")
        logger.info("==============================================")
        for hotmix in self.hotmixes:
            hotmix.mostrar_agenda()

    def obter_status_hotmixes(self) -> dict:
        """Retorna o status atual de todas as HotMixes."""
        status = {}
        for hotmix in self.hotmixes:
            ocupacoes_ativas = [
                {
                    'id_ordem': oc[0],
                    'id_pedido': oc[1],
                    'id_atividade': oc[2],
                    'id_item': oc[3],
                    'quantidade': oc[4],
                    'velocidade': oc[5].name,
                    'chama': oc[6].name,
                    'pressoes': [p.name for p in oc[7]],
                    'inicio': oc[8].strftime('%H:%M'),
                    'fim': oc[9].strftime('%H:%M')
                }
                for oc in hotmix.ocupacoes
            ]
            
            status[hotmix.nome] = {
                'capacidade_minima': hotmix.capacidade_gramas_min,
                'capacidade_maxima': hotmix.capacidade_gramas_max,
                'total_ocupacoes': len(hotmix.ocupacoes),
                'ocupacoes_ativas': ocupacoes_ativas
            }
        
        return status

    def verificar_disponibilidade(
        self,
        inicio: datetime,
        fim: datetime,
        id_item: Optional[int] = None,
        quantidade: Optional[int] = None
    ) -> List[HotMix]:
        """
        Verifica quais HotMixes estão disponíveis no período para um item específico.
        """
        disponiveis = []
        
        for hotmix in self.hotmixes:
            if id_item is not None:
                if hotmix.esta_disponivel_para_item(inicio, fim, id_item):
                    if quantidade is None:
                        disponiveis.append(hotmix)
                    else:
                        # Verifica se pode adicionar a quantidade especificada
                        if hotmix.validar_nova_ocupacao_item(id_item, quantidade, inicio, fim):
                            disponiveis.append(hotmix)
            else:
                # Comportamento original para compatibilidade
                if hotmix.esta_disponivel(inicio, fim):
                    if quantidade is None or hotmix.validar_capacidade(quantidade):
                        disponiveis.append(hotmix)
        
        return disponiveis

    def obter_utilizacao_por_item(self, id_item: int) -> dict:
        """
        📊 Retorna informações de utilização de um item específico em todas as HotMixes.
        """
        utilizacao = {}
        
        for hotmix in self.hotmixes:
            ocupacoes_item = [
                oc for oc in hotmix.ocupacoes if oc[3] == id_item
            ]
            
            if ocupacoes_item:
                quantidade_total = sum(oc[4] for oc in ocupacoes_item)
                periodo_inicio = min(oc[8] for oc in ocupacoes_item)
                periodo_fim = max(oc[9] for oc in ocupacoes_item)
                
                utilizacao[hotmix.nome] = {
                    'quantidade_total': quantidade_total,
                    'num_ocupacoes': len(ocupacoes_item),
                    'periodo_inicio': periodo_inicio.strftime('%H:%M'),
                    'periodo_fim': periodo_fim.strftime('%H:%M'),
                    'ocupacoes': [
                        {
                            'id_ordem': oc[0],
                            'id_pedido': oc[1],
                            'quantidade': oc[4],
                            'inicio': oc[8].strftime('%H:%M'),
                            'fim': oc[9].strftime('%H:%M')
                        }
                        for oc in ocupacoes_item
                    ]
                }
        
        return utilizacao

    def calcular_pico_utilizacao_item(self, id_item: int) -> dict:
        """
        📈 Calcula o pico de utilização de um item específico em cada HotMix.
        """
        picos = {}
        
        for hotmix in self.hotmixes:
            ocupacoes_item = [oc for oc in hotmix.ocupacoes if oc[3] == id_item]
            
            if not ocupacoes_item:
                continue
                
            # Usa método da própria HotMix para calcular pico
            periodo_inicio = min(oc[8] for oc in ocupacoes_item)
            periodo_fim = max(oc[9] for oc in ocupacoes_item)
            
            pico_quantidade = hotmix.obter_quantidade_maxima_item_periodo(
                id_item, periodo_inicio, periodo_fim
            )
            
            if pico_quantidade > 0:
                picos[hotmix.nome] = {
                    'pico_quantidade': pico_quantidade,
                    'periodo_analise': f"{periodo_inicio.strftime('%H:%M')} - {periodo_fim.strftime('%H:%M')}",
                    'percentual_capacidade': (pico_quantidade / hotmix.capacidade_gramas_max) * 100
                }
        
        return picos

    def obter_relatorio_detalhado_item(self, id_item: int) -> dict:
        """
        NOVO: Gera relatório detalhado de um item específico em todas as HotMixes.
        """
        relatorio = {
            'id_item': id_item,
            'resumo_geral': {
                'total_hotmixes_utilizadas': 0,
                'quantidade_total_alocada': 0,
                'periodo_global': None
            },
            'detalhes_por_hotmix': {}
        }
        
        hotmixes_utilizadas = 0
        quantidade_total = 0
        periodo_global_inicio = None
        periodo_global_fim = None
        
        for hotmix in self.hotmixes:
            ocupacoes_item = [oc for oc in hotmix.ocupacoes if oc[3] == id_item]
            
            if ocupacoes_item:
                hotmixes_utilizadas += 1
                quantidade_hotmix = sum(oc[4] for oc in ocupacoes_item)
                quantidade_total += quantidade_hotmix
                
                periodo_inicio = min(oc[8] for oc in ocupacoes_item)
                periodo_fim = max(oc[9] for oc in ocupacoes_item)
                
                if periodo_global_inicio is None or periodo_inicio < periodo_global_inicio:
                    periodo_global_inicio = periodo_inicio
                if periodo_global_fim is None or periodo_fim > periodo_global_fim:
                    periodo_global_fim = periodo_fim
                
                pico_quantidade = hotmix.obter_quantidade_maxima_item_periodo(
                    id_item, periodo_inicio, periodo_fim
                )
                
                relatorio['detalhes_por_hotmix'][hotmix.nome] = {
                    'quantidade_total': quantidade_hotmix,
                    'pico_simultaneo': pico_quantidade,
                    'num_ocupacoes': len(ocupacoes_item),
                    'periodo': f"{periodo_inicio.strftime('%H:%M')} - {periodo_fim.strftime('%H:%M')}",
                    'percentual_capacidade': (pico_quantidade / hotmix.capacidade_gramas_max) * 100,
                    'capacidade_disponivel': hotmix.capacidade_gramas_max - pico_quantidade
                }
        
        relatorio['resumo_geral'] = {
            'total_hotmixes_utilizadas': hotmixes_utilizadas,
            'quantidade_total_alocada': quantidade_total,
            'periodo_global': f"{periodo_global_inicio.strftime('%H:%M')} - {periodo_global_fim.strftime('%H:%M')}" if periodo_global_inicio else None
        }
        
        return relatorio