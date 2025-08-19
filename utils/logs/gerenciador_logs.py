# utils/logs/gerenciador_logs.py
import os
import sys
import glob
from utils.logs.logger_factory import setup_logger
from datetime import datetime
import traceback 

logger = setup_logger("GerenciadorLogs")

PASTAS = [
    "logs/erros",
    "logs/funcionarios",
    "logs/equipamentos"
]

# 🆕 Pastas para limpeza na inicialização
PASTAS_INICIALIZACAO = [
    "logs/funcionarios",
    "logs/equipamentos", 
    "logs/erros",
    "logs/execucoes"
]

def limpar_arquivo_pedidos_salvos():
    """
    🆕 Remove arquivo de pedidos salvos na inicialização.
    
    Returns:
        bool: True se arquivo foi removido, False se não existia
    """
    arquivo_pedidos = "data/pedidos/pedidos_salvos.json"
    
    try:
        if os.path.exists(arquivo_pedidos):
            os.remove(arquivo_pedidos)
            print(f"🗑️ Arquivo de pedidos salvos removido: {arquivo_pedidos}")
            return True
        else:
            print(f"📄 Arquivo de pedidos salvos não existe: {arquivo_pedidos}")
            return False
    except Exception as e:
        print(f"⚠️ Erro ao remover arquivo de pedidos salvos: {e}")
        return False

