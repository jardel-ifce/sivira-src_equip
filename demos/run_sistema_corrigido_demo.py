import os, sys, json
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")

# ✅ IMPORTAÇÕES ADAPTADAS AO SISTEMA EXISTENTE
try:
    from otimizador.parser_json import carregar_por_ids
except ImportError:
    print("⚠️ Usando import alternativo para parser_json")
    from parser_json import carregar_por_ids

try:
    from otimizador.builder import montar_instancia
except ImportError:
    print("⚠️ builder.py precisa ser atualizado com as correções")
    sys.exit(1)

# ✅ IMPLEMENTAÇÃO INLINE DAS FUNÇÕES NECESSÁRIAS
def criar_config_simples():
    """Cria configuração básica sem depender de schema complexo"""
    class ConfigSimples:
        def __init__(self):
            self.inicio_hhmm = "06:00"
            self.fim_hhmm = "17:00"
            self.t_step_min = 2
    return ConfigSimples()

def expandir_atividade_simples(atividade_dados, duracao_total):
    """
    ✅ FUNÇÃO SIMPLIFICADA: Expande atividade em fases sem depender de classes complexas
    """
    tipos_equipamento = atividade_dados.get("tipo_equipamento", {})
    
    if not tipos_equipamento:
        # Atividade sem equipamento
        return [{
            "fase_id": 1,
            "nome": f"execucao_manual_{atividade_dados.get('nome', 'atividade')}",
            "tipo_equipamento": None,
            "equipamentos_elegiveis": [],
            "duracao_min": duracao_total,
            "sem_equipamento": True,
            "tipos_profissionais": atividade_dados.get("tipos_profissionais_permitidos", []),
            "quantidade_funcionarios": atividade_dados.get("quantidade_funcionarios", 0)
        }]
    
    # Atividade com equipamentos - criar fase para cada tipo
    fases = []
    num_tipos = len(tipos_equipamento)
    duracao_por_fase = duracao_total // num_tipos
    
    equipamentos_elegiveis = atividade_dados.get("equipamentos_elegiveis", [])
    
    for i, (tipo_nome, quantidade) in enumerate(tipos_equipamento.items(), 1):
        # Filtrar equipamentos por tipo
        equipamentos_tipo = filtrar_equipamentos_por_tipo(equipamentos_elegiveis, tipo_nome)
        
        fase = {
            "fase_id": i,
            "nome": f"{atividade_dados.get('nome', 'atividade')}_fase_{i}_{tipo_nome.lower()}",
            "tipo_equipamento": tipo_nome,
            "equipamentos_elegiveis": equipamentos_tipo,
            "duracao_min": duracao_por_fase,
            "sem_equipamento": False,
            "tipos_profissionais": atividade_dados.get("tipos_profissionais_permitidos", []),
            "quantidade_funcionarios": atividade_dados.get("quantidade_funcionarios", 0),
            "configuracoes": atividade_dados.get("configuracoes_equipamentos", {})
        }
        fases.append(fase)
        
        print(f"  ✅ Fase {i}: {tipo_nome} com {len(equipamentos_tipo)} equipamentos ({duracao_por_fase} min)")
    
    return fases

def filtrar_equipamentos_por_tipo(equipamentos_elegiveis, tipo_nome):
    """Filtra equipamentos por tipo baseado em prefixos"""
    mapeamento = {
        "BALANCAS": ["balanca_"],
        "BANCADAS": ["bancada_"],
        "FORNOS": ["forno_"],
        "ARMARIOS_PARA_FERMENTACAO": ["armario_fermentador_"],
        "MISTURADORAS": ["masseira_"],
        "DIVISORAS_BOLEADORAS": ["divisora_"],
        "MODELADORAS": ["modeladora_"],
        "EMBALADORAS": ["embaladora_"],
    }
    
    prefixos = mapeamento.get(tipo_nome, [])
    
    resultado = []
    for equipamento in equipamentos_elegiveis:
        for prefixo in prefixos:
            if equipamento.startswith(prefixo):
                resultado.append(equipamento)
                break
    
    return resultado

