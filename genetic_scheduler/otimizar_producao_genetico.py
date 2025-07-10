

class GeneticScheduler:
    def __init__(self, pedidos: List[PedidoDeProducao], config: ConfiguracaoGA = None):
        self.pedidos = pedidos
        self.config = config or ConfiguracaoGA()
        self.atividades = self._extrair_atividades()
        self.melhor_solucao = None
        self.historico_fitness = []
        
        # Pesos para função multi-objetivo
        self.pesos = {
            'makespan': 0.4,
            'utilizacao': 0.3,
            'atraso': 0.2,
            'viabilidade': 0.1
        }
        
        logger.info(f"Inicializando GA com {len(self.atividades)} atividades")

    def _extrair_atividades(self) -> List[AtividadeModular]:
        """Extrai todas as atividades de todos os pedidos"""
        atividades = []
        for pedido in self.pedidos:
            pedido.criar_atividades_modulares_necessarias()
            atividades.extend(pedido.atividades_modulares)
        return atividades

    def gerar_cromossomo_inicial(self) -> List[int]:
        """Gera cromossomo inicial respeitando precedências"""
        cromossomo = []
        atividades_por_pedido = {}
        
        # Agrupa atividades por pedido
        for i, atividade in enumerate(self.atividades):
            pedido_id = atividade.pedido_id
            if pedido_id not in atividades_por_pedido:
                atividades_por_pedido[pedido_id] = []
            atividades_por_pedido[pedido_id].append(i)
        
        # Gera ordem respeitando precedências dentro de cada pedido
        for pedido_id, indices in atividades_por_pedido.items():
            # Ordena por tipo (PRODUTO depois SUBPRODUTO) e ID da atividade
            indices_ordenados = sorted(indices, key=lambda i: (
                self.atividades[i].tipo_item.value,
                -self.atividades[i].id_atividade
            ))
            cromossomo.extend(indices_ordenados)
        
        return cromossomo

    def gerar_populacao_inicial(self) -> List[List[int]]:
        """Gera população inicial diversificada"""
        populacao = []
        
        # 30% soluções gulosas (respeitando precedências)
        for _ in range(int(self.config.tamanho_populacao * 0.3)):
            cromossomo = self.gerar_cromossomo_inicial()
            populacao.append(cromossomo)
        
        # 40% soluções semi-aleatórias
        for _ in range(int(self.config.tamanho_populacao * 0.4)):
            cromossomo = self.gerar_cromossomo_inicial()
            # Aplica perturbação limitada
            self._mutacao_scramble(cromossomo, intensidade=0.3)
            populacao.append(cromossomo)
        
        # 30% soluções completamente aleatórias (que respeitem precedências)
        for _ in range(self.config.tamanho_populacao - len(populacao)):
            cromossomo = self.gerar_cromossomo_inicial()
            random.shuffle(cromossomo)
            cromossomo = self._reparar_precedencias(cromossomo)
            populacao.append(cromossomo)
        
        return populacao

    def _reparar_precedencias(self, cromossomo: List[int]) -> List[int]:
        """Repara cromossomo para respeitar precedências"""
        cromossomo_reparado = []
        atividades_por_pedido = {}
        
        # Agrupa por pedido
        for gene in cromossomo:
            atividade = self.atividades[gene]
            pedido_id = atividade.pedido_id
            if pedido_id not in atividades_por_pedido:
                atividades_por_pedido[pedido_id] = []
            atividades_por_pedido[pedido_id].append(gene)
        
        # Ordena cada pedido respeitando precedências
        for pedido_id, genes in atividades_por_pedido.items():
            genes_ordenados = sorted(genes, key=lambda g: (
                self.atividades[g].tipo_item.value,
                -self.atividades[g].id_atividade
            ))
            cromossomo_reparado.extend(genes_ordenados)
        
        return cromossomo_reparado

    def avaliar_fitness(self, cromossomo: List[int]) -> IndividuoResultado:
        """Avalia fitness de um cromossomo simulando execução"""
        try:
            # Simula execução do cronograma
            resultado_simulacao = self._simular_execucao(cromossomo)
            
            # Calcula métricas
            makespan = resultado_simulacao['makespan']
            utilizacao = resultado_simulacao['utilizacao_equipamentos']
            atraso_total = resultado_simulacao['atraso_total']
            viabilidade = resultado_simulacao['viabilidade']
            
            # Função de fitness multi-objetivo (minimização)
            fitness = (
                self.pesos['makespan'] * makespan.total_seconds() / 3600 +  # horas
                self.pesos['utilizacao'] * (1 - utilizacao) +  # maximizar utilização
                self.pesos['atraso'] * atraso_total.total_seconds() / 3600 +  # horas
                self.pesos['viabilidade'] * (0 if viabilidade else 1000)  # penalidade
            )
            
            return IndividuoResultado(
                cromossomo=cromossomo,
                fitness=fitness,
                makespan=makespan,
                utilizacao_equipamentos=utilizacao,
                atraso_total=atraso_total,
                viabilidade=viabilidade,
                detalhes=resultado_simulacao
            )
            
        except Exception as e:
            logger.error(f"Erro ao avaliar fitness: {e}")
            return IndividuoResultado(
                cromossomo=cromossomo,
                fitness=float('inf'),
                makespan=timedelta(hours=24),
                utilizacao_equipamentos=0.0,
                atraso_total=timedelta(hours=24),
                viabilidade=False,
                detalhes={}
            )

    def _simular_execucao(self, cromossomo: List[int]) -> Dict:
        """Simula execução do cronograma representado pelo cromossomo"""
        # Cria cópia dos equipamentos e funcionários para simulação
        equipamentos_simulacao = self._criar_copia_equipamentos()
        funcionarios_simulacao = self._criar_copia_funcionarios()
        
        tempo_inicio = min(p.inicio_jornada for p in self.pedidos)
        tempo_fim = max(p.fim_jornada for p in self.pedidos)
        
        alocacoes_realizadas = []
        tempo_total_equipamentos = timedelta()
        tempo_utilizado_equipamentos = timedelta()
        atraso_total = timedelta()
        
        for gene in cromossomo:
            atividade = self.atividades[gene]
            
            # Simula alocação da atividade
            sucesso, inicio_real, fim_real = self._simular_alocacao_atividade(
                atividade, equipamentos_simulacao, funcionarios_simulacao,
                tempo_inicio, tempo_fim
            )
            
            if sucesso:
                alocacoes_realizadas.append({
                    'atividade': atividade,
                    'inicio': inicio_real,
                    'fim': fim_real
                })
                tempo_utilizado_equipamentos += (fim_real - inicio_real)
            else:
                # Atividade não pode ser alocada
                atraso_total += atividade.duracao
        
        # Calcula métricas
        makespan = max(a['fim'] for a in alocacoes_realizadas) - tempo_inicio if alocacoes_realizadas else timedelta()
        tempo_total_equipamentos = (tempo_fim - tempo_inicio) * len(equipamentos_simulacao)
        utilizacao = tempo_utilizado_equipamentos / tempo_total_equipamentos if tempo_total_equipamentos > timedelta() else 0
        viabilidade = len(alocacoes_realizadas) == len(cromossomo)
        
        return {
            'makespan': makespan,
            'utilizacao_equipamentos': utilizacao,
            'atraso_total': atraso_total,
            'viabilidade': viabilidade,
            'alocacoes': alocacoes_realizadas
        }

    def _simular_alocacao_atividade(self, atividade, equipamentos, funcionarios, 
                                   tempo_inicio, tempo_fim) -> Tuple[bool, datetime, datetime]:
        """Simula alocação de uma atividade específica"""
        # Simplificação: tenta alocar no primeiro horário disponível
        horario_tentativa = tempo_fim - atividade.duracao
        
        while horario_tentativa >= tempo_inicio:
            # Verifica se equipamentos estão disponíveis
            equipamentos_disponiveis = self._verificar_disponibilidade_equipamentos(
                atividade, equipamentos, horario_tentativa, horario_tentativa + atividade.duracao
            )
            
            # Verifica se funcionários estão disponíveis
            funcionarios_disponiveis = self._verificar_disponibilidade_funcionarios(
                atividade, funcionarios, horario_tentativa, horario_tentativa + atividade.duracao
            )
            
            if equipamentos_disponiveis and funcionarios_disponiveis:
                # Aloca recursos
                self._alocar_recursos_simulacao(
                    atividade, equipamentos, funcionarios,
                    horario_tentativa, horario_tentativa + atividade.duracao
                )
                return True, horario_tentativa, horario_tentativa + atividade.duracao
            
            horario_tentativa -= timedelta(minutes=15)  # Incremento de busca
        
        return False, None, None

    def _verificar_disponibilidade_equipamentos(self, atividade, equipamentos, inicio, fim) -> bool:
        """Verifica se equipamentos necessários estão disponíveis"""
        # Implementação simplificada
        return True  # Assume disponibilidade para simulação rápida

    def _verificar_disponibilidade_funcionarios(self, atividade, funcionarios, inicio, fim) -> bool:
        """Verifica se funcionários necessários estão disponíveis"""
        # Implementação simplificada
        return True  # Assume disponibilidade para simulação rápida

    def _alocar_recursos_simulacao(self, atividade, equipamentos, funcionarios, inicio, fim):
        """Aloca recursos na simulação"""
        # Implementação simplificada - marca recursos como ocupados
        pass

    def _criar_copia_equipamentos(self):
        """Cria cópia dos equipamentos para simulação"""
        # Implementação simplificada
        return {}

    def _criar_copia_funcionarios(self):
        """Cria cópia dos funcionários para simulação"""
        # Implementação simplificada
        return {}

    def selecao_torneio(self, populacao_fitness: List[IndividuoResultado]) -> IndividuoResultado:
        """Seleção por torneio"""
        torneio = random.sample(populacao_fitness, min(self.config.pressao_selecao, len(populacao_fitness)))
        return min(torneio, key=lambda x: x.fitness)

    def cruzamento_ox(self, pai1: List[int], pai2: List[int]) -> Tuple[List[int], List[int]]:
        """Cruzamento Order Crossover (OX) - preserva ordem relativa"""
        tamanho = len(pai1)
        
        # Seleciona segmento aleatório
        start, end = sorted(random.sample(range(tamanho), 2))
        
        # Cria filhos
        filho1 = [-1] * tamanho
        filho2 = [-1] * tamanho
        
        # Copia segmento dos pais
        filho1[start:end] = pai1[start:end]
        filho2[start:end] = pai2[start:end]
        
        # Preenche o restante mantendo ordem
        self._preencher_ox(filho1, pai2, start, end)
        self._preencher_ox(filho2, pai1, start, end)
        
        # Repara precedências
        filho1 = self._reparar_precedencias(filho1)
        filho2 = self._reparar_precedencias(filho2)
        
        return filho1, filho2

    def _preencher_ox(self, filho: List[int], pai: List[int], start: int, end: int):
        """Preenche filho no cruzamento OX"""
        genes_usados = set(filho[start:end])
        posicao = end
        
        for gene in pai[end:] + pai[:end]:
            if gene not in genes_usados:
                filho[posicao % len(filho)] = gene
                posicao += 1

    def mutacao_adaptativa(self, cromossomo: List[int], geracao: int) -> List[int]:
        """Mutação adaptativa - intensidade diminui com gerações"""
        if random.random() > self.config.taxa_mutacao:
            return cromossomo
        
        # Taxa de mutação adaptativa
        taxa_adaptativa = self.config.taxa_mutacao * (1 - geracao / self.config.numero_geracoes)
        
        cromossomo_mutado = cromossomo.copy()
        
        # Escolhe tipo de mutação aleatoriamente
        tipo_mutacao = random.choice(list(TipoMutacao))
        
        if tipo_mutacao == TipoMutacao.SWAP:
            self._mutacao_swap(cromossomo_mutado)
        elif tipo_mutacao == TipoMutacao.INSERT:
            self._mutacao_insert(cromossomo_mutado)
        elif tipo_mutacao == TipoMutacao.INVERT:
            self._mutacao_invert(cromossomo_mutado)
        elif tipo_mutacao == TipoMutacao.SCRAMBLE:
            self._mutacao_scramble(cromossomo_mutado, taxa_adaptativa)
        
        return self._reparar_precedencias(cromossomo_mutado)

    def _mutacao_swap(self, cromossomo: List[int]):
        """Mutação por troca de genes"""
        if len(cromossomo) > 1:
            i, j = random.sample(range(len(cromossomo)), 2)
            cromossomo[i], cromossomo[j] = cromossomo[j], cromossomo[i]

    def _mutacao_insert(self, cromossomo: List[int]):
        """Mutação por inserção"""
        if len(cromossomo) > 1:
            i = random.randint(0, len(cromossomo) - 1)
            j = random.randint(0, len(cromossomo) - 1)
            gene = cromossomo.pop(i)
            cromossomo.insert(j, gene)

    def _mutacao_invert(self, cromossomo: List[int]):
        """Mutação por inversão de segmento"""
        if len(cromossomo) > 1:
            start, end = sorted(random.sample(range(len(cromossomo)), 2))
            cromossomo[start:end] = reversed(cromossomo[start:end])

    def _mutacao_scramble(self, cromossomo: List[int], intensidade: float = 0.1):
        """Mutação por embaralhamento parcial"""
        num_genes = int(len(cromossomo) * intensidade)
        if num_genes > 1:
            indices = random.sample(range(len(cromossomo)), num_genes)
            genes = [cromossomo[i] for i in indices]
            random.shuffle(genes)
            for i, gene in zip(indices, genes):
                cromossomo[i] = gene

    def evolucao(self) -> IndividuoResultado:
        """Executa algoritmo genético completo"""
        logger.info("Iniciando evolução do algoritmo genético")
        
        # Gera população inicial
        populacao = self.gerar_populacao_inicial()
        
        # Avalia população inicial
        populacao_fitness = [self.avaliar_fitness(cromossomo) for cromossomo in populacao]
        
        melhor_global = min(populacao_fitness, key=lambda x: x.fitness)
        geracoes_sem_melhoria = 0
        
        for geracao in range(self.config.numero_geracoes):
            # Elitismo - mantém os melhores
            populacao_fitness.sort(key=lambda x: x.fitness)
            num_elite = int(self.config.tamanho_populacao * self.config.taxa_elitismo)
            nova_populacao = [ind.cromossomo for ind in populacao_fitness[:num_elite]]
            
            # Gera nova população
            while len(nova_populacao) < self.config.tamanho_populacao:
                if random.random() < self.config.taxa_cruzamento:
                    # Cruzamento
                    pai1 = self.selecao_torneio(populacao_fitness)
                    pai2 = self.selecao_torneio(populacao_fitness)
                    filho1, filho2 = self.cruzamento_ox(pai1.cromossomo, pai2.cromossomo)
                    nova_populacao.extend([filho1, filho2])
                else:
                    # Reprodução
                    pai = self.selecao_torneio(populacao_fitness)
                    nova_populacao.append(pai.cromossomo.copy())
            
            # Mutação
            nova_populacao = [
                self.mutacao_adaptativa(cromossomo, geracao) 
                for cromossomo in nova_populacao[:self.config.tamanho_populacao]
            ]
            
            # Avalia nova população
            populacao_fitness = [self.avaliar_fitness(cromossomo) for cromossomo in nova_populacao]
            
            # Atualiza melhor solução
            melhor_atual = min(populacao_fitness, key=lambda x: x.fitness)
            if melhor_atual.fitness < melhor_global.fitness:
                melhor_global = melhor_atual
                geracoes_sem_melhoria = 0
                logger.info(f"Geração {geracao}: Nova melhor solução - Fitness: {melhor_atual.fitness:.2f}")
            else:
                geracoes_sem_melhoria += 1
            
            # Registra histórico
            self.historico_fitness.append(melhor_atual.fitness)
            
            # Critério de parada por convergência
            if geracoes_sem_melhoria >= self.config.convergencia_limite:
                logger.info(f"Convergência atingida na geração {geracao}")
                break
            
            # Log periódico
            if geracao % 50 == 0:
                logger.info(f"Geração {geracao}: Melhor fitness = {melhor_atual.fitness:.2f}")
        
        self.melhor_solucao = melhor_global
        logger.info(f"Evolução concluída. Melhor fitness: {melhor_global.fitness:.2f}")
        return melhor_global

    def aplicar_melhor_solucao(self) -> bool:
        """Aplica a melhor solução encontrada aos pedidos reais"""
        if not self.melhor_solucao:
            logger.error("Nenhuma solução disponível para aplicar")
            return False
        
        try:
            # Executa cronograma na ordem otimizada
            for gene in self.melhor_solucao.cromossomo:
                atividade = self.atividades[gene]
                # Aplica alocação real usando o método original
                sucesso, inicio, fim, tempo_espera, equipamentos = atividade.tentar_alocar_e_iniciar_equipamentos(
                    atividade.pedido.inicio_jornada,
                    atividade.pedido.fim_jornada
                )
                
                if not sucesso:
                    logger.warning(f"Falha ao aplicar solução na atividade {atividade.id_atividade}")
                    return False
            
            logger.info("Melhor solução aplicada com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao aplicar melhor solução: {e}")
            return False

    def relatorio_otimizacao(self) -> Dict:
        """Gera relatório da otimização"""
        if not self.melhor_solucao:
            return {"erro": "Nenhuma solução disponível"}
        
        return {
            "fitness_final": self.melhor_solucao.fitness,
            "makespan": str(self.melhor_solucao.makespan),
            "utilizacao_equipamentos": f"{self.melhor_solucao.utilizacao_equipamentos:.2%}",
            "atraso_total": str(self.melhor_solucao.atraso_total),
            "viabilidade": self.melhor_solucao.viabilidade,
            "cromossomo_otimo": self.melhor_solucao.cromossomo,
            "ordem_atividades": [
                f"Atividade {self.atividades[gene].id_atividade} (Pedido {self.atividades[gene].pedido_id})"
                for gene in self.melhor_solucao.cromossomo
            ],
            "configuracao": {
                "populacao": self.config.tamanho_populacao,
                "geracoes": self.config.numero_geracoes,
                "taxa_cruzamento": self.config.taxa_cruzamento,
                "taxa_mutacao": self.config.taxa_mutacao
            }
        }
