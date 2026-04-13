# Research: Custom signup flow with tenant provisioning

**Feature:** Formulário de cadastro empresarial com campos tenant_name + phone_number que provisiona o tenant automaticamente.

**Date:** 2026-04-06  
**Project:** /home/RID

---

## 1. Current state analysis

### Project architecture (RID vs RockItDown)

RID é um projeto separado e mais moderno que o RockItDown. Diferenças chave:

| Aspecto | RID | RockItDown (referência) |
|---------|-----|------------------------|
| Python | 3.12 | 3.10 |
| django-tenants | vanilla `django_tenants` | `django_tenants_url` |
| User model | `accounts.TenantUser` (UUID PK) | `customers.TenantUser` |
| Tenant model | `tenants.Customer` (sem phone, sem tenant_name field) | `customers.Customer` (com phone_number, tenant_name) |
| Schema creation | Assíncrono via thread (post_save signal) | Síncrono em `provision_tenant_for_user` |
| Users location | Schema público (SHARED_APPS) | Migrados para schema do tenant |
| Membership | `TenantMembership` (user↔tenant_schema, roles) | Não existe |
| Langflow | Provisionamento automático de workspace por tenant | Embutido no Django |
| Allauth | v65+ com `ACCOUNT_SIGNUP_FIELDS` | Versão anterior com `ACCOUNT_SIGNUP_FORM_CLASS` |

### What exists in RID

| Component | File | Status |
|-----------|------|--------|
| `TenantAwareAccountAdapter` | `core/adapters.py` | Existe — salva `tenant_name` na session, fallback para `username` |
| `Customer` model | `apps/tenants/models.py` | Existe — `name`, `schema_name`, `public_tenant_id` (UUID), `plan`, Langflow fields |
| `Domain` model | `apps/tenants/models.py` | Existe — vanilla `DomainMixin` |
| `TenantUser` model | `apps/accounts/models.py` | Existe — `AbstractUser` com UUID PK, Langflow fields |
| `TenantMembership` model | `apps/accounts/models.py` | Existe — user↔tenant_schema com roles (owner/admin/member/viewer) |
| `provision_tenant_for_user` | `apps/tenants/services.py:50` | Existe — cria Customer + Domain, idempotente |
| `post_save` signal | `apps/tenants/signals.py` | Existe — provisiona schema + Langflow em background thread |
| `TenantAwareBackend` | `core/auth_backends.py` | Existe — auth via `user@tenant-domain` |
| Signup form customizado | — | **NÃO EXISTE** |
| Signup template customizado | — | **NÃO EXISTE** (usa default do allauth) |
| Signal allauth (email_confirmed) | — | **NÃO EXISTE** |
| `ACCOUNT_SIGNUP_FORM_CLASS` | — | **NÃO CONFIGURADO** no settings |

### What's missing (the gap)

O allauth está **completamente default** no RID. O adapter existe mas não faz nada útil porque:
1. Não existe form customizado com campo `tenant_name`
2. Não existe signal que leia a session e chame `provision_tenant_for_user`
3. `ACCOUNT_SIGNUP_FORM_CLASS` não está configurado no settings
4. Não existe template de signup customizado

### Settings allauth (RID)

```python
# core/settings.py
AUTH_USER_MODEL = "accounts.TenantUser"
ACCOUNT_LOGIN_METHODS = {"email"}                     # :181
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]  # :182
ACCOUNT_EMAIL_VERIFICATION = "mandatory"              # :183
ACCOUNT_ADAPTER = "core.adapters.TenantAwareAccountAdapter"     # :184
# NÃO tem: ACCOUNT_SIGNUP_FORM_CLASS
```

**Nota:** `ACCOUNT_SIGNUP_FIELDS` é uma configuração do allauth v65+ que define os campos do signup. Atualmente só tem email + password. Username **não está incluído**.

## 2. Architecture decisions (from framework analysis)

### allauth v65+ ACCOUNT_SIGNUP_FORM_CLASS

A cadeia de herança:

```
SignupExtraForm (ACCOUNT_SIGNUP_FORM_CLASS)    ← FORM CUSTOMIZADO
    ↑ herda
BaseSignupForm                                  ← allauth adiciona campos de ACCOUNT_SIGNUP_FIELDS
    ↑ herda
SignupForm                                      ← allauth adiciona password
```

**Contrato obrigatório:**
- Deve ser `forms.Form` (NÃO ModelForm)
- Deve implementar `def signup(self, request, user) -> None`
- `user` já está salvo no banco quando `signup()` é chamado

**Ordem de execução:**
1. `adapter.new_user(request)` — cria instância vazia
2. `adapter.save_user(request, user, form)` — popula e salva
3. `form.custom_signup(request, user)` — chama `signup()`
4. `setup_user_email()` — cria EmailAddress

### Session-based vs direct provisioning