def processar_atividades_com_fases(problema, pedidos):
    """
    ✅ FUNÇÃO PRINCIPAL: Processa atividades e expande em fases
    """
    print("\n🔄 Expandindo atividades em fases...")
    
    atividades_expandidas = []
    todas_fases = []
    
    for ped in pedidos:
        pid = ped["id_pedido"]
        iid = ped["id_item"]
        qtd = ped.get("quantidade_unidades", 0)
        
        # Buscar item
        item = None
        for it in problema.itens:
            if it.id_item == iid:
                item = it
                break
        
        if not item:
            print(f"⚠️ Item {iid} não encontrado")
            continue
        
        print(f"\n📋 Processando pedido {pid} - item {iid} ({qtd} unidades)")
        
        for atividade in item.atividades:
            # Calcular duração total
            duracao_total = calcular_duracao_simples(atividade.faixas, qtd)
            
            # Dados da atividade para processamento
            atividade_dados = {
                "nome": atividade.nome,
                "tipo_equipamento": atividade.tipo_equipamento,
                "equipamentos_elegiveis": atividade.equipamentos_elegiveis,
                "tipos_profissionais_permitidos": atividade.tipos_profissionais_permitidos,
                "quantidade_funcionarios": atividade.quantidade_funcionarios,
                "configuracoes_equipamentos": atividade.configuracoes_equipamentos
            }
            
            # Expandir em fases
            fases = expandir_atividade_simples(atividade_dados, duracao_total)
            
            # Criar atividade expandida
            atividade_expandida = {
                "id_atividade": atividade.id_atividade,
                "id_pedido": pid,
                "id_item": iid,
                "nome": atividade.nome,
                "duracao_total": duracao_total,
                "fases": fases,
                "chave": f"ped{pid}-{atividade.id_atividade}"
            }
            
            atividades_expandidas.append(atividade_expandida)
            
            # Adicionar fases à lista global
            for fase in fases:
                fase_expandida = fase.copy()
                fase_expandida["chave_atividade"] = atividade_expandida["chave"]
                fase_expandida["chave_fase"] = f"{atividade_expandida['chave']}-fase{fase['fase_id']}"
                fase_expandida["id_pedido"] = pid
                fase_expandida["id_atividade"] = atividade.id_atividade
                todas_fases.append(fase_expandida)
            
            print(f"  🔧 Atividade {atividade.id_atividade}: {len(fases)} fases, {duracao_total} min total")
    
    return atividades_expandidas, todas_fases

def calcular_duracao_simples(faixas, quantidade):
    """Calcula duração baseada nas faixas"""
    if not faixas:
        return 30  # Default 30 minutos
    
    for faixa in faixas:
        if faixa.quantidade_min <= quantidade <= faixa.quantidade_max:
            # Parse simples de HH:MM:SS
            partes = faixa.duracao_str.split(":")
            if len(partes) >= 2:
                horas = int(partes[0])
                minutos = int(partes[1])
                return horas * 60 + minutos
    
    # Usar última faixa como fallback
    if faixas:
        partes = faixas[-1].duracao_str.split(":")
        if len(partes) >= 2:
            horas = int(partes[0])
            minutos = int(partes[1])
            return horas * 60 + minutos
    
    return 30

def gerar_logs_das_fases(fases_alocadas, nomes_itens):
    """
    ✅ GERADOR DE LOGS SIMPLIFICADO
    """
    logs_por_pedido = {}
    
    for fase in fases_alocadas:
        if not fase.get("alocada", False):
            continue
            
        pedido_id = fase["id_pedido"]
        id_atividade = fase["id_atividade"]
        
        # Nome do item
        nome_item = nomes_itens.get(fase.get("id_item", 0), "item_desconhecido")
        
        # Nome do equipamento
        recurso = fase.get("recurso_alocado", "")
        if not recurso and fase.get("sem_equipamento"):
            nome_recurso = "—"
        else:
            nome_recurso = converter_nome_equipamento(recurso)
        
        # Horários
        inicio_str = fase.get("inicio", "06:00")
        fim_str = fase.get("fim", "06:30")
        
        # Linha do log
        linha = (
            f"1 | {pedido_id} | {id_atividade} | {nome_item} | {fase['nome']} | "
            f"{nome_recurso} | {inicio_str} [26/06] | {fim_str} [26/06]"
        )
        
        if pedido_id not in logs_por_pedido:
            logs_por_pedido[pedido_id] = []
        
        logs_por_pedido[pedido_id].append(linha)
    
    return logs_por_pedido

