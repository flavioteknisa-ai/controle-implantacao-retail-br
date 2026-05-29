"""
Script para importar dados de colaboradores de um arquivo Excel existente
para o sistema de controle de férias
"""

import sys
import pandas as pd
from datetime import datetime
from excel_handler import ExcelHandler
from models import Colaborador


def importar_colaboradores(caminho_origem: str, coluna_nome: str, coluna_data_admissao: str,
                          coluna_time: str = None, planilha: int = 0):
    """
    Importa colaboradores de um arquivo Excel externo.

    Args:
        caminho_origem: Caminho do arquivo Excel origem
        coluna_nome: Nome da coluna com nomes dos colaboradores
        coluna_data_admissao: Nome da coluna com datas de admissão
        coluna_time: Nome da coluna com times/departamentos (opcional)
        planilha: Índice da planilha (0 = primeira)

    Exemplo:
        importar_colaboradores(
            'caminho/arquivo.xlsx',
            coluna_nome='Nome',
            coluna_data_admissao='Data Admissão',
            coluna_time='Departamento'
        )
    """

    print("=" * 60)
    print("IMPORTADOR DE COLABORADORES - SISTEMA DE FÉRIAS")
    print("=" * 60)
    print()

    try:
        # Ler arquivo de origem
        print(f"📂 Lendo arquivo: {caminho_origem}")
        df = pd.read_excel(caminho_origem, sheet_name=planilha)
        print(f"   ✓ Lido com sucesso ({len(df)} linhas)")
        print()

        # Validar colunas
        print("🔍 Validando colunas...")
        colunas_necessarias = [coluna_nome, coluna_data_admissao]
        if coluna_time:
            colunas_necessarias.append(coluna_time)

        colunas_faltantes = [c for c in colunas_necessarias if c not in df.columns]
        if colunas_faltantes:
            print(f"   ✗ Erro: Colunas não encontradas: {colunas_faltantes}")
            print(f"   Colunas disponíveis: {list(df.columns)}")
            return False

        print(f"   ✓ Colunas validadas")
        print()

        # Carregar colaboradores existentes
        excel_handler = ExcelHandler()
        colaboradores_existentes = excel_handler.carregar_colaboradores()
        proximo_id = max([c.id for c in colaboradores_existentes], default=0) + 1

        # Processar dados
        print("👥 Processando colaboradores...")
        novos_colaboradores = []
        erros = 0

        for idx, row in df.iterrows():
            try:
                nome = str(row[coluna_nome]).strip()

                # Pula linhas vazias
                if not nome or nome.lower() == 'nan':
                    continue

                # Pula header se existir na data
                if nome.lower() == coluna_nome.lower():
                    continue

                # Data de admissão
                data_str = str(row[coluna_data_admissao]).strip()
                try:
                    data_admissao = pd.to_datetime(data_str)
                except:
                    print(f"   ⚠ Aviso: Data inválida para '{nome}': {data_str}")
                    erros += 1
                    continue

                # Time/Departamento
                time = str(row[coluna_time]).strip() if coluna_time else "Não informado"
                if time.lower() == 'nan':
                    time = "Não informado"

                # Verifica se já existe
                ja_existe = any(c.nome.lower() == nome.lower() for c in colaboradores_existentes + novos_colaboradores)
                if ja_existe:
                    print(f"   ⚠ '{nome}' já existe - pulando")
                    continue

                # Cria novo colaborador
                novo = Colaborador(proximo_id, nome, data_admissao, time, ativo=True)
                novos_colaboradores.append(novo)
                proximo_id += 1

                print(f"   ✓ {nome} ({data_admissao.strftime('%d/%m/%Y')})")

            except Exception as e:
                print(f"   ✗ Erro na linha {idx+2}: {str(e)}")
                erros += 1

        if not novos_colaboradores:
            print("   ✗ Nenhum colaborador foi importado")
            return False

        print()
        print(f"📊 Resumo:")
        print(f"   Total importados: {len(novos_colaboradores)}")
        print(f"   Erros: {erros}")
        print()

        # Confirmar importação
        resposta = input("Deseja salvar esses colaboradores? (s/n): ").strip().lower()
        if resposta != 's':
            print("   Importação cancelada")
            return False

        # Salvar todos os colaboradores (existentes + novos)
        todos = colaboradores_existentes + novos_colaboradores
        excel_handler.salvar_colaboradores(todos)

        print()
        print("=" * 60)
        print(f"✓ {len(novos_colaboradores)} colaboradores importados com sucesso!")
        print("=" * 60)
        return True

    except FileNotFoundError:
        print(f"✗ Arquivo não encontrado: {caminho_origem}")
        return False
    except Exception as e:
        print(f"✗ Erro ao processar arquivo: {str(e)}")
        return False


if __name__ == "__main__":
    # Exemplo de uso
    print()
    print("MODO INTERATIVO")
    print("-" * 60)

    caminho = input("Caminho do arquivo Excel: ").strip()
    coluna_nome = input("Nome da coluna com NOMES: ").strip()
    coluna_data = input("Nome da coluna com DATAS DE ADMISSÃO: ").strip()
    coluna_time = input("Nome da coluna com TIMES/DEPARTAMENTOS (ou deixe vazio): ").strip()

    sucesso = importar_colaboradores(
        caminho,
        coluna_nome,
        coluna_data,
        coluna_time if coluna_time else None
    )

    sys.exit(0 if sucesso else 1)
