# -*- coding: utf-8 -*-
"""
Script para inicializar o banco de dados Supabase
Cria todas as tabelas e adiciona o usuário admin
"""
import os
from dotenv import load_dotenv

load_dotenv()

from app import app, db
from database import User, ColaboradorDB

def init_database():
    """Inicializa o banco de dados no Supabase"""
    print("🔄 Iniciando banco de dados Supabase...")

    try:
        with app.app_context():
            # Criar todas as tabelas
            print("📊 Criando tabelas...")
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")

            # Verificar se usuário admin existe
            admin = User.query.filter_by(username='admin').first()

            if not admin:
                print("👤 Criando usuário admin...")
                admin = User(
                    username='admin',
                    nome='Administrador',
                    perfil='gestor',
                    ativo=True
                )
                admin.set_senha('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuário admin criado!")
            else:
                print("✅ Usuário admin já existe!")

            print("\n" + "="*50)
            print("✅ BANCO DE DADOS INICIALIZADO COM SUCESSO!")
            print("="*50)
            print("\n📝 Credenciais de acesso:")
            print("   Usuário: admin")
            print("   Senha: admin123")
            print("\n🚀 Aplicação pronta para usar!")

            return True

    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)
