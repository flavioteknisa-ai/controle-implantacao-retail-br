# ──────────────────────────────────────────────────────────────────
# ARQUIVO WSGI PARA PYTHONANYWHERE
#
# Instrução de uso:
# 1. No PythonAnywhere, vá em Web → clique no seu app
# 2. Clique em "WSGI configuration file" (link azul)
# 3. APAGUE todo o conteúdo existente
# 4. Cole este arquivo inteiro
# 5. Substitua SEUUSERNAME pelo seu username do PythonAnywhere
# 6. Troque SECRET_KEY e ADMIN_PASSWORD por valores seus
# 7. Salve e clique em "Reload" no painel Web
# ──────────────────────────────────────────────────────────────────

import sys
import os

# Caminho do projeto (substitua SEUUSERNAME)
PROJECT_PATH = '/home/SEUUSERNAME/sistema_ferias'
if PROJECT_PATH not in sys.path:
    sys.path.insert(0, PROJECT_PATH)

# Variáveis de ambiente (substitua os valores)
os.environ['SECRET_KEY']      = 'troque-por-chave-longa-e-aleatoria-aqui'
os.environ['ADMIN_USER']      = 'admin'
os.environ['ADMIN_PASSWORD']  = 'troque-por-senha-forte'

# Importa o app Flask
from app import app as application  # noqa