def limpar_logs_inicializacao():
    """
    🧹 Limpa logs na inicialização do sistema.
    
    Remove todos os arquivos .log e .json das pastas:
    - logs/funcionarios
    - logs/equipamentos
    - logs/erros  
    - logs/execucoes
    
    🆕 NOVA FUNCIONALIDADE: Também limpa logs gerais execucao_pedidos_*.log
    
    Returns:
        str: Relatório formatado da limpeza realizada
    """
    relatorio = {
        'total_arquivos_removidos': 0,
        'pastas_processadas': {},
        'logs_gerais_removidos': 0,
        'erros': [],
        'sucesso': True
    }
    
    print("🧹 Limpando logs anteriores...")
    
    # Limpar pastas específicas
    for pasta in PASTAS_INICIALIZACAO:
        relatorio['pastas_processadas'][pasta] = {
            'logs_removidos': 0,
            'jsons_removidos': 0,
            'outros_removidos': 0,
            'total': 0
        }
        
        # Cria pasta se não existir
        try:
            os.makedirs(pasta, exist_ok=True)
        except Exception as e:
            relatorio['erros'].append(f"Erro ao criar pasta {pasta}: {e}")
            continue
        
        if not os.path.exists(pasta):
            relatorio['erros'].append(f"📁 Pasta não encontrada: {pasta}")
            continue

        # Conta e remove arquivos
        try:
            arquivos = os.listdir(pasta)
            if not arquivos:
                print(f"   📂 {pasta}: já está vazia")
                continue
                
            for nome_arquivo in arquivos:
                caminho = os.path.join(pasta, nome_arquivo)
                
                try:
                    if os.path.isfile(caminho):
                        # Remove arquivos .log
                        if nome_arquivo.endswith(".log"):
                            os.remove(caminho)
                            relatorio['pastas_processadas'][pasta]['logs_removidos'] += 1
                        
                        # Remove arquivos .json
                        elif nome_arquivo.endswith(".json"):
                            os.remove(caminho)
                            relatorio['pastas_processadas'][pasta]['jsons_removidos'] += 1
                        
                        # Remove outros arquivos (txt, csv, etc.)
                        else:
                            os.remove(caminho)
                            relatorio['pastas_processadas'][pasta]['outros_removidos'] += 1
                            
                except Exception as e:
                    relatorio['erros'].append(f"Erro ao remover {caminho}: {e}")
            
            # Calcula total da pasta
            pasta_stats = relatorio['pastas_processadas'][pasta]
            pasta_stats['total'] = (pasta_stats['logs_removidos'] + 
                                  pasta_stats['jsons_removidos'] + 
                                  pasta_stats['outros_removidos'])
            
            relatorio['total_arquivos_removidos'] += pasta_stats['total']
            
            # Mostra resultado da pasta
            if pasta_stats['total'] > 0:
                detalhes = []
                if pasta_stats['logs_removidos'] > 0:
                    detalhes.append(f"{pasta_stats['logs_removidos']} logs")
                if pasta_stats['jsons_removidos'] > 0:
                    detalhes.append(f"{pasta_stats['jsons_removidos']} JSONs")
                if pasta_stats['outros_removidos'] > 0:
                    detalhes.append(f"{pasta_stats['outros_removidos']} outros")
                
                print(f"   ✅ {pasta}: {pasta_stats['total']} arquivos removidos ({', '.join(detalhes)})")
            else:
                print(f"   📂 {pasta}: já estava vazia")
                
        except Exception as e:
            relatorio['erros'].append(f"Erro ao processar pasta {pasta}: {e}")
            relatorio['sucesso'] = False
    
    # 🆕 Limpar logs gerais na pasta raiz de logs
    try:
        pasta_logs = "logs"
        if os.path.exists(pasta_logs):
            # Busca por arquivos execucao_pedidos_*.log
            pattern = os.path.join(pasta_logs, "execucao_pedidos_*.log")
            arquivos_gerais = glob.glob(pattern)
            
            for arquivo in arquivos_gerais:
                try:
                    os.remove(arquivo)
                    relatorio['logs_gerais_removidos'] += 1
                except Exception as e:
                    relatorio['erros'].append(f"Erro ao remover {arquivo}: {e}")
            
            if relatorio['logs_gerais_removidos'] > 0:
                print(f"   ✅ logs/: {relatorio['logs_gerais_removidos']} logs gerais removidos")
            
            relatorio['total_arquivos_removidos'] += relatorio['logs_gerais_removidos']
            
    except Exception as e:
        relatorio['erros'].append(f"Erro ao limpar logs gerais: {e}")
    
    # 🆕 Limpar arquivo de pedidos salvos
    try:
        pedidos_removido = limpar_arquivo_pedidos_salvos()
        if pedidos_removido:
            print("   ✅ data/pedidos/: arquivo de pedidos salvos removido")
    except Exception as e:
        relatorio['erros'].append(f"Erro ao limpar pedidos salvos: {e}")
    
    # Resumo final
    if relatorio['total_arquivos_removidos'] > 0:
        print(f"🗑️ Total: {relatorio['total_arquivos_removidos']} arquivos de log removidos")
    else:
        print("📭 Nenhum arquivo de log encontrado para remover")
    
    # Mostra erros se houver
    if relatorio['erros']:
        print(f"⚠️ {len(relatorio['erros'])} erro(s) durante limpeza:")
        for erro in relatorio['erros']:
            print(f"   • {erro}")
        relatorio['sucesso'] = False
    
    # 🆕 Retorna relatório formatado como string
    resultado = []
    resultado.append("🧹 LIMPEZA AUTOMÁTICA DE LOGS")
    resultado.append("=" * 50)
    
    for pasta, stats in relatorio['pastas_processadas'].items():
        emoji = {
            'logs/equipamentos': '🔧',
            'logs/funcionarios': '👷',
            'logs/erros': '❌',
            'logs/execucoes': '🚀'
        }.get(pasta, '📄')
        
        resultado.append(f"{emoji} {pasta}: {stats['total']} arquivo(s) removido(s)")
    
    if relatorio['logs_gerais_removidos'] > 0:
        resultado.append(f"📊 logs gerais: {relatorio['logs_gerais_removidos']} arquivo(s) removido(s)")
    
    resultado.append("─" * 50)
    resultado.append(f"✅ Total: {relatorio['total_arquivos_removidos']} arquivo(s) de log removido(s)")
    resultado.append("📁 Pastas equipamentos/, erros/, funcionarios/, execucoes/ preservadas")
    
    if relatorio['erros']:
        resultado.append(f"⚠️ {len(relatorio['erros'])} erro(s) durante limpeza")
    
    return "\n".join(resultado)

