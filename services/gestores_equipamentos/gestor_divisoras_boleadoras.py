from datetime import datetime, timedelta
from typing import Optional, Tuple, List, TYPE_CHECKING
from models.equipamentos.divisora_de_massas import DivisoraDeMassas
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logs.logger_factory import setup_logger
import unicodedata

logger = setup_logger('GestorDivisoras')


class GestorDivisorasBoleadoras:
    """
    🏭 Gestor especializado para controle de divisoras de massas com ou sem boleadora,
    utilizando backward scheduling com prioridade por FIP.
    
    Funcionalidades:
    - Soma quantidades do mesmo id_item em intervalos sobrepostos  
    - Validação de capacidade dinâmica considerando todos os momentos de sobreposição
    - Priorização por FIP com possibilidade de múltiplas divisoras
    - Intervalos flexíveis para cada ordem/pedido
    """

    def __init__(self, divisoras: List[DivisoraDeMassas]):
        self.divisoras = divisoras

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[DivisoraDeMassas]:
        ordenadas = sorted(
            self.divisoras,
            key=lambda d: atividade.fips_equipamentos.get(d, 999)
        )
        return ordenadas
    
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================  
    def _obter_capacidade_explicita_do_json(self, atividade: "AtividadeModular") -> Optional[float]:
        """
        🔍 Verifica se há um valor explícito de 'capacidade_gramas' no JSON da atividade
        para alguma chave que contenha 'divisora' no nome. Se houver, retorna esse valor.
        """
        try:
            config = atividade.configuracoes_equipamentos or {}
            for chave, conteudo in config.items():
                chave_normalizada = unicodedata.normalize("NFKD", chave).encode("ASCII", "ignore").decode("utf-8").lower()
                if "divisora" in chave_normalizada:
                    capacidade_gramas = conteudo.get("capacidade_gramas")
                    if capacidade_gramas is not None:
                        logger.info(
                            f"📦 JSON da atividade {atividade.id_atividade} define capacidade_gramas = {capacidade_gramas}g para o equipamento '{chave}'"
                        )
                        return capacidade_gramas
            logger.info(f"ℹ️ Nenhuma capacidade_gramas definida no JSON da atividade {atividade.id_atividade}.")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar capacidade_gramas no JSON da atividade: {e}")
            return None

    def _obter_flag_boleadora(self, atividade: "AtividadeModular", divisora: DivisoraDeMassas) -> bool:
        try:
            nome_bruto = divisora.nome.lower().replace(" ", "_")
            nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")

            config = atividade.configuracoes_equipamentos.get(nome_chave)
            if config:
                return str(config.get("boleadora", "False")).lower() == "true"
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter flag boleadora para {divisora.nome}: {e}")
        return False
    
    # ==========================================================
    # 🔍 Métodos auxiliares para extração de dados da atividade
    # ==========================================================
    def _obter_ids_atividade(self, atividade: "AtividadeModular") -> Tuple[int, int, int, int]:
        """
        Extrai os IDs da atividade de forma consistente.
        Retorna: (id_ordem, id_pedido, id_atividade, id_item)
        """
        id_ordem = getattr(atividade, 'id_ordem', 0)
        id_pedido = getattr(atividade, 'id_pedido', 0) 
        id_atividade = getattr(atividade, 'id_atividade', 0)
        id_item = getattr(atividade, 'id_item', 0)
        
        return id_ordem, id_pedido, id_atividade, id_item

    # ==========================================================
    # 🎯 Alocação principal - ATUALIZADA COM VALIDAÇÃO POR ITEM
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        **kwargs
    ) -> Tuple[bool, Optional[DivisoraDeMassas], Optional[datetime], Optional[datetime]]:

        # Extrai IDs da atividade
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        duracao = atividade.duracao
        horario_final_tentativa = fim

        divisoras_ordenadas = self._ordenar_por_fip(atividade)
        peso_json = self._obter_capacidade_explicita_do_json(atividade)
        
        # Determina quantidade final (JSON tem prioridade)
        if peso_json is not None:
            quantidade_final = peso_json
            logger.debug(
                f"📊 Usando capacidade_gramas do JSON para atividade {id_atividade}: "
                f"{quantidade_final}g (original: {quantidade_produto}g)"
            )
        else:
            quantidade_final = float(quantidade_produto)
            
        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for divisora in divisoras_ordenadas:
                # Verifica se pode alocar (só impede se item diferente com sobreposição)
                if not divisora.esta_disponivel_para_item(horario_inicio_tentativa, horario_final_tentativa, id_item):
                    continue

                # Verifica se a nova ocupação respeitará a capacidade em todos os momentos
                if not divisora.validar_nova_ocupacao_item(id_item, quantidade_final, horario_inicio_tentativa, horario_final_tentativa):
                    continue

                boleadora_flag = self._obter_flag_boleadora(atividade, divisora)

                sucesso = divisora.ocupar(
                    id_ordem=id_ordem,
                    id_pedido=id_pedido,
                    id_atividade=id_atividade,
                    id_item=id_item,
                    quantidade=quantidade_final,
                    inicio=horario_inicio_tentativa,
                    fim=horario_final_tentativa,
                    usar_boleadora=boleadora_flag
                )

                if sucesso:
                    atividade.equipamento_alocado = divisora
                    atividade.equipamentos_selecionados = [divisora]
                    atividade.alocada = True
                    atividade.inicio_planejado = horario_inicio_tentativa
                    atividade.fim_planejado = horario_final_tentativa

                    logger.info(
                        f"✅ Atividade {id_atividade} (Item {id_item}) alocada na {divisora.nome} "
                        f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')} "
                        f"com {quantidade_final}g (fonte: {'JSON' if peso_json else 'parâmetro'}) "
                        f"e boleadora={boleadora_flag}."
                    )
                    return True, divisora, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {id_atividade} (Item {id_item}) não pôde ser alocada em nenhuma divisora "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔄 Alocação com múltiplas divisoras
    # ==========================================================
    def alocar_multiplas_divisoras(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_total: float,
        max_divisoras: Optional[int] = None,
        **kwargs
    ) -> Tuple[bool, List[Tuple[DivisoraDeMassas, float]], Optional[datetime], Optional[datetime]]:
        """
        Aloca múltiplas divisoras se necessário para processar a quantidade total.
        Considera soma de quantidades do mesmo item em intervalos sobrepostos.
        
        Args:
            inicio: Horário de início da janela
            fim: Horário de fim da janela
            atividade: Atividade a ser alocada
            quantidade_total: Quantidade total a ser processada
            max_divisoras: Número máximo de divisoras a usar (None = sem limite)
            
        Returns:
            Tupla com (sucesso, lista de (divisora, quantidade), início, fim)
        """
        # Extrai IDs da atividade
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        duracao = atividade.duracao
        horario_final_tentativa = fim
        
        divisoras_ordenadas = self._ordenar_por_fip(atividade)
        
        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao
            
            divisoras_alocadas = []
            quantidade_restante = quantidade_total
            divisoras_tentadas = 0
            
            for divisora in divisoras_ordenadas:
                if max_divisoras and divisoras_tentadas >= max_divisoras:
                    break
                    
                # Verifica disponibilidade considerando mesmo item
                if not divisora.esta_disponivel_para_item(horario_inicio_tentativa, horario_final_tentativa, id_item):
                    continue
                
                # Determina capacidade máxima da divisora
                capacidade_maxima = divisora.capacidade_gramas_max
                
                if capacidade_maxima is None or capacidade_maxima <= 0:
                    continue
                
                # Calcula quanto já está sendo processado do mesmo item no período
                quantidade_atual_item = divisora.obter_quantidade_maxima_item_periodo(
                    id_item, horario_inicio_tentativa, horario_final_tentativa
                )
                
                # Determina capacidade disponível para o item
                capacidade_disponivel = capacidade_maxima - quantidade_atual_item
                
                if capacidade_disponivel <= 0:
                    continue
                    
                # Calcula quanto essa divisora pode processar adicionalmente
                quantidade_divisora = min(quantidade_restante, capacidade_disponivel)
                
                # Verifica se a quantidade mínima será respeitada
                if quantidade_divisora >= divisora.capacidade_gramas_min:
                    divisoras_alocadas.append((divisora, quantidade_divisora))
                    quantidade_restante -= quantidade_divisora
                    divisoras_tentadas += 1
                    
                    if quantidade_restante <= 0:
                        break
            
            # Se conseguiu alocar toda a quantidade
            if quantidade_restante <= 0:
                # Confirma as alocações
                todas_alocadas = True
                for divisora, qtd in divisoras_alocadas:
                    boleadora_flag = self._obter_flag_boleadora(atividade, divisora)
                    sucesso = divisora.ocupar(
                        id_ordem=id_ordem,
                        id_pedido=id_pedido,
                        id_atividade=id_atividade,
                        id_item=id_item,
                        quantidade=qtd,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        usar_boleadora=boleadora_flag
                    )
                    if not sucesso:
                        todas_alocadas = False
                        # Libera as já alocadas
                        for d_liberada, _ in divisoras_alocadas:
                            d_liberada.liberar_por_atividade(
                                id_atividade=id_atividade,
                                id_pedido=id_pedido,
                                id_ordem=id_ordem
                            )
                        break
                
                if todas_alocadas:
                    atividade.equipamentos_selecionados = [d for d, _ in divisoras_alocadas]
                    atividade.alocada = True
                    
                    logger.info(
                        f"✅ Atividade {id_atividade} (Item {id_item}) alocada em {len(divisoras_alocadas)} divisoras "
                        f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}:"
                    )
                    for divisora, qtd in divisoras_alocadas:
                        logger.info(f"   🔹 {divisora.nome}: {qtd}g")
                    
                    return True, divisoras_alocadas, horario_inicio_tentativa, horario_final_tentativa
            
            horario_final_tentativa -= timedelta(minutes=1)
        
        logger.warning(
            f"❌ Não foi possível alocar {quantidade_total}g do item {id_item} em múltiplas divisoras "
            f"para atividade {id_atividade}"
        )
        return False, [], None, None
    
    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular") -> None:
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for divisora in self.divisoras:
            divisora.liberar_por_atividade(id_ordem=id_ordem, id_pedido=id_pedido, id_atividade=id_atividade)

    def liberar_por_pedido(self, atividade: "AtividadeModular") -> None:
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for divisora in self.divisoras:
            divisora.liberar_por_pedido(id_ordem=id_ordem, id_pedido=id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular") -> None:
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for divisora in self.divisoras:
            divisora.liberar_por_ordem(id_ordem=id_ordem)

    def liberar_por_item(self, id_item: int):
        """
        🔓 Libera todas as ocupações de um item específico em todas as divisoras.
        """
        for divisora in self.divisoras:
            divisora.liberar_por_item(id_item)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime) -> None:
        for divisora in self.divisoras:
            divisora.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for divisora in self.divisoras:
            divisora.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Divisoras")
        logger.info("==============================================")
        for divisora in self.divisoras:
            divisora.mostrar_agenda()

    # ==========================================================
    # 📊 Status e Análise
    # ==========================================================
    def obter_status_divisoras(self) -> dict:
        """
        Retorna o status atual de todas as divisoras.
        """
        status = {}
        for divisora in self.divisoras:
            ocupacoes_ativas = [
                {
                    'id_ordem': oc[0],
                    'id_pedido': oc[1],
                    'id_atividade': oc[2],
                    'id_item': oc[3],
                    'quantidade': oc[4],
                    'usa_boleadora': oc[5],
                    'inicio': oc[6].strftime('%H:%M'),
                    'fim': oc[7].strftime('%H:%M')
                }
                for oc in divisora.ocupacoes
            ]
            
            status[divisora.nome] = {
                'capacidade_minima': divisora.capacidade_gramas_min,
                'capacidade_maxima': divisora.capacidade_gramas_max,
                'tem_boleadora': divisora.boleadora,
                'total_ocupacoes': len(divisora.ocupacoes),
                'ocupacoes_ativas': ocupacoes_ativas
            }
        
        return status

    def verificar_disponibilidade(
        self,
        inicio: datetime,
        fim: datetime,
        id_item: Optional[int] = None,
        quantidade: Optional[float] = None
    ) -> List[DivisoraDeMassas]:
        """
        Verifica quais divisoras estão disponíveis no período para um item específico.
        """
        disponiveis = []
        
        for divisora in self.divisoras:
            if id_item is not None:
                if divisora.esta_disponivel_para_item(inicio, fim, id_item):
                    if quantidade is None:
                        disponiveis.append(divisora)
                    else:
                        # Verifica se pode adicionar a quantidade especificada
                        if divisora.validar_nova_ocupacao_item(id_item, quantidade, inicio, fim):
                            disponiveis.append(divisora)
            else:
                # Comportamento original para compatibilidade
                if divisora.esta_disponivel(inicio, fim):
                    if quantidade is None or divisora.validar_capacidade(quantidade):
                        disponiveis.append(divisora)
        
        return disponiveis

    def obter_utilizacao_por_item(self, id_item: int) -> dict:
        """
        📊 Retorna informações de utilização de um item específico em todas as divisoras.
        """
        utilizacao = {}
        
        for divisora in self.divisoras:
            utilizacao_divisora = divisora.obter_utilizacao_por_item(id_item)
            if utilizacao_divisora:
                utilizacao[divisora.nome] = utilizacao_divisora
        
        return utilizacao

    def calcular_pico_utilizacao_item(self, id_item: int) -> dict:
        """
        📈 Calcula o pico de utilização de um item específico em cada divisora.
        """
        picos = {}
        
        for divisora in self.divisoras:
            pico_divisora = divisora.calcular_pico_utilizacao_item(id_item)
            if pico_divisora:
                picos[divisora.nome] = pico_divisora
        
        return picos

    def obter_capacidade_total_disponivel_item(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        📊 Calcula a capacidade total disponível para um item específico no período.
        """
        capacidade_total_disponivel = 0.0
        
        for divisora in self.divisoras:
            if divisora.esta_disponivel_para_item(inicio, fim, id_item):
                quantidade_atual = divisora.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
                capacidade_disponivel = divisora.capacidade_gramas_max - quantidade_atual
                capacidade_total_disponivel += max(0, capacidade_disponivel)
        
        return capacidade_total_disponivel

    def otimizar_distribuicao_item(
        self, 
        id_item: int, 
        quantidade_total: float, 
        inicio: datetime, 
        fim: datetime
    ) -> List[Tuple[DivisoraDeMassas, float]]:
        """
        📊 Otimiza a distribuição de uma quantidade total de um item entre divisoras disponíveis.
        Retorna lista de (divisora, quantidade_sugerida).
        """
        divisoras_disponiveis = []
        
        # Coleta divisoras disponíveis e suas capacidades
        for divisora in self.divisoras:
            if divisora.esta_disponivel_para_item(inicio, fim, id_item):
                quantidade_atual = divisora.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
                capacidade_disponivel = divisora.capacidade_gramas_max - quantidade_atual
                
                if capacidade_disponivel >= divisora.capacidade_gramas_min:
                    divisoras_disponiveis.append((divisora, capacidade_disponivel))
        
        if not divisoras_disponiveis:
            return []
        
        # Ordena por capacidade disponível (maior primeiro)
        divisoras_disponiveis.sort(key=lambda x: x[1], reverse=True)
        
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for divisora, capacidade_disponivel in divisoras_disponiveis:
            if quantidade_restante <= 0:
                break
                
            quantidade_alocar = min(quantidade_restante, capacidade_disponivel)
            
            if quantidade_alocar >= divisora.capacidade_gramas_min:
                distribuicao.append((divisora, quantidade_alocar))
                quantidade_restante -= quantidade_alocar
        
        return distribuicao