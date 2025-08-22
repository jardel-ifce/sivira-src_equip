"""
Integrador de Equipamentos
==========================

Módulo para integração com o sistema de equipamentos real,
permitindo acesso aos métodos mostrar_agenda() dos gestores
e equipamentos individuais do AtividadeModular.
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime

class IntegradorEquipamentos:
    """Integra com o sistema real de equipamentos para visualização de agendas"""
    
    def __init__(self):
        self._gestores_cache = {}
        self._equipamentos_cache = {}
        self._fabrica_carregada = False
        
    def _carregar_fabrica_equipamentos(self) -> bool:
        """Carrega a fábrica de equipamentos do sistema"""
        try:
            if self._fabrica_carregada:
                return True
                
            # Adiciona o diretório raiz ao path se necessário
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if root_dir not in sys.path:
                sys.path.append(root_dir)
            
            # Importa factory e enums necessários
            from factory import fabrica_equipamentos
            from enums.equipamentos.tipo_equipamento import TipoEquipamento
            from services.mapas.mapa_gestor_equipamento import MAPA_GESTOR
            
            self.fabrica_equipamentos = fabrica_equipamentos
            self.TipoEquipamento = TipoEquipamento
            self.MAPA_GESTOR = MAPA_GESTOR
            
            self._fabrica_carregada = True
            return True
            
        except ImportError as e:
            print(f"Erro ao carregar factory de equipamentos: {e}")
            return False
        except Exception as e:
            print(f"Erro inesperado ao carregar equipamentos: {e}")
            return False
    
    def listar_equipamentos_disponiveis(self) -> Dict[str, List[str]]:
        """
        Lista todos os equipamentos disponíveis organizados por tipo.
        
        Returns:
            Dict[str, List[str]]: Mapeamento tipo -> lista de equipamentos
        """
        if not self._carregar_fabrica_equipamentos():
            return {}
        
        try:
            equipamentos_por_tipo = {}
            
            # Itera sobre todos os atributos da fábrica
            for nome_attr in dir(self.fabrica_equipamentos):
                if not nome_attr.startswith('_'):
                    try:
                        equipamento = getattr(self.fabrica_equipamentos, nome_attr)
                        
                        # Verifica se tem atributo tipo_equipamento
                        if hasattr(equipamento, 'tipo_equipamento'):
                            tipo = equipamento.tipo_equipamento.name
                            nome = getattr(equipamento, 'nome', nome_attr)
                            
                            if tipo not in equipamentos_por_tipo:
                                equipamentos_por_tipo[tipo] = []
                            
                            equipamentos_por_tipo[tipo].append(nome)
                    
                    except Exception:
                        continue  # Ignora atributos que não são equipamentos
            
            return equipamentos_por_tipo
            
        except Exception as e:
            print(f"Erro ao listar equipamentos: {e}")
            return {}
    
    def obter_agenda_equipamento_especifico(self, nome_equipamento: str) -> Optional[str]:
        """
        Obtém a agenda de um equipamento específico.
        
        Args:
            nome_equipamento: Nome do equipamento
            
        Returns:
            str: Saída do método mostrar_agenda() ou None se não encontrado
        """
        if not self._carregar_fabrica_equipamentos():
            return None
        
        try:
            # Procura o equipamento na fábrica
            equipamento = None
            for nome_attr in dir(self.fabrica_equipamentos):
                if not nome_attr.startswith('_'):
                    try:
                        eq = getattr(self.fabrica_equipamentos, nome_attr)
                        if hasattr(eq, 'nome') and eq.nome == nome_equipamento:
                            equipamento = eq
                            break
                        elif nome_attr == nome_equipamento:
                            equipamento = eq
                            break
                    except Exception:
                        continue
            
            if not equipamento:
                return None
            
            # Tenta chamar mostrar_agenda()
            if hasattr(equipamento, 'mostrar_agenda'):
                # Captura saída do método
                import io
                import contextlib
                
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    equipamento.mostrar_agenda()
                
                return output.getvalue()
            else:
                return f"Equipamento {nome_equipamento} não possui método mostrar_agenda()"
                
        except Exception as e:
            return f"Erro ao obter agenda do equipamento {nome_equipamento}: {e}"
    
    def obter_agenda_gestor_tipo(self, tipo_equipamento: str) -> Optional[str]:
        """
        Obtém a agenda de um gestor de tipo específico.
        
        Args:
            tipo_equipamento: Nome do tipo de equipamento
            
        Returns:
            str: Saída do método mostrar_agenda() do gestor ou None se erro
        """
        if not self._carregar_fabrica_equipamentos():
            return None
        
        try:
            # Converte string para enum
            try:
                tipo_enum = self.TipoEquipamento[tipo_equipamento]
            except KeyError:
                return f"Tipo de equipamento '{tipo_equipamento}' não encontrado"
            
            # Obtém classe do gestor
            classe_gestor = self.MAPA_GESTOR.get(tipo_enum)
            if not classe_gestor:
                return f"Gestor não encontrado para tipo '{tipo_equipamento}'"
            
            # Coleta equipamentos do tipo
            equipamentos_do_tipo = []
            for nome_attr in dir(self.fabrica_equipamentos):
                if not nome_attr.startswith('_'):
                    try:
                        eq = getattr(self.fabrica_equipamentos, nome_attr)
                        if hasattr(eq, 'tipo_equipamento') and eq.tipo_equipamento == tipo_enum:
                            equipamentos_do_tipo.append(eq)
                    except Exception:
                        continue
            
            if not equipamentos_do_tipo:
                return f"Nenhum equipamento encontrado do tipo '{tipo_equipamento}'"
            
            # Cria instância do gestor
            gestor = classe_gestor(equipamentos_do_tipo)
            
            # Tenta chamar mostrar_agenda()
            if hasattr(gestor, 'mostrar_agenda'):
                import io
                import contextlib
                
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    gestor.mostrar_agenda()
                
                return output.getvalue()
            else:
                return f"Gestor do tipo '{tipo_equipamento}' não possui método mostrar_agenda()"
                
        except Exception as e:
            return f"Erro ao obter agenda do gestor {tipo_equipamento}: {e}"
    
    def obter_estatisticas_equipamentos(self) -> Dict[str, Any]:
        """
        Obtém estatísticas dos equipamentos disponíveis.
        
        Returns:
            Dict com estatísticas dos equipamentos
        """
        if not self._carregar_fabrica_equipamentos():
            return {"erro": "Não foi possível carregar fábrica de equipamentos"}
        
        try:
            equipamentos_por_tipo = self.listar_equipamentos_disponiveis()
            
            total_equipamentos = sum(len(equipamentos) for equipamentos in equipamentos_por_tipo.values())
            total_tipos = len(equipamentos_por_tipo)
            
            # Calcula estatísticas por tipo
            stats_por_tipo = {}
            for tipo, equipamentos in equipamentos_por_tipo.items():
                stats_por_tipo[tipo] = {
                    "quantidade": len(equipamentos),
                    "porcentagem": (len(equipamentos) / total_equipamentos * 100) if total_equipamentos > 0 else 0
                }
            
            return {
                "total_equipamentos": total_equipamentos,
                "total_tipos": total_tipos,
                "equipamentos_por_tipo": equipamentos_por_tipo,
                "estatisticas_por_tipo": stats_por_tipo,
                "tipos_disponiveis": list(equipamentos_por_tipo.keys())
            }
            
        except Exception as e:
            return {"erro": f"Erro ao calcular estatísticas: {e}"}
    
    def verificar_disponibilidade_equipamento(self, nome_equipamento: str) -> Dict[str, Any]:
        """
        Verifica disponibilidade de um equipamento específico.
        
        Args:
            nome_equipamento: Nome do equipamento
            
        Returns:
            Dict com informações de disponibilidade
        """
        if not self._carregar_fabrica_equipamentos():
            return {"erro": "Não foi possível carregar fábrica de equipamentos"}
        
        try:
            # Procura o equipamento
            equipamento = None
            for nome_attr in dir(self.fabrica_equipamentos):
                if not nome_attr.startswith('_'):
                    try:
                        eq = getattr(self.fabrica_equipamentos, nome_attr)
                        if hasattr(eq, 'nome') and eq.nome == nome_equipamento:
                            equipamento = eq
                            break
                    except Exception:
                        continue
            
            if not equipamento:
                return {"erro": f"Equipamento '{nome_equipamento}' não encontrado"}
            
            # Coleta informações básicas
            info = {
                "nome": getattr(equipamento, 'nome', 'N/A'),
                "tipo": getattr(equipamento, 'tipo_equipamento', 'N/A').name if hasattr(equipamento, 'tipo_equipamento') else 'N/A',
                "encontrado": True,
                "tem_agenda": hasattr(equipamento, 'mostrar_agenda'),
                "metodos_disponiveis": []
            }
            
            # Lista métodos públicos disponíveis
            for attr in dir(equipamento):
                if not attr.startswith('_') and callable(getattr(equipamento, attr)):
                    info["metodos_disponiveis"].append(attr)
            
            return info
            
        except Exception as e:
            return {"erro": f"Erro ao verificar equipamento: {e}"}
    
    def listar_tipos_equipamento(self) -> List[str]:
        """
        Lista todos os tipos de equipamento disponíveis.
        
        Returns:
            List[str]: Lista de nomes dos tipos
        """
        if not self._carregar_fabrica_equipamentos():
            return []
        
        try:
            return [tipo.name for tipo in self.TipoEquipamento]
        except Exception:
            return []
    
    def sistema_disponivel(self) -> bool:
        """
        Verifica se o sistema de equipamentos está disponível.
        
        Returns:
            bool: True se sistema carregado com sucesso
        """
        return self._carregar_fabrica_equipamentos()
    
    def obter_info_sistema(self) -> Dict[str, Any]:
        """
        Obtém informações sobre o sistema de equipamentos.
        
        Returns:
            Dict com informações do sistema
        """
        info = {
            "sistema_disponivel": self.sistema_disponivel(),
            "fabrica_carregada": self._fabrica_carregada,
            "timestamp": datetime.now().isoformat()
        }
        
        if self.sistema_disponivel():
            stats = self.obter_estatisticas_equipamentos()
            if "erro" not in stats:
                info.update({
                    "total_equipamentos": stats["total_equipamentos"],
                    "total_tipos": stats["total_tipos"],
                    "tipos_disponiveis": stats["tipos_disponiveis"]
                })
        
        return info