def limpar_logs_equipamentos():
    """🔧 Limpa apenas logs de equipamentos"""
    pasta = "logs/equipamentos"
    try:
        if not os.path.exists(pasta):
            print(f"📁 Pasta não encontrada: {pasta}")
            return False
        
        arquivos = glob.glob(os.path.join(pasta, "*.log"))
        removidos = 0
        
        for arquivo in arquivos:
            try:
                os.remove(arquivo)
                removidos += 1
            except Exception as e:
                print(f"⚠️ Erro ao remover {arquivo}: {e}")
        
        print(f"🔧 {removidos} arquivo(s) de equipamentos removido(s)")
        return True
    except Exception as e:
        print(f"❌ Erro ao limpar logs de equipamentos: {e}")
        return False

def limpar_logs_funcionarios():
    """👷 Limpa apenas logs de funcionários"""
    pasta = "logs/funcionarios"
    try:
        if not os.path.exists(pasta):
            print(f"📁 Pasta não encontrada: {pasta}")
            return False
        
        arquivos = glob.glob(os.path.join(pasta, "*.log"))
        removidos = 0
        
        for arquivo in arquivos:
            try:
                os.remove(arquivo)
                removidos += 1
            except Exception as e:
                print(f"⚠️ Erro ao remover {arquivo}: {e}")
        
        print(f"👷 {removidos} arquivo(s) de funcionários removido(s)")
        return True
    except Exception as e:
        print(f"❌ Erro ao limpar logs de funcionários: {e}")
        return False

def limpar_logs_erros():
    """❌ Limpa apenas logs de erros"""
    pasta = "logs/erros"
    try:
        if not os.path.exists(pasta):
            print(f"📁 Pasta não encontrada: {pasta}")
            return False
        
        arquivos = glob.glob(os.path.join(pasta, "*.log"))
        jsons = glob.glob(os.path.join(pasta, "*.json"))
        removidos = 0
        
        for arquivo in arquivos + jsons:
            try:
                os.remove(arquivo)
                removidos += 1
            except Exception as e:
                print(f"⚠️ Erro ao remover {arquivo}: {e}")
        
        print(f"❌ {removidos} arquivo(s) de erros removido(s)")
        return True
    except Exception as e:
        print(f"❌ Erro ao limpar logs de erros: {e}")
        return False

def limpar_logs_execucoes():
    """🚀 Limpa apenas logs de execuções"""
    pasta = "logs/execucoes"
    try:
        if not os.path.exists(pasta):
            print(f"📁 Pasta não encontrada: {pasta}")
            return False
        
        arquivos = glob.glob(os.path.join(pasta, "*.log"))
        removidos = 0
        
        for arquivo in arquivos:
            try:
                os.remove(arquivo)
                removidos += 1
            except Exception as e:
                print(f"⚠️ Erro ao remover {arquivo}: {e}")
        
        print(f"🚀 {removidos} arquivo(s) de execuções removido(s)")
        return True
    except Exception as e:
        print(f"❌ Erro ao limpar logs de execuções: {e}")
        return False

