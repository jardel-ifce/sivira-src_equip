# Por Que Algoritmos Gulosos Superam Programação Linear em Sistemas de Produção Reais

**Autor:** Claude (Anthropic)
**Sistema:** SIVIRA - Sistema Inteligente para Visualização e Replanejamento de Atividades
**Data:** 14 de Novembro de 2025

---

## Introdução

A otimização de processos produtivos em ambientes industriais representa um desafio clássico da pesquisa operacional. Intuitivamente, modelos matemáticos rigorosos baseados em Programação Linear (PL) deveriam superar heurísticas simples como algoritmos gulosos. Este trabalho apresenta evidências empíricas que contradizem essa intuição, demonstrando como um método sequencial guloso alcançou taxa de sucesso de 84,6% enquanto um otimizador baseado em PL falhou em 69,2% dos casos, apesar de encontrar soluções matematicamente "ótimas".

A análise foi conduzida no contexto do SIVIRA, um sistema de agendamento para produção de panificação e confeitaria, utilizando um conjunto de 13 pedidos reais com características complexas: restrições temporais rígidas, recursos compartilhados limitados e dependências entre atividades. Os resultados revelam que a eficácia de técnicas de otimização depende criticamente da completude da modelagem matemática e que abstrações inadequadas podem tornar soluções "ótimas" completamente infactíveis.

---

## O Problema: Job Shop Scheduling em Produção de Alimentos

O problema de agendamento estudado pertence à classe NP-difícil conhecida como Job Shop Scheduling Problem (JSSP), estendido com restrições específicas do domínio de produção alimentícia. Cada pedido consiste em uma sequência de atividades com dependências de precedência, durações variáveis baseadas em quantidade e requisitos de equipamentos específicos.

A complexidade do problema é amplificada por três fatores críticos. Primeiro, restrições de gap temporal: algumas atividades possuem `tempo_maximo_de_espera` igual a zero, significando que processos sucessivos devem iniciar imediatamente após o término do anterior. Esta restrição é comum em processos que envolvem massas frescas ou produtos perecíveis, onde atrasos podem comprometer a qualidade. Segundo, recursos únicos e compartilhados: equipamentos como fritadeiras e fornos existem em quantidade limitada (algumas vezes única) e devem ser compartilhados entre múltiplos pedidos concorrentes. Terceiro, interdependências em cascata: produtos finais dependem de subprodutos que, por sua vez, requerem preparação prévia, criando árvores de dependências que devem ser respeitadas.

O dataset experimental consistiu em 13 pedidos com dois grupos de deadlines distintos: cinco pedidos com prazo às 07:00 e oito pedidos com prazo às 08:00. Do total, seis pedidos (46,2%) continham atividades com restrições de gap zero, representando casos críticos onde flexibilidade temporal é inexistente.

---

## Metodologia Comparativa

Dois métodos foram implementados e comparados sob condições controladas: execução sequencial com backward scheduling guloso e otimização via Programação Linear com OR-Tools. Ambos processaram o mesmo conjunto de entrada e foram avaliados quanto a taxa de atendimento, makespan, utilização de recursos e tempo computacional.

O método sequencial implementa uma estratégia gulosa de alocação reversa. Os pedidos são ordenados por deadline (Earliest Deadline First) e processados sequencialmente. Para cada pedido, as atividades são ordenadas topologicamente em ordem reversa, iniciando pela atividade final que deve terminar no deadline. A alocação procede de trás para frente: para cada atividade, o sistema busca no pool de equipamentos disponíveis aqueles que possuem janela de tempo livre suficiente antes do horário de referência. Se encontrado, o equipamento é imediatamente reservado e o horário de referência é atualizado para o início dessa atividade. Este processo continua até a primeira atividade ou até detectar impossibilidade de alocação.

O método baseado em PL segue um pipeline em três fases. Na fase de extração, todos os dados de pedidos são convertidos em estruturas matemáticas: duração de atividades, dependências de precedência, requisitos de equipamentos e restrições temporais. Na fase de modelagem, cria-se uma formulação de programação linear inteira mista onde variáveis binárias indicam a seleção de janelas temporais para cada atividade, e a função objetivo minimiza o makespan total. O solver OR-Tools (SCIP/CBC) é então invocado com timeout de 600 segundos. Na fase de execução, pedidos selecionados pelo otimizador são executados primeiro, seguidos por execução sequencial dos pedidos não selecionados como estratégia de fallback.

