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
    "logs/execucoes",
    "logs/restricoes"  # Incluir restrições na limpeza
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
    
    # 🆕 LIMPEZA COMPLETA: Limpar todos os logs em logs/ e subpastas (EXCETO restricoes)
    try:
        pasta_logs = "logs"
        if os.path.exists(pasta_logs):

            # 1. Limpar logs na raiz de logs/
            patterns_raiz = [
                os.path.join(pasta_logs, "execucao_pedidos_*.log"),
                os.path.join(pasta_logs, "execucao_coxinhas_*.log"),
                os.path.join(pasta_logs, "*.log")  # Todos os .log na raiz
            ]

            for pattern in patterns_raiz:
                arquivos_encontrados = glob.glob(pattern)
                for arquivo in arquivos_encontrados:
                    try:
                        os.remove(arquivo)
                        relatorio['logs_gerais_removidos'] += 1
                    except Exception as e:
                        relatorio['erros'].append(f"Erro ao remover {arquivo}: {e}")

            # 2. Limpar TODAS as subpastas em logs/ (exceto restricoes)
            for item in os.listdir(pasta_logs):
                subpasta = os.path.join(pasta_logs, item)

                # Pular se não for diretório
                if not os.path.isdir(subpasta):
                    continue

                # Todas as pastas serão limpas - nenhuma preservação especial

                # Limpar subpasta se não estiver na lista padrão
                if subpasta not in [os.path.join(pasta_logs, p.split('/')[-1]) for p in PASTAS_INICIALIZACAO]:
                    try:
                        arquivos_subpasta = glob.glob(os.path.join(subpasta, "*"))
                        removidos_subpasta = 0

                        for arquivo in arquivos_subpasta:
                            if os.path.isfile(arquivo):
                                try:
                                    os.remove(arquivo)
                                    removidos_subpasta += 1
                                except Exception as e:
                                    relatorio['erros'].append(f"Erro ao remover {arquivo}: {e}")

                        if removidos_subpasta > 0:
                            print(f"   ✅ logs/{item}/: {removidos_subpasta} arquivos removidos")
                            relatorio['logs_gerais_removidos'] += removidos_subpasta

                    except Exception as e:
                        relatorio['erros'].append(f"Erro ao limpar subpasta {subpasta}: {e}")

            if relatorio['logs_gerais_removidos'] > 0:
                print(f"   ✅ logs/ (completa): {relatorio['logs_gerais_removidos']} arquivos removidos")

            relatorio['total_arquivos_removidos'] += relatorio['logs_gerais_removidos']

    except Exception as e:
        relatorio['erros'].append(f"Erro ao limpar logs completos: {e}")
    
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
    resultado.append("📁 Todas as pastas de logs foram limpas")
    
    if relatorio['erros']:
        resultado.append(f"⚠️ {len(relatorio['erros'])} erro(s) durante limpeza")
    
    return "\n".join(resultado)

