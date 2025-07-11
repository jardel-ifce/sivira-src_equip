# utils/gerenciador_logs.py
import os
import sys
from utils.logs.logger_factory import setup_logger
from datetime import datetime
import traceback 

logger = setup_logger("GerenciadorLogs")


PASTAS = [
    "logs/erros",
    "logs/funcionarios",
    "logs/equipamentos"
]

def limpar_todos_os_logs():
    for pasta in PASTAS:
        if not os.path.exists(pasta):
            print(f"📁 Pasta não encontrada: {pasta}")
            continue

        for nome_arquivo in os.listdir(pasta):
            if nome_arquivo.endswith(".log"):
                caminho = os.path.join(pasta, nome_arquivo)
                try:
                    os.remove(caminho)
                    print(f"🗑️ Removido: {caminho}")
                except Exception as e:
                    print(f"❌ Erro ao remover {caminho}: {e}")


def remover_logs_pedido(pedido_id: int):
    """
    🗑️ Remove arquivos de log relacionados à um pedido (funcionários e equipamentos).
    """
    logs = [
        f"logs/pedido_{pedido_id}.log",
        f"logs/funcionarios_{pedido_id}.log"
    ]
    for caminho in logs:
        try:
            if os.path.exists(caminho):
                os.remove(caminho)
                logger.info(f"🗑️ Arquivo de log removido: {caminho}")
        except Exception as e:
            logger.warning(f"⚠️ Falha ao remover log {caminho}: {e}")

def registrar_erro_execucao_pedido(ordem_id: int, pedido_id: int, erro: Exception):
    """
    🔥 Registra erro de execução no terminal e em arquivo de log (snapshot).
    """
    logger.error(f"❌ Erro na execução do pedido {pedido_id}: {erro.__class__.__name__}: {erro}")
    
    # Captura traceback da exceção atual
    traceback_str = traceback.format_exc()
    logger.error("🔍 Traceback completo abaixo:")
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
        nome_arquivo = f"logs/erros/ordem: {ordem_id} | pedido: {pedido_id}.log"
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write("==============================================\n")
            f.write(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"🧾 Ordem: {ordem_id} | Pedido: {pedido_id}\n")
            f.write(f"❌ Erro: {erro.__class__.__name__}: {erro}\n")
            if exc_traceback:
                f.write(f"📍 Local: {ultima_chamada.filename}, linha {ultima_chamada.lineno}, função {ultima_chamada.name}\n")
            f.write("--------------------------------------------------\n")
            f.write(traceback_str)
            f.write("==============================================\n")
    except Exception as log_erro:
        logger.warning(f"⚠️ Falha ao registrar erro em arquivo: {log_erro}")


def registrar_log_equipamentos(ordem_id: int, pedido_id: int, id_atividade: int, nome_item: str,
                               nome_atividade: str, equipamentos_alocados: list[tuple]): 
        if pedido_id:
            os.makedirs("logs/equipamentos", exist_ok=True)
            caminho = f"logs/equipamentos/ordem: {ordem_id} | pedido: {pedido_id}.log"
            with open(caminho, "a", encoding="utf-8") as arq:
                for _, equipamento, inicio_eqp, fim_eqp in equipamentos_alocados:
                    linha = (
                        f"{ordem_id} | "
                        f"{pedido_id} | "
                        f"{id_atividade} | {nome_item} | {nome_atividade} | "
                        f"{equipamento.nome} | {inicio_eqp.strftime('%H:%M')} | {fim_eqp.strftime('%H:%M')} \n"
                    )
                    arq.write(linha)


def registrar_log_funcionarios(ordem_id: int, pedido_id: int, id_atividade: int, 
                               funcionarios_alocados: list[tuple], nome_item: str, 
                               nome_atividade: str, inicio: datetime, fim: datetime):
        if pedido_id:
            os.makedirs("logs/funcionarios", exist_ok=True)
            caminho = f"logs/funcionarios/ordem: {ordem_id} | pedido: {pedido_id}.log"
            with open(caminho, "a", encoding="utf-8") as arq:
                for funcionario in funcionarios_alocados:
                    linha = (
                        f"{ordem_id} | "
                        f"{pedido_id} | "
                        f"{id_atividade} | {nome_item} | {nome_atividade} | "
                        f"{funcionario.nome} | {inicio.strftime('%H:%M')} | {fim.strftime('%H:%M')} \n"
                    )
                    arq.write(linha)


