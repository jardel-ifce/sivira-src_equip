#!/usr/bin/env python3
"""
Liberador de Equipamentos - Sistema de Produção
==============================================

Módulo responsável pela liberação de equipamentos alocados
para pedidos específicos, suportando diferentes tipos de
estruturas de ocupação.

✅ CARACTERÍSTICAS:
- Suporte a bancadas (fracoes_ocupacoes)
- Suporte a câmaras refrigeradas (niveis_ocupacoes + caixas_ocupacoes) 
- Suporte a armários (niveis_ocupacoes)
- Suporte a equipamentos padrão (ocupacoes)
- Suporte a fogões (ocupacoes_por_boca)
- Suporte a fornos (niveis_ocupacoes)
- Suporte a freezers (caixas_ocupacoes)
- Suporte a fritadeiras (ocupacoes_por_fracao)
- Suporte a hotmix, masseiras e modeladoras (ocupacoes)
- Liberação por ordem/pedido específico
- Relatório detalhado de liberações
- Tratamento de erros robusto
- Arquitetura expansível para novos tipos
"""

from typing import Tuple, List, Dict, Any
import traceback


class LiberadorEquipamentos:
    """Gerencia a liberação de equipamentos alocados para pedidos específicos"""
    
    def __init__(self, debug: bool = True):
        self.debug = debug
        # Registro de equipamentos processados para estatísticas
        self.equipamentos_processados = []
        
    def liberar_equipamentos_pedido(self, id_ordem: int, id_pedido: int) -> Tuple[int, List[str]]:
        """
        Libera equipamentos alocados para uma ordem/pedido específico.
        
        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido
            
        Returns:
            Tuple[int, List[str]]: (quantidade_liberada, detalhes_liberacao)
        """
        equipamentos_liberados = 0
        detalhes_liberacao = []
        self.equipamentos_processados = []  # Reset para nova operação
        
        try:
            if self.debug:
                detalhes_liberacao.append(f"Buscando ocupações da Ordem {id_ordem} | Pedido {id_pedido}...")
            
            from factory.fabrica_equipamentos import equipamentos_disponiveis
            
            for equipamento in equipamentos_disponiveis:
                try:
                    nome_equipamento = getattr(equipamento, 'nome', 'Equipamento desconhecido')
                    tipo_equipamento = self._identificar_tipo_equipamento(equipamento)
                    
                    # Processa cada tipo de equipamento
                    liberado, detalhes = self._processar_equipamento_por_tipo(
                        equipamento, nome_equipamento, tipo_equipamento, id_ordem, id_pedido
                    )
                    
                    # Registra processamento
                    self.equipamentos_processados.append({
                        'nome': nome_equipamento,
                        'tipo': tipo_equipamento,
                        'liberado': liberado
                    })
                    
                    if liberado:
                        equipamentos_liberados += 1
                        detalhes_liberacao.extend(detalhes)
                        
                except Exception as e:
                    if self.debug:
                        detalhes_liberacao.append(f"   Erro ao processar {nome_equipamento}: {e}")
                    continue
            
            # Mensagem final se nenhum equipamento foi liberado
            if equipamentos_liberados == 0:
                detalhes_liberacao.extend([
                    "   Nenhuma ocupação encontrada para este pedido",
                    "   Isso pode indicar que:",
                    "      • O pedido não foi executado ainda",
                    "      • Os equipamentos já foram liberados",
                    "      • O pedido foi executado mas não gerou ocupações"
                ])
            
            return equipamentos_liberados, detalhes_liberacao
            
        except ImportError as e:
            erro_msg = f"   Erro ao acessar fábrica de equipamentos: {e}"
            return 0, [erro_msg]
            
        except Exception as e:
            erro_msg = f"   Erro geral na liberação: {e}"
            detalhes_liberacao.append(erro_msg)
            if self.debug:
                detalhes_liberacao.append("   Traceback:")
                detalhes_liberacao.extend([f"   {line}" for line in traceback.format_exc().split('\n') if line.strip()])
            return 0, detalhes_liberacao
    
    def _identificar_tipo_equipamento(self, equipamento: Any) -> str:
        """Identifica o tipo de equipamento baseado em suas características"""
        
        # FOGÕES - têm ocupacoes_por_boca
        if hasattr(equipamento, 'ocupacoes_por_boca'):
            return 'fogao'
            
        # FRITADEIRAS - têm ocupacoes_por_fracao
        elif hasattr(equipamento, 'ocupacoes_por_fracao'):
            return 'fritadeira'
            
        # BANCADAS - têm fracoes_ocupacoes
        elif hasattr(equipamento, 'fracoes_ocupacoes'):
            return 'bancada'
            
        # CÂMARAS REFRIGERADAS - têm niveis_ocupacoes E caixas_ocupacoes
        elif hasattr(equipamento, 'niveis_ocupacoes') and hasattr(equipamento, 'caixas_ocupacoes'):
            return 'camara_refrigerada'
            
        # FREEZERS - têm caixas_ocupacoes mas não têm niveis_ocupacoes
        elif hasattr(equipamento, 'caixas_ocupacoes') and not hasattr(equipamento, 'niveis_ocupacoes'):
            return 'freezer'
            
        # FORNOS - têm niveis_ocupacoes mas não têm caixas_ocupacoes
        elif hasattr(equipamento, 'niveis_ocupacoes') and not hasattr(equipamento, 'caixas_ocupacoes'):
            return 'forno'
            
        # EQUIPAMENTOS PADRÃO - têm ocupacoes (HotMix, Masseira, ModeladoraDePaes, etc.)
        elif hasattr(equipamento, 'ocupacoes'):
            return 'equipamento_padrao'
            
        # TIPO DESCONHECIDO
        else:
            return 'desconhecido'
    
    def _processar_equipamento_por_tipo(self, equipamento: Any, nome: str, tipo: str, 
                                      id_ordem: int, id_pedido: int) -> Tuple[bool, List[str]]:
        """
        Processa um equipamento individual baseado em seu tipo.
        
        Args:
            equipamento: Instância do equipamento
            nome: Nome do equipamento
            tipo: Tipo identificado do equipamento
            id_ordem: ID da ordem
            id_pedido: ID do pedido
            
        Returns:
            Tuple[bool, List[str]]: (foi_liberado, detalhes)
        """
        
        if tipo == 'fogao':
            return self._processar_fogao(equipamento, nome, id_ordem, id_pedido)
            
        elif tipo == 'fritadeira':
            return self._processar_fritadeira(equipamento, nome, id_ordem, id_pedido)
            
        elif tipo == 'bancada':
            return self._processar_bancada(equipamento, nome, id_ordem, id_pedido)
            
        elif tipo == 'camara_refrigerada':
            return self._processar_camara_refrigerada(equipamento, nome, id_ordem, id_pedido)
            
        elif tipo == 'freezer':
            return self._processar_freezer(equipamento, nome, id_ordem, id_pedido)
            
        elif tipo == 'forno':
            return self._processar_forno(equipamento, nome, id_ordem, id_pedido)
            
        elif tipo == 'equipamento_padrao':
            return self._processar_equipamento_padrao(equipamento, nome, id_ordem, id_pedido)
            
        else:
            return False, [f"   {nome}: Tipo não reconhecido ({tipo})"]
    
    def _processar_fogao(self, equipamento: Any, nome: str, id_ordem: int, id_pedido: int) -> Tuple[bool, List[str]]:
        """Processa fogões com ocupacoes_por_boca"""
        
        if not hasattr(equipamento, 'liberar_por_pedido'):
            return False, [f"   {nome}: Método liberar_por_pedido não encontrado"]
        
        # Conta ocupações antes da liberação (soma de todas as bocas)
        ocupacoes_antes = sum(len(boca) for boca in equipamento.ocupacoes_por_boca)
        
        if ocupacoes_antes == 0:
            return False, []  # Sem ocupações, sem necessidade de liberar
        
        # Verifica se tem ocupações do pedido específico
        tem_ocupacoes_do_pedido = self._verificar_ocupacoes_fogao(equipamento, id_ordem, id_pedido)
        
        if not tem_ocupacoes_do_pedido:
            return False, []  # Sem ocupações deste pedido
        
        # Chama método de liberação do fogão
        equipamento.liberar_por_pedido(id_ordem, id_pedido)
        
        # Conta ocupações depois da liberação
        ocupacoes_depois = sum(len(boca) for boca in equipamento.ocupacoes_por_boca)
        
        if ocupacoes_antes > ocupacoes_depois:
            liberadas = ocupacoes_antes - ocupacoes_depois
            return True, [f"   {nome}: {liberadas} ocupação(ões) liberada(s) das bocas"]
        
        return False, [f"   {nome}: Nenhuma ocupação foi liberada"]
    
    def _processar_fritadeira(self, equipamento: Any, nome: str, id_ordem: int, id_pedido: int) -> Tuple[bool, List[str]]:
        """Processa fritadeiras com ocupacoes_por_fracao"""
        
        if not hasattr(equipamento, 'liberar_por_pedido'):
            return False, [f"   {nome}: Método liberar_por_pedido não encontrado"]
        
        # Conta ocupações antes da liberação (soma de todas as frações)
        ocupacoes_antes = sum(len(fracao) for fracao in equipamento.ocupacoes_por_fracao)
        
        if ocupacoes_antes == 0:
            return False, []  # Sem ocupações, sem necessidade de liberar
        
        # Verifica se tem ocupações do pedido específico
        tem_ocupacoes_do_pedido = self._verificar_ocupacoes_fritadeira(equipamento, id_ordem, id_pedido)
        
        if not tem_ocupacoes_do_pedido:
            return False, []  # Sem ocupações deste pedido
        
        # Chama método de liberação da fritadeira
        equipamento.liberar_por_pedido(id_ordem, id_pedido)
        
        # Conta ocupações depois da liberação
        ocupacoes_depois = sum(len(fracao) for fracao in equipamento.ocupacoes_por_fracao)
        
        if ocupacoes_antes > ocupacoes_depois:
            liberadas = ocupacoes_antes - ocupacoes_depois
            return True, [f"   {nome}: {liberadas} ocupação(ões) liberada(s) das frações"]
        
        return False, [f"   {nome}: Nenhuma ocupação foi liberada"]
    
    def _processar_freezer(self, equipamento: Any, nome: str, id_ordem: int, id_pedido: int) -> Tuple[bool, List[str]]:
        """Processa freezers com caixas_ocupacoes"""
        
        if not hasattr(equipamento, 'liberar_por_pedido'):
            return False, [f"   {nome}: Método liberar_por_pedido não encontrado"]
        
        # Conta ocupações antes da liberação
        ocupacoes_antes = sum(len(ocupacoes) for ocupacoes in equipamento.caixas_ocupacoes)
        
        if ocupacoes_antes == 0:
            return False, []  # Sem ocupações, sem necessidade de liberar
        
        # Verifica se tem ocupações do pedido específico
        tem_ocupacoes_do_pedido = self._verificar_ocupacoes_freezer(equipamento, id_ordem, id_pedido)
        
        if not tem_ocupacoes_do_pedido:
            return False, []  # Sem ocupações deste pedido
        
        # Chama método de liberação do freezer
        equipamento.liberar_por_pedido(id_ordem, id_pedido)
        
        # Conta ocupações depois da liberação
        ocupacoes_depois = sum(len(ocupacoes) for ocupacoes in equipamento.caixas_ocupacoes)
        
        if ocupacoes_antes > ocupacoes_depois:
            liberadas = ocupacoes_antes - ocupacoes_depois
            return True, [f"   {nome}: {liberadas} ocupação(ões) liberada(s) das caixas"]
        
        return False, [f"   {nome}: Nenhuma ocupação foi liberada"]
    
    def _processar_forno(self, equipamento: Any, nome: str, id_ordem: int, id_pedido: int) -> Tuple[bool, List[str]]:
        """Processa fornos com niveis_ocupacoes (sem caixas)"""
        
        if not hasattr(equipamento, 'liberar_por_pedido'):
            return False, [f"   {nome}: Método liberar_por_pedido não encontrado"]
        
        # Conta ocupações antes da liberação
        ocupacoes_antes = sum(len(ocupacoes) for ocupacoes in equipamento.niveis_ocupacoes)
        
        if ocupacoes_antes == 0:
            return False, []  # Sem ocupações, sem necessidade de liberar
        
        # Verifica se tem ocupações do pedido específico
        tem_ocupacoes_do_pedido = self._verificar_ocupacoes_forno(equipamento, id_ordem, id_pedido)
        
        if not tem_ocupacoes_do_pedido:
            return False, []  # Sem ocupações deste pedido
        
        # Chama método de liberação do forno
        equipamento.liberar_por_pedido(id_ordem, id_pedido)
        
        # Conta ocupações depois da liberação
        ocupacoes_depois = sum(len(ocupacoes) for ocupacoes in equipamento.niveis_ocupacoes)
        
        if ocupacoes_antes > ocupacoes_depois:
            liberadas = ocupacoes_antes - ocupacoes_depois
            return True, [f"   {nome}: {liberadas} ocupação(ões) liberada(s) dos níveis"]
        
        return False, [f"   {nome}: Nenhuma ocupação foi liberada"]
    
    def _processar_bancada(self, equipamento: Any, nome: str, id_ordem: int, id_pedido: int) -> Tuple[bool, List[str]]:
        """Processa bancadas com fracoes_ocupacoes"""
        
        if not hasattr(equipamento, 'liberar_por_pedido'):
            return False, [f"   {nome}: Método liberar_por_pedido não encontrado"]
        
        # Conta ocupações antes da liberação (soma de todas as frações)
        ocupacoes_antes = sum(len(fracoes) for fracoes in equipamento.fracoes_ocupacoes)
        
        if ocupacoes_antes == 0:
            return False, []  # Sem ocupações, sem necessidade de liberar
        
        # Verifica se tem ocupações do pedido específico
        tem_ocupacoes_do_pedido = self._verificar_ocupacoes_bancada(equipamento, id_ordem, id_pedido)
        
        if not tem_ocupacoes_do_pedido:
            return False, []  # Sem ocupações deste pedido
        
        # Chama método de liberação da bancada
        equipamento.liberar_por_pedido(id_ordem, id_pedido)
        
        # Conta ocupações depois da liberação
        ocupacoes_depois = sum(len(fracoes) for fracoes in equipamento.fracoes_ocupacoes)
        
        if ocupacoes_antes > ocupacoes_depois:
            liberadas = ocupacoes_antes - ocupacoes_depois
            return True, [f"   {nome}: {liberadas} ocupação(ões) liberada(s)"]
        
        return False, [f"   {nome}: Nenhuma ocupação foi liberada"]
    
    def _processar_camara_refrigerada(self, equipamento: Any, nome: str, id_ordem: int, id_pedido: int) -> Tuple[bool, List[str]]:
        """Processa câmaras refrigeradas com niveis_ocupacoes + caixas_ocupacoes"""
        
        if not hasattr(equipamento, 'liberar_por_pedido'):
            return False, [f"   {nome}: Método liberar_por_pedido não encontrado"]
        
        # Conta ocupações antes da liberação (níveis + caixas)
        ocupacoes_niveis_antes = sum(len(ocupacoes) for ocupacoes in equipamento.niveis_ocupacoes)
        ocupacoes_caixas_antes = sum(len(ocupacoes) for ocupacoes in equipamento.caixas_ocupacoes)
        ocupacoes_antes = ocupacoes_niveis_antes + ocupacoes_caixas_antes
        
        if ocupacoes_antes == 0:
            return False, []  # Sem ocupações, sem necessidade de liberar
        
        # Verifica se tem ocupações do pedido específico
        tem_ocupacoes_do_pedido = self._verificar_ocupacoes_camara(equipamento, id_ordem, id_pedido)
        
        if not tem_ocupacoes_do_pedido:
            return False, []  # Sem ocupações deste pedido
        
        # Chama método de liberação da câmara
        equipamento.liberar_por_pedido(id_ordem, id_pedido)
        
        # Conta ocupações depois da liberação
        ocupacoes_niveis_depois = sum(len(ocupacoes) for ocupacoes in equipamento.niveis_ocupacoes)
        ocupacoes_caixas_depois = sum(len(ocupacoes) for ocupacoes in equipamento.caixas_ocupacoes)
        ocupacoes_depois = ocupacoes_niveis_depois + ocupacoes_caixas_depois
        
        if ocupacoes_antes > ocupacoes_depois:
            liberadas = ocupacoes_antes - ocupacoes_depois
            return True, [f"   {nome}: {liberadas} ocupação(ões) liberada(s) (níveis+caixas)"]
        
        return False, [f"   {nome}: Nenhuma ocupação foi liberada"]
    
    def _processar_equipamento_padrao(self, equipamento: Any, nome: str, id_ordem: int, id_pedido: int) -> Tuple[bool, List[str]]:
        """Processa equipamentos padrão com ocupacoes (HotMix, Masseira, ModeladoraDePaes, etc.)"""
        
        if not hasattr(equipamento, 'liberar_por_pedido'):
            return False, [f"   {nome}: Método liberar_por_pedido não encontrado"]
        
        # Conta ocupações antes da liberação
        ocupacoes_antes = len(equipamento.ocupacoes)
        
        if ocupacoes_antes == 0:
            return False, []  # Sem ocupações, sem necessidade de liberar
        
        # Verifica se tem ocupações do pedido específico
        tem_ocupacoes_do_pedido = self._verificar_ocupacoes_padrao(equipamento, id_ordem, id_pedido)
        
        if not tem_ocupacoes_do_pedido:
            return False, []  # Sem ocupações deste pedido
        
        # Chama método de liberação do equipamento
        equipamento.liberar_por_pedido(id_ordem, id_pedido)
        
        # Conta ocupações depois da liberação
        ocupacoes_depois = len(equipamento.ocupacoes)
        
        if ocupacoes_antes > ocupacoes_depois:
            liberadas = ocupacoes_antes - ocupacoes_depois
            return True, [f"   {nome}: {liberadas} ocupação(ões) liberada(s)"]
        
        return False, [f"   {nome}: Nenhuma ocupação foi liberada"]
    
    # =========================================================================
    #                      MÉTODOS DE VERIFICAÇÃO DE OCUPAÇÕES
    # =========================================================================
    
    def _verificar_ocupacoes_fogao(self, equipamento: Any, id_ordem: int, id_pedido: int) -> bool:
        """Verifica se fogão tem ocupações do pedido específico"""
        for boca in equipamento.ocupacoes_por_boca:
            for ocupacao in boca:
                # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, tipo_chama, pressoes_chama, inicio, fim)
                if (len(ocupacao) >= 2 and 
                    ocupacao[0] == id_ordem and 
                    ocupacao[1] == id_pedido):
                    return True
        return False
    
    def _verificar_ocupacoes_fritadeira(self, equipamento: Any, id_ordem: int, id_pedido: int) -> bool:
        """Verifica se fritadeira tem ocupações do pedido específico"""
        for fracao in equipamento.ocupacoes_por_fracao:
            for ocupacao in fracao:
                # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade, temperatura, setup_minutos, inicio, fim)
                if (len(ocupacao) >= 2 and 
                    ocupacao[0] == id_ordem and 
                    ocupacao[1] == id_pedido):
                    return True
        return False
    
    def _verificar_ocupacoes_freezer(self, equipamento: Any, id_ordem: int, id_pedido: int) -> bool:
        """Verifica se freezer tem ocupações do pedido específico"""
        for ocupacoes_caixa in equipamento.caixas_ocupacoes:
            for ocupacao in ocupacoes_caixa:
                # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
                if (len(ocupacao) >= 2 and 
                    ocupacao[0] == id_ordem and 
                    ocupacao[1] == id_pedido):
                    return True
        return False
    
    def _verificar_ocupacoes_forno(self, equipamento: Any, id_ordem: int, id_pedido: int) -> bool:
        """Verifica se forno tem ocupações do pedido específico"""
        for ocupacoes_nivel in equipamento.niveis_ocupacoes:
            for ocupacao in ocupacoes_nivel:
                # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, inicio, fim)
                if (len(ocupacao) >= 2 and 
                    ocupacao[0] == id_ordem and 
                    ocupacao[1] == id_pedido):
                    return True
        return False
    
    def _verificar_ocupacoes_bancada(self, equipamento: Any, id_ordem: int, id_pedido: int) -> bool:
        """Verifica se bancada tem ocupações do pedido específico"""
        for fracoes in equipamento.fracoes_ocupacoes:
            for ocupacao in fracoes:
                # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, inicio, fim)
                if (len(ocupacao) >= 2 and 
                    ocupacao[0] == id_ordem and 
                    ocupacao[1] == id_pedido):
                    return True
        return False
    
    def _verificar_ocupacoes_camara(self, equipamento: Any, id_ordem: int, id_pedido: int) -> bool:
        """Verifica se câmara refrigerada tem ocupações do pedido específico"""
        # Verifica níveis
        for ocupacoes_nivel in equipamento.niveis_ocupacoes:
            for ocupacao in ocupacoes_nivel:
                # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, inicio, fim)
                if (len(ocupacao) >= 2 and 
                    ocupacao[0] == id_ordem and 
                    ocupacao[1] == id_pedido):
                    return True
        
        # Verifica caixas
        for ocupacoes_caixa in equipamento.caixas_ocupacoes:
            for ocupacao in ocupacoes_caixa:
                # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, inicio, fim)
                if (len(ocupacao) >= 2 and 
                    ocupacao[0] == id_ordem and 
                    ocupacao[1] == id_pedido):
                    return True
        
        return False
    
    def _verificar_ocupacoes_padrao(self, equipamento: Any, id_ordem: int, id_pedido: int) -> bool:
        """Verifica se equipamento padrão tem ocupações do pedido específico"""
        for ocupacao in equipamento.ocupacoes:
            # ocupacao pode variar em tamanho, mas sempre tem (id_ordem, id_pedido, ...) nos primeiros índices
            if (len(ocupacao) >= 2 and 
                ocupacao[0] == id_ordem and 
                ocupacao[1] == id_pedido):
                return True
        return False
    
    # =========================================================================
    #                           MÉTODOS DE ESTATÍSTICA
    # =========================================================================
    
    def obter_estatisticas_processamento(self) -> Dict[str, Any]:
        """Retorna estatísticas do último processamento realizado"""
        if not self.equipamentos_processados:
            return {}
        
        total_equipamentos = len(self.equipamentos_processados)
        equipamentos_liberados = sum(1 for eq in self.equipamentos_processados if eq['liberado'])
        
        # Agrupa por tipo
        tipos_count = {}
        tipos_liberados = {}
        
        for eq in self.equipamentos_processados:
            tipo = eq['tipo']
            if tipo not in tipos_count:
                tipos_count[tipo] = 0
                tipos_liberados[tipo] = 0
            
            tipos_count[tipo] += 1
            if eq['liberado']:
                tipos_liberados[tipo] += 1
        
        return {
            'total_equipamentos': total_equipamentos,
            'equipamentos_liberados': equipamentos_liberados,
            'tipos_processados': tipos_count,
            'tipos_liberados': tipos_liberados,
            'taxa_liberacao': (equipamentos_liberados / total_equipamentos * 100) if total_equipamentos > 0 else 0
        }
    
    def listar_equipamentos_por_tipo(self) -> Dict[str, List[str]]:
        """Lista equipamentos processados agrupados por tipo"""
        if not self.equipamentos_processados:
            return {}
        
        tipos = {}
        for eq in self.equipamentos_processados:
            tipo = eq['tipo']
            if tipo not in tipos:
                tipos[tipo] = []
            
            status = "LIBERADO" if eq['liberado'] else "SEM OCUPAÇÕES"
            tipos[tipo].append(f"{eq['nome']} ({status})")
        
        return tipos
    
    # =========================================================================
    #                         MÉTODOS PARA EXPANSÃO
    # =========================================================================
    
    def registrar_tipo_personalizado(self, nome_tipo: str, funcao_processamento):
        """
        Permite registrar novos tipos de equipamento dinamicamente.
        
        Args:
            nome_tipo: Nome do novo tipo
            funcao_processamento: Função que processa este tipo específico
                                Deve retornar Tuple[bool, List[str]]
        """
        # Placeholder para futura expansão
        # Seria implementado com um registry de tipos
        pass
    
    def validar_estrutura_equipamento(self, equipamento: Any) -> Dict[str, Any]:
        """
        Valida a estrutura de um equipamento e retorna informações diagnósticas.
        Útil para debugging de novos tipos de equipamento.
        """
        diagnostico = {
            'nome': getattr(equipamento, 'nome', 'Desconhecido'),
            'tipo_identificado': self._identificar_tipo_equipamento(equipamento),
            'atributos_encontrados': [],
            'metodos_liberacao': []
        }
        
        # Lista atributos relacionados a ocupações
        atributos_ocupacao = [
            'ocupacoes', 'fracoes_ocupacoes', 'niveis_ocupacoes', 
            'caixas_ocupacoes', 'ocupacoes_por_boca', 'ocupacoes_por_fracao',
            'intervalos_temperatura'
        ]
        
        for attr in atributos_ocupacao:
            if hasattr(equipamento, attr):
                valor = getattr(equipamento, attr)
                if isinstance(valor, list):
                    diagnostico['atributos_encontrados'].append(f"{attr}: lista com {len(valor)} elementos")
                else:
                    diagnostico['atributos_encontrados'].append(f"{attr}: {type(valor).__name__}")
        
        # Lista métodos de liberação
        metodos_liberacao = [
            'liberar_por_pedido', 'liberar_por_ordem', 'liberar_por_atividade', 
            'liberar_todas_ocupacoes'
        ]
        
        for metodo in metodos_liberacao:
            if hasattr(equipamento, metodo) and callable(getattr(equipamento, metodo)):
                diagnostico['metodos_liberacao'].append(metodo)
        
        return diagnostico