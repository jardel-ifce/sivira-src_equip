from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Union, TYPE_CHECKING
from models.equipamentos.batedeira_industrial import BatedeiraIndustrial
from models.equipamentos.batedeira_planetaria import BatedeiraPlanetaria
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logs.logger_factory import setup_logger
import unicodedata

# 🏭 Logger específico para o gestor de batedeiras
logger = setup_logger('GestorBatedeiras')

Batedeiras = Union[BatedeiraIndustrial, BatedeiraPlanetaria]


class GestorBatedeiras:
    """
    🏭 Gestor especializado para controle de batedeiras industriais e planetárias,
    utilizando backward scheduling com prioridade por FIP.
    
    Funcionalidades:
    - Soma quantidades do mesmo id_item em intervalos sobrepostos
    - Validação de capacidade dinâmica considerando todos os momentos de sobreposição
    - Priorização por FIP com possibilidade de múltiplas batedeiras
    - Intervalos flexíveis para cada ordem/pedido
    """

    def __init__(self, batedeiras: List[Batedeiras]):
        self.batedeiras = batedeiras

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Batedeiras]:
        ordenadas = sorted(
            self.batedeiras,
            key=lambda b: atividade.fips_equipamentos.get(b, 999)
        )
        return ordenadas

    # ==========================================================
    # 🔁 Obter velocidade 
    # ==========================================================
    def _obter_velocidade(self, atividade: "AtividadeModular", batedeira: Batedeiras) -> Optional[int]:
        """
        🔍 Busca no JSON a velocidade (inteira) configurada para a batedeira específica,
        retornando None se não encontrar.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = batedeira.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                
                logger.debug(f"🔎 Procurando velocidade para: '{nome_chave}'")
                logger.debug(f"🗂️ Chaves disponíveis: {list(atividade.configuracoes_equipamentos.keys())}")

                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "velocidade" in config:
                    velocidade = int(config["velocidade"])
                    logger.debug(f"✅ Velocidade encontrada para {nome_chave}: {velocidade}")
                    return velocidade
                else:
                    logger.debug(f"❌ Nenhuma velocidade definida para: '{nome_chave}'")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter velocidade para {batedeira.nome}: {e}")
        return None

    # ==========================================================
    # 📏 Obter capacidade em gramas
    # ==========================================================
    def _obter_capacidade_gramas(self, atividade: "AtividadeModular", batedeira: Batedeiras) -> Optional[int]:
        """
        Obtém a capacidade de gramas da batedeira da configuração da atividade.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = batedeira.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                
                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "capacidade_gramas" in config:
                    capacidade = int(config["capacidade_gramas"])
                    logger.debug(f"✅ Capacidade em gramas encontrada para {nome_chave}: {capacidade}g")
                    return capacidade
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter capacidade gramas para {batedeira.nome}: {e}")
        return None

    # ==========================================================
    # 🎯 Alocação principal
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade: float,
        id_item: int
    ) -> Tuple[bool, Optional[Batedeiras], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        horario_final_tentativa = fim

        # Primeiro tenta obter capacidade_gramas do JSON para cada batedeira
        # Se não encontrar, usa o parâmetro quantidade
        batedeiras_ordenadas = self._ordenar_por_fip(atividade)

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for batedeira in batedeiras_ordenadas:
                # Determina a quantidade a ser usada: capacidade_gramas do JSON ou parâmetro quantidade
                capacidade_gramas = self._obter_capacidade_gramas(atividade, batedeira)
                quantidade_final = capacidade_gramas if capacidade_gramas is not None else quantidade
                
                if quantidade_final != quantidade:
                    logger.debug(
                        f"📊 Usando capacidade_gramas do JSON para {batedeira.nome}: "
                        f"{quantidade_final}g (original: {quantidade}g)"
                    )
                
                # Verifica se pode alocar (só impede se item diferente com sobreposição)
                if not batedeira.esta_disponivel_para_item(horario_inicio_tentativa, horario_final_tentativa, id_item):
                    continue

                velocidade_configurada = self._obter_velocidade(atividade, batedeira)

                sucesso = batedeira.ocupar(
                    id_ordem=atividade.id_ordem,
                    id_pedido=atividade.id_pedido,
                    id_atividade=atividade.id_atividade,
                    id_item=id_item,
                    quantidade_gramas=quantidade_final,
                    inicio=horario_inicio_tentativa,
                    fim=horario_final_tentativa,
                    velocidade=velocidade_configurada
                )
                if sucesso:
                    atividade.equipamento_alocado = batedeira
                    atividade.equipamentos_selecionados = [batedeira]
                    atividade.alocada = True

                    logger.info(
                        f"✅ Atividade {atividade.id_atividade} (Item {id_item}) alocada na batedeira {batedeira.nome} "
                        f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')} "
                        f"com {quantidade_final}g (fonte: {'JSON' if capacidade_gramas else 'parâmetro'})."
                    )
                    return True, batedeira, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {atividade.id_atividade} (Item {id_item}) não pôde ser alocada em nenhuma batedeira "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔄 Alocação com múltiplas batedeiras
    # ==========================================================
    def alocar_multiplas_batedeiras(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_total: float,
        id_item: int,
        max_batedeiras: Optional[int] = None
    ) -> Tuple[bool, List[Tuple[Batedeiras, float]], Optional[datetime], Optional[datetime]]:
        """
        Aloca múltiplas batedeiras se necessário para processar a quantidade total.
        Considera soma de quantidades do mesmo item em intervalos sobrepostos.
        
        Args:
            inicio: Horário de início da janela
            fim: Horário de fim da janela
            atividade: Atividade a ser alocada
            quantidade_total: Quantidade total a ser processada
            id_item: ID do item a ser processado
            max_batedeiras: Número máximo de batedeiras a usar (None = sem limite)
            
        Returns:
            Tupla com (sucesso, lista de (batedeira, quantidade), início, fim)
        """
        duracao = atividade.duracao
        horario_final_tentativa = fim
        
        batedeiras_ordenadas = self._ordenar_por_fip(atividade)
        
        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao
            
            batedeiras_alocadas = []
            quantidade_restante = quantidade_total
            batedeiras_tentadas = 0
            
            for batedeira in batedeiras_ordenadas:
                if max_batedeiras and batedeiras_tentadas >= max_batedeiras:
                    break
                    
                # Verifica disponibilidade considerando mesmo item
                if not batedeira.esta_disponivel_para_item(horario_inicio_tentativa, horario_final_tentativa, id_item):
                    continue
                
                # Determina capacidade da batedeira
                capacidade_gramas = self._obter_capacidade_gramas(atividade, batedeira)
                capacidade_maxima = capacidade_gramas if capacidade_gramas else batedeira.capacidade_gramas_max
                
                if capacidade_maxima is None or capacidade_maxima <= 0:
                    continue
                
                # Calcula quanto já está sendo processado do mesmo item no período
                quantidade_atual_item = batedeira.obter_quantidade_maxima_item_periodo(
                    id_item, horario_inicio_tentativa, horario_final_tentativa
                )
                
                # Determina capacidade disponível para o item
                capacidade_disponivel = capacidade_maxima - quantidade_atual_item
                
                if capacidade_disponivel <= 0:
                    continue
                    
                # Calcula quanto essa batedeira pode processar adicionalmente
                quantidade_batedeira = min(quantidade_restante, capacidade_disponivel)
                
                # Verifica se a quantidade mínima será respeitada
                if quantidade_batedeira >= batedeira.capacidade_gramas_min:
                    batedeiras_alocadas.append((batedeira, quantidade_batedeira))
                    quantidade_restante -= quantidade_batedeira
                    batedeiras_tentadas += 1
                    
                    if quantidade_restante <= 0:
                        break
            
            # Se conseguiu alocar toda a quantidade
            if quantidade_restante <= 0:
                # Confirma as alocações
                todas_alocadas = True
                for batedeira, qtd in batedeiras_alocadas:
                    velocidade = self._obter_velocidade(atividade, batedeira)
                    sucesso = batedeira.ocupar(
                        id_ordem=atividade.id_ordem,
                        id_pedido=atividade.id_pedido,
                        id_atividade=atividade.id_atividade,
                        id_item=id_item,
                        quantidade_gramas=qtd,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa,
                        velocidade=velocidade
                    )
                    if not sucesso:
                        todas_alocadas = False
                        # Libera as já alocadas
                        for b_liberada, _ in batedeiras_alocadas:
                            b_liberada.liberar_por_atividade(
                                id_atividade=atividade.id_atividade,
                                id_pedido=atividade.id_pedido,
                                id_ordem=atividade.id_ordem
                            )
                        break
                
                if todas_alocadas:
                    atividade.equipamentos_selecionados = [b for b, _ in batedeiras_alocadas]
                    atividade.alocada = True
                    
                    logger.info(
                        f"✅ Atividade {atividade.id_atividade} (Item {id_item}) alocada em {len(batedeiras_alocadas)} batedeiras "
                        f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}:"
                    )
                    for batedeira, qtd in batedeiras_alocadas:
                        logger.info(f"   🔹 {batedeira.nome}: {qtd}g")
                    
                    return True, batedeiras_alocadas, horario_inicio_tentativa, horario_final_tentativa
            
            horario_final_tentativa -= timedelta(minutes=1)
        
        logger.warning(
            f"❌ Não foi possível alocar {quantidade_total}g do item {id_item} em múltiplas batedeiras "
            f"para atividade {atividade.id_atividade}"
        )
        return False, [], None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for batedeira in self.batedeiras:
            batedeira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        for batedeira in self.batedeiras:
            batedeira.liberar_por_atividade(id_atividade=atividade.id_atividade, id_pedido=atividade.id_pedido, id_ordem=atividade.id_ordem)
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for batedeira in self.batedeiras:
            batedeira.liberar_por_pedido(id_ordem=atividade.id_ordem, id_pedido=atividade.id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for batedeira in self.batedeiras:
            batedeira.liberar_por_ordem(atividade.id_ordem)

    def liberar_por_item(self, id_item: int):
        """
        🔓 Libera todas as ocupações de um item específico em todas as batedeiras.
        """
        for batedeira in self.batedeiras:
            batedeira.liberar_por_item(id_item)

    def liberar_todas_ocupacoes(self):
        for batedeira in self.batedeiras:
            batedeira.ocupacoes.clear()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Batedeiras")
        logger.info("==============================================")
        for batedeira in self.batedeiras:
            batedeira.mostrar_agenda()

    # ==========================================================
    # 📊 Status e Análise
    # ==========================================================
    def obter_status_batedeiras(self) -> dict:
        """
        Retorna o status atual de todas as batedeiras.
        """
        status = {}
        for batedeira in self.batedeiras:
            ocupacoes_ativas = [
                {
                    'id_ordem': oc[0],
                    'id_pedido': oc[1],
                    'id_atividade': oc[2],
                    'id_item': oc[3],
                    'quantidade': oc[4],
                    'velocidade': oc[5],
                    'inicio': oc[6].strftime('%H:%M'),
                    'fim': oc[7].strftime('%H:%M')
                }
                for oc in batedeira.ocupacoes
            ]
            
            status[batedeira.nome] = {
                'capacidade_minima': batedeira.capacidade_gramas_min,
                'capacidade_maxima': batedeira.capacidade_gramas_max,
                'total_ocupacoes': len(batedeira.ocupacoes),
                'ocupacoes_ativas': ocupacoes_ativas
            }
        
        return status

    def verificar_disponibilidade(
        self,
        inicio: datetime,
        fim: datetime,
        id_item: Optional[int] = None,
        quantidade: Optional[float] = None
    ) -> List[Batedeiras]:
        """
        Verifica quais batedeiras estão disponíveis no período para um item específico.
        """
        disponiveis = []
        
        for batedeira in self.batedeiras:
            if id_item is not None:
                if batedeira.esta_disponivel_para_item(inicio, fim, id_item):
                    if quantidade is None:
                        disponiveis.append(batedeira)
                    else:
                        # Verifica se pode adicionar a quantidade especificada
                        if batedeira.validar_nova_ocupacao_item(id_item, quantidade, inicio, fim):
                            disponiveis.append(batedeira)
            else:
                # Comportamento original para compatibilidade
                if batedeira.esta_disponivel(inicio, fim):
                    if quantidade is None or batedeira.validar_capacidade(quantidade):
                        disponiveis.append(batedeira)
        
        return disponiveis

    def obter_utilizacao_por_item(self, id_item: int) -> dict:
        """
        📊 Retorna informações de utilização de um item específico em todas as batedeiras.
        """
        utilizacao = {}
        
        for batedeira in self.batedeiras:
            ocupacoes_item = [
                oc for oc in batedeira.ocupacoes if oc[3] == id_item
            ]
            
            if ocupacoes_item:
                quantidade_total = sum(oc[4] for oc in ocupacoes_item)
                periodo_inicio = min(oc[6] for oc in ocupacoes_item)
                periodo_fim = max(oc[7] for oc in ocupacoes_item)
                
                utilizacao[batedeira.nome] = {
                    'quantidade_total': quantidade_total,
                    'num_ocupacoes': len(ocupacoes_item),
                    'periodo_inicio': periodo_inicio.strftime('%H:%M'),
                    'periodo_fim': periodo_fim.strftime('%H:%M'),
                    'ocupacoes': [
                        {
                            'id_ordem': oc[0],
                            'id_pedido': oc[1],
                            'quantidade': oc[4],
                            'inicio': oc[6].strftime('%H:%M'),
                            'fim': oc[7].strftime('%H:%M')
                        }
                        for oc in ocupacoes_item
                    ]
                }
        
        return utilizacao

    def calcular_pico_utilizacao_item(self, id_item: int) -> dict:
        """
        📈 Calcula o pico de utilização de um item específico em cada batedeira.
        """
        picos = {}
        
        for batedeira in self.batedeiras:
            ocupacoes_item = [oc for oc in batedeira.ocupacoes if oc[3] == id_item]
            
            if not ocupacoes_item:
                continue
                
            # Coleta todos os pontos temporais
            pontos_temporais = set()
            for oc in ocupacoes_item:
                pontos_temporais.add(oc[6])  # início
                pontos_temporais.add(oc[7])  # fim
            
            pontos_ordenados = sorted(pontos_temporais)
            
            pico_quantidade = 0.0
            momento_pico = None
            
            # Analisa cada intervalo
            for i in range(len(pontos_ordenados) - 1):
                momento_inicio = pontos_ordenados[i]
                momento_fim = pontos_ordenados[i + 1]
                momento_meio = momento_inicio + (momento_fim - momento_inicio) / 2
                
                quantidade_momento = 0.0
                for oc in ocupacoes_item:
                    if oc[6] <= momento_meio < oc[7]:
                        quantidade_momento += oc[4]
                
                if quantidade_momento > pico_quantidade:
                    pico_quantidade = quantidade_momento
                    momento_pico = momento_meio
            
            if momento_pico:
                picos[batedeira.nome] = {
                    'pico_quantidade': pico_quantidade,
                    'momento_pico': momento_pico.strftime('%H:%M'),
                    'percentual_capacidade': (pico_quantidade / batedeira.capacidade_gramas_max) * 100
                }
        
        return picos