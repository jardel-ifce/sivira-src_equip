from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union, TYPE_CHECKING
from models.equipamentos.camara_refrigerada import CamaraRefrigerada
from models.equipamentos.freezer import Freezer
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.producao.conversores_ocupacao import gramas_para_caixas, gramas_para_niveis_tela
from utils.logs.logger_factory import setup_logger
import unicodedata

# ❄️ Logger específico
logger = setup_logger('GestorRefrigeracaoCongelamento')

RefrigeradoresCongeladores = Union[CamaraRefrigerada, Freezer]

class GestorRefrigeracaoCongelamento:
    """
    ❄️ Gestor especializado no controle de câmaras de refrigeração/congelamento.
    Compatível com a interface da CamaraRefrigerada e Freezer.
    Suporte dual: GRAMAS (subprodutos) e UNIDADES (produtos finais).
    Detecção automática baseada nas chaves de configuração JSON.
    Algoritmo de escalabilidade: testa viabilidade ANTES de alocar (sem rollback).
    Retorno padrão: (sucesso: bool, equipamento, inicio, fim)
    
    ✅ ATUALIZADO para compatibilidade com níveis de tela (nivel_fisico + tela)
    ✅ NOVO: Verificação dinâmica de intervalos para ocupação
    """

    def __init__(self, equipamentos: List[RefrigeradoresCongeladores]):
        self.equipamentos = equipamentos
        
    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[RefrigeradoresCongeladores]:
        ordenadas = sorted(
            self.equipamentos,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        return ordenadas

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
    # 🔍 Leitura dos parâmetros via JSON - DETECÇÃO AUTOMÁTICA
    # ==========================================================       
    def _obter_faixa_temperatura(self, atividade: "AtividadeModular", equipamento) -> Optional[int]:
        """
        🌡️ Busca no JSON a faixa de temperatura configurada para o equipamento específico.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = equipamento.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "faixa_temperatura" in config:
                    return int(config["faixa_temperatura"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter faixa de temperatura para {equipamento.nome}: {e}")
        return None

    def _obter_tipo_armazenamento(self, atividade: "AtividadeModular", equipamento) -> Optional[str]:
        """
        📦 Busca no JSON o tipo de armazenamento (CAIXAS, NIVEIS_TELA, etc.) para o equipamento específico.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = equipamento.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "tipo_de_armazenamento" in config:
                    return str(config["tipo_de_armazenamento"]).upper()
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter tipo de armazenamento para {equipamento.nome}: {e}")
        return None

    def _obter_faixa_temperatura_atividade_atual(self, atividade: "AtividadeModular" = None, equipamento = None) -> Optional[int]:
        """
        🌡️ Obtém a temperatura necessária da atividade atual em contexto.
        (Implementação corrigida para acessar a atividade corretamente)
        """
        if atividade is not None and equipamento is not None:
            return self._obter_faixa_temperatura(atividade, equipamento)
        return None

    def _obter_gramas_por_caixa(self, atividade: "AtividadeModular", equipamento) -> Optional[int]:
        """
        📦 Busca no JSON a quantidade de gramas por caixa para o equipamento específico.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = equipamento.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "gramas_por_caixa" in config:
                    return int(config["gramas_por_caixa"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter gramas por caixa para {equipamento.nome}: {e}")
        return None

    def _obter_gramas_por_nivel(self, atividade: "AtividadeModular", equipamento) -> Optional[int]:
        """
        📦 Busca no JSON a quantidade de gramas por nível para o equipamento específico.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = equipamento.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "gramas_por_nivel" in config:
                    return int(config["gramas_por_nivel"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter gramas por nível para {equipamento.nome}: {e}")
        return None

    def _obter_unidades_por_caixa(self, atividade: "AtividadeModular", equipamento) -> Optional[int]:
        """
        📦 Busca no JSON a quantidade de unidades por caixa para o equipamento específico.
        Usado para produtos finais (em unidades, não gramas).
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = equipamento.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "unidades_por_caixa" in config:
                    return int(config["unidades_por_caixa"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter unidades por caixa para {equipamento.nome}: {e}")
        return None

    def _obter_unidades_por_nivel(self, atividade: "AtividadeModular", equipamento) -> Optional[int]:
        """
        📋 Busca no JSON a quantidade de unidades por nível para o equipamento específico.
        Usado para produtos finais (em unidades, não gramas).
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = equipamento.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "unidades_por_nivel" in config:
                    return int(config["unidades_por_nivel"])
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter unidades por nível para {equipamento.nome}: {e}")
        return None

    def _obter_tipo_produto(self, atividade: "AtividadeModular", equipamento) -> str:
        """
        🏷️ Determina automaticamente se o produto é medido em GRAMAS ou UNIDADES.
        Baseado na presença das chaves de configuração no JSON.
        Retorna 'GRAMAS' ou 'UNIDADES'.
        """
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = equipamento.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                config = atividade.configuracoes_equipamentos.get(nome_chave, {})
                
                # Detecta automaticamente baseado na presença das chaves
                tem_unidades = "unidades_por_caixa" in config or "unidades_por_nivel" in config
                tem_gramas = "gramas_por_caixa" in config or "gramas_por_nivel" in config
                
                if tem_unidades and tem_gramas:
                    logger.warning(f"⚠️ {equipamento.nome}: Configuração ambígua - tem tanto unidades quanto gramas. Priorizando UNIDADES.")
                    return "UNIDADES"
                elif tem_unidades:
                    return "UNIDADES"
                elif tem_gramas:
                    return "GRAMAS"
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao determinar tipo de produto para {equipamento.nome}: {e}")
        
        # Fallback padrão: assume GRAMAS (comportamento original)
        logger.debug(f"🔄 {equipamento.nome}: Nenhuma configuração específica encontrada - assumindo GRAMAS (fallback)")
        return "GRAMAS"

    # ==========================================================
    # 🆕 VERIFICAÇÃO DINÂMICA DE INTERVALOS (NOVO)
    # ==========================================================
    def _calcular_quantidade_maxima_recipiente_item(
        self, 
        equipamento: RefrigeradoresCongeladores, 
        numero_recipiente: Union[int, Tuple[int, int]], 
        id_item: int, 
        inicio: datetime, 
        fim: datetime,
        tipo_recipiente: str = "caixa"
    ) -> float:
        """
        🔍 Calcula a quantidade máxima do mesmo item que estará sendo processada
        simultaneamente no recipiente durante qualquer momento do período especificado.
        
        Args:
            equipamento: CamaraRefrigerada ou Freezer
            numero_recipiente: int para caixa ou Tuple[int, int] para (nivel_fisico, tela)
            id_item: ID do item a verificar
            inicio: Início do período
            fim: Fim do período
            tipo_recipiente: "caixa" ou "nivel_tela"
        """
        # Coleta todos os pontos temporais relevantes das ocupações do mesmo item
        pontos_temporais = set()
        ocupacoes_mesmo_item = []
        
        # Obtém ocupações baseado no tipo de recipiente
        if tipo_recipiente == "caixa" and isinstance(numero_recipiente, int):
            ocupacoes_recipiente = equipamento.obter_ocupacoes_caixa(numero_recipiente)
        elif tipo_recipiente == "nivel_tela" and isinstance(numero_recipiente, tuple) and len(numero_recipiente) == 2:
            if isinstance(equipamento, CamaraRefrigerada):
                nivel_fisico, tela = numero_recipiente
                ocupacoes_recipiente = equipamento.obter_ocupacoes_nivel_tela(nivel_fisico, tela)
            else:
                return 0.0  # Freezer não suporta níveis de tela
        else:
            logger.warning(f"⚠️ Tipo de recipiente inválido: {tipo_recipiente} para {numero_recipiente}")
            return 0.0
        
        # Filtra ocupações do mesmo item
        for ocupacao in ocupacoes_recipiente:
            if len(ocupacao) >= 7:  # Formato completo
                _, _, _, item_ocup, _, inicio_ocup, fim_ocup = ocupacao[:7]
                if item_ocup == id_item:
                    ocupacoes_mesmo_item.append(ocupacao)
                    pontos_temporais.add(inicio_ocup)
                    pontos_temporais.add(fim_ocup)
        
        # Adiciona pontos do novo período
        pontos_temporais.add(inicio)
        pontos_temporais.add(fim)
        
        # Ordena pontos temporais
        pontos_ordenados = sorted(pontos_temporais)
        
        quantidade_maxima = 0.0
        
        # Verifica quantidade em cada intervalo
        for i in range(len(pontos_ordenados) - 1):
            momento_inicio = pontos_ordenados[i]
            momento_fim = pontos_ordenados[i + 1]
            momento_meio = momento_inicio + (momento_fim - momento_inicio) / 2
            
            # Soma quantidade de todas as ocupações do mesmo item ativas neste momento
            quantidade_momento = 0.0
            for ocupacao in ocupacoes_mesmo_item:
                _, _, _, _, quantidade_ocup, inicio_ocup, fim_ocup = ocupacao[:7]
                if inicio_ocup <= momento_meio < fim_ocup:  # ocupação ativa neste momento
                    quantidade_momento += quantidade_ocup
            
            quantidade_maxima = max(quantidade_maxima, quantidade_momento)
        
        return quantidade_maxima

    def _validar_nova_ocupacao_recipiente(
        self,
        equipamento: RefrigeradoresCongeladores,
        numero_recipiente: Union[int, Tuple[int, int]],
        id_item: int,
        quantidade_nova: float,
        capacidade_recipiente: float,
        inicio: datetime,
        fim: datetime,
        tipo_recipiente: str = "caixa"
    ) -> bool:
        """
        🔍 Valida se uma nova ocupação pode ser adicionada ao recipiente sem exceder a capacidade.
        ✅ CORRIGIDO: Itens diferentes podem coexistir em recipientes diferentes.
        ❌ Rejeita apenas se o mesmo recipiente tem item diferente com sobreposição temporal.

        Args:
            equipamento: CamaraRefrigerada ou Freezer
            numero_recipiente: int para caixa ou Tuple[int, int] para (nivel_fisico, tela)
            id_item: ID do item
            quantidade_nova: Quantidade a adicionar
            capacidade_recipiente: Capacidade máxima do recipiente
            inicio: Início do período
            fim: Fim do período
            tipo_recipiente: "caixa" ou "nivel_tela"
        """
        # Verifica se há itens diferentes ocupando o recipiente no período
        if tipo_recipiente == "caixa" and isinstance(numero_recipiente, int):
            ocupacoes_recipiente = equipamento.obter_ocupacoes_caixa(numero_recipiente)
        elif tipo_recipiente == "nivel_tela" and isinstance(numero_recipiente, tuple) and len(numero_recipiente) == 2:
            if isinstance(equipamento, CamaraRefrigerada):
                nivel_fisico, tela = numero_recipiente
                ocupacoes_recipiente = equipamento.obter_ocupacoes_nivel_tela(nivel_fisico, tela)
            else:
                return False  # Freezer não suporta níveis de tela
        else:
            return False

        # ✅ REMOVIDO: Validação de temperatura movida para método específico
        # (A validação será feita durante o cálculo de capacidade do equipamento)

        # ✅ CORRIGIDO: Verifica conflitos de itens diferentes no MESMO recipiente
        for ocupacao in ocupacoes_recipiente:
            if len(ocupacao) >= 7:
                _, _, _, item_ocup, _, inicio_ocup, fim_ocup = ocupacao[:7]
                if not (fim <= inicio_ocup or inicio >= fim_ocup):  # há sobreposição temporal
                    if item_ocup != id_item:  # item diferente
                        logger.debug(f"🚫 {equipamento.nome}[{numero_recipiente}]: item {item_ocup} já presente, não pode adicionar item {id_item} - tentando próximo recipiente")
                        return False  # ❌ Só para ESTE recipiente específico
        
        # Calcula quantidade máxima atual do mesmo item
        quantidade_atual_maxima = self._calcular_quantidade_maxima_recipiente_item(
            equipamento, numero_recipiente, id_item, inicio, fim, tipo_recipiente
        )
        
        # Simula todos os pontos temporais com a nova ocupação
        pontos_temporais = set()
        ocupacoes_mesmo_item = []
        
        for ocupacao in ocupacoes_recipiente:
            if len(ocupacao) >= 7:
                _, _, _, item_ocup, _, inicio_ocup, fim_ocup = ocupacao[:7]
                if item_ocup == id_item:
                    ocupacoes_mesmo_item.append(ocupacao)
                    pontos_temporais.add(inicio_ocup)
                    pontos_temporais.add(fim_ocup)
        
        # Adiciona nova ocupação simulada
        pontos_temporais.add(inicio)
        pontos_temporais.add(fim)
        
        pontos_ordenados = sorted(pontos_temporais)
        
        # Verifica se em algum momento a capacidade será excedida
        for i in range(len(pontos_ordenados) - 1):
            momento_inicio = pontos_ordenados[i]
            momento_fim = pontos_ordenados[i + 1]
            momento_meio = momento_inicio + (momento_fim - momento_inicio) / 2
            
            quantidade_total = 0.0
            
            # Soma ocupações existentes ativas neste momento
            for ocupacao in ocupacoes_mesmo_item:
                _, _, _, _, quantidade_ocup, inicio_ocup, fim_ocup = ocupacao[:7]
                if inicio_ocup <= momento_meio < fim_ocup:
                    quantidade_total += quantidade_ocup
            
            # Soma nova ocupação se ativa neste momento
            if inicio <= momento_meio < fim:
                quantidade_total += quantidade_nova
            
            # Verifica se excede capacidade
            if quantidade_total > capacidade_recipiente:
                logger.debug(
                    f"❌ {equipamento.nome}[{numero_recipiente}]: Item {id_item} excederia capacidade no momento {momento_meio.strftime('%H:%M')} "
                    f"({quantidade_total} > {capacidade_recipiente})"
                )
                return False
        
        return True

    def _verificar_compatibilidade_recipiente(
        self, 
        equipamento: RefrigeradoresCongeladores, 
        numero_recipiente: Union[int, Tuple[int, int]], 
        id_item: int,
        quantidade: float, 
        capacidade_recipiente: float,
        inicio: datetime, 
        fim: datetime,
        tipo_recipiente: str = "caixa"
    ) -> Tuple[bool, float]:
        """
        🔍 Verifica se um item pode ser adicionado a um recipiente específico e retorna a capacidade disponível.
        Retorna (pode_adicionar, capacidade_disponivel_para_item)
        """
        # Valida se a nova ocupação é possível
        if not self._validar_nova_ocupacao_recipiente(equipamento, numero_recipiente, id_item, quantidade, capacidade_recipiente, inicio, fim, tipo_recipiente):
            return False, 0.0
        
        # Calcula capacidade disponível para o item
        quantidade_atual_maxima = self._calcular_quantidade_maxima_recipiente_item(
            equipamento, numero_recipiente, id_item, inicio, fim, tipo_recipiente
        )
        
        capacidade_disponivel = capacidade_recipiente - quantidade_atual_maxima
        
        return True, max(0.0, capacidade_disponivel)

    # ==========================================================
    # 🔧 Métodos de Cálculo de Capacidade e Alocação Escalável (ATUALIZADOS)
    # ==========================================================
    def _calcular_capacidade_equipamento(
        self,
        equipamento: RefrigeradoresCongeladores,
        atividade: "AtividadeModular",
        tipo_armazenamento: str,
        inicio: datetime,
        fim: datetime
    ) -> int:
        """
        Calcula capacidade disponível do equipamento para o período especificado.
        Considera aproveitamento de espaços parcialmente ocupados pelo mesmo item.
        Retorna capacidade em gramas ou unidades (dependendo do tipo de produto).
        ✅ ATUALIZADO com verificação dinâmica de intervalos
        """
        try:
            tipo_produto = self._obter_tipo_produto(atividade, equipamento)
            logger.debug(f"🏷️ {equipamento.nome}: tipo de produto = {tipo_produto}")
            
            if tipo_armazenamento == "CAIXAS":
                if tipo_produto == "UNIDADES":
                    # Produtos finais medidos em unidades
                    unidades_por_caixa = self._obter_unidades_por_caixa(atividade, equipamento)
                    if unidades_por_caixa is None:
                        logger.debug(f"❌ {equipamento.nome}: unidades_por_caixa não definido")
                        return 0
                    capacidade_por_recipiente = unidades_por_caixa
                    unidade_medida = "unidades"
                else:
                    # Subprodutos medidos em gramas
                    gramas_por_caixa = self._obter_gramas_por_caixa(atividade, equipamento)
                    if gramas_por_caixa is None:
                        logger.debug(f"❌ {equipamento.nome}: gramas_por_caixa não definido")
                        return 0
                    capacidade_por_recipiente = gramas_por_caixa
                    unidade_medida = "gramas"
                
                return self._calcular_capacidade_caixas_dinamica(
                    equipamento, atividade, capacidade_por_recipiente, unidade_medida, inicio, fim
                )
                
            elif tipo_armazenamento == "NIVEIS_TELA":
                if tipo_produto == "UNIDADES":
                    # Produtos finais medidos em unidades
                    unidades_por_nivel = self._obter_unidades_por_nivel(atividade, equipamento)
                    if unidades_por_nivel is None:
                        logger.debug(f"❌ {equipamento.nome}: unidades_por_nivel não definido")
                        return 0
                    capacidade_por_recipiente = unidades_por_nivel
                    unidade_medida = "unidades"
                else:
                    # Subprodutos medidos em gramas
                    gramas_por_nivel = self._obter_gramas_por_nivel(atividade, equipamento)
                    if gramas_por_nivel is None:
                        logger.debug(f"❌ {equipamento.nome}: gramas_por_nivel não definido")
                        return 0
                    capacidade_por_recipiente = gramas_por_nivel
                    unidade_medida = "gramas"
                
                return self._calcular_capacidade_niveis_dinamica(
                    equipamento, atividade, capacidade_por_recipiente, unidade_medida, inicio, fim
                )
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao calcular capacidade de {equipamento.nome}: {e}")
            return 0
        
        return 0

    def _calcular_capacidade_caixas_dinamica(
        self,
        equipamento: RefrigeradoresCongeladores,
        atividade: "AtividadeModular",
        capacidade_por_caixa: int,
        unidade_medida: str,
        inicio: datetime,
        fim: datetime
    ) -> int:
        """
        Calcula capacidade específica para caixas com verificação dinâmica.
        ✅ NOVO: Usa verificação dinâmica de intervalos
        """
        capacidade_total = 0
        id_item = getattr(atividade, 'id_item', 0)
        
        # Para câmara refrigerada e freezer
        if isinstance(equipamento, (CamaraRefrigerada, Freezer)):
            # Capacidade máxima teórica
            if isinstance(equipamento, CamaraRefrigerada):
                capacidade_maxima_caixas = equipamento.total_caixas_disponiveis
                range_min, range_max = equipamento.capacidade_caixa_min, equipamento.capacidade_caixa_max
            else:  # Freezer
                capacidade_maxima_caixas = equipamento.total_caixas_disponiveis
                range_min, range_max = equipamento.capacidade_caixa_min, equipamento.capacidade_caixa_max
            
            capacidade_maxima_teorica = capacidade_maxima_caixas * capacidade_por_caixa
            logger.debug(f"📊 {equipamento.nome}: capacidade máxima teórica = {capacidade_maxima_caixas} caixas × {capacidade_por_caixa} {unidade_medida}/caixa = {capacidade_maxima_teorica} {unidade_medida}")
            
            # Soma capacidade de caixas livres
            caixas_disponiveis = equipamento.caixas_disponiveis_periodo(inicio, fim)
            capacidade_caixas_livres = len(caixas_disponiveis) * capacidade_por_caixa
            capacidade_total += capacidade_caixas_livres
            logger.debug(f"📦 {equipamento.nome}: {len(caixas_disponiveis)} caixas livres × {capacidade_por_caixa} {unidade_medida}/caixa = {capacidade_caixas_livres} {unidade_medida}")
            
            # ✅ NOVO: Adiciona espaços aproveitáveis em caixas ocupadas usando ordem de índice
            capacidade_aproveitamento = 0

            # Ordem por índice: primeiro tenta caixas já ocupadas (aproveitamento), depois caixas livres
            for numero_caixa in range(range_min, range_max + 1):
                if numero_caixa in caixas_disponiveis:
                    continue  # Já contada como livre

                # Usa verificação dinâmica para verificar compatibilidade
                compativel, capacidade_disponivel = self._verificar_compatibilidade_recipiente(
                    equipamento, numero_caixa, id_item, 0, capacidade_por_caixa, inicio, fim, "caixa"
                )

                if compativel and capacidade_disponivel > 0:
                    capacidade_aproveitamento += capacidade_disponivel
                    logger.debug(f"♻️ {equipamento.nome}: caixa {numero_caixa} com {capacidade_disponivel} {unidade_medida} aproveitáveis (índice: {numero_caixa})")

            capacidade_total += capacidade_aproveitamento
            logger.debug(f"📊 {equipamento.nome}: capacidade total = {capacidade_caixas_livres} {unidade_medida} (livres) + {capacidade_aproveitamento} {unidade_medida} (aproveitamento dinâmico) = {capacidade_total} {unidade_medida}")
        
        return capacidade_total

    def _calcular_capacidade_niveis_dinamica(
        self,
        equipamento: RefrigeradoresCongeladores,
        atividade: "AtividadeModular",
        capacidade_por_nivel: int,
        unidade_medida: str,
        inicio: datetime,
        fim: datetime
    ) -> int:
        """
        Calcula capacidade específica para níveis de tela com verificação dinâmica.
        ✅ NOVO: Usa verificação dinâmica de intervalos
        ✅ ATUALIZADO para usar níveis de tela (nivel_fisico + tela)
        """
        capacidade_total = 0
        id_item = getattr(atividade, 'id_item', 0)
        
        # Só câmara refrigerada suporta níveis
        if isinstance(equipamento, CamaraRefrigerada):
            # Capacidade máxima teórica da câmara
            capacidade_maxima_teorica = equipamento.total_niveis_disponiveis * capacidade_por_nivel
            logger.debug(f"📋 {equipamento.nome}: capacidade máxima teórica = {equipamento.total_niveis_disponiveis} níveis de tela × {capacidade_por_nivel} {unidade_medida}/nível = {capacidade_maxima_teorica} {unidade_medida}")
            
            # Soma capacidade de níveis de tela livres
            niveis_tela_livres = equipamento.niveis_tela_disponiveis_periodo(inicio, fim)
            capacidade_niveis_livres = len(niveis_tela_livres) * capacidade_por_nivel
            capacidade_total += capacidade_niveis_livres
            logger.debug(f"📋 {equipamento.nome}: {len(niveis_tela_livres)} níveis de tela livres × {capacidade_por_nivel} {unidade_medida}/nível = {capacidade_niveis_livres} {unidade_medida}")
            
            # Adiciona espaços aproveitáveis em níveis de tela ocupados usando verificação dinâmica
            capacidade_aproveitamento = 0
            for nivel_fisico, tela in equipamento.obter_numeros_niveis_tela_disponiveis():
                if (nivel_fisico, tela) in niveis_tela_livres:
                    continue  # Já contado como livre
                    
                # Usa verificação dinâmica para verificar compatibilidade
                compativel, capacidade_disponivel = self._verificar_compatibilidade_recipiente(
                    equipamento, (nivel_fisico, tela), id_item, 0, capacidade_por_nivel, inicio, fim, "nivel_tela"
                )
                
                if compativel and capacidade_disponivel > 0:
                    capacidade_aproveitamento += capacidade_disponivel
                    logger.debug(f"♻️ {equipamento.nome}: nível {nivel_fisico}, tela {tela} com {capacidade_disponivel} {unidade_medida} aproveitáveis (dinâmico)")
            
            capacidade_total += capacidade_aproveitamento
            logger.debug(f"📋 {equipamento.nome}: capacidade total = {capacidade_niveis_livres} {unidade_medida} (livres) + {capacidade_aproveitamento} {unidade_medida} (aproveitamento dinâmico) = {capacidade_total} {unidade_medida}")
        
        return capacidade_total

    # ==========================================================
    # 🎯 Alocação Principal com Algoritmo de Escalabilidade
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        bypass_capacidade: bool = False,
        **kwargs
    ) -> Tuple[bool, Optional[RefrigeradoresCongeladores], Optional[datetime], Optional[datetime]]:
        """
        ❄️ Faz a alocação utilizando algoritmo de escalabilidade para volumes grandes:
        1. Verifica capacidade total de todos os equipamentos
        2. Testa equipamentos individuais primeiro
        3. Se falhar, testa combinações de 2, 3, até N equipamentos
        4. Se ainda falhar, usa backward scheduling (sabendo que é possível)
        
        Retorna (True, equipamento_principal, inicio_real, fim_real) se sucesso.
        Caso contrário: (False, None, None, None)
        
        ✅ ATUALIZADO com verificação dinâmica de intervalos
        """
        
        duracao = atividade.duracao
        atividade.quantidade_produto = quantidade_produto

        # Obter IDs de forma consistente
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)

        equipamentos_ordenados = self._ordenar_por_fip(atividade)

        logger.info(f"🎯 Iniciando alocação escalável atividade {id_atividade}: {quantidade_produto}")
        
        # Detecta automaticamente o tipo de produto baseado no primeiro equipamento compatível
        tipo_produto_detectado = None
        for equipamento in equipamentos_ordenados:
            tipo_produto_detectado = self._obter_tipo_produto(atividade, equipamento)
            if tipo_produto_detectado:
                break
        
        unidade_medida = "unidades" if tipo_produto_detectado == "UNIDADES" else "gramas"
        logger.info(f"📏 Tipo de produto: {tipo_produto_detectado} ({quantidade_produto} {unidade_medida})")
        logger.info(f"📅 Janela: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} (duração: {duracao})")

        # ==========================================================
        # 📊 ETAPA 1: VERIFICAÇÃO DE CAPACIDADE TOTAL
        # ==========================================================
        temperatura_desejada = None
        capacidade_total_disponivel = 0
        equipamentos_compativeis = []

        logger.info(f"📊 Verificando capacidade de {len(equipamentos_ordenados)} equipamentos...")

        for equipamento in equipamentos_ordenados:
            temp = self._obter_faixa_temperatura(atividade, equipamento)
            tipo_armazenamento = self._obter_tipo_armazenamento(atividade, equipamento)
            
            logger.info(f"🔍 {equipamento.nome}: temp={temp}°C, tipo={tipo_armazenamento}")

            if temp is None or tipo_armazenamento not in {"CAIXAS", "NIVEIS_TELA"}:
                logger.warning(f"❌ {equipamento.nome}: configuração inválida - temp={temp}, tipo={tipo_armazenamento}")
                continue
                
            # Freezer só suporta CAIXAS
            if isinstance(equipamento, Freezer) and tipo_armazenamento != "CAIXAS":
                logger.debug(f"❌ {equipamento.nome}: freezer só suporta CAIXAS")
                continue
                
            # Primeira temperatura válida define o padrão
            if temperatura_desejada is None:
                temperatura_desejada = temp
                logger.info(f"🌡️ Temperatura padrão definida: {temperatura_desejada}°C")
            elif temperatura_desejada != temp:
                logger.debug(f"⚠️ {equipamento.nome}: temperatura {temp}°C diferente do padrão {temperatura_desejada}°C")
                continue
            
            # Calcula capacidade do equipamento (agora com verificação dinâmica)
            capacidade_equipamento = self._calcular_capacidade_equipamento(
                equipamento, atividade, tipo_armazenamento, inicio, fim
            )
            
            if capacidade_equipamento > 0:
                equipamentos_compativeis.append((equipamento, tipo_armazenamento, capacidade_equipamento))
                capacidade_total_disponivel += capacidade_equipamento
                logger.info(f"✅ {equipamento.nome}: {capacidade_equipamento} {unidade_medida} disponível (tipo: {tipo_armazenamento})")
            else:
                logger.debug(f"❌ {equipamento.nome}: capacidade zero")

        logger.info(f"📊 RESUMO DE CAPACIDADE:")
        logger.info(f"   💾 Total disponível: {capacidade_total_disponivel} {unidade_medida}")
        logger.info(f"   🎯 Necessário: {quantidade_produto} {unidade_medida}")
        logger.info(f"   🏭 Equipamentos compatíveis: {len(equipamentos_compativeis)}")

        if not equipamentos_compativeis:
            logger.warning(f"❌ Nenhum equipamento compatível encontrado para atividade {id_atividade}")
            return False, None, None, None

        if capacidade_total_disponivel < quantidade_produto:
            logger.warning(
                f"❌ Capacidade total insuficiente para atividade {id_atividade}: "
                f"necessário {quantidade_produto} {unidade_medida}, disponível {capacidade_total_disponivel} {unidade_medida}"
            )
            # Log detalhado de cada equipamento para diagnóstico
            logger.warning("📋 Detalhamento por equipamento:")
            for equipamento, tipo, capacidade in equipamentos_compativeis:
                logger.warning(f"   - {equipamento.nome}: {capacidade} {unidade_medida} ({tipo})")
            return False, None, None, None

        logger.info(
            f"✅ Capacidade total suficiente: {capacidade_total_disponivel} {unidade_medida} >= {quantidade_produto} {unidade_medida} "
            f"({len(equipamentos_compativeis)} equipamentos compatíveis)"
        )

        # ==========================================================
        # 🔄 ETAPA 2: TESTE EQUIPAMENTO ÚNICO PRIORITÁRIO (pedido concentrado)
        # ==========================================================
        logger.info(f"🎯 Testando equipamentos individuais (prioridade: pedido concentrado)")

        # ✅ NOVO: Testa cada equipamento individualmente na ordem de prioridade
        for equipamento, tipo_armazenamento, capacidade_disponivel in equipamentos_compativeis:
            if capacidade_disponivel >= quantidade_produto:
                logger.info(f"🔍 Testando {equipamento.nome} individualmente: {capacidade_disponivel} >= {quantidade_produto} {unidade_medida}")

                # Tenta alocação direta neste equipamento específico
                sucesso_individual = self._tentar_alocacao_equipamento_unico(
                    equipamento, tipo_armazenamento, atividade, quantidade_produto, temperatura_desejada,
                    inicio, fim, id_ordem, id_pedido, id_atividade, id_item
                )

                if sucesso_individual:
                    equipamento_usado, inicio_real, fim_real = sucesso_individual
                    atividade.equipamento_alocado = equipamento_usado
                    atividade.equipamentos_selecionados = [equipamento_usado]
                    atividade.alocada = True

                    logger.info(
                        f"✅ Atividade {id_atividade} alocada em equipamento único: {equipamento.nome} "
                        f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                        f"| Temp: {temperatura_desejada}°C"
                    )
                    return True, equipamento_usado, inicio_real, fim_real
                else:
                    logger.debug(f"❌ {equipamento.nome}: falha na alocação individual apesar da capacidade")

        # ==========================================================
        # 🔄 ETAPA 3: ALOCAÇÃO DISTRIBUÍDA (último recurso)
        # ==========================================================
        logger.info(f"🔄 Nenhum equipamento individual conseguiu atender - tentando distribuição")

        sucesso_distribuido = self._tentar_alocacao_direta(
            equipamentos_compativeis, atividade, quantidade_produto, temperatura_desejada,
            inicio, fim, id_ordem, id_pedido, id_atividade, id_item
        )

        if sucesso_distribuido:
            equipamento_usado, inicio_real, fim_real = sucesso_distribuido
            atividade.equipamento_alocado = equipamento_usado
            atividade.equipamentos_selecionados = [equipamento_usado] if not isinstance(equipamento_usado, list) else equipamento_usado
            atividade.alocada = True

            logger.info(
                f"✅ Atividade {id_atividade} alocada distribuída "
                f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                f"| Temp: {temperatura_desejada}°C"
            )
            return True, equipamento_usado, inicio_real, fim_real

        # ==========================================================
        # ⏰ ETAPA 3: BACKWARD SCHEDULING (sabemos que é possível)
        # ==========================================================
        logger.info(f"🔄 Iniciando backward scheduling para atividade {id_atividade} (capacidade confirmada)")
        
        horario_final_tentativa = fim
        tentativas = 0
        
        while horario_final_tentativa - duracao >= inicio:
            tentativas += 1
            horario_inicio_tentativa = horario_final_tentativa - duracao

            if tentativas % 10 == 0:
                logger.debug(f"⏰ Tentativa {tentativas}: {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}")

            # Recalcula equipamentos compatíveis para esta janela específica (com verificação dinâmica)
            equipamentos_janela = []
            for equipamento, tipo_armazenamento, _ in equipamentos_compativeis:
                capacidade_janela = self._calcular_capacidade_equipamento(
                    equipamento, atividade, tipo_armazenamento, horario_inicio_tentativa, horario_final_tentativa
                )
                if capacidade_janela > 0:
                    equipamentos_janela.append((equipamento, tipo_armazenamento, capacidade_janela))

            # Tenta alocação nesta janela específica
            sucesso_janela = self._tentar_alocacao_direta(
                equipamentos_janela, atividade, quantidade_produto, temperatura_desejada,
                horario_inicio_tentativa, horario_final_tentativa, id_ordem, id_pedido, id_atividade, id_item
            )
            
            if sucesso_janela:
                equipamento_usado, inicio_real, fim_real = sucesso_janela
                atividade.equipamento_alocado = equipamento_usado
                atividade.equipamentos_selecionados = [equipamento_usado] if not isinstance(equipamento_usado, list) else equipamento_usado
                atividade.alocada = True
                
                minutos_retrocedidos = int((fim - fim_real).total_seconds() / 60)
                logger.info(
                    f"✅ Atividade {id_atividade} alocada via backward scheduling "
                    f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                    f"| Temp: {temperatura_desejada}°C (retrocedeu {minutos_retrocedidos} minutos)"
                )
                return True, equipamento_usado, inicio_real, fim_real

            # Retrocede 1 minuto
            horario_final_tentativa -= timedelta(minutes=1)

        # Não deveria chegar aqui se a capacidade total foi confirmada
        logger.error(
            f"❌ ERRO CRÍTICO: Atividade {id_atividade} não pôde ser alocada após {tentativas} tentativas, "
            f"mesmo com capacidade total confirmada! Possível problema de fragmentação."
        )
        return False, None, None, None

    def _tentar_alocacao_equipamento_unico(
        self,
        equipamento: RefrigeradoresCongeladores,
        tipo_armazenamento: str,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        temperatura_desejada: int,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int
    ) -> Optional[Tuple[RefrigeradoresCongeladores, datetime, datetime]]:
        """
        ✅ NOVO: Tenta alocação em um único equipamento específico.
        Estratégia prioritária para manter pedido concentrado.
        """
        logger.debug(f"🔍 Tentando alocação única em {equipamento.nome}: {quantidade_produto} unidades")

        try:
            # Determina método de ocupação baseado no tipo
            if tipo_armazenamento == "CAIXAS":
                tipo_produto = self._obter_tipo_produto(atividade, equipamento)
                if tipo_produto == "UNIDADES":
                    capacidade_por_recipiente = self._obter_unidades_por_caixa(atividade, equipamento)
                else:
                    capacidade_por_recipiente = self._obter_gramas_por_caixa(atividade, equipamento)

                if capacidade_por_recipiente is None:
                    return None

                # Tenta ocupação usando método dinâmico
                if isinstance(equipamento, CamaraRefrigerada):
                    sucesso = self._ocupar_camara_caixas_volume_real_dinamico(
                        equipamento, id_ordem, id_pedido, id_atividade, id_item,
                        quantidade_produto, capacidade_por_recipiente, inicio, fim, temperatura_desejada
                    )
                elif isinstance(equipamento, Freezer):
                    sucesso = self._ocupar_freezer_caixas_volume_real_dinamico(
                        equipamento, id_ordem, id_pedido, id_atividade, id_item,
                        quantidade_produto, capacidade_por_recipiente, inicio, fim, temperatura_desejada
                    )
                else:
                    return None

            elif tipo_armazenamento == "NIVEIS_TELA" and isinstance(equipamento, CamaraRefrigerada):
                tipo_produto = self._obter_tipo_produto(atividade, equipamento)
                if tipo_produto == "UNIDADES":
                    capacidade_por_recipiente = self._obter_unidades_por_nivel(atividade, equipamento)
                else:
                    capacidade_por_recipiente = self._obter_gramas_por_nivel(atividade, equipamento)

                if capacidade_por_recipiente is None:
                    return None

                sucesso = self._ocupar_camara_niveis_volume_real_dinamico(
                    equipamento, id_ordem, id_pedido, id_atividade, id_item,
                    quantidade_produto, capacidade_por_recipiente, inicio, fim, temperatura_desejada
                )
            else:
                return None

            if sucesso:
                logger.info(f"✅ Alocação única bem-sucedida em {equipamento.nome}")
                return equipamento, inicio, fim
            else:
                logger.debug(f"❌ Falha na alocação única em {equipamento.nome}")
                return None

        except Exception as e:
            logger.warning(f"⚠️ Erro na alocação única em {equipamento.nome}: {e}")
            return None

    def _tentar_alocacao_direta(
        self,
        equipamentos_compativeis: List[Tuple[RefrigeradoresCongeladores, str, int]],
        atividade: "AtividadeModular",
        quantidade_produto: int,
        temperatura_desejada: int,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int
    ) -> Optional[Tuple[RefrigeradoresCongeladores, datetime, datetime]]:
        """
        Tenta alocação direta seguindo a estratégia de escalabilidade:
        1. Testa equipamentos individuais (por FIP)
        2. Se falhar, testa combinações de 2 equipamentos
        3. Depois 3, 4, até N equipamentos
        ✅ ATUALIZADO com verificação dinâmica de intervalos
        """
        from itertools import combinations
        
        # ESTRATÉGIA 1: Equipamentos individuais
        logger.debug("🔍 Testando equipamentos individuais...")
        for equipamento, tipo_armazenamento, capacidade in equipamentos_compativeis:
            if capacidade >= quantidade_produto:
                logger.debug(f"🎯 Testando {equipamento.nome} individual ({capacidade} >= {quantidade_produto})")
                
                sucesso = self._tentar_alocacao_equipamento_unico(
                    equipamento, atividade, quantidade_produto, tipo_armazenamento,
                    temperatura_desejada, inicio, fim, id_ordem, id_pedido, id_atividade, id_item
                )
                
                if sucesso:
                    logger.info(f"✅ Alocação individual bem-sucedida: {equipamento.nome}")
                    return equipamento, inicio, fim
        
        # ESTRATÉGIA 2: Combinações múltiplas (2, 3, ..., N equipamentos)
        for num_equipamentos in range(2, len(equipamentos_compativeis) + 1):
            logger.debug(f"🔍 Testando combinações de {num_equipamentos} equipamentos...")
            
            for combinacao in combinations(equipamentos_compativeis, num_equipamentos):
                capacidade_combinacao = sum(cap for _, _, cap in combinacao)
                
                if capacidade_combinacao >= quantidade_produto:
                    equipamentos_combo = [eq for eq, _, _ in combinacao]
                    logger.debug(f"🎯 Testando combinação: {[eq.nome for eq in equipamentos_combo]} ({capacidade_combinacao})")
                    
                    sucesso = self._tentar_alocacao_equipamentos_multiplos(
                        list(combinacao), atividade, quantidade_produto, temperatura_desejada,
                        inicio, fim, id_ordem, id_pedido, id_atividade, id_item
                    )
                    
                    if sucesso:
                        logger.info(f"✅ Alocação múltipla bem-sucedida: {[eq.nome for eq in equipamentos_combo]}")
                        # Retorna o primeiro equipamento como principal (por FIP)
                        return equipamentos_combo, inicio, fim
        
        logger.debug("❌ Nenhuma combinação de equipamentos foi bem-sucedida")
        return None

    def _tentar_alocacao_equipamento_unico(
        self,
        equipamento: RefrigeradoresCongeladores,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        tipo_armazenamento: str,
        temperatura_desejada: int,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int
    ) -> bool:
        """Tenta alocar em um único equipamento. ✅ ATUALIZADO com verificação dinâmica"""
        try:
            if isinstance(equipamento, CamaraRefrigerada):
                return self._tentar_alocacao_camara_refrigerada(
                    equipamento, atividade, quantidade_produto, tipo_armazenamento,
                    temperatura_desejada, inicio, fim, id_ordem, id_pedido, id_atividade, id_item
                )
            elif isinstance(equipamento, Freezer):
                return self._tentar_alocacao_freezer(
                    equipamento, atividade, quantidade_produto, tipo_armazenamento,
                    temperatura_desejada, inicio, fim, id_ordem, id_pedido, id_atividade, id_item
                )
            else:
                logger.warning(f"⚠️ Tipo de equipamento não suportado: {type(equipamento)}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar alocação em {equipamento.nome}: {e}")
            return False

    def _tentar_alocacao_equipamentos_multiplos(
        self,
        equipamentos_combinacao: List[Tuple[RefrigeradoresCongeladores, str, int]],
        atividade: "AtividadeModular",
        quantidade_produto: int,
        temperatura_desejada: int,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int
    ) -> bool:
        """
        Tenta alocar distribuindo entre múltiplos equipamentos.
        PRIMEIRO testa viabilidade, SÓ DEPOIS aloca para evitar rollback.
        ✅ ATUALIZADO com verificação dinâmica
        """
        # ==========================================================
        # 🔍 FASE 1: TESTE DE VIABILIDADE (sem alocar nada)
        # ==========================================================
        quantidade_restante = quantidade_produto
        plano_alocacao = []  # Lista de (equipamento, tipo, quantidade_planejada)
        
        logger.debug(f"🔍 Testando viabilidade da combinação para {quantidade_produto}")
        
        for equipamento, tipo_armazenamento, capacidade_disponivel in equipamentos_combinacao:
            if quantidade_restante <= 0:
                break
            
            # Calcula quanto seria alocado neste equipamento
            quantidade_neste_equipamento = min(quantidade_restante, capacidade_disponivel)
            
            logger.debug(f"📋 Planejando {quantidade_neste_equipamento} em {equipamento.nome}")
            
            # TESTA se este equipamento pode receber essa quantidade (SEM ALOCAR)
            if self._testar_viabilidade_equipamento(
                equipamento, atividade, quantidade_neste_equipamento, tipo_armazenamento,
                temperatura_desejada, inicio, fim
            ):
                # Adiciona ao plano se viável
                plano_alocacao.append((equipamento, tipo_armazenamento, quantidade_neste_equipamento))
                quantidade_restante -= quantidade_neste_equipamento
                logger.debug(f"✅ {equipamento.nome}: {quantidade_neste_equipamento} viável, restam {quantidade_restante}")
            else:
                logger.debug(f"❌ {equipamento.nome}: {quantidade_neste_equipamento} não viável")
                return False  # Se qualquer equipamento falhar, combinação inviável
        
        # Verifica se o plano cobre toda a quantidade necessária
        if quantidade_restante > 0:
            logger.debug(f"❌ Plano incompleto: {quantidade_restante} não cobertos")
            return False
        
        logger.debug(f"✅ Plano de alocação viável: {len(plano_alocacao)} equipamentos")
        
        # ==========================================================
        # 🎯 FASE 2: EXECUÇÃO DO PLANO (agora que sabemos que funciona)
        # ==========================================================
        sucesso_total = True
        
        for equipamento, tipo_armazenamento, quantidade_planejada in plano_alocacao:
            logger.debug(f"🎯 Executando alocação: {quantidade_planejada} em {equipamento.nome}")
            
            sucesso = self._tentar_alocacao_equipamento_unico(
                equipamento, atividade, quantidade_planejada, tipo_armazenamento,
                temperatura_desejada, inicio, fim, id_ordem, id_pedido, id_atividade, id_item
            )
            
            if not sucesso:
                logger.error(f"❌ ERRO CRÍTICO: Falha na execução do plano em {equipamento.nome} "
                            f"(deveria ser viável!)")
                sucesso_total = False
                break
            else:
                logger.debug(f"✅ Alocação executada: {quantidade_planejada} em {equipamento.nome}")
        
        if sucesso_total:
            logger.info(f"✅ Alocação múltipla executada com sucesso: {len(plano_alocacao)} equipamentos")
            return True
        else:
            logger.error(f"❌ Falha crítica na execução do plano de alocação múltipla")
            return False

    def _testar_viabilidade_equipamento(
        self,
        equipamento: RefrigeradoresCongeladores,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        tipo_armazenamento: str,
        temperatura_desejada: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """
        Testa se um equipamento pode receber uma quantidade específica SEM ALOCAR.
        Verifica temperatura, capacidade e disponibilidade.
        ✅ ATUALIZADO com verificação dinâmica
        """
        try:
            # Teste de compatibilidade por tipo de equipamento
            if isinstance(equipamento, CamaraRefrigerada):
                return self._testar_viabilidade_camara(
                    equipamento, atividade, quantidade_produto, tipo_armazenamento,
                    temperatura_desejada, inicio, fim
                )
            elif isinstance(equipamento, Freezer):
                return self._testar_viabilidade_freezer(
                    equipamento, atividade, quantidade_produto, tipo_armazenamento,
                    temperatura_desejada, inicio, fim
                )
            else:
                logger.warning(f"⚠️ Tipo de equipamento não suportado para teste: {type(equipamento)}")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Erro ao testar viabilidade em {equipamento.nome}: {e}")
            return False

    def _testar_viabilidade_camara(
        self,
        camara: CamaraRefrigerada,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        tipo_armazenamento: str,
        temperatura_desejada: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """
        Testa viabilidade de alocação na câmara refrigerada SEM ALOCAR.
        ✅ ATUALIZADO para usar níveis de tela (nivel_fisico + tela)
        ✅ ATUALIZADO com verificação dinâmica
        """
        
        # Teste 1: Compatibilidade de temperatura
        if not camara.verificar_compatibilidade_temperatura(temperatura_desejada, inicio, fim):
            temp_atual = camara.obter_temperatura_periodo(inicio, fim)
            if temp_atual is not None and temp_atual != temperatura_desejada:
                logger.debug(f"❌ {camara.nome}: temperatura incompatível ({temperatura_desejada}°C vs {temp_atual}°C)")
                return False
        
        # Teste 2: Capacidade baseada no tipo de armazenamento
        tipo_produto = self._obter_tipo_produto(atividade, camara)
        
        if tipo_armazenamento == "CAIXAS":
            if tipo_produto == "UNIDADES":
                unidades_por_caixa = self._obter_unidades_por_caixa(atividade, camara)
                if unidades_por_caixa is None:
                    logger.debug(f"❌ {camara.nome}: unidades_por_caixa não definido")
                    return False
                return self._testar_viabilidade_caixas_camara_dinamica(
                    camara, atividade, quantidade_produto, unidades_por_caixa, inicio, fim
                )
            else:  # GRAMAS
                gramas_por_caixa = self._obter_gramas_por_caixa(atividade, camara)
                if gramas_por_caixa is None:
                    logger.debug(f"❌ {camara.nome}: gramas_por_caixa não definido")
                    return False
                return self._testar_viabilidade_caixas_camara_dinamica(
                    camara, atividade, quantidade_produto, gramas_por_caixa, inicio, fim
                )
            
        elif tipo_armazenamento == "NIVEIS_TELA":
            if tipo_produto == "UNIDADES":
                unidades_por_nivel = self._obter_unidades_por_nivel(atividade, camara)
                if unidades_por_nivel is None:
                    logger.debug(f"❌ {camara.nome}: unidades_por_nivel não definido")
                    return False
                return self._testar_viabilidade_niveis_camara_dinamica(
                    camara, atividade, quantidade_produto, unidades_por_nivel, inicio, fim
                )
            else:  # GRAMAS
                gramas_por_nivel = self._obter_gramas_por_nivel(atividade, camara)
                if gramas_por_nivel is None:
                    logger.debug(f"❌ {camara.nome}: gramas_por_nivel não definido")
                    return False
                return self._testar_viabilidade_niveis_camara_dinamica(
                    camara, atividade, quantidade_produto, gramas_por_nivel, inicio, fim
                )
        else:
            logger.debug(f"❌ {camara.nome}: tipo de armazenamento inválido ({tipo_armazenamento})")
            return False

    def _testar_viabilidade_freezer(
        self,
        freezer: Freezer,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        tipo_armazenamento: str,
        temperatura_desejada: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Testa viabilidade de alocação no freezer SEM ALOCAR. ✅ ATUALIZADO com verificação dinâmica"""
        
        # Freezer só suporta caixas
        if tipo_armazenamento != "CAIXAS":
            logger.debug(f"❌ {freezer.nome}: freezer só suporta CAIXAS")
            return False
        
        # Teste 1: Compatibilidade de temperatura
        if not freezer.verificar_compatibilidade_temperatura(temperatura_desejada, inicio, fim):
            logger.debug(f"❌ {freezer.nome}: temperatura incompatível")
            return False
        
        # Teste 2: Capacidade de caixas
        tipo_produto = self._obter_tipo_produto(atividade, freezer)
        
        if tipo_produto == "UNIDADES":
            unidades_por_caixa = self._obter_unidades_por_caixa(atividade, freezer)
            if unidades_por_caixa is None:
                logger.debug(f"❌ {freezer.nome}: unidades_por_caixa não definido")
                return False
            return self._testar_viabilidade_caixas_freezer_dinamica(
                freezer, atividade, quantidade_produto, unidades_por_caixa, inicio, fim
            )
        else:  # GRAMAS
            gramas_por_caixa = self._obter_gramas_por_caixa(atividade, freezer)
            if gramas_por_caixa is None:
                logger.debug(f"❌ {freezer.nome}: gramas_por_caixa não definido")
                return False
            return self._testar_viabilidade_caixas_freezer_dinamica(
                freezer, atividade, quantidade_produto, gramas_por_caixa, inicio, fim
            )

    # ==========================================================
    # 🆕 MÉTODOS DE TESTE DE VIABILIDADE COM VERIFICAÇÃO DINÂMICA
    # ==========================================================
    def _testar_viabilidade_caixas_camara_dinamica(
        self,
        camara: CamaraRefrigerada,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        capacidade_por_caixa: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """
        Testa se há capacidade suficiente em caixas da câmara com verificação dinâmica.
        ✅ NOVO: Usa verificação dinâmica de intervalos
        """
        id_item = getattr(atividade, 'id_item', 0)
        capacidade_disponivel = 0
        
        # Soma capacidade de caixas livres
        caixas_livres = camara.caixas_disponiveis_periodo(inicio, fim)
        capacidade_disponivel += len(caixas_livres) * capacidade_por_caixa
        
        # Soma espaços aproveitáveis em caixas ocupadas usando verificação dinâmica
        for numero_caixa in range(camara.capacidade_caixa_min, camara.capacidade_caixa_max + 1):
            if numero_caixa in caixas_livres:
                continue  # Já contada como livre
            
            # Usa verificação dinâmica para verificar compatibilidade
            compativel, capacidade_disponivel_caixa = self._verificar_compatibilidade_recipiente(
                camara, numero_caixa, id_item, 0, capacidade_por_caixa, inicio, fim, "caixa"
            )
            
            if compativel and capacidade_disponivel_caixa > 0:
                capacidade_disponivel += capacidade_disponivel_caixa
        
        viavel = capacidade_disponivel >= quantidade_produto
        
        if not viavel:
            logger.debug(f"❌ {camara.nome}: capacidade insuficiente em caixas "
                        f"({capacidade_disponivel} disponível < {quantidade_produto} necessário)")
        
        return viavel

    def _testar_viabilidade_niveis_camara_dinamica(
        self,
        camara: CamaraRefrigerada,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        capacidade_por_nivel: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """
        Testa se há capacidade suficiente em níveis de tela da câmara com verificação dinâmica.
        ✅ NOVO: Usa verificação dinâmica de intervalos
        ✅ ATUALIZADO para usar níveis de tela (nivel_fisico + tela)
        """
        id_item = getattr(atividade, 'id_item', 0)
        capacidade_disponivel = 0
        
        # Soma capacidade de níveis de tela livres
        niveis_tela_livres = camara.niveis_tela_disponiveis_periodo(inicio, fim)
        capacidade_disponivel += len(niveis_tela_livres) * capacidade_por_nivel
        
        # Soma espaços aproveitáveis em níveis de tela ocupados usando verificação dinâmica
        for nivel_fisico, tela in camara.obter_numeros_niveis_tela_disponiveis():
            if (nivel_fisico, tela) in niveis_tela_livres:
                continue  # Já contado como livre
            
            # Usa verificação dinâmica para verificar compatibilidade
            compativel, capacidade_disponivel_nivel = self._verificar_compatibilidade_recipiente(
                camara, (nivel_fisico, tela), id_item, 0, capacidade_por_nivel, inicio, fim, "nivel_tela"
            )
            
            if compativel and capacidade_disponivel_nivel > 0:
                capacidade_disponivel += capacidade_disponivel_nivel
        
        viavel = capacidade_disponivel >= quantidade_produto
        
        if not viavel:
            logger.debug(f"❌ {camara.nome}: capacidade insuficiente em níveis de tela "
                        f"({capacidade_disponivel} disponível < {quantidade_produto} necessário)")
        
        return viavel

    def _testar_viabilidade_caixas_freezer_dinamica(
        self,
        freezer: Freezer,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        capacidade_por_caixa: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """
        Testa se há capacidade suficiente em caixas do freezer com verificação dinâmica.
        ✅ NOVO: Usa verificação dinâmica de intervalos
        """
        id_item = getattr(atividade, 'id_item', 0)
        capacidade_disponivel = 0
        
        # Soma capacidade de caixas livres
        caixas_livres = freezer.caixas_disponiveis_periodo(inicio, fim)
        capacidade_disponivel += len(caixas_livres) * capacidade_por_caixa
        
        # Soma espaços aproveitáveis em caixas ocupadas usando verificação dinâmica
        for numero_caixa in range(freezer.capacidade_caixa_min, freezer.capacidade_caixa_max + 1):
            if numero_caixa in caixas_livres:
                continue
            
            # Usa verificação dinâmica para verificar compatibilidade
            compativel, capacidade_disponivel_caixa = self._verificar_compatibilidade_recipiente(
                freezer, numero_caixa, id_item, 0, capacidade_por_caixa, inicio, fim, "caixa"
            )
            
            if compativel and capacidade_disponivel_caixa > 0:
                capacidade_disponivel += capacidade_disponivel_caixa
        
        viavel = capacidade_disponivel >= quantidade_produto
        
        if not viavel:
            logger.debug(f"❌ {freezer.nome}: capacidade insuficiente em caixas "
                        f"({capacidade_disponivel} disponível < {quantidade_produto} necessário)")
        
        return viavel

    # ==========================================================
    # 🔧 Métodos de Alocação para Equipamentos Específicos (ATUALIZADOS)
    # ==========================================================
    def _tentar_alocacao_camara_refrigerada(
        self,
        camara: CamaraRefrigerada,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        tipo_armazenamento: str,
        temperatura_desejada: int,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int
    ) -> bool:
        """
        Tenta alocar na câmara refrigerada usando sua interface correta.
        ✅ ATUALIZADO para usar níveis de tela (nivel_fisico + tela)
        ✅ ATUALIZADO com verificação dinâmica
        """
        
        # Verifica compatibilidade de temperatura
        if not camara.verificar_compatibilidade_temperatura(temperatura_desejada, inicio, fim):
            logger.debug(f"❌ {camara.nome}: temperatura incompatível")
            return False

        # Configura temperatura se necessário - MARCANDO PARA POSSÍVEL ROLLBACK
        temp_atual = camara.obter_temperatura_periodo(inicio, fim)
        temperatura_configurada_aqui = False

        if temp_atual is None:
            if not camara.configurar_temperatura(temperatura_desejada, inicio, fim):
                logger.debug(f"❌ {camara.nome}: falha ao configurar temperatura")
                return False
            temperatura_configurada_aqui = True  # Marcamos que configuramos aqui

        # Testa alocação baseada no tipo de armazenamento
        tipo_produto = self._obter_tipo_produto(atividade, camara)
        resultado_alocacao = False

        if tipo_armazenamento == "CAIXAS":
            if tipo_produto == "UNIDADES":
                unidades_por_caixa = self._obter_unidades_por_caixa(atividade, camara)
                if unidades_por_caixa is None:
                    logger.warning(f"⚠️ Unidades por caixa não definido para {camara.nome}. Usando conversão padrão.")
                    quantidade_ocupacao = gramas_para_caixas(quantidade_produto)
                    resultado_alocacao = self._ocupar_camara_caixas_compativel(
                        camara, id_ordem, id_pedido, id_atividade, id_item,
                        quantidade_ocupacao, inicio, fim, temperatura_desejada
                    )
                else:
                    resultado_alocacao = self._ocupar_camara_caixas_volume_real_dinamico(
                        camara, id_ordem, id_pedido, id_atividade, id_item,
                        quantidade_produto, unidades_por_caixa, inicio, fim, temperatura_desejada
                    )
            else:  # GRAMAS
                gramas_por_caixa = self._obter_gramas_por_caixa(atividade, camara)
                if gramas_por_caixa is None:
                    logger.warning(f"⚠️ Gramas por caixa não definido para {camara.nome}. Usando conversão padrão.")
                    quantidade_ocupacao = gramas_para_caixas(quantidade_produto)
                    resultado_alocacao = self._ocupar_camara_caixas_compativel(
                        camara, id_ordem, id_pedido, id_atividade, id_item,
                        quantidade_ocupacao, inicio, fim, temperatura_desejada
                    )
                else:
                    resultado_alocacao = self._ocupar_camara_caixas_volume_real_dinamico(
                        camara, id_ordem, id_pedido, id_atividade, id_item,
                        quantidade_produto, gramas_por_caixa, inicio, fim, temperatura_desejada
                    )

        elif tipo_armazenamento == "NIVEIS_TELA":
            if tipo_produto == "UNIDADES":
                unidades_por_nivel = self._obter_unidades_por_nivel(atividade, camara)
                if unidades_por_nivel is None:
                    logger.warning(f"⚠️ Unidades por nível não definido para {camara.nome}. Usando conversão padrão.")
                    quantidade_ocupacao = gramas_para_niveis_tela(quantidade_produto)
                    resultado_alocacao = self._ocupar_camara_niveis_compativel(
                        camara, id_ordem, id_pedido, id_atividade, id_item,
                        quantidade_ocupacao, inicio, fim, temperatura_desejada
                    )
                else:
                    resultado_alocacao = self._ocupar_camara_niveis_volume_real_dinamico(
                        camara, id_ordem, id_pedido, id_atividade, id_item,
                        quantidade_produto, unidades_por_nivel, inicio, fim, temperatura_desejada
                    )
            else:  # GRAMAS
                gramas_por_nivel = self._obter_gramas_por_nivel(atividade, camara)
                if gramas_por_nivel is None:
                    logger.warning(f"⚠️ Gramas por nível não definido para {camara.nome}. Usando conversão padrão.")
                    quantidade_ocupacao = gramas_para_niveis_tela(quantidade_produto)
                    resultado_alocacao = self._ocupar_camara_niveis_compativel(
                        camara, id_ordem, id_pedido, id_atividade, id_item,
                        quantidade_ocupacao, inicio, fim, temperatura_desejada
                    )
                else:
                    resultado_alocacao = self._ocupar_camara_niveis_volume_real_dinamico(
                        camara, id_ordem, id_pedido, id_atividade, id_item,
                        quantidade_produto, gramas_por_nivel, inicio, fim, temperatura_desejada
                    )

        # 🔧 ROLLBACK: Se alocação falhou E configuramos temperatura aqui, remove configuração órfã
        if not resultado_alocacao and temperatura_configurada_aqui:
            logger.debug(f"🔄 Rollback: removendo configuração de temperatura órfã da {camara.nome}")
            try:
                # Remove da lista intervalos_temperatura (formato: [(temperatura, inicio, fim), ...])
                if hasattr(camara, 'intervalos_temperatura'):
                    # Filtra removendo configurações órfãs que coincidem com inicio e fim
                    camara.intervalos_temperatura = [
                        (temp, inicio_config, fim_config)
                        for temp, inicio_config, fim_config in camara.intervalos_temperatura
                        if not (inicio_config == inicio and fim_config == fim)
                    ]
                    logger.debug(f"✅ Configuração órfã removida da {camara.nome} (temperatura {temperatura_desejada}°C, {inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')})")
                else:
                    logger.warning(f"⚠️ Não foi possível fazer rollback: {camara.nome} não tem intervalos_temperatura")
            except Exception as e:
                logger.warning(f"⚠️ Erro no rollback de temperatura da {camara.nome}: {e}")

        return resultado_alocacao

    def _tentar_alocacao_freezer(
        self,
        freezer: Freezer,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        tipo_armazenamento: str,
        temperatura_desejada: int,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int
    ) -> bool:
        """
        Tenta alocar no freezer usando volume real por caixas.
        Freezer só funciona com CAIXAS.
        ✅ ATUALIZADO com verificação dinâmica
        """
        # Freezer só suporta armazenamento em caixas
        if tipo_armazenamento != "CAIXAS":
            logger.warning(f"❌ {freezer.nome}: freezer só suporta armazenamento em CAIXAS, recebido: {tipo_armazenamento}")
            return False
        
        # Verifica compatibilidade de temperatura
        if not freezer.verificar_compatibilidade_temperatura(temperatura_desejada, inicio, fim):
            logger.debug(f"❌ {freezer.nome}: temperatura incompatível")
            return False

        # Configura temperatura se necessário - MARCANDO PARA POSSÍVEL ROLLBACK
        temp_atual = freezer.obter_temperatura_periodo(inicio, fim)
        temperatura_configurada_aqui = False

        if temp_atual is None:
            if not freezer.configurar_temperatura(temperatura_desejada, inicio, fim):
                logger.debug(f"❌ {freezer.nome}: falha ao configurar temperatura")
                return False
            temperatura_configurada_aqui = True  # Marcamos que configuramos aqui

        # Obtém a capacidade por recipiente baseada no tipo de produto
        tipo_produto = self._obter_tipo_produto(atividade, freezer)
        resultado_alocacao = False

        if tipo_produto == "UNIDADES":
            unidades_por_caixa = self._obter_unidades_por_caixa(atividade, freezer)
            if unidades_por_caixa is None:
                logger.warning(f"⚠️ Unidades por caixa não definido para {freezer.nome}. Usando conversão padrão.")
                quantidade_ocupacao = gramas_para_caixas(quantidade_produto)
                resultado_alocacao = self._ocupar_freezer_caixas_compativel(
                    freezer, id_ordem, id_pedido, id_atividade, id_item,
                    quantidade_ocupacao, inicio, fim, temperatura_desejada
                )
            else:
                resultado_alocacao = self._ocupar_freezer_caixas_volume_real_dinamico(
                    freezer, id_ordem, id_pedido, id_atividade, id_item,
                    quantidade_produto, unidades_por_caixa, inicio, fim, temperatura_desejada
                )
        else:  # GRAMAS
            gramas_por_caixa = self._obter_gramas_por_caixa(atividade, freezer)
            if gramas_por_caixa is None:
                logger.warning(f"⚠️ Gramas por caixa não definido para {freezer.nome}. Usando conversão padrão.")
                quantidade_ocupacao = gramas_para_caixas(quantidade_produto)
                resultado_alocacao = self._ocupar_freezer_caixas_compativel(
                    freezer, id_ordem, id_pedido, id_atividade, id_item,
                    quantidade_ocupacao, inicio, fim, temperatura_desejada
                )
            else:
                resultado_alocacao = self._ocupar_freezer_caixas_volume_real_dinamico(
                    freezer, id_ordem, id_pedido, id_atividade, id_item,
                    quantidade_produto, gramas_por_caixa, inicio, fim, temperatura_desejada
                )

        # 🔧 ROLLBACK: Se alocação falhou E configuramos temperatura aqui, remove configuração órfã
        if not resultado_alocacao and temperatura_configurada_aqui:
            logger.debug(f"🔄 Rollback: removendo configuração de temperatura órfã do {freezer.nome}")
            try:
                # Remove da lista intervalos_temperatura (formato: [(temperatura, inicio, fim), ...])
                if hasattr(freezer, 'intervalos_temperatura'):
                    # Filtra removendo configurações órfãs que coincidem com inicio e fim
                    freezer.intervalos_temperatura = [
                        (temp, inicio_config, fim_config)
                        for temp, inicio_config, fim_config in freezer.intervalos_temperatura
                        if not (inicio_config == inicio and fim_config == fim)
                    ]
                    logger.debug(f"✅ Configuração órfã removida do {freezer.nome} (temperatura {temperatura_desejada}°C, {inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')})")
                else:
                    logger.warning(f"⚠️ Não foi possível fazer rollback: {freezer.nome} não tem intervalos_temperatura")
            except Exception as e:
                logger.warning(f"⚠️ Erro no rollback de temperatura do {freezer.nome}: {e}")

        return resultado_alocacao

    # ==========================================================
    # 🆕 MÉTODOS DE OCUPAÇÃO COM VERIFICAÇÃO DINÂMICA
    # ==========================================================
    def _ocupar_camara_caixas_volume_real_dinamico(
        self,
        camara: CamaraRefrigerada,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_produto: int,
        capacidade_por_caixa: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int] = None
    ) -> bool:
        """
        Ocupa caixas na câmara refrigerada baseado no volume real com verificação dinâmica.
        ✅ NOVO: Usa verificação dinâmica de intervalos
        ✅ ATUALIZADO para usar novos atributos da câmara
        """
        logger.debug(f"🎯 Tentando ocupar {quantidade_produto} em caixas de {capacidade_por_caixa}/caixa na {camara.nome} (dinâmico)")
        
        # ETAPA 1: Tenta aproveitar caixas existentes do mesmo item usando verificação dinâmica
        quantidade_restante = quantidade_produto
        
        for numero_caixa in range(camara.capacidade_caixa_min, camara.capacidade_caixa_max + 1):
            if quantidade_restante <= 0:
                break
                
            # Usa verificação dinâmica para determinar quanto pode ser adicionado
            compativel, capacidade_disponivel = self._verificar_compatibilidade_recipiente(
                camara, numero_caixa, id_item, quantidade_restante, capacidade_por_caixa, inicio, fim, "caixa"
            )
            
            if compativel and capacidade_disponivel > 0:
                quantidade_adicionar = min(quantidade_restante, capacidade_disponivel)
                
                # Valida novamente antes de alocar
                if self._validar_nova_ocupacao_recipiente(camara, numero_caixa, id_item, quantidade_adicionar, capacidade_por_caixa, inicio, fim, "caixa"):
                    sucesso = camara.adicionar_ocupacao_caixa(
                        numero_caixa=numero_caixa,
                        id_ordem=id_ordem,
                        id_pedido=id_pedido,
                        id_atividade=id_atividade,
                        id_item=id_item,
                        quantidade=quantidade_adicionar,
                        inicio=inicio,
                        fim=fim,
                        temperatura=temperatura
                    )
                    
                    if sucesso:
                        quantidade_restante -= quantidade_adicionar
                        logger.debug(f"♻️ Aproveitada caixa {numero_caixa} existente (dinâmico): +{quantidade_adicionar}")

        # ETAPA 2: Para quantidade restante, ocupa caixas novas
        if quantidade_restante > 0:
            logger.debug(f"📦 Quantidade restante: {quantidade_restante} - procurando caixas livres")
            
            caixas_novas_necessarias = int((quantidade_restante + capacidade_por_caixa - 1) // capacidade_por_caixa)
            caixas_disponiveis = camara.caixas_disponiveis_periodo(inicio, fim)
            
            if len(caixas_disponiveis) < caixas_novas_necessarias:
                logger.warning(f"❌ Não há caixas livres suficientes na {camara.nome}. "
                            f"Necessárias: {caixas_novas_necessarias} caixas, "
                            f"Disponíveis: {len(caixas_disponiveis)} caixas")
                return False

            caixas_para_ocupar = caixas_disponiveis[:caixas_novas_necessarias]
            quantidade_a_alocar = quantidade_restante
            
            for numero_caixa in caixas_para_ocupar:
                quantidade_nesta_caixa = min(quantidade_a_alocar, capacidade_por_caixa)
                
                # Valida antes de alocar
                if self._validar_nova_ocupacao_recipiente(camara, numero_caixa, id_item, quantidade_nesta_caixa, capacidade_por_caixa, inicio, fim, "caixa"):
                    sucesso = camara.adicionar_ocupacao_caixa(
                        numero_caixa=numero_caixa,
                        id_ordem=id_ordem,
                        id_pedido=id_pedido,
                        id_atividade=id_atividade,
                        id_item=id_item,
                        quantidade=quantidade_nesta_caixa,
                        inicio=inicio,
                        fim=fim,
                        temperatura=temperatura
                    )
                    
                    if sucesso:
                        quantidade_a_alocar -= quantidade_nesta_caixa
                        logger.debug(f"📦 Nova caixa {numero_caixa} ocupada com {quantidade_nesta_caixa} (dinâmico)")
                    else:
                        logger.warning(f"❌ Falha ao ocupar caixa {numero_caixa}")
                        return False
                else:
                    logger.warning(f"❌ Validação dinâmica falhou para caixa {numero_caixa}")
                    return False

        logger.info(f"📦 Ocupação concluída na {camara.nome}: {quantidade_produto} total (dinâmico)")
        return True

    def _ocupar_camara_niveis_volume_real_dinamico(
        self,
        camara: CamaraRefrigerada,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_produto: int,
        capacidade_por_nivel: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int] = None
    ) -> bool:
        """
        Ocupa níveis de tela na câmara refrigerada baseado no volume real com verificação dinâmica.
        ✅ NOVO: Usa verificação dinâmica de intervalos
        ✅ ATUALIZADO para usar níveis de tela (nivel_fisico + tela)
        """
        logger.debug(f"🎯 Tentando ocupar {quantidade_produto} em níveis de tela de {capacidade_por_nivel}/nível na {camara.nome} (dinâmico)")
        
        # ETAPA 1: Tenta aproveitar níveis de tela existentes do mesmo item usando verificação dinâmica
        quantidade_restante = quantidade_produto
        
        for nivel_fisico, tela in camara.obter_numeros_niveis_tela_disponiveis():
            if quantidade_restante <= 0:
                break
                
            # Usa verificação dinâmica para determinar quanto pode ser adicionado
            compativel, capacidade_disponivel = self._verificar_compatibilidade_recipiente(
                camara, (nivel_fisico, tela), id_item, quantidade_restante, capacidade_por_nivel, inicio, fim, "nivel_tela"
            )
            
            if compativel and capacidade_disponivel > 0:
                quantidade_adicionar = min(quantidade_restante, capacidade_disponivel)
                
                # Valida novamente antes de alocar
                if self._validar_nova_ocupacao_recipiente(camara, (nivel_fisico, tela), id_item, quantidade_adicionar, capacidade_por_nivel, inicio, fim, "nivel_tela"):
                    sucesso = camara.adicionar_ocupacao_nivel_tela(
                        numero_nivel_fisico=nivel_fisico,
                        numero_tela=tela,
                        id_ordem=id_ordem,
                        id_pedido=id_pedido,
                        id_atividade=id_atividade,
                        id_item=id_item,
                        quantidade=quantidade_adicionar,
                        inicio=inicio,
                        fim=fim,
                        temperatura=temperatura
                    )
                    
                    if sucesso:
                        quantidade_restante -= quantidade_adicionar
                        logger.debug(f"♻️ Aproveitado nível {nivel_fisico}, tela {tela} existente (dinâmico): +{quantidade_adicionar}")

        # ETAPA 2: Para quantidade restante, ocupa níveis de tela novos
        if quantidade_restante > 0:
            logger.debug(f"📋 Quantidade restante: {quantidade_restante} - procurando níveis de tela livres")
            
            niveis_novos_necessarios = int((quantidade_restante + capacidade_por_nivel - 1) // capacidade_por_nivel)
            niveis_tela_disponiveis = camara.niveis_tela_disponiveis_periodo(inicio, fim)
            
            if len(niveis_tela_disponiveis) < niveis_novos_necessarios:
                logger.warning(f"❌ Não há níveis de tela livres suficientes na {camara.nome}. "
                            f"Necessários: {niveis_novos_necessarios} níveis de tela, "
                            f"Disponíveis: {len(niveis_tela_disponiveis)} níveis de tela")
                return False

            niveis_tela_para_ocupar = niveis_tela_disponiveis[:niveis_novos_necessarios]
            quantidade_a_alocar = quantidade_restante
            
            for nivel_fisico, tela in niveis_tela_para_ocupar:
                quantidade_neste_nivel = min(quantidade_a_alocar, capacidade_por_nivel)
                
                # Valida antes de alocar
                if self._validar_nova_ocupacao_recipiente(camara, (nivel_fisico, tela), id_item, quantidade_neste_nivel, capacidade_por_nivel, inicio, fim, "nivel_tela"):
                    sucesso = camara.adicionar_ocupacao_nivel_tela(
                        numero_nivel_fisico=nivel_fisico,
                        numero_tela=tela,
                        id_ordem=id_ordem,
                        id_pedido=id_pedido,
                        id_atividade=id_atividade,
                        id_item=id_item,
                        quantidade=quantidade_neste_nivel,
                        inicio=inicio,
                        fim=fim,
                        temperatura=temperatura
                    )
                    
                    if sucesso:
                        quantidade_a_alocar -= quantidade_neste_nivel
                        logger.debug(f"📋 Novo nível {nivel_fisico}, tela {tela} ocupado com {quantidade_neste_nivel} (dinâmico)")
                    else:
                        logger.warning(f"❌ Falha ao ocupar nível {nivel_fisico}, tela {tela}")
                        return False
                else:
                    logger.warning(f"❌ Validação dinâmica falhou para nível {nivel_fisico}, tela {tela}")
                    return False

        logger.info(f"📋 Ocupação concluída na {camara.nome}: {quantidade_produto} total (dinâmico)")
        return True

    def _ocupar_freezer_caixas_volume_real_dinamico(
        self,
        freezer: Freezer,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_produto: int,
        capacidade_por_caixa: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int] = None
    ) -> bool:
        """
        Ocupa caixas no freezer baseado no volume real com verificação dinâmica.
        ✅ NOVO: Usa verificação dinâmica de intervalos
        """
        logger.debug(f"🧊 Tentando ocupar {quantidade_produto} em caixas de {capacidade_por_caixa}/caixa no {freezer.nome} (dinâmico)")
        
        # ETAPA 1: Tenta aproveitar caixas existentes do mesmo item usando verificação dinâmica
        quantidade_restante = quantidade_produto
        
        for numero_caixa in range(freezer.capacidade_caixa_min, freezer.capacidade_caixa_max + 1):
            if quantidade_restante <= 0:
                break
                
            # Usa verificação dinâmica para determinar quanto pode ser adicionado
            compativel, capacidade_disponivel = self._verificar_compatibilidade_recipiente(
                freezer, numero_caixa, id_item, quantidade_restante, capacidade_por_caixa, inicio, fim, "caixa"
            )
            
            if compativel and capacidade_disponivel > 0:
                quantidade_adicionar = min(quantidade_restante, capacidade_disponivel)
                
                # Valida novamente antes de alocar
                if self._validar_nova_ocupacao_recipiente(freezer, numero_caixa, id_item, quantidade_adicionar, capacidade_por_caixa, inicio, fim, "caixa"):
                    sucesso = freezer.adicionar_ocupacao_caixa(
                        numero_caixa=numero_caixa,
                        id_ordem=id_ordem,
                        id_pedido=id_pedido,
                        id_atividade=id_atividade,
                        id_item=id_item,
                        quantidade=quantidade_adicionar,
                        inicio=inicio,
                        fim=fim,
                        temperatura=temperatura
                    )
                    
                    if sucesso:
                        quantidade_restante -= quantidade_adicionar
                        logger.debug(f"♻️ Aproveitada caixa {numero_caixa} existente no freezer (dinâmico): +{quantidade_adicionar}")

        # ETAPA 2: Para quantidade restante, ocupa caixas novas
        if quantidade_restante > 0:
            logger.debug(f"🧊 Quantidade restante: {quantidade_restante} - procurando caixas livres")
            
            caixas_novas_necessarias = int((quantidade_restante + capacidade_por_caixa - 1) // capacidade_por_caixa)
            caixas_disponiveis = freezer.caixas_disponiveis_periodo(inicio, fim)
            
            if len(caixas_disponiveis) < caixas_novas_necessarias:
                logger.warning(f"❌ Não há caixas livres suficientes no {freezer.nome}. "
                            f"Necessárias: {caixas_novas_necessarias} caixas, "
                            f"Disponíveis: {len(caixas_disponiveis)} caixas")
                return False

            caixas_para_ocupar = caixas_disponiveis[:caixas_novas_necessarias]
            quantidade_a_alocar = quantidade_restante
            
            for numero_caixa in caixas_para_ocupar:
                quantidade_nesta_caixa = min(quantidade_a_alocar, capacidade_por_caixa)
                
                # Valida antes de alocar
                if self._validar_nova_ocupacao_recipiente(freezer, numero_caixa, id_item, quantidade_nesta_caixa, capacidade_por_caixa, inicio, fim, "caixa"):
                    sucesso = freezer.adicionar_ocupacao_caixa(
                        numero_caixa=numero_caixa,
                        id_ordem=id_ordem,
                        id_pedido=id_pedido,
                        id_atividade=id_atividade,
                        id_item=id_item,
                        quantidade=quantidade_nesta_caixa,
                        inicio=inicio,
                        fim=fim,
                        temperatura=temperatura
                    )
                    
                    if sucesso:
                        quantidade_a_alocar -= quantidade_nesta_caixa
                        logger.debug(f"🧊 Nova caixa {numero_caixa} ocupada com {quantidade_nesta_caixa} no freezer (dinâmico)")
                    else:
                        logger.warning(f"❌ Falha ao ocupar caixa {numero_caixa} no freezer")
                        return False
                else:
                    logger.warning(f"❌ Validação dinâmica falhou para caixa {numero_caixa} no freezer")
                    return False

        logger.info(f"🧊 Ocupação concluída no {freezer.nome}: {quantidade_produto} total (dinâmico)")
        return True

    # ==========================================================
    # 🔧 Métodos de Ocupação Compatíveis (Fallback) - MANTIDOS
    # ==========================================================
    def _ocupar_camara_caixas_compativel(
        self,
        camara: CamaraRefrigerada,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_caixas: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int] = None
    ) -> bool:
        """
        Método de compatibilidade para ocupar caixas quando não há configuração específica.
        Usa a conversão padrão (1 unidade por caixa).
        """
        caixas_disponiveis = camara.caixas_disponiveis_periodo(inicio, fim)
        
        if len(caixas_disponiveis) < quantidade_caixas:
            logger.warning(f"❌ Não há caixas suficientes na {camara.nome}. "
                         f"Necessárias: {quantidade_caixas}, Disponíveis: {len(caixas_disponiveis)}")
            return False

        caixas_para_ocupar = caixas_disponiveis[:quantidade_caixas]
        
        for numero_caixa in caixas_para_ocupar:
            sucesso = camara.adicionar_ocupacao_caixa(
                numero_caixa=numero_caixa,
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade=1.0,  # 1 unidade por caixa (método padrão)
                inicio=inicio,
                fim=fim,
                temperatura=temperatura
            )
            if not sucesso:
                logger.warning(f"❌ Falha ao ocupar caixa {numero_caixa} na {camara.nome}")
                return False

        logger.info(f"📦 Ocupadas {quantidade_caixas} caixas na {camara.nome} (método padrão)")
        return True

    def _ocupar_camara_niveis_compativel(
        self,
        camara: CamaraRefrigerada,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_niveis: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int] = None
    ) -> bool:
        """
        Método de compatibilidade para ocupar níveis de tela quando não há configuração específica.
        Usa a conversão padrão (1 unidade por nível de tela).
        ✅ ATUALIZADO para usar níveis de tela (nivel_fisico + tela)
        """
        niveis_tela_disponiveis = camara.niveis_tela_disponiveis_periodo(inicio, fim)
        
        if len(niveis_tela_disponiveis) < quantidade_niveis:
            logger.warning(f"❌ Não há níveis de tela suficientes na {camara.nome}. "
                         f"Necessários: {quantidade_niveis}, Disponíveis: {len(niveis_tela_disponiveis)}")
            return False

        niveis_tela_para_ocupar = niveis_tela_disponiveis[:quantidade_niveis]
        
        for nivel_fisico, tela in niveis_tela_para_ocupar:
            sucesso = camara.adicionar_ocupacao_nivel_tela(
                numero_nivel_fisico=nivel_fisico,
                numero_tela=tela,
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade=1.0,  # 1 unidade por nível de tela (método padrão)
                inicio=inicio,
                fim=fim,
                temperatura=temperatura
            )
            if not sucesso:
                logger.warning(f"❌ Falha ao ocupar nível {nivel_fisico}, tela {tela} na {camara.nome}")
                return False

        logger.info(f"📋 Ocupados {quantidade_niveis} níveis de tela na {camara.nome} (método padrão)")
        return True

    def _ocupar_freezer_caixas_compativel(
        self,
        freezer: Freezer,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_caixas: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int] = None
    ) -> bool:
        """
        Método de compatibilidade para ocupar caixas do freezer quando não há configuração específica.
        Usa a conversão padrão (1 unidade por caixa).
        """
        caixas_disponiveis = freezer.caixas_disponiveis_periodo(inicio, fim)
        
        if len(caixas_disponiveis) < quantidade_caixas:
            logger.warning(f"❌ Não há caixas suficientes no {freezer.nome}. "
                         f"Necessárias: {quantidade_caixas}, Disponíveis: {len(caixas_disponiveis)}")
            return False

        caixas_para_ocupar = caixas_disponiveis[:quantidade_caixas]
        
        for numero_caixa in caixas_para_ocupar:
            sucesso = freezer.adicionar_ocupacao_caixa(
                numero_caixa=numero_caixa,
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade=1.0,  # 1 unidade por caixa (método padrão)
                inicio=inicio,
                fim=fim,
                temperatura=temperatura
            )
            if not sucesso:
                logger.warning(f"❌ Falha ao ocupar caixa {numero_caixa} no {freezer.nome}")
                return False

        logger.info(f"🧊 Ocupadas {quantidade_caixas} caixas no {freezer.nome} (método padrão)")
        return True

    # ==========================================================
    # 🔓 Liberações (Corrigidas para Consistência)
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por atividade."""
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for equipamento in self.equipamentos:
            equipamento.liberar_por_atividade(id_ordem, id_pedido, id_atividade)

    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por pedido."""
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for equipamento in self.equipamentos:
            equipamento.liberar_por_pedido(id_ordem, id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por ordem."""
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for equipamento in self.equipamentos:
            equipamento.liberar_por_ordem(id_ordem)
    
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        for equipamento in self.equipamentos:
            equipamento.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        """Libera todas as ocupações."""
        for equipamento in self.equipamentos:
            equipamento.liberar_todas_ocupacoes()

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        for equipamento in self.equipamentos:
            equipamento.liberar_por_intervalo(inicio, fim)

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        """
        📅 Exibe no log as agendas de todos os equipamentos refrigeradores e congeladores.
        """
        logger.info("==============================================")
        logger.info("📅 Agenda das Câmaras de Refrigeração/Congelamento")
        logger.info("==============================================")
        for equipamento in self.equipamentos:
            equipamento.mostrar_agenda()

    # ==========================================================
    # 📊 Estatísticas e Relatórios
    # ==========================================================
    def obter_estatisticas_globais(self, inicio: datetime, fim: datetime) -> dict:
        """
        Retorna estatísticas consolidadas de todos os equipamentos.
        ✅ ATUALIZADO para usar novos métodos dos equipamentos
        """
        estatisticas = {
            'total_equipamentos': len(self.equipamentos),
            'equipamentos_utilizados': 0,
            'detalhes_por_equipamento': {}
        }

        for equipamento in self.equipamentos:
            nome_equipamento = equipamento.nome
            
            # Tenta obter estatísticas específicas do tipo de equipamento
            if isinstance(equipamento, CamaraRefrigerada):
                # Para câmaras, verifica ocupação em níveis de tela e caixas
                tem_ocupacao_niveis = equipamento.tem_ocupacao_niveis_periodo(inicio, fim)
                tem_ocupacao_caixas = equipamento.tem_ocupacao_caixas_periodo(inicio, fim)
                tem_ocupacao = tem_ocupacao_niveis or tem_ocupacao_caixas
                
                estatisticas['detalhes_por_equipamento'][nome_equipamento] = {
                    'tipo': 'CamaraRefrigerada',
                    'tem_ocupacao': tem_ocupacao,
                    'ocupacao_niveis_tela': tem_ocupacao_niveis,
                    'ocupacao_caixas': tem_ocupacao_caixas,
                    'capacidades': equipamento.obter_estatisticas_capacidade()
                }
            elif isinstance(equipamento, Freezer):
                # Para freezer, verifica ocupação em caixas
                tem_ocupacao_caixas = equipamento.tem_ocupacao_caixas_periodo(inicio, fim)
                
                estatisticas['detalhes_por_equipamento'][nome_equipamento] = {
                    'tipo': 'Freezer',
                    'tem_ocupacao': tem_ocupacao_caixas,
                    'ocupacao_caixas': tem_ocupacao_caixas,
                    'capacidades': equipamento.obter_estatisticas_capacidade()
                }
            else:
                # Para outros tipos
                tem_ocupacao = equipamento.tem_ocupacao_periodo(inicio, fim) if hasattr(equipamento, 'tem_ocupacao_periodo') else False
                
                estatisticas['detalhes_por_equipamento'][nome_equipamento] = {
                    'tipo': type(equipamento).__name__,
                    'tem_ocupacao': tem_ocupacao
                }
            
            if estatisticas['detalhes_por_equipamento'][nome_equipamento]['tem_ocupacao']:
                estatisticas['equipamentos_utilizados'] += 1

        return estatisticas

    def obter_equipamentos_disponiveis(self, inicio: datetime, fim: datetime, tipo_armazenamento: str = None) -> List[RefrigeradoresCongeladores]:
        """
        Retorna lista de equipamentos que têm capacidade disponível.
        ✅ ATUALIZADO para usar novos métodos dos equipamentos
        """
        equipamentos_disponiveis = []
        
        for equipamento in self.equipamentos:
            disponivel = False
            
            if isinstance(equipamento, CamaraRefrigerada):
                if tipo_armazenamento == "CAIXAS":
                    caixas_disponiveis = equipamento.caixas_disponiveis_periodo(inicio, fim)
                    disponivel = len(caixas_disponiveis) > 0
                elif tipo_armazenamento == "NIVEIS_TELA":
                    niveis_tela_disponiveis = equipamento.niveis_tela_disponiveis_periodo(inicio, fim)
                    disponivel = len(niveis_tela_disponiveis) > 0
                else:
                    # Verifica se tem qualquer tipo de espaço disponível
                    disponivel = (len(equipamento.caixas_disponiveis_periodo(inicio, fim)) > 0 or
                                len(equipamento.niveis_tela_disponiveis_periodo(inicio, fim)) > 0)
            elif isinstance(equipamento, Freezer):
                # Freezer só tem caixas
                if tipo_armazenamento is None or tipo_armazenamento == "CAIXAS":
                    caixas_disponiveis = equipamento.caixas_disponiveis_periodo(inicio, fim)
                    disponivel = len(caixas_disponiveis) > 0
                else:
                    disponivel = False  # Freezer não suporta outros tipos
            else:
                # Para outros tipos de equipamento
                if hasattr(equipamento, 'tem_ocupacao_periodo'):
                    disponivel = not equipamento.tem_ocupacao_periodo(inicio, fim)
                else:
                    disponivel = True  # Assume disponível se não conseguir verificar
            
            if disponivel:
                equipamentos_disponiveis.append(equipamento)
        
        return equipamentos_disponiveis

    # ==========================================================
    # 🆕 MÉTODOS DE ANÁLISE COM VERIFICAÇÃO DINÂMICA
    # ==========================================================
    def obter_relatorio_ocupacao_detalhado_dinamico(self, inicio: datetime, fim: datetime) -> dict:
        """
        Retorna relatório detalhado da ocupação com análise temporal dinâmica.
        ✅ NOVO: Relatório com verificação dinâmica de intervalos
        """
        relatorio = {
            'periodo': f"{inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}",
            'equipamentos': {},
            'picos_ocupacao': {},
            'conflitos_temporais': []
        }

        for equipamento in self.equipamentos:
            nome_equipamento = equipamento.nome
            relatorio['equipamentos'][nome_equipamento] = {
                'tipo': type(equipamento).__name__,
                'itens_processados': set(),
                'recipientes_utilizados': [],
                'pico_ocupacao_total': 0
            }

            # Analisa ocupação por recipiente
            if isinstance(equipamento, CamaraRefrigerada):
                # Analisa caixas
                for numero_caixa in range(equipamento.capacidade_caixa_min, equipamento.capacidade_caixa_max + 1):
                    ocupacoes = equipamento.obter_ocupacoes_caixa(numero_caixa)
                    if ocupacoes:
                        for ocupacao in ocupacoes:
                            if len(ocupacao) >= 7:
                                _, _, _, id_item, quantidade, inicio_ocup, fim_ocup = ocupacao[:7]
                                if not (fim <= inicio_ocup or inicio >= fim_ocup):  # há sobreposição
                                    relatorio['equipamentos'][nome_equipamento]['itens_processados'].add(id_item)
                                    relatorio['equipamentos'][nome_equipamento]['recipientes_utilizados'].append({
                                        'tipo': 'caixa',
                                        'numero': numero_caixa,
                                        'item': id_item,
                                        'quantidade': quantidade,
                                        'inicio': inicio_ocup.strftime('%H:%M'),
                                        'fim': fim_ocup.strftime('%H:%M')
                                    })

                # Analisa níveis de tela
                for nivel_fisico, tela in equipamento.obter_numeros_niveis_tela_disponiveis():
                    ocupacoes = equipamento.obter_ocupacoes_nivel_tela(nivel_fisico, tela)
                    if ocupacoes:
                        for ocupacao in ocupacoes:
                            _, _, _, id_item, quantidade, inicio_ocup, fim_ocup = ocupacao
                            if not (fim <= inicio_ocup or inicio >= fim_ocup):  # há sobreposição
                                relatorio['equipamentos'][nome_equipamento]['itens_processados'].add(id_item)
                                relatorio['equipamentos'][nome_equipamento]['recipientes_utilizados'].append({
                                    'tipo': 'nivel_tela',
                                    'numero': f"{nivel_fisico}-{tela}",
                                    'item': id_item,
                                    'quantidade': quantidade,
                                    'inicio': inicio_ocup.strftime('%H:%M'),
                                    'fim': fim_ocup.strftime('%H:%M')
                                })

            elif isinstance(equipamento, Freezer):
                # Analisa apenas caixas para freezer
                for numero_caixa in range(equipamento.capacidade_caixa_min, equipamento.capacidade_caixa_max + 1):
                    ocupacoes = equipamento.obter_ocupacoes_caixa(numero_caixa)
                    if ocupacoes:
                        for ocupacao in ocupacoes:
                            if len(ocupacao) >= 7:
                                _, _, _, id_item, quantidade, inicio_ocup, fim_ocup = ocupacao[:7]
                                if not (fim <= inicio_ocup or inicio >= fim_ocup):  # há sobreposição
                                    relatorio['equipamentos'][nome_equipamento]['itens_processados'].add(id_item)
                                    relatorio['equipamentos'][nome_equipamento]['recipientes_utilizados'].append({
                                        'tipo': 'caixa',
                                        'numero': numero_caixa,
                                        'item': id_item,
                                        'quantidade': quantidade,
                                        'inicio': inicio_ocup.strftime('%H:%M'),
                                        'fim': fim_ocup.strftime('%H:%M')
                                    })

            # Converte sets para listas para serialização
            relatorio['equipamentos'][nome_equipamento]['itens_processados'] = list(
                relatorio['equipamentos'][nome_equipamento]['itens_processados']
            )

        return relatorio

    def verificar_conflitos_capacidade_dinamica(self, inicio: datetime, fim: datetime) -> List[dict]:
        """
        Verifica conflitos de capacidade usando análise temporal dinâmica.
        ✅ NOVO: Detecção de conflitos com verificação dinâmica
        """
        conflitos = []

        for equipamento in self.equipamentos:
            nome_equipamento = equipamento.nome

            if isinstance(equipamento, CamaraRefrigerada):
                # Verifica conflitos em caixas
                for numero_caixa in range(equipamento.capacidade_caixa_min, equipamento.capacidade_caixa_max + 1):
                    ocupacoes = equipamento.obter_ocupacoes_caixa(numero_caixa)
                    if len(ocupacoes) > 1:  # Múltiplas ocupações na mesma caixa
                        # Agrupa por item para verificar sobreposições
                        itens_ocupacao = {}
                        for ocupacao in ocupacoes:
                            if len(ocupacao) >= 7:
                                _, _, _, id_item, quantidade, inicio_ocup, fim_ocup = ocupacao[:7]
                                if not (fim <= inicio_ocup or inicio >= fim_ocup):  # há sobreposição temporal
                                    if id_item not in itens_ocupacao:
                                        itens_ocupacao[id_item] = []
                                    itens_ocupacao[id_item].append({
                                        'quantidade': quantidade,
                                        'inicio': inicio_ocup,
                                        'fim': fim_ocup
                                    })

                        # Verifica se há múltiplos itens ou excesso de capacidade
                        if len(itens_ocupacao) > 1:
                            conflitos.append({
                                'equipamento': nome_equipamento,
                                'recipiente': f"caixa_{numero_caixa}",
                                'tipo_conflito': 'multiplos_itens',
                                'itens': list(itens_ocupacao.keys()),
                                'detalhes': itens_ocupacao
                            })

                # Verifica conflitos em níveis de tela
                for nivel_fisico, tela in equipamento.obter_numeros_niveis_tela_disponiveis():
                    ocupacoes = equipamento.obter_ocupacoes_nivel_tela(nivel_fisico, tela)
                    if len(ocupacoes) > 1:  # Múltiplas ocupações no mesmo nível de tela
                        # Similar à análise de caixas
                        itens_ocupacao = {}
                        for ocupacao in ocupacoes:
                            _, _, _, id_item, quantidade, inicio_ocup, fim_ocup = ocupacao
                            if not (fim <= inicio_ocup or inicio >= fim_ocup):  # há sobreposição temporal
                                if id_item not in itens_ocupacao:
                                    itens_ocupacao[id_item] = []
                                itens_ocupacao[id_item].append({
                                    'quantidade': quantidade,
                                    'inicio': inicio_ocup,
                                    'fim': fim_ocup
                                })

                        if len(itens_ocupacao) > 1:
                            conflitos.append({
                                'equipamento': nome_equipamento,
                                'recipiente': f"nivel_{nivel_fisico}_tela_{tela}",
                                'tipo_conflito': 'multiplos_itens',
                                'itens': list(itens_ocupacao.keys()),
                                'detalhes': itens_ocupacao
                            })

            elif isinstance(equipamento, Freezer):
                # Verifica conflitos em caixas do freezer
                for numero_caixa in range(equipamento.capacidade_caixa_min, equipamento.capacidade_caixa_max + 1):
                    ocupacoes = equipamento.obter_ocupacoes_caixa(numero_caixa)
                    if len(ocupacoes) > 1:  # Múltiplas ocupações na mesma caixa
                        itens_ocupacao = {}
                        for ocupacao in ocupacoes:
                            if len(ocupacao) >= 7:
                                _, _, _, id_item, quantidade, inicio_ocup, fim_ocup = ocupacao[:7]
                                if not (fim <= inicio_ocup or inicio >= fim_ocup):  # há sobreposição temporal
                                    if id_item not in itens_ocupacao:
                                        itens_ocupacao[id_item] = []
                                    itens_ocupacao[id_item].append({
                                        'quantidade': quantidade,
                                        'inicio': inicio_ocup,
                                        'fim': fim_ocup
                                    })

                        if len(itens_ocupacao) > 1:
                            conflitos.append({
                                'equipamento': nome_equipamento,
                                'recipiente': f"caixa_{numero_caixa}",
                                'tipo_conflito': 'multiplos_itens',
                                'itens': list(itens_ocupacao.keys()),
                                'detalhes': itens_ocupacao
                            })

        return conflitos