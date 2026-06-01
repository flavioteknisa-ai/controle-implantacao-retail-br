# -*- coding: utf-8 -*-
"""
Script para migrar dados do banco local para o Vercel online
"""
import os
import sys
import sqlite3
from datetime import datetime, date
import requests
import json

# Configurar encoding para Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

LOCAL_DB = 'data/ferias_data.db'
VERCEL_URL = 'https://controle-implantacao-retail-br.vercel.app'
MIGRATION_ENDPOINT = f'{VERCEL_URL}/migrate-data'

def serialize_date(obj):
    """Converte date/datetime para string"""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def extract_data_from_local_db():
    """Extrai todos os dados do banco local"""
    if not os.path.exists(LOCAL_DB):
        print(f"❌ Arquivo {LOCAL_DB} não encontrado!")
        return None

    print(f"📂 Conectando ao banco local: {LOCAL_DB}")

    try:
        conn = sqlite3.connect(LOCAL_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        data = {}

        # Extrair colaboradores
        print("📋 Extraindo colaboradores...")
        cursor.execute("SELECT * FROM colaboradores")
        data['colaboradores'] = [dict(row) for row in cursor.fetchall()]
        print(f"   ✅ {len(data['colaboradores'])} colaboradores")

        # Extrair usuários
        print("📋 Extraindo usuários...")
        cursor.execute("SELECT * FROM users")
        data['users'] = [dict(row) for row in cursor.fetchall()]
        print(f"   ✅ {len(data['users'])} usuários")

        # Extrair férias
        print("📋 Extraindo férias...")
        cursor.execute("SELECT * FROM ferias")
        data['ferias'] = [dict(row) for row in cursor.fetchall()]
        print(f"   ✅ {len(data['ferias'])} registros de férias")

        # Extrair projetos ERP
        print("📋 Extraindo projetos ERP...")
        cursor.execute("SELECT * FROM erp_projetos")
        data['erp_projetos'] = [dict(row) for row in cursor.fetchall()]
        print(f"   ✅ {len(data['erp_projetos'])} projetos")

        # Extrair módulos
        print("📋 Extraindo módulos...")
        cursor.execute("SELECT * FROM erp_modulos_projeto")
        data['erp_modulos'] = [dict(row) for row in cursor.fetchall()]
        print(f"   ✅ {len(data['erp_modulos'])} módulos")

        # Extrair unidades
        print("📋 Extraindo unidades...")
        cursor.execute("SELECT * FROM erp_unidades_projeto")
        data['erp_unidades'] = [dict(row) for row in cursor.fetchall()]
        print(f"   ✅ {len(data['erp_unidades'])} unidades")

        # Extrair atividades
        print("📋 Extraindo atividades...")
        cursor.execute("SELECT * FROM erp_atividades_projeto")
        data['erp_atividades'] = [dict(row) for row in cursor.fetchall()]
        print(f"   ✅ {len(data['erp_atividades'])} atividades")

        # Extrair comissionamentos
        print("📋 Extraindo comissionamentos...")
        cursor.execute("SELECT * FROM comissionamentos")
        data['comissionamentos'] = [dict(row) for row in cursor.fetchall()]
        print(f"   ✅ {len(data['comissionamentos'])} comissionamentos")

        conn.close()
        return data

    except Exception as e:
        print(f"❌ Erro ao extrair dados: {str(e)}")
        return None

def send_data_to_vercel(data):
    """Envia os dados para o Vercel via endpoint"""
    print(f"\n📤 Enviando dados para {VERCEL_URL}...")

    try:
        # Serializar os dados com conversão de dates
        payload = json.loads(json.dumps(data, default=serialize_date))

        response = requests.post(
            MIGRATION_ENDPOINT,
            json=payload,
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ {result.get('message', 'Migração concluída com sucesso!')}")
            print(f"\n📊 Resumo da migração:")
            summary = result.get('summary', {})
            for table, count in summary.items():
                print(f"   • {table}: {count} registros")
            return True
        else:
            print(f"❌ Erro na migração (status {response.status_code})")
            print(f"   Resposta: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Erro ao enviar dados: {str(e)}")
        return False

def main():
    print("="*60)
    print("🔄 MIGRAÇÃO: Dados Locais → Vercel Online")
    print("="*60)

    # Extrair dados locais
    data = extract_data_from_local_db()
    if not data:
        print("\n❌ Falha na extração de dados")
        return False

    print(f"\n✅ {sum(len(v) for k, v in data.items() if isinstance(v, list))} registros extraídos do banco local")

    # Se não tiver argumento --confirm, pedir confirmação
    print("\n" + "="*60)
    if '--confirm' not in sys.argv:
        print("💡 Dica: Execute com --confirm para pular confirmação")
        print("   python migrate_local_to_vercel.py --confirm")
        try:
            response = input("✅ Deseja enviar estes dados para o Vercel? (s/n): ")
            if response.lower() != 's':
                print("❌ Migração cancelada")
                return False
        except EOFError:
            # Se não conseguir ler entrada (ex: Bash), usar --confirm
            print("Nenhuma entrada de usuário detectada. Use: python migrate_local_to_vercel.py --confirm")
            return False
    else:
        print("✅ Enviando dados automaticamente (--confirm)...")

    # Enviar para Vercel
    success = send_data_to_vercel(data)

    if success:
        print("\n" + "="*60)
        print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print(f"\n✅ Acesse a aplicação: {VERCEL_URL}")
        print("✅ Todos os seus dados estão online agora!")
        return True
    else:
        print("\n" + "="*60)
        print("❌ ERRO NA MIGRAÇÃO")
        print("="*60)
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
