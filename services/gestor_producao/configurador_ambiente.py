"""
Configurador de Ambiente - IMPLEMENTADO
=======================================

Inicializa o ambiente de produção conectando com o sistema real.
"""

import os
from typing import Optional


class ConfiguradorAmbiente:
    """
    Configurador de ambiente do sistema de produção.
    
    Responsabilidades:
    - Inicialização do almoxarifado
    - Limpeza de logs e comandas
    - Setup de funcionários
    """
    
    def __init__(self):
        """Inicializa configurador"""
        self.almoxarifado = None
        self.gestor_almoxarifado = None
        self.inicializado = False
        print("📋 ConfiguradorAmbiente criado")
    
    def inicializar_ambiente(self) -> bool:
        """
        Inicializa ambiente de produção REAL.
        
        Returns:
            bool: True se sucesso
        """
        try:
            print("🔧 Inicializando ambiente de produção...")
            
            # ✅ IMPORTA SISTEMA REAL
            print("   📦 Importando módulos do sistema...")
            from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
            from models.almoxarifado.almoxarifado import Almoxarifado
            from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
            from utils.comandas.limpador_comandas import apagar_todas_as_comandas
            from utils.logs.gerenciador_logs import limpar_todos_os_logs
            
            # ✅ LIMPEZA INICIAL
            print("   🧹 Limpando dados anteriores...")
            try:
                apagar_todas_as_comandas()
                print("     ✅ Comandas limpas")
            except Exception as e:
                print(f"     ⚠️ Aviso na limpeza de comandas: {e}")
            
            try:
                limpar_todos_os_logs()
                print("     ✅ Logs limpos")
            except Exception as e:
                print(f"     ⚠️ Aviso na limpeza de logs: {e}")
            
            # ✅ CARREGAMENTO DO ALMOXARIFADO
            print("   📦 Carregando itens do almoxarifado...")
            caminho_itens = "data/almoxarifado/itens_almoxarifado.json"
            
            if not os.path.exists(caminho_itens):
                print(f"     ❌ Arquivo não encontrado: {caminho_itens}")
                return False
            
            itens = carregar_itens_almoxarifado(caminho_itens)
            print(f"     ✅ {len(itens)} itens carregados")
            
            # ✅ INICIALIZAÇÃO DO ALMOXARIFADO
            print("   🏪 Inicializando almoxarifado...")
            self.almoxarifado = Almoxarifado()
            
            for item in itens:
                self.almoxarifado.adicionar_item(item)
            
            print(f"     ✅ Almoxarifado criado com {len(itens)} itens")
            
            # ✅ CRIAÇÃO DO GESTOR
            print("   👨‍💼 Criando gestor do almoxarifado...")
            self.gestor_almoxarifado = GestorAlmoxarifado(self.almoxarifado)
            print("     ✅ Gestor criado")
            
            # ✅ FINALIZAÇÃO
            self.inicializado = True
            print("✅ Ambiente inicializado com sucesso!")
            print(f"   📊 Status: {len(itens)} itens no almoxarifado")
            print(f"   🏪 Gestor: Operacional")
            print(f"   🧹 Logs: Limpos")
            
            return True
            
        except ImportError as e:
            print(f"❌ Erro de importação: {e}")
            print("💡 Verifique se está executando do diretório correto")
            return False
            
        except FileNotFoundError as e:
            print(f"❌ Arquivo não encontrado: {e}")
            print("💡 Verifique se os arquivos de dados existem")
            return False
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def limpar_ambiente(self) -> bool:
        """
        Limpa logs e comandas.
        
        Returns:
            bool: True se sucesso
        """
        try:
            print("🧹 Limpando ambiente...")
            
            from utils.comandas.limpador_comandas import apagar_todas_as_comandas
            from utils.logs.gerenciador_logs import limpar_todos_os_logs
            
            apagar_todas_as_comandas()
            limpar_todos_os_logs()
            
            print("✅ Ambiente limpo com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro na limpeza: {e}")
            return False
    
    def obter_status(self) -> dict:
        """
        Retorna status do ambiente.
        
        Returns:
            dict: Status detalhado
        """
        total_itens = 0
        if self.almoxarifado:
            try:
                # Tenta diferentes atributos possíveis
                if hasattr(self.almoxarifado, 'inventario'):
                    total_itens = len(self.almoxarifado.inventario)
                elif hasattr(self.almoxarifado, 'itens'):
                    total_itens = len(self.almoxarifado.itens)
                elif hasattr(self.almoxarifado, '_itens'):
                    total_itens = len(self.almoxarifado._itens)
                else:
                    # Método mais seguro - usa o gestor
                    if self.gestor_almoxarifado:
                        total_itens = "via_gestor"
                    else:
                        total_itens = "desconhecido"
            except Exception:
                total_itens = "erro"
        
        return {
            "inicializado": self.inicializado,
            "tem_almoxarifado": self.almoxarifado is not None,
            "tem_gestor": self.gestor_almoxarifado is not None,
            "total_itens": total_itens
        }
    
    def reinicializar(self) -> bool:
        """
        Reinicializa o ambiente completamente.
        
        Returns:
            bool: True se sucesso
        """
        print("🔄 Reinicializando ambiente...")
        
        # Limpa estado atual
        self.almoxarifado = None
        self.gestor_almoxarifado = None
        self.inicializado = False
        
        # Inicializa novamente
        return self.inicializar_ambiente()