from datetime import datetime, timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING
from models.equipamentos.embaladora import Embaladora
from enums.equipamentos.tipo_embalagem import TipoEmbalagem
from utils.logs.logger_factory import setup_logger
import unicodedata

if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular

logger = setup_logger("GestorEmbaladoras")

class GestorEmbaladoras:
    """
    ✉️ Gestor responsável pela alocação de Embaladoras.
    Utiliza backward scheduling com validação por tipo de embalagem e capacidade.
    
    Funcionalidades:
    - Soma quantidades do mesmo id_item em intervalos sobrepostos  
    - Validação de capacidade dinâmica considerando todos os momentos de sobreposição
    - Priorização por FIP com possibilidade de múltiplas embaladoras
    - Intervalos flexíveis para cada ordem/pedido
    """

    def __init__(self, embaladoras: List[Embaladora]):
        self.embaladoras = embaladoras

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
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Embaladora]:
        return sorted(
            self.embaladoras,
            key=lambda e: atividade.fips_equipamentos.get(e, 999)
        )
        
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    def _obter_capacidade_explicita_do_json(self, atividade: "AtividadeModular") -> Optional[float]:
        """
        🔍 Verifica se há um valor explícito de 'capacidade_gramas' no JSON da atividade
        para alguma chave que contenha 'embaladora' no nome. Se houver, retorna esse valor.
        """
        try:
            config = atividade.configuracoes_equipamentos or {}
            for chave, conteudo in config.items():
                chave_normalizada = unicodedata.normalize("NFKD", chave).encode("ASCII", "ignore").decode("utf-8").lower()
                if "embaladora" in chave_normalizada:
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

    def _normalizar_nome(self, nome: str) -> str:
        return nome.strip().lower().replace(" ", "_")
    
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
    ) -> Tuple[bool, Optional[Embaladora], Optional[datetime], Optional[datetime]]:

        # Extrai IDs da atividade
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)

        duracao = atividade.duracao
        horario_final = fim
        embaladoras_ordenadas = self._ordenar_por_fip(atividade)

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
            
        while horario_final - duracao >= inicio:
            horario_inicio = horario_final - duracao

            for embaladora in embaladoras_ordenadas:
                # Verifica se pode alocar (só impede se item diferente com sobreposição)
                if not embaladora.esta_disponivel_para_item(horario_inicio, horario_final, id_item):
                    continue

                # Verifica se a nova ocupação respeitará a capacidade em todos os momentos
                if not embaladora.validar_nova_ocupacao_item(id_item, quantidade_final, horario_inicio, horario_final):
                    continue

                # Obtém configuração de tipos de embalagem
                nome_eqp = self._normalizar_nome(embaladora.nome)
                config_emb = atividade.configuracoes_equipamentos.get(nome_eqp, {})
                tipos_embalagem_strs = config_emb.get("tipo_embalagem", [])

                try:
                    tipos_embalagem = [TipoEmbalagem[t.upper()] for t in tipos_embalagem_strs]
                except KeyError as e:
                    logger.warning(f"⚠️ Tipo de embalagem inválido para {embaladora.nome}: {e}")
                    continue

                sucesso = embaladora.ocupar(
                    id_ordem=id_ordem,
                    id_pedido=id_pedido,
                    id_atividade=id_atividade,
                    id_item=id_item,
                    quantidade=quantidade_final,
                    lista_tipo_embalagem=tipos_embalagem,
                    inicio=horario_inicio,
                    fim=horario_final
                )

                if sucesso:
                    atividade.equipamento_alocado = embaladora
                    atividade.equipamentos_selecionados = [embaladora]
                    atividade.inicio_planejado = horario_inicio
                    atividade.fim_planejado = horario_final
                    atividade.alocada = True

                    logger.info(
                        f"✅ Atividade {id_atividade} (Item {id_item}) alocada na embaladora {embaladora.nome} "
                        f"de {horario_inicio.strftime('%H:%M')} até {horario_final.strftime('%H:%M')} "
                        f"com {quantidade_final}g (fonte: {'JSON' if peso_json else 'parâmetro'})."
                    )
                    return True, embaladora, horario_inicio, horario_final

            horario_final -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {id_atividade} (Item {id_item}) não pôde ser alocada em nenhuma embaladora "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔄 Alocação com múltiplas embaladoras
    # ==========================================================
    def alocar_multiplas_embaladoras(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_total: float,
        max_embaladoras: Optional[int] = None,
        **kwargs
    ) -> Tuple[bool, List[Tuple[Embaladora, float]], Optional[datetime], Optional[datetime]]:
        """
        Aloca múltiplas embaladoras se necessário para processar a quantidade total.
        Considera soma de quantidades do mesmo item em intervalos sobrepostos.
        
        Args:
            inicio: Horário de início da janela
            fim: Horário de fim da janela
            atividade: Atividade a ser alocada
            quantidade_total: Quantidade total a ser processada
            max_embaladoras: Número máximo de embaladoras a usar (None = sem limite)
            
        Returns:
            Tupla com (sucesso, lista de (embaladora, quantidade), início, fim)
        """
        # Extrai IDs da atividade
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        duracao = atividade.duracao
        horario_final_tentativa = fim
        
        embaladoras_ordenadas = self._ordenar_por_fip(atividade)
        
        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao
            
            embaladoras_alocadas = []
            quantidade_restante = quantidade_total
            embaladoras_tentadas = 0
            
            for embaladora in embaladoras_ordenadas:
                if max_embaladoras and embaladoras_tentadas >= max_embaladoras:
                    break
                    
                # Verifica disponibilidade considerando mesmo item
                if not embaladora.esta_disponivel_para_item(horario_inicio_tentativa, horario_final_tentativa, id_item):
                    continue
                
                # Determina capacidade máxima da embaladora
                capacidade_maxima = embaladora.capacidade_gramas
                
                if capacidade_maxima is None or capacidade_maxima <= 0:
                    continue
                
                # Calcula quanto já está sendo processado do mesmo item no período
                quantidade_atual_item = embaladora.obter_quantidade_maxima_item_periodo(
                    id_item, horario_inicio_tentativa, horario_final_tentativa
                )
                
                # Determina capacidade disponível para o item
                capacidade_disponivel = capacidade_maxima - quantidade_atual_item
                
                if capacidade_disponivel <= 0:
                    continue
                    
                # Calcula quanto essa embaladora pode processar adicionalmente
                quantidade_embaladora = min(quantidade_restante, capacidade_disponivel)
                
                # Verifica se consegue processar alguma quantidade útil
                if quantidade_embaladora > 0:
                    embaladoras_alocadas.append((embaladora, quantidade_embaladora))
                    quantidade_restante -= quantidade_embaladora
                    embaladoras_tentadas += 1
                    
                    if quantidade_restante <= 0:
                        break
            
            # Se conseguiu alocar toda a quantidade
            if quantidade_restante <= 0:
                # Confirma as alocações
                todas_alocadas = True
                for embaladora, qtd in embaladoras_alocadas:
                    # Obtém configuração de tipos de embalagem
                    nome_eqp = self._normalizar_nome(embaladora.nome)
                    config_emb = atividade.configuracoes_equipamentos.get(nome_eqp, {})
                    tipos_embalagem_strs = config_emb.get("tipo_embalagem", [])

                    try:
                        tipos_embalagem = [TipoEmbalagem[t.upper()] for t in tipos_embalagem_strs]
                    except KeyError as e:
                        logger.warning(f"⚠️ Tipo de embalagem inválido para {embaladora.nome}: {e}")
                        todas_alocadas = False
                        break

                    sucesso = embaladora.ocupar(
                        id_ordem=id_ordem,
                        id_pedido=id_pedido,
                        id_atividade=id_atividade,
                        id_item=id_item,
                        quantidade=qtd,
                        lista_tipo_embalagem=tipos_embalagem,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa
                    )
                    if not sucesso:
                        todas_alocadas = False
                        # Libera as já alocadas
                        for e_liberada, _ in embaladoras_alocadas:
                            e_liberada.liberar_por_atividade(
                                id_ordem=id_ordem,
                                id_pedido=id_pedido,
                                id_atividade=id_atividade
                            )
                        break
                
                if todas_alocadas:
                    atividade.equipamentos_selecionados = [e for e, _ in embaladoras_alocadas]
                    atividade.alocada = True
                    
                    logger.info(
                        f"✅ Atividade {id_atividade} (Item {id_item}) alocada em {len(embaladoras_alocadas)} embaladoras "
                        f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}:"
                    )
                    for embaladora, qtd in embaladoras_alocadas:
                        logger.info(f"   🔹 {embaladora.nome}: {qtd}g")
                    
                    return True, embaladoras_alocadas, horario_inicio_tentativa, horario_final_tentativa
            
            horario_final_tentativa -= timedelta(minutes=1)
        
        logger.warning(
            f"❌ Não foi possível alocar {quantidade_total}g do item {id_item} em múltiplas embaladoras "
            f"para atividade {id_atividade}"
        )
        return False, [], None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for emb in self.embaladoras:
            emb.liberar_por_atividade(id_ordem, id_pedido, id_atividade)

    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for emb in self.embaladoras:
            emb.liberar_por_pedido(id_ordem, id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for emb in self.embaladoras:
            emb.liberar_por_ordem(id_ordem)

    def liberar_por_item(self, id_item: int):
        """
        🔓 Libera todas as ocupações de um item específico em todas as embaladoras.
        """
        for embaladora in self.embaladoras:
            embaladora.liberar_por_item(id_item)
    
    def liberar_ocupacoes_anteriores_a(self, horario_atual: datetime):
        for emb in self.embaladoras:
            emb.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for embaladora in self.embaladoras:
            embaladora.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Embaladoras")
        logger.info("==============================================")
        for emb in self.embaladoras:
            emb.mostrar_agenda()

    # ==========================================================
    # 📊 Status e Análise
    # ==========================================================
    def obter_status_embaladoras(self) -> dict:
        """
        Retorna o status atual de todas as embaladoras.
        """
        status = {}
        for embaladora in self.embaladoras:
            ocupacoes_ativas = [
                {
                    'id_ordem': oc[0],
                    'id_pedido': oc[1],
                    'id_atividade': oc[2],
                    'id_item': oc[3],
                    'quantidade': oc[4],
                    'tipos_embalagem': [emb.name for emb in oc[5]],
                    'inicio': oc[6].strftime('%H:%M'),
                    'fim': oc[7].strftime('%H:%M')
                }
                for oc in embaladora.ocupacoes
            ]
            
            status[embaladora.nome] = {
                'capacidade_maxima': embaladora.capacidade_gramas,
                'tipos_embalagem_suportados': [emb.name for emb in embaladora.lista_tipo_embalagem],
                'total_ocupacoes': len(embaladora.ocupacoes),
                'ocupacoes_ativas': ocupacoes_ativas
            }
        
        return status

    def verificar_disponibilidade(
        self,
        inicio: datetime,
        fim: datetime,
        id_item: Optional[int] = None,
        quantidade: Optional[float] = None
    ) -> List[Embaladora]:
        """
        Verifica quais embaladoras estão disponíveis no período para um item específico.
        """
        disponiveis = []
        
        for embaladora in self.embaladoras:
            if id_item is not None:
                if embaladora.esta_disponivel_para_item(inicio, fim, id_item):
                    if quantidade is None:
                        disponiveis.append(embaladora)
                    else:
                        # Verifica se pode adicionar a quantidade especificada
                        if embaladora.validar_nova_ocupacao_item(id_item, quantidade, inicio, fim):
                            disponiveis.append(embaladora)
            else:
                # Comportamento original para compatibilidade
                if embaladora.esta_disponivel(inicio, fim):
                    if quantidade is None or embaladora.validar_capacidade(quantidade):
                        disponiveis.append(embaladora)
        
        return disponiveis

    def obter_utilizacao_por_item(self, id_item: int) -> dict:
        """
        📊 Retorna informações de utilização de um item específico em todas as embaladoras.
        """
        utilizacao = {}
        
        for embaladora in self.embaladoras:
            utilizacao_embaladora = embaladora.obter_utilizacao_por_item(id_item)
            if utilizacao_embaladora:
                utilizacao[embaladora.nome] = utilizacao_embaladora
        
        return utilizacao

    def calcular_pico_utilizacao_item(self, id_item: int) -> dict:
        """
        📈 Calcula o pico de utilização de um item específico em cada embaladora.
        """
        picos = {}
        
        for embaladora in self.embaladoras:
            pico_embaladora = embaladora.calcular_pico_utilizacao_item(id_item)
            if pico_embaladora:
                picos[embaladora.nome] = pico_embaladora
        
        return picos

    def obter_capacidade_total_disponivel_item(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        📊 Calcula a capacidade total disponível para um item específico no período.
        """
        capacidade_total_disponivel = 0.0
        
        for embaladora in self.embaladoras:
            if embaladora.esta_disponivel_para_item(inicio, fim, id_item):
                quantidade_atual = embaladora.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
                capacidade_disponivel = embaladora.capacidade_gramas - quantidade_atual
                capacidade_total_disponivel += max(0, capacidade_disponivel)
        
        return capacidade_total_disponivel

    def otimizar_distribuicao_item(
        self, 
        id_item: int, 
        quantidade_total: float, 
        inicio: datetime, 
        fim: datetime
    ) -> List[Tuple[Embaladora, float]]:
        """
        📊 Otimiza a distribuição de uma quantidade total de um item entre embaladoras disponíveis.
        Retorna lista de (embaladora, quantidade_sugerida).
        """
        embaladoras_disponiveis = []
        
        # Coleta embaladoras disponíveis e suas capacidades
        for embaladora in self.embaladoras:
            if embaladora.esta_disponivel_para_item(inicio, fim, id_item):
                quantidade_atual = embaladora.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
                capacidade_disponivel = embaladora.capacidade_gramas - quantidade_atual
                
                if capacidade_disponivel > 0:
                    embaladoras_disponiveis.append((embaladora, capacidade_disponivel))
        
        if not embaladoras_disponiveis:
            return []
        
        # Ordena por capacidade disponível (maior primeiro)
        embaladoras_disponiveis.sort(key=lambda x: x[1], reverse=True)
        
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for embaladora, capacidade_disponivel in embaladoras_disponiveis:
            if quantidade_restante <= 0:
                break
                
            quantidade_alocar = min(quantidade_restante, capacidade_disponivel)
            
            if quantidade_alocar > 0:
                distribuicao.append((embaladora, quantidade_alocar))
                quantidade_restante -= quantidade_alocar
        
        return distribuicao

    def obter_estatisticas_embalagem_global(self, inicio: datetime, fim: datetime) -> dict:
        """
        📊 Retorna estatísticas globais de uso por tipo de embalagem em todas as embaladoras.
        """
        estatisticas_globais = {}
        
        for embaladora in self.embaladoras:
            estatisticas_emb = embaladora.obter_estatisticas_embalagem(inicio, fim)
            
            for tipo_embalagem, dados in estatisticas_emb.items():
                if tipo_embalagem not in estatisticas_globais:
                    estatisticas_globais[tipo_embalagem] = {
                        'quantidade_total': 0.0,
                        'ocorrencias_total': 0,
                        'embaladoras_utilizadas': set()
                    }
                
                estatisticas_globais[tipo_embalagem]['quantidade_total'] += dados['quantidade_total']
                estatisticas_globais[tipo_embalagem]['ocorrencias_total'] += dados['ocorrencias']
                estatisticas_globais[tipo_embalagem]['embaladoras_utilizadas'].add(embaladora.nome)
        
        # Converte sets para listas para serialização
        for tipo_embalagem in estatisticas_globais:
            estatisticas_globais[tipo_embalagem]['embaladoras_utilizadas'] = list(
                estatisticas_globais[tipo_embalagem]['embaladoras_utilizadas']
            )
        
        return estatisticas_globais