def limpar_todos_os_logs():
    """
    🧹 Limpa todos os logs do sistema, incluindo:
    - Arquivos .log tradicionais
    - Arquivos .json de erros de exceções (quantidade, timing, etc.)
    """
    for pasta in PASTAS:
        if not os.path.exists(pasta):
            print(f"📁 Pasta não encontrada: {pasta}")
            continue

        # Contar arquivos por tipo para relatório
        logs_removidos = 0
        jsons_removidos = 0
        
        for nome_arquivo in os.listdir(pasta):
            caminho = os.path.join(pasta, nome_arquivo)
            
            try:
                # Limpar arquivos .log tradicionais
                if nome_arquivo.endswith(".log"):
                    os.remove(caminho)
                    logs_removidos += 1
                    print(f"🗑️ Log removido: {caminho}")
                
                # 🆕 Limpar arquivos .json de erros de exceções
                elif nome_arquivo.endswith(".json"):
                    # Verificar se é arquivo de erro de exceção
                    if any(prefix in nome_arquivo for prefix in [
                        "quantity_",     # Erros de quantidade
                        "timing_",       # Erros de timing
                        "relatorio_"     # Relatórios gerados
                    ]):
                        os.remove(caminho)
                        jsons_removidos += 1
                        print(f"🗑️ JSON de erro removido: {caminho}")
                    else:
                        print(f"ℹ️ JSON mantido (não é arquivo de erro): {nome_arquivo}")
                        
            except Exception as e:
                print(f"⚠️ Erro ao remover {caminho}: {e}")
        
        # Relatório por pasta
        if logs_removidos > 0 or jsons_removidos > 0:
            print(f"📊 Pasta {pasta}: {logs_removidos} logs + {jsons_removidos} JSONs removidos")
    
    print("✅ Limpeza de logs concluída!")

def limpar_apenas_jsons_erros():
    """
    🧹 Limpa APENAS os arquivos JSON de erros de exceções, mantendo logs tradicionais.
    Útil para limpeza seletiva.
    """
    pasta_erros = "logs/erros"
    
    if not os.path.exists(pasta_erros):
        print(f"📁 Pasta de erros não encontrada: {pasta_erros}")
        return
    
    jsons_removidos = 0
    
    for nome_arquivo in os.listdir(pasta_erros):
        if nome_arquivo.endswith(".json"):
            # Verificar se é arquivo de erro de exceção
            if any(prefix in nome_arquivo for prefix in [
                "quantity_",           # Erros de quantidade
                "timing_",            # Erros de timing  
                "relatorio_quantity_", # Relatórios de quantidade
                "relatorio_timing_"   # Relatórios de timing
            ]):
                caminho = os.path.join(pasta_erros, nome_arquivo)
                try:
                    os.remove(caminho)
                    jsons_removidos += 1
                    print(f"🗑️ JSON de erro removido: {caminho}")
                except Exception as e:
                    print(f"⚠️ Erro ao remover {caminho}: {e}")
    
    print(f"📊 {jsons_removidos} arquivos JSON de erros removidos da pasta {pasta_erros}")

def limpar_jsons_erros_por_tipo(tipo_erro: str):
    """
    🧹 Limpa JSONs de erros de um tipo específico.
    
    Args:
        tipo_erro: "quantity", "timing", ou "relatorio"
    """
    pasta_erros = "logs/erros"
    
    if not os.path.exists(pasta_erros):
        print(f"📁 Pasta de erros não encontrada: {pasta_erros}")
        return
    
    prefixos_validos = {
        "quantity": ["quantity_"],
        "timing": ["timing_"],
        "relatorio": ["relatorio_quantity_", "relatorio_timing_"],
        "all": ["quantity_", "timing_", "relatorio_"]
    }
    
    if tipo_erro not in prefixos_validos:
        print(f"⚠️ Tipo de erro inválido: {tipo_erro}. Opções: {list(prefixos_validos.keys())}")
        return
    
    prefixos = prefixos_validos[tipo_erro]
    jsons_removidos = 0
    
    for nome_arquivo in os.listdir(pasta_erros):
        if nome_arquivo.endswith(".json"):
            if any(prefixo in nome_arquivo for prefixo in prefixos):
                caminho = os.path.join(pasta_erros, nome_arquivo)
                try:
                    os.remove(caminho)
                    jsons_removidos += 1
                    print(f"🗑️ JSON removido: {caminho}")
                except Exception as e:
                    print(f"⚠️ Erro ao remover {caminho}: {e}")
    
    print(f"📊 {jsons_removidos} arquivos JSON do tipo '{tipo_erro}' removidos")

def remover_logs_pedido(id_pedido: int):
    """
    🗑️ Remove arquivos de log relacionados à um pedido (funcionários e equipamentos).
    """
    logs = [
        f"logs/pedido_{id_pedido}.log",
        f"logs/funcionarios_{id_pedido}.log"
    ]
    for caminho in logs:
        try:
            if os.path.exists(caminho):
                os.remove(caminho)
                logger.info(f"🗑️ Arquivo de log removido: {caminho}")
        except Exception as e:
            logger.warning(f"⚠️ Falha ao remover log {caminho}: {e}")

