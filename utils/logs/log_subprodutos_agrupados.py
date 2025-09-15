# utils/logs/log_subprodutos_agrupados.py
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from utils.logs.logger_factory import setup_logger

logger = setup_logger("LogSubprodutosAgrupados")

def registrar_log_subproduto_agrupado(
    ordens_e_pedidos: List[Dict[str, int]],
    id_atividade: int,
    nome_item: str,
    nome_atividade: str,
    equipamentos_alocados: List[tuple],
    quantidade_total: float,
    detalhes_consolidacao: Optional[Dict[str, Any]] = None
):
    """
    Registra log de subproduto agrupado em /logs/equipamentos com padrão específico.

    Args:
        ordens_e_pedidos: Lista de dicts com 'id_ordem' e 'id_pedido' dos pedidos agrupados
        id_atividade: ID da atividade consolidada
        nome_item: Nome do subproduto (ex: "massa_para_frituras")
        nome_atividade: Nome da atividade (ex: "mistura_de_massas_para_frituras")
        equipamentos_alocados: Lista de tuplas (_, equipamento, inicio_eqp, fim_eqp)
        quantidade_total: Quantidade total consolidada
        detalhes_consolidacao: Informações adicionais sobre a consolidação
    """
    if not ordens_e_pedidos:
        logger.warning("Lista de ordens e pedidos vazia. Log não será criado.")
        return

    # Criar nome do arquivo baseado em ordens e pedidos agrupados
    nome_arquivo = _gerar_nome_arquivo_agrupado(ordens_e_pedidos)

    os.makedirs("logs/equipamentos", exist_ok=True)
    caminho = f"logs/equipamentos/{nome_arquivo}"

    # Escrever cabeçalho se arquivo não existir
    arquivo_novo = not os.path.exists(caminho)

    with open(caminho, "a", encoding="utf-8") as arq:
        if arquivo_novo:
            _escrever_cabecalho_agrupado(arq, ordens_e_pedidos, quantidade_total, detalhes_consolidacao)

        # Registrar cada equipamento utilizado
        for _, equipamento, inicio_eqp, fim_eqp in equipamentos_alocados:
            str_inicio = inicio_eqp.strftime('%H:%M') + f" [{inicio_eqp.strftime('%d/%m')}]"
            str_fim = fim_eqp.strftime('%H:%M') + f" [{fim_eqp.strftime('%d/%m')}]"

            # Se for lista, junta os nomes dos equipamentos
            if isinstance(equipamento, list):
                nomes_equipamentos = ', '.join(e.nome for e in equipamento)
            else:
                nomes_equipamentos = equipamento.nome

            # Formato: AGRUPADO | <id_atividade> | <nome_item> | <nome_atividade> | <equipamento> | <inicio> | <fim>
            linha = (
                f"AGRUPADO | "
                f"{id_atividade} | {nome_item} | {nome_atividade} | "
                f"{nomes_equipamentos} | {str_inicio} | {str_fim} \n"
            )
            arq.write(linha)

    logger.info(f"Log de subproduto agrupado registrado: {caminho}")

def _gerar_nome_arquivo_agrupado(ordens_e_pedidos: List[Dict[str, int]]) -> str:
    """
    Gera nome do arquivo baseado nas ordens e pedidos agrupados.
    Formato: agrupado_ordem_X_pedidos_Y_Z.log
    """
    # Extrair ordens únicas
    ordens = sorted(set(item['id_ordem'] for item in ordens_e_pedidos))

    # Extrair pedidos únicos
    pedidos = sorted(set(item['id_pedido'] for item in ordens_e_pedidos))

    # Gerar nome do arquivo
    if len(ordens) == 1:
        ordens_str = f"ordem_{ordens[0]}"
    else:
        ordens_str = f"ordens_{'+'.join(map(str, ordens))}"

    pedidos_str = '+'.join(map(str, pedidos))

    return f"agrupado_{ordens_str}_pedidos_{pedidos_str}.log"

def _escrever_cabecalho_agrupado(
    arquivo,
    ordens_e_pedidos: List[Dict[str, int]],
    quantidade_total: float,
    detalhes_consolidacao: Optional[Dict[str, Any]] = None
):
    """
    Escreve cabeçalho informativo no arquivo de log agrupado.
    """
    arquivo.write("=" * 80 + "\n")
    arquivo.write("LOG DE SUBPRODUTO AGRUPADO\n")
    arquivo.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    arquivo.write(f"Quantidade total consolidada: {quantidade_total}g\n")
    arquivo.write("-" * 80 + "\n")

    arquivo.write("Pedidos consolidados:\n")
    for item in ordens_e_pedidos:
        arquivo.write(f"  - Ordem: {item['id_ordem']} | Pedido: {item['id_pedido']}\n")

    if detalhes_consolidacao:
        arquivo.write("-" * 40 + "\n")
        arquivo.write("Detalhes da consolidação:\n")

        if 'economia_equipamentos' in detalhes_consolidacao:
            arquivo.write(f"  - Economia de equipamentos: {detalhes_consolidacao['economia_equipamentos']}\n")

        if 'tipo_consolidacao' in detalhes_consolidacao:
            arquivo.write(f"  - Tipo de consolidação: {detalhes_consolidacao['tipo_consolidacao']}\n")

        if 'motivo' in detalhes_consolidacao:
            arquivo.write(f"  - Motivo: {detalhes_consolidacao['motivo']}\n")

    arquivo.write("=" * 80 + "\n")
    arquivo.write("Estrutura: AGRUPADO | ID_ATIVIDADE | NOME_ITEM | NOME_ATIVIDADE | EQUIPAMENTO | INICIO | FIM\n")
    arquivo.write("-" * 80 + "\n")