| Abordagem | Prós | Contras |
|-----------|------|---------|
| **Session** (adapter atual) | Desacoplado | Frágil; dados perdem-se; debug difícil |
| **Direct no signup()** | Simples; atômico; testável | Form conhece o service |
| **Signal email_confirmed** | Provisiona só após verificação | Depende de session; race conditions |

**Recomendação para RID:** Provisionar no `signup()` method. O signal `post_save` no Customer já faz a criação de schema + Langflow em background thread. Basta criar o Customer no `signup()`.

### Fluxo proposto

```
User preenche form → allauth cria TenantUser → signup() cria Customer + Domain + TenantMembership(role=owner)
                                                    ↓
                                              post_save signal (já existe)
                                                    ↓
                                              Thread: schema migration + Langflow provision
```

### django-tenants constraints

- `TenantMixin.save()` DEVE ser chamado no public schema
- `schema_name`: max 63 chars, lowercase, `unique=True`
- No RID: `auto_create_schema = False` — schema criado via signal em background thread
- Users ficam no schema público (SHARED_APPS), não no schema do tenant

## 3. Key differences from RockItDown adapter

O adapter do RockItDown (`/home/RockItDown/src/core/adapters.py`) serviu como **inspiração** mas o RID tem diferenças:

| Aspecto | RockItDown | RID |
|---------|------------|-----|
| `save_user` stores | tenant_name + phone_number na session | Só tenant_name na session |
| Signal handler | `email_confirmed` + `user_signed_up` (dual) | Não existe (precisa criar) |
| Form | `SignupExtraForm` com phone_number | Não existe |
| Username | Usado como fallback para tenant_name | Não está em `ACCOUNT_SIGNUP_FIELDS` |
| Membership | Não existe | `TenantMembership` com role=owner |

## 4. UX research findings

### Recommended field order (conversion-optimized)
1. **Nome da Empresa** (tenant_name) — identidade primária, motivo da página
2. **Email Corporativo** — já em ACCOUNT_SIGNUP_FIELDS
3. **Telefone** — com máscara `(XX) XXXXX-XXXX`
4. **Senha** — já em ACCOUNT_SIGNUP_FIELDS
5. **Confirmar Senha** — já em ACCOUNT_SIGNUP_FIELDS

### Key UX decisions
- **Label:** "Nome da Empresa" (consistente com contexto B2B de consultoria/franquia)
- **Single form** — com 5 campos, wizard é overhead
- **Validação inline via fetch on blur** — endpoint para uniqueness de empresa e email
- **Help text:** "Será o identificador da sua empresa. Apenas letras e números."
- **Username:** NÃO incluir — allauth v65+ com `ACCOUNT_LOGIN_METHODS = {"email"}` não precisa

### Error states per field
| Campo | Help Text | Errors |
|-------|-----------|--------|
| Nome da Empresa | "Será o identificador da sua empresa" | "Nome já em uso", "Apenas letras e números", "Mínimo 3 caracteres" |
| Email | "Use o email principal da empresa" | "Email inválido", "Email já cadastrado" |
| Telefone | "Com DDD. Ex: (11) 99999-9999" | "Número inválido" |
| Senha | "Mínimo 8 caracteres" | "Muito curta" |
| Confirmar Senha | — | "Senhas não conferem" |

## 5. Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema creation falha | Tenant sem schema | `post_save` signal já faz rollback; Thread daemon loga erros |
| Race condition: dois signups com mesmo nome | `IntegrityError` | `clean_tenant_name()` no form + `unique` no DB + `get_or_create` no service |
| Session data perdida | Tenant não criado | Migrar para provisioning direto no `signup()` — sem session |
| Langflow provision falha | Tenant sem workspace | Graceful degradation — `langflow_workspace_id` fica null |
| Template allauth default não mostra campos custom | Form não funciona | Criar template `templates/account/signup.html` com iteração genérica |

## 6. Scope assessment — Small Track confirmed

- [x] <2 dias para implementar — infraestrutura existe (models, services, signals)
- [x] Usa padrões existentes — django-tenants + allauth já configurados
- [x] Sem dependências externas novas
- [x] Sem modelos novos — Customer, TenantUser, TenantMembership já existem
- [x] Sem integração multi-serviço — Django internal
- [x] Desenvolvedor único

## 7. What needs to be built (summary)

1. **`SignupExtraForm`** — form com `tenant_name` + `phone_number` + `signup()` method
2. **Settings** — adicionar `ACCOUNT_SIGNUP_FORM_CLASS` + `phone_number` ao `TenantUser` model
3. **`signup()` method** — cria Customer + Domain + TenantMembership(role=owner)
4. **Simplificar adapter** — remover lógica de session (provisioning direto no form)
5. **Template** — `templates/account/signup.html` customizado
6. **Validação** — `clean_tenant_name()` com uniqueness check
7. **Testes** — signup flow end-to-end
