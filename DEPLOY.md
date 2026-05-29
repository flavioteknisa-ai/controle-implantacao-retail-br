# 📱 Guia de Deployment Online

Instruções para colocar seu sistema online usando **Supabase + GitHub + Vercel**.

## ✅ Passo 1: Criar Repositório no GitHub

1. Acesse [github.com/new](https://github.com/new)
2. Crie um repositório com o nome: **`controle-implantacao-retail-br`**
3. **NÃO** inicialize com README (vamos fazer push do código existente)
4. Clique em "Create repository"

**Resultado**: Você terá uma URL tipo `https://github.com/seu-usuario/controle-implantacao-retail-br.git`

---

## ✅ Passo 2: Criar Projeto no Supabase

1. Acesse [supabase.com](https://supabase.com)
2. Clique em "New Project"
3. Preencha:
   - **Name**: `controle-implantacao-retail-br`
   - **Database Password**: Gere uma senha forte (salve em local seguro)
   - **Region**: Escolha a mais próxima (ex: Brazil/São Paulo)
4. Aguarde criação do projeto (~5 minutos)

**Resultado**: Você terá as credenciais de conexão

---

## ✅ Passo 3: Obter Credenciais do Supabase

No painel do Supabase, vá para **Settings → Database → Connection string**:

```
postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

Salve também:
- **Host**: `[HOST]`
- **Database**: `postgres`
- **User**: `postgres`
- **Password**: `[PASSWORD]`
- **Port**: `5432`

---

## ✅ Passo 4: Fazer Push do Código para GitHub

No terminal do seu projeto:

```bash
cd C:/Users/Teknisa/Desktop/Claude/sistema_ferias

# Inicializar git
git init

# Adicionar todos os arquivos
git add .

# Commit inicial
git commit -m "Initial commit: Sistema Controle Implantação Retail BR"

# Adicionar remote (SUBSTITUA pela URL do seu repositório)
git remote add origin https://github.com/SEU-USUARIO/controle-implantacao-retail-br.git

# Push para main
git branch -M main
git push -u origin main
```

---

## ✅ Passo 5: Migrar Dados para Supabase

1. Copie a connection string do Supabase
2. Crie um arquivo `.env` no projeto com:

```env
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres?sslmode=require
FLASK_ENV=production
SECRET_KEY=sua-chave-secreta-super-segura-aqui
```

3. Execute a migração:

```bash
python migrate_to_supabase.py
```

✅ Se vir "MIGRAÇÃO CONCLUÍDA COM SUCESSO!", está tudo ok!

---

## ✅ Passo 6: Deploy no Vercel

1. Acesse [vercel.com](https://vercel.com)
2. Clique em "New Project"
3. Clique em "Import Git Repository"
4. Conecte sua conta GitHub e selecione seu repositório
5. Na tela de configuração:
   - **Framework Preset**: Other
   - **Root Directory**: `.`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`

6. Clique em "Environment Variables" e adicione:

```
DATABASE_URL=postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres?sslmode=require
FLASK_ENV=production
SECRET_KEY=sua-chave-secreta-super-segura-aqui
```

7. Clique em "Deploy"

✅ Seu sistema estará online em alguns minutos!

---

## 🔗 Resultado Final

- **URL do Sistema**: `https://seu-projeto.vercel.app`
- **Database**: Supabase PostgreSQL
- **Repositório**: GitHub (seu código versionado)
- **Deployment**: Automático (qualquer push no main = atualização online)

---

## 📋 Checklist Final

- [ ] Repositório GitHub criado
- [ ] Projeto Supabase criado
- [ ] Código feito push para GitHub
- [ ] Dados migrados para Supabase
- [ ] Deploy realizado no Vercel
- [ ] Site online e funcionando

---

## ⚠️ Troubleshooting

**"Database connection refused"**
- Verifique se a connection string está correta em `.env`
- Confira se a senha não tem caracteres especiais não-encoded

**"Port already in use"**
- Use porta diferente: `python app.py --port 5001`

**"Module not found"**
- Instale dependências: `pip install -r requirements.txt`

---

**Pronto! Seu sistema agora está online, seguro e escalável!** 🎉