def converter_nome_equipamento(recurso_id):
    """Converte ID para nome legível"""
    if not recurso_id:
        return "—"
    
    mapeamento = {
        "forno_1": "Forno 1",
        "forno_2": "Forno 2",
        "bancada_1": "Bancada 1", 
        "bancada_2": "Bancada 2",
        "bancada_3": "Bancada 3",
        "balanca_digital_1": "Balança Digital 1",
        "armario_fermentador_1": "Armário Fermentador 1",
        "armario_fermentador_2": "Armário Fermentador 2",
        "armario_fermentador_3": "Armário Fermentador 3",
        "armario_fermentador_4": "Armário Fermentador 4",
        "masseira_1": "Masseira 1",
        "masseira_2": "Masseira 2",
        "divisora_de_massas_1": "Divisoras de Massas 1",
        "divisora_de_massas_2": "Divisoras de Massas 2",
        "modeladora_de_paes_1": "Modeladora de Pães 1",
        "embaladora_1": "Embaladora 1",
    }
    
    return mapeamento.get(recurso_id, recurso_id)

def simular_alocacao_basica(fases):
    """
    ✅ SIMULAÇÃO BÁSICA: Aloca fases sequencialmente para demonstrar o conceito
    (Para teste até o MILP ser implementado)
    """
    print("\n🔄 Simulando alocação básica de fases...")
    
    # Horário atual
    minuto_atual = 6 * 60  # 06:00 em minutos
    
    fases_alocadas = []
    
    for fase in fases:
        # Simular alocação
        inicio_min = minuto_atual
        fim_min = inicio_min + fase["duracao_min"]
        
        # Converter para HH:MM
        inicio_h, inicio_m = inicio_min // 60, inicio_min % 60
        fim_h, fim_m = fim_min // 60, fim_min % 60
        
        fase_alocada = fase.copy()
        fase_alocada["alocada"] = True
        fase_alocada["inicio"] = f"{inicio_h:02d}:{inicio_m:02d}"
        fase_alocada["fim"] = f"{fim_h:02d}:{fim_m:02d}"
        
        # Simular escolha de equipamento
        if fase["equipamentos_elegiveis"]:
            fase_alocada["recurso_alocado"] = fase["equipamentos_elegiveis"][0]
        else:
            fase_alocada["recurso_alocado"] = ""
            
        fases_alocadas.append(fase_alocada)
        
        # Avançar tempo
        minuto_atual = fim_min
        
        print(f"  ✅ {fase['nome']}: {fase_alocada['inicio']}-{fase_alocada['fim']} ({fase_alocada.get('recurso_alocado', '—')})")
    
    return fases_alocadas

