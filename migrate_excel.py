#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migração: Excel → SQLite
Execute UMA VEZ antes de subir o sistema online:
    python migrate_excel.py
"""
import os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DATA_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
EXCEL_PATH = os.path.join(DATA_DIR, 'ferias_data.xlsx')

def migrar():
    if not os.path.exists(EXCEL_PATH):
        print(f'[AVISO] Arquivo não encontrado: {EXCEL_PATH}')
        print('        Iniciando banco vazio.')

    from app import app, db
    from database import ColaboradorDB, FeriasDB, User

    with app.app_context():
        db.create_all()

        if not os.path.exists(EXCEL_PATH):
            print('[OK] Banco criado vazio.')
            return

        from excel_handler import ExcelHandler
        import openpyxl

        handler = ExcelHandler()

        # ── Limpar tabelas ──
        FeriasDB.query.delete()
        ColaboradorDB.query.delete()
        db.session.commit()

        # ── Colaboradores ──
        colaboradores = handler.carregar_colaboradores()
        for c in colaboradores:
            adm = c.data_admissao.date() if isinstance(c.data_admissao, datetime) else c.data_admissao
            db.session.add(ColaboradorDB(
                id=c.id, nome=c.nome, data_admissao=adm,
                time=c.time or '', cidade=c.cidade or '', ativo=c.ativo,
            ))
        db.session.commit()
        print(f'[OK] {len(colaboradores)} colaboradores migrados')

        # ── Férias planejadas ──
        ferias_plan = handler.carregar_ferias_planejadas()
        for f in ferias_plan:
            ini = f.data_inicio.date() if isinstance(f.data_inicio, datetime) else f.data_inicio
            fim = f.data_fim.date()    if isinstance(f.data_fim,    datetime) else f.data_fim
            db.session.add(FeriasDB(
                id=f.id, colaborador_id=f.colaborador_id,
                data_inicio=ini, data_fim=fim, dias=f.dias, status=f.status,
                conflito_detectado=getattr(f, 'conflito_detectado', False),
                conflito_aprovado=getattr(f, 'conflito_aprovado', False),
            ))
        db.session.commit()
        print(f'[OK] {len(ferias_plan)} férias planejadas migradas')

        # ── Férias realizadas ──
        try:
            wb  = openpyxl.load_workbook(EXCEL_PATH)
            ws  = wb['Férias Realizadas']
            max_id = max((f.id for f in ferias_plan), default=0)
            count  = 0
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] is None: continue
                try:
                    ini = datetime.strptime(str(row[3]), '%Y-%m-%d').date()
                    fim = datetime.strptime(str(row[4]), '%Y-%m-%d').date()
                    max_id += 1
                    db.session.add(FeriasDB(
                        id=max_id, colaborador_id=int(row[1]),
                        data_inicio=ini, data_fim=fim,
                        dias=(fim - ini).days + 1, status='Realizado',
                    ))
                    count += 1
                except Exception as e:
                    print(f'  [linha ignorada] {e}')
            wb.close()
            db.session.commit()
            print(f'[OK] {count} férias realizadas migradas')
        except Exception as e:
            print(f'[AVISO] Férias realizadas não migradas: {e}')

        # ── Admin padrão ──
        if User.query.count() == 0:
            admin = User(username='admin', nome='Gestor', perfil='gestor')
            admin.set_senha(os.environ.get('ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()
            print('[OK] Usuário admin criado (senha: admin123) — troque imediatamente!')

        print('\n[OK] Migração concluída com sucesso!')

if __name__ == '__main__':
    migrar()
