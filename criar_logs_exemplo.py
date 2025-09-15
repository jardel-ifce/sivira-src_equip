"""
Script para criar logs de exemplo para demonstração do agente
"""

import os
from datetime import datetime

def criar_logs_exemplo():
    # Cria diretórios se não existirem
    os.makedirs("logs/erros", exist_ok=True)
    os.makedirs("logs/equipamentos", exist_ok=True)
    
    # Log de erro 1: Falta de material
    with open("logs/erros/erro_producao_001.log", "w") as f:
        f.write(f"""[{datetime.now()}] ERROR: Produção interrompida
Motivo: Material insuficiente para completar pedido
Item: Parafuso M8
Quantidade necessária: 100
Quantidade em estoque: 23
Ação: Pedido pausado aguardando reposição de material
""")
    
    # Log de erro 2: Falha em equipamento
    with open("logs/erros/erro_equipamento_001.log", "w") as f:
        f.write(f"""[{datetime.now()}] ERROR: Equipamento com falha
Equipamento: Torno CNC #003
Tipo de falha: Superaquecimento do motor principal
Status: Equipamento parado para manutenção
Tempo estimado: 2 horas
Impacto: 5 pedidos em atraso
""")
    
    # Log de erro 3: Timeout
    with open("logs/erros/erro_timeout_001.log", "w") as f:
        f.write(f"""[{datetime.now()}] WARNING: Timeout na operação
Processo: Usinagem de peça complexa
Tempo esperado: 45 minutos
Tempo decorrido: 120 minutos
Status: Processo cancelado por tempo excedido
""")
    
    # Log de equipamento normal
    with open("logs/equipamentos/equipamento_001.log", "w") as f:
        f.write(f"""[{datetime.now()}] INFO: Status do equipamento
Equipamento: Fresadora #001
Status: Operacional
Horas de operação: 1234
Última manutenção: 2024-08-15
Próxima manutenção: 2024-09-15
Eficiência: 92%
""")
    
    # Log com múltiplos erros
    with open("logs/erros/erro_multiplo_001.log", "w") as f:
        f.write(f"""[{datetime.now()}] ERROR: Múltiplas falhas detectadas
1. Falta de material: Chapa de aço 2mm
2. Equipamento em manutenção: Serra de fita
3. Timeout no processo de soldagem
4. Material sem estoque: Eletrodo E6013
5. Falha na comunicação com CLP
Status: Linha de produção parada
""")
    
    print("✅ Logs de exemplo criados com sucesso!")
    print("\nArquivos criados:")
    print("  • logs/erros/erro_producao_001.log")
    print("  • logs/erros/erro_equipamento_001.log") 
    print("  • logs/erros/erro_timeout_001.log")
    print("  • logs/erros/erro_multiplo_001.log")
    print("  • logs/equipamentos/equipamento_001.log")

if __name__ == "__main__":
    criar_logs_exemplo()