def limpar_logs_equipamentos():
    """🔧 Limpa apenas logs de equipamentos (incluindo subprodutos agrupados)"""
    pasta = "logs/equipamentos"
    try:
        if not os.path.exists(pasta):
            print(f"📁 Pasta não encontrada: {pasta}")
            return False

        arquivos = glob.glob(os.path.join(pasta, "*.log"))
        removidos = 0
        agrupados_removidos = 0

        for arquivo in arquivos:
            try:
                nome_arquivo = os.path.basename(arquivo)
                if nome_arquivo.startswith("agrupado_"):
                    agrupados_removidos += 1
                os.remove(arquivo)
                removidos += 1
            except Exception as e:
                print(f"⚠️ Erro ao remover {arquivo}: {e}")

        if agrupados_removidos > 0:
            print(f"🔧 {removidos} arquivo(s) de equipamentos removido(s) (incluindo {agrupados_removidos} logs agrupados)")
        else:
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
    Registra erro de execução no terminal e em arquivo de log.
    ATUALIZADO: Detecta erros de timing e usa formato limpo.
    """
    logger.error(f"Erro na execução do pedido {id_pedido}: {erro.__class__.__name__}: {erro}")
    
    # Captura traceback da exceção atual
    traceback_str = traceback.format_exc()
    logger.error("Traceback completo abaixo:")
    logger.error(traceback_str)

    # Localização exata do erro
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if exc_traceback:
        ultima_chamada = traceback.extract_tb(exc_traceback)[-1]
        logger.error(
            f"Local do erro: {ultima_chamada.filename}, "
            f"linha {ultima_chamada.lineno}, função {ultima_chamada.name}"
        )

    # NOVO: Verificar se é erro de timing e usar formato específico
    erro_str = str(erro)
    if "Tempo máximo de espera excedido entre atividades" in erro_str:
        # Tentar salvar no formato limpo
        if salvar_erro_timing_formato_limpo(id_ordem, id_pedido, erro):
            logger.info("Erro de timing salvo no formato limpo especificado")
            return
    
    # Para outros tipos de erro, usar formato padrão
    salvar_erro_em_log(id_ordem, id_pedido, erro)


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

def _gerar_descricao_erro_legivel(id_ordem: int, id_pedido: int, excecao: Exception) -> str:
    """
    Gera uma descrição legível do erro baseada nos arquivos JSON de erro.
    """
    import json
    import glob
    
    descricao = ""
    
    # Procurar por arquivos JSON de erro relacionados a este pedido
    pasta_erros = "logs/erros"
    
    # Padrões de arquivos JSON para buscar
    padroes = [
        f"{pasta_erros}/quantidade_*_{id_ordem}_{id_pedido}_*.json",
        f"{pasta_erros}/timing_*_{id_ordem}_{id_pedido}_*.json"
    ]
    
    arquivos_json = []
    for padrao in padroes:
        arquivos_json.extend(glob.glob(padrao))
    
    # Se encontrar JSONs, extrair informações legíveis
    if arquivos_json:
        # Ordenar por timestamp (nome do arquivo)
        arquivos_json.sort()
        
        # Usar o JSON mais recente
        arquivo_json = arquivos_json[-1]
        
        try:
            with open(arquivo_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                
            # Identificar tipo de erro e formatar descrição
            if 'erro_quantidade' in dados:
                erro = dados['erro_quantidade']
                descricao = f"❌ ERRO DE QUANTIDADE\n\n"
                descricao += f"Problema: {erro.get('message', 'Erro de quantidade')}\n\n"
                
                if 'details' in erro:
                    detalhes = erro['details']
                    descricao += f"📊 Detalhes:\n"
                    descricao += f"   • Quantidade solicitada: {detalhes.get('requested_quantity', 'N/A')}g\n"
                    descricao += f"   • Capacidade mínima: {detalhes.get('minimum_capacity', 'N/A')}g\n"
                    descricao += f"   • Diferença: {detalhes.get('deficit', 'N/A')}g\n"
                    descricao += f"   • Tipo de equipamento: {detalhes.get('equipment_type', 'N/A')}\n\n"
                    
                    if 'available_equipment' in detalhes:
                        descricao += f"🔧 Equipamentos disponíveis:\n"
                        for equip in detalhes['available_equipment']:
                            descricao += f"   • {equip['nome']}: {equip['capacidade_min']}g - {equip['capacidade_max']}g\n"
                        descricao += "\n"
                
                if 'suggestions' in erro:
                    descricao += f"💡 Sugestões:\n"
                    for sugestao in erro['suggestions']:
                        descricao += f"   • {sugestao}\n"
                        
            elif 'erro_tempo' in dados:
                erro = dados['erro_tempo']
                descricao = f"❌ ERRO DE TEMPO/CONFLITO\n\n"
                descricao += f"Problema: {erro.get('message', 'Erro de tempo')}\n\n"
                
                if 'details' in erro:
                    detalhes = erro['details']
                    
                    if 'current_activity' in detalhes:
                        ativ_atual = detalhes['current_activity']
                        descricao += f"📋 Atividade atual:\n"
                        descricao += f"   • ID: {ativ_atual.get('id', 'N/A')}\n"
                        descricao += f"   • Nome: {ativ_atual.get('name', 'N/A')}\n"
                        descricao += f"   • Término: {ativ_atual.get('end_time_formatted', 'N/A')}\n\n"
                    
                    if 'successor_activity' in detalhes:
                        ativ_sucessora = detalhes['successor_activity']
                        descricao += f"📋 Atividade sucessora:\n"
                        descricao += f"   • ID: {ativ_sucessora.get('id', 'N/A')}\n"
                        descricao += f"   • Nome: {ativ_sucessora.get('name', 'N/A')}\n"
                        descricao += f"   • Início: {ativ_sucessora.get('start_time_formatted', 'N/A')}\n\n"
                    
                    if 'timing_violation' in detalhes:
                        violacao = detalhes['timing_violation']
                        descricao += f"⏱️ Violação de tempo:\n"
                        descricao += f"   • Tempo máximo de espera: {violacao.get('maximum_wait_time_formatted', 'N/A')}\n"
                        descricao += f"   • Atraso real: {violacao.get('actual_delay_formatted', 'N/A')}\n"
                        descricao += f"   • Excesso: {violacao.get('excess_time_formatted', 'N/A')}\n\n"
                
                if 'suggestions' in erro:
                    descricao += f"💡 Sugestões:\n"
                    for sugestao in erro['suggestions']:
                        descricao += f"   • {sugestao}\n"
                        
        except Exception as e:
            # Se falhar ao ler JSON, tentar usar a mensagem da exceção
            if excecao and str(excecao):
                descricao = f"Erro: {str(excecao)}\n"
    
    # Se não encontrou JSONs mas tem exceção, usar a mensagem
    elif excecao and str(excecao) and str(excecao) != "None":
        descricao = f"Erro: {str(excecao)}\n"
    
    return descricao
def salvar_erro_timing_formato_limpo(id_ordem: int, id_pedido: int, timing_error: Exception):
    """
    Salva erro de timing no formato limpo especificado.
    Esta função tem prioridade sobre salvar_erro_em_log para erros de timing.
    """
    from utils.logs.formatador_timing_limpo import reformatar_erro_timing_para_novo_formato
    
    try:
        # Detectar se é erro de timing
        erro_str = str(timing_error)
        if "Tempo máximo de espera excedido entre atividades" in erro_str:
            
            # Gerar log no formato limpo
            log_limpo = reformatar_erro_timing_para_novo_formato(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                erro_original=erro_str
            )
            
            # Salvar arquivo
            os.makedirs("logs/erros", exist_ok=True)
            nome_arquivo = f"logs/erros/ordem: {id_ordem} | pedido: {id_pedido}.log"
            
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                f.write(log_limpo)
            
            logger.info(f"Log de timing limpo salvo: {nome_arquivo}")
            return True
            
    except Exception as e:
        logger.error(f"Falha ao salvar log de timing limpo: {e}")
    
    return False

def salvar_erro_detalhado(id_ordem: int, id_pedido: int, tipo_erro: str, descricao_detalhada: dict):
    """
    💾 Salva um log detalhado e legível do erro baseado em informações estruturadas.
    
    Args:
        id_ordem: ID da ordem
        id_pedido: ID do pedido
        tipo_erro: Tipo do erro (QUANTIDADE, TEMPO, etc)
        descricao_detalhada: Dicionário com detalhes do erro
    """
    os.makedirs("logs/erros", exist_ok=True)
    nome_arquivo = f"logs/erros/ordem: {id_ordem} | pedido: {id_pedido}.log"
    
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("==============================================\n")
        f.write(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"🧾 Ordem: {id_ordem} | Pedido: {id_pedido}\n")
        f.write(f"⚠️ Tipo de Erro: {tipo_erro}\n")
        f.write("--------------------------------------------------\n\n")
        
        if tipo_erro == "QUANTIDADE":
            f.write("❌ ERRO DE QUANTIDADE\n\n")
            f.write(f"Problema: {descricao_detalhada.get('mensagem', 'Erro de quantidade')}\n\n")
            
            if 'detalhes' in descricao_detalhada:
                det = descricao_detalhada['detalhes']
                f.write("📊 Detalhes:\n")
                f.write(f"   • Atividade: {det.get('nome_atividade', 'N/A')}\n")
                f.write(f"   • Quantidade solicitada: {det.get('quantidade_solicitada', 'N/A')}g\n")
                f.write(f"   • Capacidade mínima: {det.get('capacidade_minima', 'N/A')}g\n")
                f.write(f"   • Diferença: {det.get('diferenca', 'N/A')}g\n")
                f.write(f"   • Tipo de equipamento: {det.get('tipo_equipamento', 'N/A')}\n\n")
                
                if 'equipamentos' in det:
                    f.write("🔧 Equipamentos disponíveis:\n")
                    for equip in det['equipamentos']:
                        f.write(f"   • {equip['nome']}: {equip['min']}g - {equip['max']}g\n")
                    f.write("\n")
            
            if 'sugestoes' in descricao_detalhada:
                f.write("💡 Sugestões:\n")
                for sug in descricao_detalhada['sugestoes']:
                    f.write(f"   • {sug}\n")
                    
        elif tipo_erro == "TEMPO":
            f.write("❌ ERRO DE TEMPO/CONFLITO\n\n")
            f.write(f"Problema: {descricao_detalhada.get('mensagem', 'Conflito de tempo')}\n\n")
            
            if 'detalhes' in descricao_detalhada:
                det = descricao_detalhada['detalhes']
                
                if 'atividade_atual' in det:
                    ativ = det['atividade_atual']
                    f.write("📋 Atividade atual:\n")
                    f.write(f"   • Nome: {ativ.get('nome', 'N/A')}\n")
                    f.write(f"   • Término: {ativ.get('fim', 'N/A')}\n\n")
                
                if 'atividade_sucessora' in det:
                    ativ = det['atividade_sucessora']
                    f.write("📋 Atividade sucessora:\n")
                    f.write(f"   • Nome: {ativ.get('nome', 'N/A')}\n")
                    f.write(f"   • Início disponível: {ativ.get('inicio', 'N/A')}\n\n")
                
                if 'conflito' in det:
                    conf = det['conflito']
                    f.write("⏱️ Conflito:\n")
                    f.write(f"   • Tempo de espera máximo: {conf.get('tempo_maximo', 'N/A')}\n")
                    f.write(f"   • Atraso real: {conf.get('atraso', 'N/A')}\n")
                    f.write(f"   • Excesso: {conf.get('excesso', 'N/A')}\n\n")
            
            if 'sugestoes' in descricao_detalhada:
                f.write("💡 Sugestões:\n")
                for sug in descricao_detalhada['sugestoes']:
                    f.write(f"   • {sug}\n")
        
        else:
            # Tipo genérico
            f.write(f"❌ ERRO: {descricao_detalhada.get('mensagem', 'Erro desconhecido')}\n\n")
            
            if 'detalhes' in descricao_detalhada:
                f.write("📊 Detalhes:\n")
                for chave, valor in descricao_detalhada['detalhes'].items():
                    f.write(f"   • {chave}: {valor}\n")
                f.write("\n")
        
        f.write("\n==============================================\n")

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
        
        # Tentar obter descrição legível do erro
        erro_legivel = _gerar_descricao_erro_legivel(id_ordem, id_pedido, excecao)
        if erro_legivel:
            f.write(erro_legivel)
        else:
            # Fallback para o traceback original se não conseguir gerar descrição
            tb = traceback.format_exc()
            if tb and tb.strip() != "NoneType: None":
                f.write(tb)
            else:
                f.write(f"Erro: {str(excecao) if excecao else 'Erro desconhecido'}\n")
        
        f.write("==============================================\n")