def registrar_erro_execucao_pedido(id_ordem: int, id_pedido: int, erro: Exception):
    """
    🔥 Registra erro de execução no terminal e em arquivo de log (snapshot).
    """
    logger.error(f"⚠️ Erro na execução do pedido {id_pedido}: {erro.__class__.__name__}: {erro}")
    
    # Captura traceback da exceção atual
    traceback_str = traceback.format_exc()
    logger.error("📋 Traceback completo abaixo:")
    logger.error(traceback_str)

    # Localização exata do erro
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if exc_traceback:
        ultima_chamada = traceback.extract_tb(exc_traceback)[-1]
        logger.error(
            f"📍 Local do erro: {ultima_chamada.filename}, "
            f"linha {ultima_chamada.lineno}, função {ultima_chamada.name}"
        )

    # Salva em arquivo detalhado
    try:
        os.makedirs("logs/erros", exist_ok=True)
        nome_arquivo = f"logs/erros/ordem: {id_ordem} | pedido: {id_pedido}.log"
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write("==============================================\n")
            f.write(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"🧾 Ordem: {id_ordem} | Pedido: {id_pedido}\n")
            f.write(f"⚠️ Erro: {erro.__class__.__name__}: {erro}\n")
            if exc_traceback:
                f.write(f"📍 Local: {ultima_chamada.filename}, linha {ultima_chamada.lineno}, função {ultima_chamada.name}\n")
            f.write("--------------------------------------------------\n")
            f.write(traceback_str)
            f.write("==============================================\n")
    except Exception as log_erro:
        logger.warning(f"⚠️ Falha ao registrar erro em arquivo: {log_erro}")

def registrar_log_equipamentos(id_ordem: int, id_pedido: int, id_atividade: int, nome_item: str,
                               nome_atividade: str, equipamentos_alocados: list[tuple]): 
    """
    🔥 Registra os logs de equipamentos.
    """
    if id_pedido:
        os.makedirs("logs/equipamentos", exist_ok=True)
        caminho = f"logs/equipamentos/ordem: {id_ordem} | pedido: {id_pedido}.log"
        with open(caminho, "a", encoding="utf-8") as arq:
            for _, equipamento, inicio_eqp, fim_eqp in equipamentos_alocados:
                str_inicio = inicio_eqp.strftime('%H:%M') + f" [{inicio_eqp.strftime('%d/%m')}]"
                str_fim = fim_eqp.strftime('%H:%M') + f" [{fim_eqp.strftime('%d/%m')}]"

                # 👉 Se for lista, junta os nomes
                if isinstance(equipamento, list):
                    nomes_equipamentos = ', '.join(e.nome for e in equipamento)
                else:
                    nomes_equipamentos = equipamento.nome

                linha = (
                    f"{id_ordem} | "
                    f"{id_pedido} | "
                    f"{id_atividade} | {nome_item} | {nome_atividade} | "
                    f"{nomes_equipamentos} | {str_inicio} | {str_fim} \n"
                )
                arq.write(linha)

def registrar_log_funcionarios(id_ordem: int, id_pedido: int, id_atividade: int, 
                               funcionarios_alocados: list[tuple], nome_item: str, 
                               nome_atividade: str, inicio: datetime, fim: datetime):
    """
    🔥 Registra os logs de funcionários.
    """
    if id_pedido:
        os.makedirs("logs/funcionarios", exist_ok=True)
        caminho = f"logs/funcionarios/ordem: {id_ordem} | pedido: {id_pedido}.log"
        with open(caminho, "a", encoding="utf-8") as arq:
            str_inicio = inicio.strftime('%H:%M') + f" [{inicio.strftime('%d/%m')}]"
            str_fim = fim.strftime('%H:%M') + f" [{fim.strftime('%d/%m')}]"

            for funcionario in funcionarios_alocados:
                linha = (
                    f"{id_ordem} | "
                    f"{id_pedido} | "
                    f"{id_atividade} | {nome_item} | {nome_atividade} | "
                    f"{funcionario.nome} | {str_inicio} | {str_fim} \n"
                )
                arq.write(linha)
                