def main():
    print("🚀 DEMO DO SISTEMA CORRIGIDO (VERSÃO ADAPTADA)")
    print("="*80)
    
    # =============================================================================
    #                           CONFIGURAÇÃO
    # =============================================================================
    
    ROOT = os.environ.get("SIVIRA_ROOT", "/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")
    IDS = os.environ.get("ITEM_IDS", "1001,2001")
    
    print(f"📁 ROOT = {ROOT}")
    print(f"🆔 ITEM_IDS = {IDS}")
    
    ids = [int(x.strip()) for x in IDS.split(",") if x.strip()]
    
    # Capacidades
    capacidades = {
        "forno_1": 3, "forno_2": 3,
        "armario_fermentador_1": 6, "armario_fermentador_2": 6, 
        "armario_fermentador_3": 6, "armario_fermentador_4": 6,
        "bancada_1": 4, "bancada_2": 4, "bancada_3": 4,
        "balanca_digital_1": 2,
        "modeladora_de_paes_1": 1,
        "divisora_de_massas_1": 1, "divisora_de_massas_2": 1,
        "masseira_1": 1, "masseira_2": 1,
        "embaladora_1": 1,
        "PADEIRO": 3, "AUXILIAR_DE_PADEIRO": 2,
    }
    
    nomes_itens = {
        1001: "pao_frances",
        2001: "massa_crocante"
    }
    
    # Pedidos de teste
    pedidos = [
        {"id_pedido": 1, "id_item": 1001, "quantidade_unidades": 240, "release": "06:00", "deadline": "09:00"},
        {"id_pedido": 3, "id_item": 2001, "quantidade_unidades": 15000, "release": "06:00", "deadline": "12:00"},
    ]
    
    # =============================================================================
    #                          CARREGAMENTO DOS DADOS
    # =============================================================================
    
    print("\n🔄 ETAPA 1: Carregando dados...")
    try:
        cfg = criar_config_simples()
        problema = carregar_por_ids(
            root=ROOT, 
            ids=ids, 
            recursos_capacidades=capacidades, 
            config=cfg
        )
        print(f"✅ Dados carregados: {len(problema.itens)} itens")
    except Exception as e:
        print(f"❌ Erro no carregamento: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # =============================================================================
    #                          EXPANSÃO EM FASES
    # =============================================================================
    
    print("\n🔄 ETAPA 2: Expandindo atividades em fases...")
    try:
        atividades_expandidas, todas_fases = processar_atividades_com_fases(problema, pedidos)
        
        print(f"\n✅ RESULTADO DA EXPANSÃO:")
        print(f"   • Atividades processadas: {len(atividades_expandidas)}")
        print(f"   • Total de fases: {len(todas_fases)}")
        
        # Mostrar detalhes
        for atividade in atividades_expandidas:
            tipos = [f["tipo_equipamento"] or "SEM_EQUIP" for f in atividade["fases"]]
            print(f"   • {atividade['chave']}: {len(atividade['fases'])} fases ({', '.join(tipos)})")
            
    except Exception as e:
        print(f"❌ Erro na expansão: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # =============================================================================
    #                          SIMULAÇÃO DE ALOCAÇÃO
    # =============================================================================
    
    print("\n🔄 ETAPA 3: Simulando alocação de fases...")
    try:
        fases_alocadas = simular_alocacao_basica(todas_fases)
        print(f"✅ {len(fases_alocadas)} fases alocadas na simulação")
        
    except Exception as e:
        print(f"❌ Erro na simulação: {e}")
        return
    
    # =============================================================================
    #                          GERAÇÃO DE LOGS
    # =============================================================================
    
    print("\n🔄 ETAPA 4: Gerando logs das fases...")
    try:
        logs_por_pedido = gerar_logs_das_fases(fases_alocadas, nomes_itens)
        
        # Escrever arquivos
        for pedido_id, linhas in logs_por_pedido.items():
            nome_arquivo = f"ordem: 1 | pedido: {pedido_id}.log"
            with open(nome_arquivo, "w", encoding="utf-8") as f:
                for linha in linhas:
                    f.write(linha + "\n")
            
            print(f"✅ {nome_arquivo} criado com {len(linhas)} linhas")
            
            # Mostrar exemplo
            print(f"   📋 Exemplo:")
            for linha in linhas[:2]:
                print(f"      {linha}")
            if len(linhas) > 2:
                print(f"      ... e mais {len(linhas) - 2} linhas")
                
    except Exception as e:
        print(f"❌ Erro na geração de logs: {e}")
        return
    
    # =============================================================================
    #                              RESUMO
    # =============================================================================
    
    print("\n" + "="*80)
    print("🎉 DEMO ADAPTADO CONCLUÍDO!")
    print("="*80)
    print("✅ Sistema demonstrou a expansão de atividades em fases")
    print("✅ Cada atividade agora produz múltiplas linhas de log")
    print("✅ Fases sem equipamento aparecem com recurso '—'")
    print("✅ Próximo passo: implementar MILP para alocação real")
    print("="*80)

if __name__ == "__main__":
    main()