| Métrica | Método Sequencial | Método PL | Interpretação |
|---------|-------------------|-----------|---------------|
| **Taxa de Sucesso** | **84,6%** (11/13) | **30,8%** (4/13) | PL falhou em 69% dos casos |
| **Makespan** | 1.753 min (11 pedidos) | 383 min (4 pedidos) | ❌ **Incomparável** - cargas diferentes |
| **Tempo de Execução** | 0,42s | 0,51s | PL 21% mais lento |

**Nota Crítica:** O makespan do método PL é menor apenas porque executou 64% menos pedidos (4 vs 11). Esta métrica **não indica superioridade**, apenas que menos trabalho foi realizado. O makespan maior do método sequencial é **esperado e natural** ao processar 2,75× mais pedidos com sucesso.

---

## Resultados: O Paradoxo da Otimalidade

Os resultados experimentais revelam um paradoxo aparente: o método PL encontrou uma solução declarada "OPTIMAL" pelo solver, mas falhou em executar 69% dos pedidos (apenas 4 de 13 completados). Em contraste, o método sequencial executou com sucesso 11 dos 13 pedidos (84,6% de taxa de atendimento). O makespan do método sequencial (1.753 minutos) é naturalmente maior que o do PL (383 minutos), pois processa 2,75 vezes mais pedidos - esta diferença não indica ineficiência, mas sim maior capacidade de entrega.

A análise detalhada das falhas revela um padrão sistemático. Dos nove pedidos que falharam no método PL, seis falharam especificamente por violação da restrição `tempo_maximo_de_espera = 0`. Em todos esses casos, o otimizador criou gaps temporais entre atividades sucessivas que deveriam ser contíguas. Por exemplo, no Pedido 7 (Coxinha de Carne de Sol), a atividade 10691 (modelagem e recheio) terminou às 06:03, mas a atividade sucessora 10692 (empanamento) foi agendada para iniciar às 06:47, criando um gap de 44 minutos onde o máximo permitido era zero. Similarmente, no Pedido 13 (Folhado de Queijos Finos), um gap de 30 minutos foi criado entre atividades que deveriam ser imediatamente consecutivas.

O método sequencial, por outro lado, executou cinco dos seis pedidos críticos com sucesso. A taxa de sucesso para pedidos com restrições de gap zero foi de 83,3% no método sequencial versus 0% no método PL. Esta diferença dramática não pode ser atribuída a limitações do solver ou qualidade da solução matemática, mas sim a uma deficiência fundamental na modelagem do problema.

---

## Análise da Causa Raiz: Abstrações Incompletas

A investigação do código-fonte do otimizador revelou três deficiências arquiteturais críticas que explicam completamente as falhas observadas.

**Primeira deficiência: restrições de tempo máximo de espera não modeladas.** Embora o extrator de dados colete corretamente o atributo `tempo_maximo_de_espera` de cada atividade (linhas 388-396 de `extrator_dados_pedidos.py`), o modelo PL jamais incorpora essas informações como restrições matemáticas. No arquivo `modelo_pl_otimizador.py`, entre as linhas 40 e 120, observa-se a criação de restrições de precedência básica (`inicio[i+1] >= fim[i]`), mas nenhuma restrição limitando o gap temporal (`inicio[i+1] - fim[i] <= tempo_maximo_de_espera`). Consequentemente, o solver é livre para criar gaps arbitrários entre atividades, violando sistematicamente uma restrição fundamental do problema real.

**Segunda deficiência: equipamentos não modelados como recursos limitados.** A análise do código revela que equipamentos são extraídos durante a fase de preparação de dados, incluindo tipos, quantidades e elegibilidade para cada atividade. Entretanto, em nenhum ponto do modelo matemático existem restrições de exclusão mútua garantindo que um equipamento não seja alocado a múltiplas atividades simultaneamente. O modelo PL "agenda" atividades assumindo disponibilidade ilimitada de recursos. Apenas durante a execução, quando o sistema tenta efetivamente alocar equipamentos do pool disponível, os conflitos são descobertos. A esta altura, a solução "ótima" do PL já foi comprometida.

**Terceira deficiência: orçamento arbitrário de restrições.** Na linha 66 de `modelo_pl_otimizador.py`, encontra-se um limite fixo: `MAX_CONSTRAINTS = 1000`. Quando o número de restrições de não-sobreposição excede este limite, o sistema simplesmente para de adicionar restrições e continua com modelo incompleto. Para o dataset de 13 pedidos, com aproximadamente 130 atividades totais, existem teoricamente C(130,2) = 8.385 pares potencialmente conflitantes. Com orçamento de 1.000 restrições, apenas 11,9% dos conflitos são protegidos. Os 88% restantes ficam desprotegidos, permitindo que o solver crie soluções matematicamente ótimas mas praticamente infactíveis.

---

## Por Que o Método Guloso Funciona

