# -*- coding: utf-8 -*-
"""
Script para migrar dados do SQLite para PostgreSQL (Supabase)
Execute este script UMA VEZ após configurar as variáveis de ambiente do Supabase
"""
import os
import sqlite3
from datetime import datetime, date
from dotenv import load_dotenv
from database import db, User, ColaboradorDB, FeriasDB, ERPProjetoDB, ERPModuloDB, ERPUnidadeDB, ERPAtividadeDB, ComissionamentoDB
from app import app

load_dotenv()

def migrate_data():
    """Migra dados do SQLite para PostgreSQL"""

    # Conectar ao banco de dados SQLite local
    sqlite_db_path = 'C:/Users/Teknisa/Desktop/Claude/sistema_ferias/data/ferias_data.db'

    if not os.path.exists(sqlite_db_path):
        print(f"❌ Erro: Arquivo SQLite não encontrado em {sqlite_db_path}")
        return False

    print("🔄 Iniciando migração de dados...")
    print(f"📁 Origem: SQLite ({sqlite_db_path})")
    print(f"📊 Destino: PostgreSQL (Supabase)")

    try:
        # Conectar ao SQLite
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()

        with app.app_context():
            # Criar tabelas no PostgreSQL
            db.create_all()
            print("✅ Tabelas criadas no PostgreSQL")

            # Migrar Colaboradores
            sqlite_cursor.execute("SELECT * FROM colaboradores")
            colaboradores = sqlite_cursor.fetchall()
            for row in colaboradores:
                colab = ColaboradorDB(
                    id=row['id'],
                    nome=row['nome'],
                    data_admissao=datetime.strptime(row['data_admissao'], '%Y-%m-%d').date() if isinstance(row['data_admissao'], str) else row['data_admissao'],
                    time=row['time'] or '',
                    cidade=row['cidade'] or '',
                    ativo=bool(row['ativo'])
                )
                db.session.add(colab)
            db.session.commit()
            print(f"✅ {len(colaboradores)} colaboradores migrados")

            # Migrar Usuários
            sqlite_cursor.execute("SELECT * FROM users")
            users = sqlite_cursor.fetchall()
            for row in users:
                user = User(
                    id=row['id'],
                    username=row['username'],
                    nome=row['nome'],
                    senha_hash=row['senha_hash'],
                    perfil=row['perfil'],
                    colaborador_id=row['colaborador_id'],
                    ativo=bool(row['ativo'])
                )
                db.session.add(user)
            db.session.commit()
            print(f"✅ {len(users)} usuários migrados")

            # Migrar Férias
            sqlite_cursor.execute("SELECT * FROM ferias")
            ferias = sqlite_cursor.fetchall()
            for row in ferias:
                feria = FeriasDB(
                    id=row['id'],
                    colaborador_id=row['colaborador_id'],
                    data_inicio=datetime.strptime(row['data_inicio'], '%Y-%m-%d').date() if isinstance(row['data_inicio'], str) else row['data_inicio'],
                    data_fim=datetime.strptime(row['data_fim'], '%Y-%m-%d').date() if isinstance(row['data_fim'], str) else row['data_fim'],
                    dias=row['dias'],
                    status=row['status'],
                    conflito_detectado=bool(row['conflito_detectado']),
                    conflito_aprovado=bool(row['conflito_aprovado'])
                )
                db.session.add(feria)
            db.session.commit()
            print(f"✅ {len(ferias)} registros de férias migrados")

            # Migrar Projetos ERP
            sqlite_cursor.execute("SELECT * FROM erp_projetos")
            projetos = sqlite_cursor.fetchall()
            for row in projetos:
                proj = ERPProjetoDB(
                    id=row['id'],
                    nome_projeto=row['nome_projeto'],
                    data_aceite=datetime.strptime(row['data_aceite'], '%Y-%m-%d').date() if isinstance(row['data_aceite'], str) else row['data_aceite'],
                    data_conclusao=datetime.strptime(row['data_conclusao'], '%Y-%m-%d').date() if isinstance(row['data_conclusao'], str) and row['data_conclusao'] else None,
                    status=row['status'],
                    responsavel_id=row['responsavel_id'],
                    valor_mensalidades=row['valor_mensalidades'] or 0,
                    descricao=row['descricao'] or '',
                    percentual_conclusao=row.get('percentual_conclusao', 0) or 0,
                    numero_unidades=row.get('numero_unidades', 1) or 1,
                    potencial_cliente=row.get('potencial_cliente', 'Médio') or 'Médio',
                    tipo_projeto=row.get('tipo_projeto', 'Novo') or 'Novo',
                    criado_em=datetime.fromisoformat(row['criado_em']) if isinstance(row['criado_em'], str) else row['criado_em'],
                    atualizado_em=datetime.fromisoformat(row['atualizado_em']) if isinstance(row['atualizado_em'], str) else row['atualizado_em']
                )
                db.session.add(proj)
            db.session.commit()
            print(f"✅ {len(projetos)} projetos migrados")

            # Migrar Módulos ERP
            sqlite_cursor.execute("SELECT * FROM erp_modulos_projeto")
            modulos = sqlite_cursor.fetchall()
            for row in modulos:
                mod = ERPModuloDB(
                    id=row['id'],
                    projeto_id=row['projeto_id'],
                    modulo=row['modulo'],
                    status_modulo=row['status_modulo'],
                    data_inicio_modulo=datetime.strptime(row['data_inicio_modulo'], '%Y-%m-%d').date() if row['data_inicio_modulo'] and isinstance(row['data_inicio_modulo'], str) else row['data_inicio_modulo'],
                    data_conclusao_modulo=datetime.strptime(row['data_conclusao_modulo'], '%Y-%m-%d').date() if row['data_conclusao_modulo'] and isinstance(row['data_conclusao_modulo'], str) else row['data_conclusao_modulo'],
                    percentual_conclusao=row.get('percentual_conclusao', 0) or 0,
                    criado_em=datetime.fromisoformat(row['criado_em']) if isinstance(row['criado_em'], str) else row['criado_em']
                )
                db.session.add(mod)
            db.session.commit()
            print(f"✅ {len(modulos)} módulos migrados")

            # Migrar Unidades ERP
            sqlite_cursor.execute("SELECT * FROM erp_unidades_projeto")
            unidades = sqlite_cursor.fetchall()
            for row in unidades:
                uni = ERPUnidadeDB(
                    id=row['id'],
                    projeto_id=row['projeto_id'],
                    unidade=row['unidade'],
                    status_unidade=row['status_unidade'],
                    data_inicio_unidade=datetime.strptime(row['data_inicio_unidade'], '%Y-%m-%d').date() if row['data_inicio_unidade'] and isinstance(row['data_inicio_unidade'], str) else row['data_inicio_unidade'],
                    data_conclusao_unidade=datetime.strptime(row['data_conclusao_unidade'], '%Y-%m-%d').date() if row['data_conclusao_unidade'] and isinstance(row['data_conclusao_unidade'], str) else row['data_conclusao_unidade'],
                    criado_em=datetime.fromisoformat(row['criado_em']) if isinstance(row['criado_em'], str) else row['criado_em']
                )
                db.session.add(uni)
            db.session.commit()
            print(f"✅ {len(unidades)} unidades migradas")

            # Migrar Atividades ERP
            sqlite_cursor.execute("SELECT * FROM erp_atividades_projeto")
            atividades = sqlite_cursor.fetchall()
            for row in atividades:
                ativ = ERPAtividadeDB(
                    id=row['id'],
                    projeto_id=row['projeto_id'],
                    titulo=row['titulo'],
                    descricao=row.get('descricao', '') or '',
                    data_reuniao=datetime.strptime(row['data_reuniao'], '%Y-%m-%d').date() if isinstance(row['data_reuniao'], str) else row['data_reuniao'],
                    responsavel_nota=row.get('responsavel_nota', '') or '',
                    status_atividade=row.get('status_atividade', 'Aberta') or 'Aberta',
                    concluida=bool(row.get('concluida', False)),
                    criado_em=datetime.fromisoformat(row['criado_em']) if isinstance(row['criado_em'], str) else row['criado_em'],
                    atualizado_em=datetime.fromisoformat(row['atualizado_em']) if isinstance(row['atualizado_em'], str) else row['atualizado_em']
                )
                db.session.add(ativ)
            db.session.commit()
            print(f"✅ {len(atividades)} atividades migradas")

            # Migrar Comissionamentos
            sqlite_cursor.execute("SELECT * FROM comissionamentos")
            comissionamentos = sqlite_cursor.fetchall()
            for row in comissionamentos:
                comis = ComissionamentoDB(
                    id=row['id'],
                    consultor_id=row['consultor_id'],
                    cliente=row['cliente'],
                    data_comissao=datetime.strptime(row['data_comissao'], '%Y-%m-%d').date() if isinstance(row['data_comissao'], str) else row['data_comissao'],
                    horas_comissionadas=row['horas_comissionadas'],
                    hora_fora_estado=row.get('hora_fora_estado', '') or '',
                    motivo=row.get('motivo', '') or '',
                    periodo_inicio=datetime.strptime(row['periodo_inicio'], '%Y-%m-%d').date() if row.get('periodo_inicio') and isinstance(row['periodo_inicio'], str) else row.get('periodo_inicio'),
                    periodo_fim=datetime.strptime(row['periodo_fim'], '%Y-%m-%d').date() if row.get('periodo_fim') and isinstance(row['periodo_fim'], str) else row.get('periodo_fim'),
                    criado_em=datetime.fromisoformat(row['criado_em']) if isinstance(row['criado_em'], str) else row['criado_em'],
                    atualizado_em=datetime.fromisoformat(row['atualizado_em']) if isinstance(row['atualizado_em'], str) else row['atualizado_em']
                )
                db.session.add(comis)
            db.session.commit()
            print(f"✅ {len(comissionamentos)} comissionamentos migrados")

        sqlite_conn.close()
        print("\n✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        return True

    except Exception as e:
        print(f"\n❌ ERRO NA MIGRAÇÃO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    migrate_data()