def obter_logs_subprodutos_agrupados() -> List[str]:
    """
    Retorna lista de arquivos de log de subprodutos agrupados existentes.
    """
    pasta_logs = "logs/equipamentos"
    if not os.path.exists(pasta_logs):
        return []

    arquivos_agrupados = []
    for arquivo in os.listdir(pasta_logs):
        if arquivo.startswith("agrupado_") and arquivo.endswith(".log"):
            arquivos_agrupados.append(os.path.join(pasta_logs, arquivo))

    return sorted(arquivos_agrupados)

def limpar_logs_subprodutos_agrupados():
    """
    Remove todos os logs de subprodutos agrupados.
    """
    logs_agrupados = obter_logs_subprodutos_agrupados()
    removidos = 0

    for caminho in logs_agrupados:
        try:
            os.remove(caminho)
            removidos += 1
            logger.info(f"Log agrupado removido: {caminho}")
        except Exception as e:
            logger.error(f"Erro ao remover log agrupado {caminho}: {e}")

    logger.info(f"Total de {removidos} logs de subprodutos agrupados removidos")
    return removidos

def ler_detalhes_log_agrupado(caminho_arquivo: str) -> Optional[Dict[str, Any]]:
    """
    Lê e extrai detalhes de um arquivo de log agrupado.

    Returns:
        Dict com informações do log ou None se houver erro
    """
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            linhas = f.readlines()

        detalhes = {
            'caminho': caminho_arquivo,
            'nome_arquivo': os.path.basename(caminho_arquivo),
            'pedidos_consolidados': [],
            'atividades': [],
            'equipamentos_utilizados': set(),
            'quantidade_total': None,
            'data_execucao': None
        }

        # Extrair informações do cabeçalho
        for i, linha in enumerate(linhas):
            linha = linha.strip()

            if linha.startswith("Data/Hora:"):
                detalhes['data_execucao'] = linha.split("Data/Hora: ")[1]

            elif linha.startswith("Quantidade total consolidada:"):
                quantidade_str = linha.split("Quantidade total consolidada: ")[1].replace('g', '')
                try:
                    detalhes['quantidade_total'] = float(quantidade_str)
                except ValueError:
                    pass

            elif linha.startswith("  - Ordem:"):
                # Extrair ordem e pedido
                partes = linha.replace("  - Ordem: ", "").split(" | Pedido: ")
                if len(partes) == 2:
                    detalhes['pedidos_consolidados'].append({
                        'id_ordem': int(partes[0]),
                        'id_pedido': int(partes[1])
                    })

            elif linha.startswith("AGRUPADO |"):
                # Extrair informações da atividade
                partes = linha.split(" | ")
                if len(partes) >= 7:
                    atividade = {
                        'id_atividade': partes[1].strip(),
                        'nome_item': partes[2].strip(),
                        'nome_atividade': partes[3].strip(),
                        'equipamento': partes[4].strip(),
                        'inicio': partes[5].strip(),
                        'fim': partes[6].strip()
                    }
                    detalhes['atividades'].append(atividade)
                    detalhes['equipamentos_utilizados'].add(partes[4].strip())

        # Converter set para lista
        detalhes['equipamentos_utilizados'] = sorted(list(detalhes['equipamentos_utilizados']))

        return detalhes

    except Exception as e:
        logger.error(f"Erro ao ler log agrupado {caminho_arquivo}: {e}")
        return None

def gerar_relatorio_consolidacao() -> str:
    """
    Gera relatório resumido de todas as consolidações realizadas.
    """
    logs_agrupados = obter_logs_subprodutos_agrupados()

    if not logs_agrupados:
        return "📄 Nenhum log de consolidação encontrado."

    relatorio = ["📊 RELATÓRIO DE CONSOLIDAÇÕES REALIZADAS"]
    relatorio.append("=" * 60)

    total_consolidacoes = 0
    total_pedidos_afetados = 0
    equipamentos_utilizados = set()

    for caminho in logs_agrupados:
        detalhes = ler_detalhes_log_agrupado(caminho)
        if not detalhes:
            continue

        total_consolidacoes += 1
        total_pedidos_afetados += len(detalhes['pedidos_consolidados'])
        equipamentos_utilizados.update(detalhes['equipamentos_utilizados'])

        relatorio.append(f"\n🔗 {detalhes['nome_arquivo']}")
        relatorio.append(f"   Quantidade: {detalhes['quantidade_total']}g")
        relatorio.append(f"   Pedidos: {len(detalhes['pedidos_consolidados'])}")
        relatorio.append(f"   Equipamentos: {', '.join(detalhes['equipamentos_utilizados'])}")
        relatorio.append(f"   Data: {detalhes['data_execucao']}")

    relatorio.append("\n" + "=" * 60)
    relatorio.append(f"📈 RESUMO GERAL:")
    relatorio.append(f"   Total de consolidações: {total_consolidacoes}")
    relatorio.append(f"   Total de pedidos afetados: {total_pedidos_afetados}")
    relatorio.append(f"   Equipamentos únicos utilizados: {len(equipamentos_utilizados)}")
    relatorio.append(f"   Equipamentos: {', '.join(sorted(equipamentos_utilizados))}")

    return "\n".join(relatorio)