O sucesso do método sequencial não se deve a superioridade algorítmica intrínseca, mas sim à sua propriedade de satisfação implícita de restrições. Enquanto o método PL tenta modelar explicitamente todas as restrições (e falha ao omitir muitas), o método guloso constrói soluções que já respeitam as restrições por design.

A satisfação da restrição de gap zero ocorre naturalmente porque o backward scheduling aloca atividades em sequência contígua. Ao processar uma atividade, o horário de referência é o fim da atividade sucessora. Portanto, se uma atividade consegue ser alocada, ela automaticamente termina exatamente quando a sucessora inicia, garantindo gap zero sem necessidade de verificação explícita.

A exclusão mútua de equipamentos é garantida pelo pool dinâmico. Em vez de pré-alocar recursos em um modelo matemático, o método sequencial mantém um conjunto de equipamentos disponíveis. Quando uma atividade requer um equipamento, o sistema consulta o pool em tempo real para verificar disponibilidade no intervalo desejado. Se disponível, o equipamento é imediatamente reservado e removido do pool para aquele período. Se indisponível, a atividade é reagendada ou o pedido falha. Este mecanismo garante que nunca ocorram alocações conflitantes.

As dependências de precedência são satisfeitas pela ordenação topológica reversa. Ao processar atividades da última para primeira, garante-se que quando uma atividade é alocada, todas suas sucessoras já foram previamente alocadas e seus horários são conhecidos. Isso elimina a possibilidade de violações de precedência.

---

## Complexidade Computacional e Eficiência

A comparação de complexidade revela outro aspecto surpreendente. O método sequencial opera em O(n × m × e), onde n é o número de pedidos, m a média de atividades por pedido e e o número de equipamentos. Para o dataset experimental, isso resulta em aproximadamente 3.900 operações, completadas em 0,42 segundos.

O método PL, usando formulação de programação linear inteira mista, possui complexidade O(k³) onde k é o número de variáveis. Com 104 variáveis binárias (13 pedidos × 8 janelas por pedido), a complexidade é aproximadamente 1.124.864 operações, executadas em 0,51 segundos incluindo overhead do solver.

Paradoxalmente, o método mais complexo computacionalmente não apenas falhou em entregar melhores resultados, mas consumiu 21% mais tempo para produzir soluções infactíveis. Este resultado ilustra que complexidade algorítmica não é sinônimo de qualidade de solução quando a modelagem do problema é inadequada.

---

## Implicações para Sistemas de Produção Reais

Os resultados deste estudo têm implicações profundas para o desenvolvimento de sistemas de otimização em ambientes industriais. Primeira implicação: completude da modelagem é mais crítica que sofisticação algorítmica. Um modelo simples que captura todas as restrições relevantes supera um modelo sofisticado que omite restrições críticas. No caso estudado, o gap de modelagem (ausência de restrições de tempo máximo de espera e equipamentos) foi fatal para o método PL.

Segunda implicação: validação pós-otimização é essencial. Sistemas que produzem soluções "ótimas" sem verificar factibilidade real podem causar falhas em produção. No SIVIRA, a ausência de validação pós-PL permitiu que soluções infactíveis fossem encaminhadas para execução, resultando em falhas apenas durante tentativa de alocação real de equipamentos.

Terceira implicação: heurísticas construtivas possuem vantagens práticas em ambientes com restrições complexas. Métodos que constroem soluções incrementalmente, verificando factibilidade a cada passo, são naturalmente robustos a restrições implícitas ou difíceis de modelar. O backward scheduling guloso nunca gera soluções infactíveis porque cada passo de construção respeita disponibilidade real de recursos.

---

## Caminhos para Correção do Método PL

A correção do otimizador baseado em PL requer três intervenções fundamentais. Primeiro, adicionar restrições explícitas de tempo máximo de espera. Para cada par de atividades sucessoras onde `tempo_maximo_de_espera` está definido, deve-se adicionar a restrição matemática: `inicio[atividade_sucessora] - fim[atividade_atual] <= tempo_maximo_de_espera`. Quando este valor é zero, a restrição se torna uma igualdade: `inicio[atividade_sucessora] = fim[atividade_atual]`.

Segundo, modelar equipamentos como recursos com capacidade limitada. Para cada equipamento e cada slot de tempo, deve-se garantir que o número de atividades alocadas não exceda a capacidade. Isso requer variáveis adicionais indicando uso de equipamento e restrições de capacidade: `soma(uso[atividade][equipamento][tempo]) <= capacidade[equipamento]` para todo equipamento e tempo.

