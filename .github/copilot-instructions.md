# Copilot Instructions para Sistema SaaS Django

## Arquitetura e Componentes

Este é um sistema SaaS multi-tenancy em Django com duas interfaces principais:
- **Admin Panel** (`/admin-panel/`): Para usuários staff/superuser gerenciarem o sistema
- **User Panel** (`/user-panel/`): Para usuários regulares gerenciarem suas contas/sites

### Estrutura de Apps
- `admin_panel/`: Interface administrativa (apenas staff)
- `user_panel/`: Interface do usuário (usuários regulares)
- `site_management/`: CRUD de sites (compartilhado entre painéis)
- `accounts/`: Sistema multi-tenancy com Account e AccountMembership
- `permissions/`: RBAC com decorators `@admin_required` e `@user_panel_required`
- `users/`: Modelo de usuário customizado
- `payments/`, `domains/`, `api/`: Módulos especializados

## Fluxos Críticos de Desenvolvimento

### Setup Local
```bash
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
npm install && npm run build-css
python manage.py migrate
python manage.py runserver
```

### Permissões e Acesso
- **Staff/Superuser**: Acesso automático ao admin panel via `@admin_required`
- **Usuários regulares**: Redirecionados para user panel se tentarem acessar admin
- **Site Management**: Acessível via `/user-panel/sites/` (inclui `site_management.urls`)

## Padrões Específicos do Projeto

### Decoradores de Permissão
```python
# Para views do admin panel
@admin_required  # Substitui @login_required + verificação manual is_staff

# Para views do user panel  
@user_panel_required  # Redireciona staff para admin (flexível com ?force_user_panel)
```

### Templates e Navegação
- **User Panel**: `templates/user_panel/base.html` + `partials/user_sidebar_content.html`
- **Admin Panel**: `templates/admin_panel/base_admin.html` + `partials/admin_sidebar_content.html`
- **Site URLs**: Use `{% url 'site_management:sites_list' %}` no user panel sidebar

### Formulários com Tailwind
```python
# Em forms.py, sempre defina widgets com classes Tailwind
widgets = {
    'field': forms.TextInput(attrs={
        'class': 'block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md...'
    })
}
```

## Integrações e Dependências

### Frontend
- **Tailwind CSS**: `npm run build-css` (produção) / `npm run dev-css` (watch)
- **Alpine.js**: Para interatividade (sidebar, dropdowns)
- **FontAwesome**: Ícones nos menus e botões

### URLs Críticas
- `/` → Redireciona baseado em `user.is_staff` (admin vs user panel)
- `/user-panel/sites/` → Inclui `site_management.urls` para usuários
- `/admin-panel/` → Interface administrativa protegida

### Banco de Dados
- **PostgreSQL** (produção): Porta 5438
- **SQLite** (desenvolvimento): Fallback automático
- **Multi-tenancy**: `Account` → `Site` → `User` via `AccountMembership`

## Comandos Não-óbvios

```bash
# CSS watch mode durante desenvolvimento
npm run dev-css

# Verificar permissões de usuário
python manage.py shell -c "from users.models import User; print([u.is_staff for u in User.objects.all()])"

# Health check Docker
curl http://localhost:8000/health/
```

## Evitar

- **Não** use `/sites/` diretamente nas URLs principais (removido para evitar conflitos de namespace)
- **Não** misture `@login_required` com verificações manuais de `is_staff` em admin views
- **Não** renderize campos de formulário sem usar os widgets definidos em `forms.py`

## Exemplos de Arquivos-Chave
- `app_project/settings.py`: configurações globais, leitura do `.env`.
- `accounts/`, `permissions/`, `api/`: exemplos de views, serializers, signals e RBAC.
- `manage.py`: entrypoint para comandos Django.
- `package.json`, `tailwind.config.js`, `build-css.js`: build frontend.

## Observações para Agentes
- Sempre consulte o `.env` para variáveis obrigatórias.
- Scripts de build e comandos de migração são essenciais para qualquer alteração estrutural.
- Siga a estrutura modular dos apps para novas features.
- Integrações externas devem ser opcionais e protegidas por checagem de variáveis de ambiente.
- Use exemplos dos apps existentes para novos endpoints, permissões ou integrações.

---
Seções ou padrões não documentados aqui podem ser encontrados em `README.md`, `plano_desenvolvimento.md` ou nos próprios apps.

## Regras que devem ser seguidas a risca!
1. o resumo dos ajustes não pode passar de um paragrafo.
2. se o mesmo problema surgir mais de uma vez, sempre mude a abordagem.
3. nunca altere estruturas fora do escopo do problema ou implementação.
4. Se não entender a solicitação, pergunte ao usuário.
5. Os ajustes devem ser especificos ao que foi solicitado e aos arquivos.
6. Só altere o necessário. Se não houver nada a ser alterado, não faça nada.
7. remoção, inclusão ou ajustes precisa validar que também foi ajustado em todos os pontos que tem essa referência.
8. Antes de confirma que o problema foi resolvido, verificar o terminal para analisar se não tem problema.
9. O uso do terminal para testes e verificações de erros estão autorizado para execuções do Agente sem necessidade de solicitação.