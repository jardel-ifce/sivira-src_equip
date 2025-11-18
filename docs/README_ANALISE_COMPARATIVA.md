# Análise Comparativa: Sequencial vs PL v2.0

## 📄 Documentos Disponíveis

### 1. Versão Markdown
**Arquivo:** `ANALISE_COMPARATIVA_SEQUENCIAL_VS_PL.md`
- Formato: Markdown com LaTeX para fórmulas
- Extensão: ~1,200 linhas
- Visualização: IDE, GitHub, GitLab, etc.

### 2. Versão PDF (LaTeX)
**Arquivo:** `ANALISE_COMPARATIVA_SEQUENCIAL_VS_PL.pdf`
- Formato: PDF acadêmico profissional
- Páginas: 13 páginas
- Tamanho: 459 KB
- Compilado com: pdfLaTeX

## 📊 Conteúdo do Documento

### Estrutura

1. **Introdução e Contexto**
   - Problema de Job Shop Scheduling
   - Características específicas da padaria
   - Classificação formal do problema (NP-difícil)

2. **Formulação Matemática do PL v2.0**
   - Conjuntos, parâmetros e variáveis
   - Função objetivo: $\max \sum_{p \in P} \sum_{j \in J_p} x_{p,j}$
   - 4 tipos de restrições com formulação formal
   - Estatísticas do modelo (117 variáveis, 1,321 restrições)

3. **Método Sequencial (Backward Scheduling)**
   - Pseudo-código completo (Algorithm 1)
   - Heurística EDD (Earliest Due Date)
   - Análise de complexidade: $O(n \log n + n^2)$

4. **Comparação Empírica**
   - Resultados com 13 pedidos reais
   - Tabelas comparativas extensivas
   - Análise de makespan e utilização de recursos
   - Perfil de tempo computacional

5. **Discussão e Trade-offs**
   - Paradoxo da otimalidade (explicação detalhada)
   - Trade-offs fundamentais (3 tipos)
   - Limitações de ambos os métodos

6. **Propostas de Melhoria**
   - PL v2.0: função multi-critério, janelas adaptativas, warm start
   - Sequencial: heurísticas alternativas, look-ahead local

7. **Conclusões e Recomendações**
   - Síntese dos resultados
   - Tabela de recomendações por cenário
   - Trabalhos futuros (curto, médio e longo prazo)

8. **Apêndices**
   - Glossário de termos técnicos
   - Dataset completo do experimento
   - Bibliografia

## 🎯 Principais Resultados

### Comparação Quantitativa

| Métrica | Sequencial | PL v2.0 Otimizado |
|---------|------------|-------------------|
| **Taxa de Sucesso** | **84.6%** (11/13) | 69.2% (9/13) |
| **Tempo de Resolução** | 0.42s | **0.18s** (-57%) |
| **Makespan** | **29h** | 73h (+151%) |
| **Utilização Recursos** | **78-100%** | 48-73% |
| **Garantias** | Nenhuma | **Otimalidade** |
| **Complexidade** | $O(n^2)$ | NP-completo |

### Principal Descoberta

> **"Completude de modelagem ≠ Superioridade prática"**

O método PL v2.0, apesar de matematicamente ótimo, teve performance inferior ao sequencial devido a:
1. Espaço de busca restrito (janelas pré-definidas)
2. Função objetivo limitada (não considera makespan)
3. Discretização temporal (30min vs busca contínua)
4. Makespan esparso (73h vs 29h)

## 🔬 Fórmulas Matemáticas Principais

### Modelo PL v2.0 Completo

```latex
max     ∑(p∈P) ∑(j∈Jp) x_{p,j}

s.a.    ∑(j∈Jp) x_{p,j} ≤ 1                                     ∀p∈P
        x_{p1,j1} + x_{p2,j2} ≤ 1    se overlap(j1,j2)
        x_{p,j} ∈ {0,1}                                          ∀p∈P, j∈Jp
```

### Complexidade Temporal

- **Sequencial:** $T_{seq}(n) = O(n \log n + n^2)$
- **PL v2.0:** $T_{PL}(n) = O(n \times p) + O((n \times j)^2) + O(2^{n \times j})$

## 📚 Referências no Documento

1. Pinedo, M. L. (2016). *Scheduling: Theory, Algorithms, and Systems*
2. Brucker, P. (2007). *Scheduling Algorithms*
3. Wolsey & Nemhauser (1999). *Integer and Combinatorial Optimization*
4. Bertsimas & Weismantel (2005). *Optimization over Integers*
5. Google OR-Tools (2024)

## 🎓 Uso Acadêmico

O documento está formatado para:
- ✅ Apresentações acadêmicas
- ✅ Dissertações/teses
- ✅ Artigos científicos
- ✅ Documentação técnica
- ✅ Benchmarking de algoritmos

## 🛠️ Compilação do PDF

### Requisitos
- LaTeX distribution (TexLive, MiKTeX, etc.)
- Pacotes: amsmath, algorithm, booktabs, tcolorbox, etc.

### Comandos
```bash
cd docs
pdflatex ANALISE_COMPARATIVA_SEQUENCIAL_VS_PL.tex
pdflatex ANALISE_COMPARATIVA_SEQUENCIAL_VS_PL.tex  # Segunda passagem para índice
```

### Arquivo Fonte
- **LaTeX:** `ANALISE_COMPARATIVA_SEQUENCIAL_VS_PL.tex`
- **Markdown:** `ANALISE_COMPARATIVA_SEQUENCIAL_VS_PL.md`

## 📊 Figuras e Tabelas

O documento inclui:
- **9 tabelas** com dados comparativos
- **3 algoritmos** em pseudo-código
- **Múltiplas equações** matemáticas formatadas
- **Boxes destacados** para conceitos importantes

## 🔗 Links para Código Fonte

O documento referencia os seguintes arquivos de implementação:

### Método Sequencial
- `services/gestores/producao/executor_pedidos.py`
- `models/atividades/atividade_modular.py`
- `utils/logs/logger_de_atividades.py`

### PL v2.0
- `otimizador_v2/modelo_pl_completo.py`
- `otimizador_v2/executor_v2.py`
- `otimizador/gerador_janelas_temporais.py`
- `otimizador_v2/aplicador_solucao.py`

### Interface
- `menu/main_menu.py` (linhas 1086-1183, 1295-1425)

## 💡 Recomendações de Uso

| Cenário | Método Recomendado | Razão |
|---------|-------------------|-------|
| **n ≤ 30 pedidos** | PL v2.0 | Rápido + otimalidade |
| **n > 50 pedidos** | Sequencial | PL não escala |
| **Deadline apertado** | Sequencial | Makespan compacto (29h vs 73h) |
| **Pedidos longos (>20h)** | Sequencial | PL rejeita sistematicamente |
| **Tempo real (<1s)** | PL v2.0 | Mais rápido (0.18s vs 0.42s) |
| **Garantia de otimalidade** | PL v2.0 | Única opção com garantia formal |

## 📞 Contato

Para dúvidas ou sugestões sobre este documento:
- Sistema: SIVIRA v2.0
- Email: contato@sivira.com
- Documentação: `/docs`

---

**Última atualização:** 14 de Novembro de 2025
**Versão:** 2.0