Terceiro, eliminar o orçamento arbitrário de restrições. O limite de 1.000 restrições deve ser removido, permitindo que todas as restrições necessárias sejam modeladas. Se o tamanho do modelo se tornar proibitivo, técnicas de decomposição ou solvers mais robustos (como Gurobi ou CPLEX) devem ser considerados.

| Métrica de Qualidade | Sequencial | PL Atual | PL Corrigido (Projeção) |
|----------------------|------------|----------|-------------------------|
| **Taxa de Sucesso** | 84,6% | 30,8% | ≥80% (objetivo) |
| **Completude do Modelo** | Implícita | 12% | 100% |
| **Makespan** | 1.753 min | N/A (inválido) | <1.753 min (esperado) |
| **Robustez** | Alta | Baixa | Alta |

---

## Conclusões

Este trabalho demonstrou empiricamente que algoritmos gulosos podem superar técnicas de otimização matemática rigorosa quando a modelagem do problema é incompleta. No contexto estudado, um método sequencial simples alcançou taxa de sucesso de 84,6% enquanto Programação Linear falhou em 69,2% dos casos, apesar de encontrar soluções matematicamente ótimas.

A análise revelou que o fracasso do método PL não se deve a limitações algorítmicas intrínsecas, mas a três deficiências específicas de modelagem: omissão de restrições de tempo máximo de espera, ausência de modelagem de recursos limitados e orçamento arbitrário que deixa 88% das restrições de conflito desprotegidas. Estas deficiências transformam o problema real em uma abstração matematicamente tratável mas praticamente irrelevante.

O método sequencial, em contraste, satisfaz implicitamente todas as restrições por construção. Backward scheduling garante gaps temporais apropriados, alocação dinâmica previne conflitos de equipamentos e ordenação topológica respeita precedências. Esta abordagem construtiva, embora não explorando globalmente o espaço de soluções, garante que toda solução produzida é factível.

A principal contribuição deste trabalho é evidenciar que em sistemas de produção reais, a completude da modelagem matemática é mais crítica que a sofisticação do método de resolução. Abstrações inadequadas, não importa quão elegantes matematicamente, produzem soluções inúteis. Heurísticas simples que respeitam fielmente as restrições do problema real frequentemente superam otimizadores sofisticados baseados em modelos incompletos.

Para trabalhos futuros, recomenda-se a correção do modelo PL para incluir todas as restrições identificadas, seguida por reavaliação experimental. Apenas quando o método PL alcançar taxa de sucesso comparável ao método sequencial (≥80%) deve-se considerar sua adoção em produção. Enquanto isso, o método sequencial guloso permanece como escolha pragmática para sistemas onde robustez e confiabilidade são prioritárias sobre otimalidade teórica.

---

## Referências

**Código-Fonte Analisado:**
- `services/gestores/producao/executor_pedidos.py` - Implementação do método sequencial (linhas 48-166)
- `otimizador/modelo_pl_otimizador.py` - Modelo de Programação Linear (linhas 40-120, deficiências nas linhas 66)
- `otimizador/extrator_dados_pedidos.py` - Extração de dados (linhas 144-173 equipamentos, 388-396 tempo máximo de espera)
- `otimizador/otimizador_integrado.py` - Execução híbrida (linhas 192-267)

**Dataset Experimental:**
- `data/csv/exemplo_pedidos.csv` - 13 pedidos de produção
- `data/produtos/atividades/1069_coxinha_de_carne_de_sol.json` - Atividades verificadas
- `data/produtos/atividades/1074_folhado_de_queijos_finos.json` - Atividades verificadas
- `data/metricas_comparacao.json` - Resultados experimentais completos

**Logs de Execução:**
- `logs/comparacao_sequencial_20251114_090610/` - Logs do método sequencial
- `logs/comparacao_otimizado_20251114_090613/` - Logs do método PL

**Literatura de Referência:**
- Pinedo, M. (2016). *Scheduling: Theory, Algorithms, and Systems*. 5th ed. Springer.
- Brucker, P., & Knust, S. (2012). *Complex Scheduling*. Springer.
- Błażewicz, J., Ecker, K. H., Pesch, E., Schmidt, G., & Węglarz, J. (2007). *Handbook on Scheduling: From Theory to Applications*. Springer.
- Graham, R. L., Lawler, E. L., Lenstra, J. K., & Rinnooy Kan, A. H. G. (1979). "Optimization and Approximation in Deterministic Sequencing and Scheduling: A Survey". *Annals of Discrete Mathematics*, 5, 287-326.

---

**Autor:** Claude (Anthropic)
**Instituição:** Sistema SIVIRA - Produção Industrial
**Contato:** noreply@anthropic.com
**Data:** 14 de Novembro de 2025
**Versão:** 1.0
