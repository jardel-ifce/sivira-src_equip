from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union, TYPE_CHECKING, Dict
from models.equipamentos.armario_esqueleto import ArmarioEsqueleto
from models.equipamentos.armario_fermentador import ArmarioFermentador
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logs.logger_factory import setup_logger
import unicodedata

# 🗄️ Logger exclusivo do gestor de Armários para Fermentação
logger = setup_logger('GestorArmariosParaFermentacao')

Armarios = Union[ArmarioEsqueleto, ArmarioFermentador]

class GestorArmariosParaFermentacao:
    """
    🗄️ Gestor especializado no controle de Armários para Fermentação (tipo Esqueleto e Fermentador).
    
    Funcionalidades:
    - Permite mesmo id_item no mesmo nível com intervalos diferentes
    - Usa capacidade por nível definida no JSON da atividade
    - Valida soma de quantidades não excede capacidade do nível
    - Mantém intervalos independentes para cada pedido/ordem
    - Suporta unidades_por_nivel_tela e gramas_por_nivel_tela
    """
    def __init__(self, armarios: List[Armarios]):
        self.armarios = armarios
    
    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Armarios]:
        ordenadas = sorted(
            self.armarios,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        return ordenadas
  
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    def _obter_capacidade_por_nivel_tela(self, atividade: "AtividadeModular", armario: Armarios) -> Tuple[Optional[int], Optional[str]]:
        """
        Obtém a capacidade por nível de tela do armário a partir da atividade.
        Suporta tanto unidades_por_nivel_tela quanto gramas_por_nivel_tela.
        CORREÇÃO: Também aceita unidades_por_nivel e gramas_por_nivel (sem "_tela")
        Retorna (capacidade, tipo_unidade) onde tipo_unidade pode ser 'unidades' ou 'gramas'
        """
        try:
            chave = self._normalizar_nome(armario.nome)
            config = atividade.configuracoes_equipamentos.get(chave)
            
            if not config:
                logger.warning(f"⚠️ Configuração não encontrada para {armario.nome}")
                logger.debug(f"🔍 Chave normalizada tentada: '{chave}'")
                logger.debug(f"🔍 Chaves disponíveis em configuracoes_equipamentos: {list(atividade.configuracoes_equipamentos.keys())}")
                return None, None
            
            logger.debug(f"🔍 Configuração encontrada para {armario.nome}: {config}")
            
       
            # Verificar se tem unidades_por_nivel (formato antigo) - NOVO
            if "unidades_por_nivel" in config:
                capacidade = int(config["unidades_por_nivel"])
                logger.debug(f"📏 {armario.nome}: {capacidade} unidades por nível (formato antigo)")
                return capacidade, "unidades"
            
            
            # Verificar se tem gramas_por_nivel (formato antigo) - NOVO
            if "gramas_por_nivel" in config:
                capacidade = int(config["gramas_por_nivel"])
                logger.debug(f"📏 {armario.nome}: {capacidade} gramas por nível (formato antigo)")
                return capacidade, "gramas"
            
            else:
                logger.warning(f"⚠️ Nenhuma configuração de capacidade encontrada para {armario.nome}")
                logger.warning(f"🔍 Chaves disponíveis: {list(config.keys())}")
                logger.info(f"💡 Formatos suportados: unidades_por_nivel_tela, unidades_por_nivel, gramas_por_nivel_tela, gramas_por_nivel")
                return None, None
                
        except Exception as e:
            logger.error(f"❌ Erro ao obter capacidade por nível de tela para {armario.nome}: {e}")
            return None, None


    def _normalizar_nome(self, nome: str) -> str:
        nome_bruto = nome.lower().replace(" ", "_")
        return unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")

    # ==========================================================
    # 🔍 Validação de Capacidade por Nível (NOVO)
    # ==========================================================
    def _calcular_quantidade_maxima_nivel_item(self, armario: Armarios, nivel_index: int, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        Calcula a quantidade máxima do mesmo item que estará sendo processada
        simultaneamente no nível durante qualquer momento do período especificado.
        """
        if nivel_index < 0 or nivel_index >= armario.total_niveis_tela:
            return 0.0
        
        # Coleta todos os pontos temporais relevantes das ocupações do mesmo item
        pontos_temporais = set()
        ocupacoes_mesmo_item = []
        
        for ocupacao in armario.niveis_ocupacoes[nivel_index]:
            # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, inicio, fim)
            if ocupacao[3] == id_item:  # mesmo id_item
                ocupacoes_mesmo_item.append(ocupacao)
                pontos_temporais.add(ocupacao[5])  # início
                pontos_temporais.add(ocupacao[6])  # fim
        
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
                if ocupacao[5] <= momento_meio < ocupacao[6]:  # ocupação ativa neste momento
                    quantidade_momento += ocupacao[4]
            
            quantidade_maxima = max(quantidade_maxima, quantidade_momento)
        
        return quantidade_maxima

    def _validar_nova_ocupacao_nivel(self, armario: Armarios, nivel_index: int, id_item: int, 
                                   quantidade_nova: float, capacidade_nivel: float,
                                   inicio: datetime, fim: datetime) -> bool:
        """
        Valida se uma nova ocupação pode ser adicionada ao nível sem exceder a capacidade.
        Considera apenas ocupações do mesmo item (itens diferentes não podem coexistir).
        """
        if nivel_index < 0 or nivel_index >= armario.total_niveis_tela:
            return False
        
        # Verifica se há itens diferentes ocupando o nível no período
        for ocupacao in armario.niveis_ocupacoes[nivel_index]:
            # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, inicio, fim)
            if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):  # há sobreposição temporal
                if ocupacao[3] != id_item:  # item diferente
                    logger.debug(f"🚫 {armario.nome}[{nivel_index}]: item {ocupacao[3]} já presente, não pode adicionar item {id_item}")
                    return False
        
        # Calcula quantidade máxima atual do mesmo item
        quantidade_atual_maxima = self._calcular_quantidade_maxima_nivel_item(
            armario, nivel_index, id_item, inicio, fim
        )
        
        # Simula todos os pontos temporais com a nova ocupação
        pontos_temporais = set()
        ocupacoes_mesmo_item = []
        
        for ocupacao in armario.niveis_ocupacoes[nivel_index]:
            if ocupacao[3] == id_item:
                ocupacoes_mesmo_item.append(ocupacao)
                pontos_temporais.add(ocupacao[5])
                pontos_temporais.add(ocupacao[6])
        
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
                if ocupacao[5] <= momento_meio < ocupacao[6]:
                    quantidade_total += ocupacao[4]
            
            # Soma nova ocupação se ativa neste momento
            if inicio <= momento_meio < fim:
                quantidade_total += quantidade_nova
            
            # Verifica se excede capacidade
            if quantidade_total > capacidade_nivel:
                logger.debug(
                    f"❌ {armario.nome}[{nivel_index}]: Item {id_item} excederia capacidade no momento {momento_meio.strftime('%H:%M')} "
                    f"({quantidade_total} > {capacidade_nivel})"
                )
                return False
        
        return True

    def _verificar_compatibilidade_nivel(self, armario: Armarios, nivel_index: int, id_item: int, 
                                       quantidade: float, capacidade_nivel: float,
                                       inicio: datetime, fim: datetime) -> Tuple[bool, float]:
        """
        Verifica se um item pode ser adicionado a um nível específico e retorna a capacidade disponível.
        Retorna (pode_adicionar, capacidade_disponivel_para_item)
        """
        if nivel_index < 0 or nivel_index >= armario.total_niveis_tela:
            return False, 0.0
        
        # Valida se a nova ocupação é possível
        if not self._validar_nova_ocupacao_nivel(armario, nivel_index, id_item, quantidade, capacidade_nivel, inicio, fim):
            return False, 0.0
        
        # Calcula capacidade disponível para o item
        quantidade_atual_maxima = self._calcular_quantidade_maxima_nivel_item(
            armario, nivel_index, id_item, inicio, fim
        )
        
        capacidade_disponivel = capacidade_nivel - quantidade_atual_maxima
        
        return True, max(0.0, capacidade_disponivel)

    # ==========================================================
    # 🎯 Alocação Principal
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade: int,
        
    ) -> Tuple[bool, Optional[List[Armarios]], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        armarios_ordenados = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim
        
        # ✅ OBTER ID_ITEM da atividade
        id_item = getattr(atividade, 'id_item', None)
        if id_item is None:
            logger.error(f"❌ Atividade {atividade.id_atividade} não possui id_item definido")
            return False, None, None, None

        # ✅ OBTER CAPACIDADES por armário
        capacidades_map = {}
        for armario in armarios_ordenados:
            capacidade, tipo_unidade = self._obter_capacidade_por_nivel_tela(atividade, armario)
            
            if capacidade is None:
                logger.warning(f"⚠️ Pulando {armario.nome} - sem configuração de capacidade")
                continue
                
            capacidades_map[armario] = (capacidade, tipo_unidade)

        if not capacidades_map:
            logger.error(f"❌ Nenhum armário com configuração válida para atividade {atividade.id_atividade}")
            return False, None, None, None

        # 🔍 Log de quantidade total requerida
        logger.info(f"📏 Atividade {atividade.id_atividade} requer {quantidade} unidades do item {id_item}")

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao
            quantidade_restante = quantidade
            alocados = []
            armarios_utilizados = set()  # ← NOVO: Set para rastrear armários únicos

            logger.debug(f"⏱️ Tentativa de alocação entre {horario_inicio_tentativa.strftime('%H:%M')} e {horario_final_tentativa.strftime('%H:%M')}")

            for armario in armarios_ordenados:
                if quantidade_restante <= 0:
                    break

                if armario not in capacidades_map:
                    continue

                capacidade_por_nivel, tipo_unidade = capacidades_map[armario]

                # ✅ BUSCAR NÍVEIS COMPATÍVEIS (mesmo item ou vazios para item diferente)
                niveis_compativeis = []
                
                for nivel_index in range(armario.total_niveis_tela):
                    # Calcula quanto pode ser alocado neste nível
                    quantidade_nivel = min(quantidade_restante, capacidade_por_nivel)
                    
                    compativel, capacidade_disponivel = self._verificar_compatibilidade_nivel(
                        armario, nivel_index, id_item, quantidade_nivel, capacidade_por_nivel,
                        horario_inicio_tentativa, horario_final_tentativa
                    )
                    
                    if compativel and capacidade_disponivel >= quantidade_nivel:
                        niveis_compativeis.append((nivel_index, min(quantidade_nivel, capacidade_disponivel)))
                        logger.debug(f"🔍 {armario.nome}[{nivel_index}]: {min(quantidade_nivel, capacidade_disponivel)} {tipo_unidade} disponíveis")

                logger.debug(f"{armario.nome} - 📊 Capacidade: {capacidade_por_nivel} {tipo_unidade}/nível, Níveis compatíveis: {len(niveis_compativeis)}")

                # ✅ ALOCAR NOS NÍVEIS COMPATÍVEIS
                armario_foi_usado = False  # ← NOVO: Flag para rastrear se o armário foi usado
                
                for nivel_index, quantidade_disponivel in niveis_compativeis:
                    if quantidade_restante <= 0:
                        break
                    
                    unidades_alocar_nivel = min(quantidade_restante, quantidade_disponivel)
                    
                    # Ocupar o nível específico
                    sucesso = armario.adicionar_ocupacao_nivel(
                        nivel_index=nivel_index,
                        id_ordem=atividade.id_ordem,
                        id_pedido=atividade.id_pedido,
                        id_atividade=atividade.id_atividade,
                        id_item=id_item,
                        quantidade=unidades_alocar_nivel,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa
                    )
                    
                    if sucesso:
                        alocados.append((armario, nivel_index, unidades_alocar_nivel, tipo_unidade))
                        quantidade_restante -= unidades_alocar_nivel
                        armario_foi_usado = True  # ← NOVO: Marca que o armário foi usado
                        
                        logger.debug(f"✅ Alocado no {armario.nome}[{nivel_index}]: {unidades_alocar_nivel} {tipo_unidade} do item {id_item}")
                    else:
                        logger.warning(f"❌ {armario.nome}[{nivel_index}] falhou na ocupação real.")
                
                # ← NOVO: Adiciona o armário ao set apenas se foi usado
                if armario_foi_usado:
                    armarios_utilizados.add(armario)

            if quantidade_restante <= 0:
                atividade.equipamento_alocado = None
                # ← MODIFICAÇÃO: Retorna lista de armários únicos em vez de repetidos
                atividade.equipamentos_selecionados = list(armarios_utilizados)
                atividade.alocada = True

                log_ocupacoes = " | ".join(f"{a.nome}[{n}]: {qtd} {tipo}" for a, n, qtd, tipo in alocados)
                logger.info(
                    f"✅ Atividade {atividade.id_atividade} (item {id_item}) alocada com sucesso: {log_ocupacoes} | "
                    f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}"
                )
                # ← MODIFICAÇÃO: Retorna lista de armários únicos
                return True, list(armarios_utilizados), horario_inicio_tentativa, horario_final_tentativa

            logger.debug(f"🔁 Tentativa falhou. Restante: {quantidade_restante}. Retrocedendo 1 minuto.")
            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {atividade.id_atividade} (item {id_item}) não alocada. "
            f"Nenhum conjunto de armários disponível entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')} "
            f"para {quantidade} unidades."
        )
        return False, None, None, None

    # ==========================================================
    # 📊 Métodos de Consulta e Análise
    # ==========================================================
    def obter_ocupacao_por_item(self, armario: Armarios, id_item: int, inicio: datetime, fim: datetime) -> Dict[int, float]:
        """
        Retorna um dicionário com {nivel_index: quantidade_ocupada_maxima} para um item específico
        """
        ocupacao_por_nivel = {}
        
        for nivel_index in range(armario.total_niveis_tela):
            quantidade_maxima = self._calcular_quantidade_maxima_nivel_item(armario, nivel_index, id_item, inicio, fim)
            
            if quantidade_maxima > 0:
                ocupacao_por_nivel[nivel_index] = quantidade_maxima
        
        return ocupacao_por_nivel

    def calcular_capacidade_disponivel_item(self, armario: Armarios, id_item: int, atividade: "AtividadeModular", inicio: datetime, fim: datetime) -> Tuple[int, str]:
        """
        Calcula quantas unidades do item específico ainda podem ser alocadas no armário
        Retorna (capacidade_disponivel, tipo_unidade)
        """
        capacidade_por_nivel, tipo_unidade = self._obter_capacidade_por_nivel_tela(atividade, armario)
        if not capacidade_por_nivel:
            return 0, "desconhecido"
        
        capacidade_total_disponivel = 0
        
        for nivel_index in range(armario.total_niveis_tela):
            compativel, capacidade_disponivel = self._verificar_compatibilidade_nivel(
                armario, nivel_index, id_item, 0, capacidade_por_nivel, inicio, fim
            )
            
            if compativel:
                capacidade_total_disponivel += int(capacidade_disponivel)
        
        return capacidade_total_disponivel, tipo_unidade

    def obter_relatorio_ocupacao_detalhado(self, armario: Armarios, inicio: datetime, fim: datetime) -> Dict:
        """
        Retorna relatório detalhado da ocupação do armário por item
        """
        relatorio = {
            'armario': armario.nome,
            'periodo': f"{inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}",
            'total_niveis': armario.total_niveis_tela,
            'niveis_ocupados': 0,
            'itens': {}
        }
        
        for nivel_index in range(armario.total_niveis_tela):
            nivel_ocupado = False
            
            for (id_o, id_p, id_a, item_nivel, qtd, ini, f) in armario.niveis_ocupacoes[nivel_index]:
                if not (fim <= ini or inicio >= f):  # há sobreposição temporal
                    nivel_ocupado = True
                    
                    if item_nivel not in relatorio['itens']:
                        relatorio['itens'][item_nivel] = {
                            'total_unidades': 0,
                            'niveis_utilizados': set(),
                            'ocupacoes': []
                        }
                    
                    relatorio['itens'][item_nivel]['total_unidades'] += qtd
                    relatorio['itens'][item_nivel]['niveis_utilizados'].add(nivel_index)
                    relatorio['itens'][item_nivel]['ocupacoes'].append({
                        'nivel': nivel_index,
                        'quantidade': qtd,
                        'ordem': id_o,
                        'pedido': id_p,
                        'atividade': id_a,
                        'inicio': ini.strftime('%H:%M'),
                        'fim': f.strftime('%H:%M')
                    })
            
            if nivel_ocupado:
                relatorio['niveis_ocupados'] += 1
        
        # Converter sets em listas para serialização
        for item_info in relatorio['itens'].values():
            item_info['niveis_utilizados'] = list(item_info['niveis_utilizados'])
        
        relatorio['taxa_ocupacao'] = (relatorio['niveis_ocupados'] / relatorio['total_niveis'] * 100) if relatorio['total_niveis'] > 0 else 0
        
        return relatorio

    def verificar_conflitos_itens(self, inicio: datetime, fim: datetime) -> List[Dict]:
        """
        Verifica se há conflitos de itens diferentes no mesmo nível/período
        """
        conflitos = []
        
        for armario in self.armarios:
            for nivel_index in range(armario.total_niveis_tela):
                itens_no_nivel = {}
                
                for (id_o, id_p, id_a, item_nivel, qtd, ini, f) in armario.niveis_ocupacoes[nivel_index]:
                    if not (fim <= ini or inicio >= f):  # há sobreposição temporal
                        if item_nivel not in itens_no_nivel:
                            itens_no_nivel[item_nivel] = []
                        itens_no_nivel[item_nivel].append({
                            'ordem': id_o,
                            'pedido': id_p,
                            'atividade': id_a,
                            'quantidade': qtd,
                            'inicio': ini,
                            'fim': f
                        })
                
                # Se há mais de um tipo de item no mesmo nível
                if len(itens_no_nivel) > 1:
                    conflitos.append({
                        'armario': armario.nome,
                        'nivel': nivel_index,
                        'itens_conflitantes': itens_no_nivel
                    })
        
        return conflitos

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular") -> None:
        for armario in self.armarios:
            armario.liberar_por_atividade(id_ordem=atividade.id_ordem, id_pedido=atividade.id_pedido, id_atividade=atividade.id_atividade)

    def liberar_por_pedido(self, atividade: "AtividadeModular") -> None:
        for armario in self.armarios:
            armario.liberar_por_pedido(id_ordem=atividade.id_ordem, id_pedido=atividade.id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular") -> None:
        for armario in self.armarios:
            armario.liberar_por_ordem(atividade.id_ordem)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime) -> None:
        for armario in self.armarios:
            armario.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self) -> None:
        for armario in self.armarios:
            armario.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self) -> None:
        logger.info("==============================================")
        logger.info("📅 Agenda dos Armários para Fermentação")
        logger.info("==============================================")
        for armario in self.armarios:
            armario.mostrar_agenda()

    def mostrar_agenda_por_item(self, inicio: datetime, fim: datetime) -> None:
        """
        Mostra agenda organizada por item em todos os armários
        """
        logger.info("==============================================")
        logger.info(f"📅 Agenda por Item - {inicio.strftime('%H:%M')} a {fim.strftime('%H:%M')}")
        logger.info("==============================================")
        
        todos_itens = {}
        
        for armario in self.armarios:
            for nivel_index in range(armario.total_niveis_tela):
                for (id_o, id_p, id_a, item_nivel, qtd, ini, f) in armario.niveis_ocupacoes[nivel_index]:
                    if not (fim <= ini or inicio >= f):  # há sobreposição temporal
                        if item_nivel not in todos_itens:
                            todos_itens[item_nivel] = []
                        
                        todos_itens[item_nivel].append({
                            'armario': armario.nome,
                            'nivel': nivel_index,
                            'quantidade': qtd,
                            'ordem': id_o,
                            'pedido': id_p,
                            'atividade': id_a,
                            'inicio': ini.strftime('%H:%M'),
                            'fim': f.strftime('%H:%M')
                        })
        
        for item_id, ocupacoes in todos_itens.items():
            # Calcula pico máximo de ocupação para este item
            pico_maximo = 0.0
            for armario in self.armarios:
                for nivel_index in range(armario.total_niveis_tela):
                    pico_nivel = self._calcular_quantidade_maxima_nivel_item(armario, nivel_index, item_id, inicio, fim)
                    pico_maximo += pico_nivel
            
            logger.info(f"🏷️ Item {item_id} - Pico máximo: {pico_maximo} unidades")
            for ocupacao in ocupacoes:
                logger.info(f"   📍 {ocupacao['armario']}[{ocupacao['nivel']}]: {ocupacao['quantidade']} | "
                          f"Pedido {ocupacao['pedido']} | {ocupacao['inicio']}-{ocupacao['fim']}")

    def obter_estatisticas_globais(self, inicio: datetime, fim: datetime) -> Dict:
        """
        Retorna estatísticas globais de todos os armários
        """
        estatisticas = {
            'total_armarios': len(self.armarios),
            'total_niveis': 0,
            'niveis_ocupados': 0,
            'itens_diferentes': set(),
            'armarios': {}
        }
        
        for armario in self.armarios:
            relatorio_armario = self.obter_relatorio_ocupacao_detalhado(armario, inicio, fim)
            estatisticas['total_niveis'] += relatorio_armario['total_niveis']
            estatisticas['niveis_ocupados'] += relatorio_armario['niveis_ocupados']
            estatisticas['itens_diferentes'].update(relatorio_armario['itens'].keys())
            estatisticas['armarios'][armario.nome] = relatorio_armario
        
        estatisticas['itens_diferentes'] = list(estatisticas['itens_diferentes'])
        estatisticas['taxa_ocupacao_global'] = (estatisticas['niveis_ocupados'] / estatisticas['total_niveis'] * 100) if estatisticas['total_niveis'] > 0 else 0
        
        return estatisticas