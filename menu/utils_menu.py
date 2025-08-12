"""
Utilitários do Menu
==================

Funções auxiliares para interface do usuário e validações.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple


class MenuUtils:
    """Utilitários para interface do menu"""
    
    def __init__(self):
        pass
    
    def limpar_tela(self):
        """Limpa a tela do terminal"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def coletar_dados_pedido(self) -> Optional[Dict]:
        """
        Coleta dados de um pedido do usuário via interface interativa.
        
        Returns:
            Dict com dados do pedido ou None se cancelado
        """
        try:
            # 1. Coleta ID do item
            id_item = self._coletar_id_item()
            if id_item is None:
                return None
            
            # 2. Coleta tipo do item
            tipo_item = self._coletar_tipo_item()
            if tipo_item is None:
                return None
            
            # 3. Valida se item existe
            if not self._validar_item_existe(id_item, tipo_item):
                return None
            
            # 4. Coleta quantidade
            quantidade = self._coletar_quantidade()
            if quantidade is None:
                return None
            
            # 5. Coleta fim da jornada
            fim_jornada = self._coletar_fim_jornada()
            if fim_jornada is None:
                return None
            
            return {
                'id_item': id_item,
                'tipo_item': tipo_item,
                'quantidade': quantidade,
                'fim_jornada': fim_jornada
            }
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Registro cancelado pelo usuário.")
            return None
        except Exception as e:
            print(f"\n❌ Erro ao coletar dados: {e}")
            return None
    
    def _coletar_id_item(self) -> Optional[int]:
        """Coleta ID do item do usuário"""
        while True:
            try:
                entrada = input("📦 Digite o ID do item (ex: 1001): ").strip()
                
                if not entrada:
                    print("⏹️ Operação cancelada.")
                    return None
                
                id_item = int(entrada)
                
                if id_item <= 0:
                    print("❌ ID deve ser um número positivo!")
                    continue
                
                return id_item
                
            except ValueError:
                print("❌ Digite um número válido!")
            except KeyboardInterrupt:
                return None
    
    def _coletar_tipo_item(self) -> Optional[str]:
        """Coleta tipo do item do usuário"""
        print("\n📝 Tipo do item:")
        print("1 - PRODUTO")
        print("2 - SUBPRODUTO")
        
        while True:
            try:
                entrada = input("🎯 Escolha (1/2): ").strip()
                
                if not entrada:
                    print("⏹️ Operação cancelada.")
                    return None
                
                if entrada == "1":
                    return "PRODUTO"
                elif entrada == "2":
                    return "SUBPRODUTO"
                else:
                    print("❌ Digite 1 para PRODUTO ou 2 para SUBPRODUTO!")
                    
            except KeyboardInterrupt:
                return None
    
    def _validar_item_existe(self, id_item: int, tipo_item: str) -> bool:
        """Valida se o item existe nos arquivos"""
        from menu.gerenciador_pedidos import GerenciadorPedidos
        
        gerenciador = GerenciadorPedidos()
        existe, resultado = gerenciador.validar_item_existe(id_item, tipo_item)
        
        if existe:
            print(f"✅ Item encontrado: {resultado}")
            return True
        else:
            print(f"❌ {resultado}")
            
            # Mostra itens disponíveis
            print(f"\n💡 Itens disponíveis em {tipo_item}S:")
            itens = gerenciador.listar_itens_disponiveis(tipo_item)
            
            if itens:
                for id_disponivel, nome in itens[:10]:  # Mostra até 10
                    print(f"   {id_disponivel} - {nome}")
                if len(itens) > 10:
                    print(f"   ... e mais {len(itens) - 10} itens")
            else:
                print("   (Nenhum item encontrado)")
            
            return False
    
    def _coletar_quantidade(self) -> Optional[int]:
        """Coleta quantidade do usuário"""
        while True:
            try:
                entrada = input("\n📊 Digite a quantidade: ").strip()
                
                if not entrada:
                    print("⏹️ Operação cancelada.")
                    return None
                
                quantidade = int(entrada)
                
                if quantidade <= 0:
                    print("❌ Quantidade deve ser maior que zero!")
                    continue
                
                if quantidade > 10000:
                    print("⚠️ Quantidade muito alta! Tem certeza?")
                    confirmacao = input("   Digite 's' para confirmar: ").strip().lower()
                    if confirmacao not in ['s', 'sim']:
                        continue
                
                return quantidade
                
            except ValueError:
                print("❌ Digite um número válido!")
            except KeyboardInterrupt:
                return None
    
    def _coletar_fim_jornada(self) -> Optional[datetime]:
        """Coleta fim da jornada do usuário com sugestão automática"""
        print("\n⏰ Fim da jornada:")
        
        # Calcula sugestão (5 dias no futuro às 07:00)
        agora = datetime.now()
        sugestao = agora + timedelta(days=5)
        sugestao = sugestao.replace(hour=7, minute=0, second=0, microsecond=0)
        
        # Mostra sugestão
        print(f"💡 Sugestão: {sugestao.strftime('%H:%M:%S %d/%m/%Y')} (5 dias no futuro às 07:00)")
        print("   Pressione ENTER para aceitar ou digite sua própria data")
        print("   Formato personalizado: HH:MM:SS DD/MM/AAAA")
        print("   Exemplo: 15:30:00 20/08/2025")
        
        while True:
            try:
                entrada = input("🎯 Fim da jornada [ENTER=sugestão]: ").strip()
                
                # Se entrada vazia, usa sugestão
                if not entrada:
                    fim_jornada = sugestao
                    print(f"✅ Usando sugestão: {fim_jornada.strftime('%H:%M:%S %d/%m/%Y')}")
                else:
                    # Tenta parsear a data customizada
                    fim_jornada = self._parsear_data_hora(entrada)
                    
                    if fim_jornada is None:
                        print("❌ Formato inválido! Use: HH:MM:SS DD/MM/AAAA")
                        print(f"💡 Ou pressione ENTER para usar: {sugestao.strftime('%H:%M:%S %d/%m/%Y')}")
                        continue
                    
                    # Valida se data não é no passado
                    if fim_jornada <= agora:
                        print("❌ Data deve ser no futuro!")
                        print(f"💡 Ou pressione ENTER para usar: {sugestao.strftime('%H:%M:%S %d/%m/%Y')}")
                        continue
                
                # Calcula e mostra início da jornada
                inicio_jornada = fim_jornada - timedelta(days=3)
                print(f"📅 Início da jornada (3 dias antes): {inicio_jornada.strftime('%H:%M:%S %d/%m/%Y')}")
                
                # Confirma se está ok
                confirmacao = input("✅ Confirma essas datas? (ENTER=sim, n=não): ").strip().lower()
                if confirmacao in ['n', 'no', 'nao', 'não']:
                    print("🔄 Vamos tentar novamente...")
                    continue
                
                return fim_jornada
                
            except KeyboardInterrupt:
                print("\n⏹️ Operação cancelada.")
                return None
    
    def _parsear_data_hora(self, entrada: str) -> Optional[datetime]:
        """
        Parseia string de data/hora em formato brasileiro SEM REGEX.
        
        Args:
            entrada: String no formato "HH:MM:SS DD/MM/AAAA" ou variações
            
        Returns:
            datetime ou None se inválido
        """
        try:
            entrada = entrada.strip()
            if not entrada:
                return None
            
            # Tenta diferentes formatos manualmente
            
            # Formato 1: HH:MM:SS DD/MM/AAAA
            if self._tem_formato_hora_data(entrada):
                return self._parsear_hora_data(entrada)
            
            # Formato 2: DD/MM/AAAA HH:MM:SS
            if self._tem_formato_data_hora(entrada):
                return self._parsear_data_hora_formato(entrada)
            
            # Formato 3: Só data DD/MM/AAAA
            if self._tem_formato_so_data(entrada):
                return self._parsear_so_data(entrada)
            
            return None
            
        except (ValueError, TypeError):
            return None
    
    def _tem_formato_hora_data(self, entrada: str) -> bool:
        """Verifica se tem formato HH:MM(:SS) DD/MM/AAAA"""
        partes = entrada.split()
        if len(partes) != 2:
            return False
        
        hora_parte = partes[0]
        data_parte = partes[1]
        
        # Verifica hora (HH:MM ou HH:MM:SS)
        if ':' not in hora_parte:
            return False
        if '/' not in data_parte:
            return False
        
        return True
    
    def _tem_formato_data_hora(self, entrada: str) -> bool:
        """Verifica se tem formato DD/MM/AAAA HH:MM(:SS)"""
        partes = entrada.split()
        if len(partes) != 2:
            return False
        
        data_parte = partes[0]
        hora_parte = partes[1]
        
        # Verifica data primeiro
        if '/' not in data_parte:
            return False
        if ':' not in hora_parte:
            return False
        
        return True
    
    def _tem_formato_so_data(self, entrada: str) -> bool:
        """Verifica se tem só data DD/MM/AAAA"""
        if ' ' in entrada:
            return False
        if '/' not in entrada:
            return False
        
        partes = entrada.split('/')
        return len(partes) == 3
    
    def _parsear_hora_data(self, entrada: str) -> Optional[datetime]:
        """Parseia formato HH:MM(:SS) DD/MM/AAAA"""
        try:
            partes = entrada.split()
            hora_str = partes[0]
            data_str = partes[1]
            
            # Parseia hora
            hora_partes = hora_str.split(':')
            if len(hora_partes) == 2:
                hora, minuto, segundo = int(hora_partes[0]), int(hora_partes[1]), 0
            elif len(hora_partes) == 3:
                hora, minuto, segundo = int(hora_partes[0]), int(hora_partes[1]), int(hora_partes[2])
            else:
                return None
            
            # Parseia data
            data_partes = data_str.split('/')
            if len(data_partes) != 3:
                return None
            
            dia, mes, ano = int(data_partes[0]), int(data_partes[1]), int(data_partes[2])
            
            # Valida
            if not self._validar_componentes_data_hora(hora, minuto, segundo, dia, mes, ano):
                return None
            
            return datetime(ano, mes, dia, hora, minuto, segundo)
            
        except (ValueError, IndexError):
            return None
    
    def _parsear_data_hora_formato(self, entrada: str) -> Optional[datetime]:
        """Parseia formato DD/MM/AAAA HH:MM(:SS)"""
        try:
            partes = entrada.split()
            data_str = partes[0]
            hora_str = partes[1]
            
            # Parseia data
            data_partes = data_str.split('/')
            if len(data_partes) != 3:
                return None
            
            dia, mes, ano = int(data_partes[0]), int(data_partes[1]), int(data_partes[2])
            
            # Parseia hora
            hora_partes = hora_str.split(':')
            if len(hora_partes) == 2:
                hora, minuto, segundo = int(hora_partes[0]), int(hora_partes[1]), 0
            elif len(hora_partes) == 3:
                hora, minuto, segundo = int(hora_partes[0]), int(hora_partes[1]), int(hora_partes[2])
            else:
                return None
            
            # Valida
            if not self._validar_componentes_data_hora(hora, minuto, segundo, dia, mes, ano):
                return None
            
            return datetime(ano, mes, dia, hora, minuto, segundo)
            
        except (ValueError, IndexError):
            return None
    
    def _parsear_so_data(self, entrada: str) -> Optional[datetime]:
        """Parseia formato DD/MM/AAAA (assume 07:00:00)"""
        try:
            data_partes = entrada.split('/')
            if len(data_partes) != 3:
                return None
            
            dia, mes, ano = int(data_partes[0]), int(data_partes[1]), int(data_partes[2])
            hora, minuto, segundo = 7, 0, 0  # 07:00:00 padrão
            
            # Valida
            if not self._validar_componentes_data_hora(hora, minuto, segundo, dia, mes, ano):
                return None
            
            return datetime(ano, mes, dia, hora, minuto, segundo)
            
        except (ValueError, IndexError):
            return None
    
    def _validar_componentes_data_hora(self, hora: int, minuto: int, segundo: int, 
                                     dia: int, mes: int, ano: int) -> bool:
        """Valida componentes individuais de data/hora"""
        if not (0 <= hora <= 23):
            return False
        if not (0 <= minuto <= 59):
            return False
        if not (0 <= segundo <= 59):
            return False
        if not (1 <= dia <= 31):
            return False
        if not (1 <= mes <= 12):
            return False
        if not (2025 <= ano <= 2030):
            return False
        
        return True
    
    def formatar_duracao(self, duracao: timedelta) -> str:
        """Formata duração para exibição amigável"""
        dias = duracao.days
        horas, resto = divmod(duracao.seconds, 3600)
        minutos, segundos = divmod(resto, 60)
        
        partes = []
        if dias > 0:
            partes.append(f"{dias}d")
        if horas > 0:
            partes.append(f"{horas}h")
        if minutos > 0:
            partes.append(f"{minutos}min")
        if segundos > 0 and not partes:  # Só mostra segundos se for muito curto
            partes.append(f"{segundos}s")
        
        return " ".join(partes) if partes else "0min"
    
    def confirmar_acao(self, mensagem: str, padrao_confirmacao: str = "s") -> bool:
        """
        Solicita confirmação do usuário.
        
        Args:
            mensagem: Mensagem para exibir
            padrao_confirmacao: String que confirma (padrão: 's')
            
        Returns:
            True se confirmado, False caso contrário
        """
        try:
            resposta = input(f"{mensagem} (s/N): ").strip().lower()
            return resposta in ['s', 'sim', 'y', 'yes'] if padrao_confirmacao == 's' else resposta == padrao_confirmacao
        except KeyboardInterrupt:
            return False
    
    def pausar(self, mensagem: str = "Pressione Enter para continuar..."):
        """Pausa execução esperando input do usuário"""
        try:
            input(f"\n{mensagem}")
        except KeyboardInterrupt:
            pass
    
    def mostrar_progresso(self, atual: int, total: int, prefixo: str = "Progresso"):
        """Mostra barra de progresso simples"""
        porcentagem = (atual / total) * 100 if total > 0 else 0
        barra_completa = int(porcentagem / 5)  # 20 caracteres max
        barra = "█" * barra_completa + "░" * (20 - barra_completa)
        
        print(f"\r{prefixo}: [{barra}] {porcentagem:.1f}% ({atual}/{total})", end="", flush=True)
        
        if atual == total:
            print()  # Nova linha no final
    
    def formatar_data_hora(self, dt: datetime, formato: str = "completo") -> str:
        """
        Formata datetime para exibição.
        
        Args:
            dt: datetime para formatar
            formato: "completo", "data", "hora", "compacto"
            
        Returns:
            String formatada
        """
        if formato == "completo":
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        elif formato == "data":
            return dt.strftime("%d/%m/%Y")
        elif formato == "hora":
            return dt.strftime("%H:%M:%S")
        elif formato == "compacto":
            return dt.strftime("%d/%m %H:%M")
        else:
            return str(dt)
    
    def validar_or_tools(self) -> Tuple[bool, str]:
        """Valida se OR-Tools está disponível"""
        try:
            from ortools.linear_solver import pywraplp
            return True, "OR-Tools disponível"
        except ImportError:
            return False, "OR-Tools não encontrado (pip install ortools)"
    
    def obter_info_sistema(self) -> Dict:
        """Obtém informações do sistema"""
        import platform
        import sys
        
        ortools_ok, ortools_msg = self.validar_or_tools()
        
        return {
            "python_version": sys.version.split()[0],
            "platform": platform.system(),
            "platform_version": platform.release(),
            "ortools_disponivel": ortools_ok,
            "ortools_status": ortools_msg
        }