def apagar_logs_por_pedido_e_ordem(ordem_id: int, pedido_id: int):
    """
    🔥 Remove logs de equipamentos e funcionários (mas mantém os logs de erros).
    """
    padrao = f"ordem: {ordem_id} | pedido: {pedido_id}.log"

    PASTAS = [
        "logs/equipamentos",
        "logs/funcionarios",
        # ❌ NÃO incluir "logs/erros"
    ]

    for pasta in PASTAS:
        caminho = os.path.join(pasta, padrao)
        if os.path.exists(caminho):
            try:
                os.remove(caminho)
                print(f"🗑️ Apagado: {caminho}")
            except Exception as e:
                logger.warning(f"⚠️ Falha ao apagar {caminho}: {e}")



def remover_log_equipamentos(ordem_id: int, pedido_id: int = None, id_atividade: int = None):
    """
    Remove logs de equipamentos com base nos parâmetros informados:
    - Se apenas ordem_id: remove todos os arquivos da ordem.
    - Se ordem_id e pedido_id: remove o arquivo específico do pedido.
    - Se ordem_id, pedido_id e id_atividade: remove apenas linhas da atividade no arquivo.
    """
    pasta_logs = "logs/equipamentos"

    if pedido_id is None:
        # Caso 1: remover todos os logs da ordem
        for nome_arquivo in os.listdir(pasta_logs):
            if nome_arquivo.startswith(f"ordem: {ordem_id}"):
                caminho = os.path.join(pasta_logs, nome_arquivo)
                try:
                    os.remove(caminho)
                    print(f"🗑️ Removido: {caminho}")
                except Exception as e:
                    print(f"❌ Erro ao remover {caminho}: {e}")
        return

    caminho = f"{pasta_logs}/ordem: {ordem_id} | pedido: {pedido_id}.log"
    if not os.path.exists(caminho):
        return

    if id_atividade is None:
        # Caso 2: remover o arquivo específico do pedido
        try:
            os.remove(caminho)
            print(f"🗑️ Removido: {caminho}")
        except Exception as e:
            print(f"❌ Erro ao remover {caminho}: {e}")
        return

    # Caso 3: remover apenas as linhas da atividade
    with open(caminho, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    with open(caminho, "w", encoding="utf-8") as f:
        for linha in linhas:
            if f"{id_atividade} |" not in linha:
                f.write(linha)

def remover_log_funcionarios(ordem_id: int, pedido_id: int, id_atividade: int):
    """
    Remove as linhas de log de funcionários associadas a uma atividade específica.
    """
    caminho = f"logs/funcionarios/ordem: {ordem_id} | pedido: {pedido_id}.log"
    if not os.path.exists(caminho):
        return

    with open(caminho, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    with open(caminho, "w", encoding="utf-8") as f:
        for linha in linhas:
            if f"{id_atividade} |" not in linha:
                f.write(linha)

def salvar_erro_em_log(ordem_id: int, pedido_id: int, excecao: Exception):
    """
    💾 Salva um snapshot do erro ocorrido durante a execução de um pedido.

    O log é salvo em logs/erros/ com o nome: ordem: <id> | pedido: <id>.log
    """
    os.makedirs("logs/erros", exist_ok=True)
    nome_arquivo = f"logs/erros/ordem: {ordem_id} | pedido: {pedido_id}.log"
    
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write("==============================================\n")
        f.write(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"🧾 Ordem: {ordem_id} | Pedido: {pedido_id}\n")
        f.write("❌ Motivo do erro:\n")
        f.write("--------------------------------------------------\n")
        f.write(traceback.format_exc())
        f.write("==============================================\n")