def apagar_logs_por_pedido_e_ordem(id_ordem: int, id_pedido: int):
    """
    🔥 Remove logs de equipamentos e funcionários (mas mantém os logs de erros).
    """
    padrao = f"ordem: {id_ordem} | pedido: {id_pedido}.log"

    PASTAS = [
        "logs/equipamentos",
        "logs/funcionarios",
        # ⚠️ NÃO incluir "logs/erros"
    ]

    for pasta in PASTAS:
        caminho = os.path.join(pasta, padrao)
        if os.path.exists(caminho):
            try:
                os.remove(caminho)
                print(f"🗑️ Apagado: {caminho}")
            except Exception as e:
                logger.warning(f"⚠️ Falha ao apagar {caminho}: {e}")

def remover_log_equipamentos(id_ordem: int, id_pedido: int = None, id_atividade: int = None):
    """
    Remove logs de equipamentos com base nos parâmetros informados:
    - Se apenas id_ordem: remove todos os arquivos da ordem.
    - Se id_ordem e id_pedido: remove o arquivo específico do pedido.
    - Se id_ordem, id_pedido e id_atividade: remove apenas linhas da atividade no arquivo.
    """
    pasta_logs = "logs/equipamentos"

    if id_pedido is None:
        # Caso 1: remover todos os logs da ordem
        for nome_arquivo in os.listdir(pasta_logs):
            if nome_arquivo.startswith(f"ordem: {id_ordem}"):
                caminho = os.path.join(pasta_logs, nome_arquivo)
                try:
                    os.remove(caminho)
                    print(f"🗑️ Removido: {caminho}")
                except Exception as e:
                    print(f"⚠️ Erro ao remover {caminho}: {e}")
        return

    caminho = f"{pasta_logs}/ordem: {id_ordem} | pedido: {id_pedido}.log"
    if not os.path.exists(caminho):
        return

    if id_atividade is None:
        # Caso 2: remover o arquivo específico do pedido
        try:
            os.remove(caminho)
            print(f"🗑️ Removido: {caminho}")
        except Exception as e:
            print(f"⚠️ Erro ao remover {caminho}: {e}")
        return

    # Caso 3: remover apenas as linhas da atividade
    with open(caminho, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    with open(caminho, "w", encoding="utf-8") as f:
        for linha in linhas:
            if f"{id_atividade} |" not in linha:
                f.write(linha)

def remover_log_funcionarios(id_ordem: int, id_pedido: int, id_atividade: int):
    """
    Remove as linhas de log de funcionários associadas a uma atividade específica.
    """
    caminho = f"logs/funcionarios/ordem: {id_ordem} | pedido: {id_pedido}.log"
    if not os.path.exists(caminho):
        return

    with open(caminho, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    with open(caminho, "w", encoding="utf-8") as f:
        for linha in linhas:
            if f"{id_atividade} |" not in linha:
                f.write(linha)

def salvar_erro_em_log(id_ordem: int, id_pedido: int, excecao: Exception):
    """
    💾 Salva um snapshot do erro ocorrido durante a execução de um pedido.

    O log é salvo em logs/erros/ com o nome: ordem: <id> | pedido: <id>.log
    """
    os.makedirs("logs/erros", exist_ok=True)
    nome_arquivo = f"logs/erros/ordem: {id_ordem} | pedido: {id_pedido}.log"
    
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("==============================================\n")
        f.write(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"🧾 Ordem: {id_ordem} | Pedido: {id_pedido}\n")
        f.write("⚠️ Motivo do erro:\n")
        f.write("--------------------------------------------------\n")
        f.write(traceback.format_exc())
        f.write("==============================================\n")