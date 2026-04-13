# PRD: Custom signup flow with tenant provisioning

**Status:** Draft  
**Date:** 2026-04-06  
**Author:** Pre-dev pipeline  
**Project:** RID (`/home/RID`)

---

## 1. Problem statement

O formulário de cadastro do RID usa o allauth completamente default — apenas email + senha. Não há como o usuário informar o nome da empresa nem telefone durante o signup. Sem esses dados, o tenant (Customer) não é provisionado automaticamente, exigindo criação manual via admin.

**Impacto:** Nenhum usuário consegue se cadastrar e ter seu workspace (tenant + Langflow) provisionado automaticamente. O fluxo self-service está bloqueado.

## 2. Goal

Permitir que donos de empresa se cadastrem via formulário web, informando nome da empresa e telefone, e que o tenant seja provisionado automaticamente após o signup — incluindo schema PostgreSQL, domínio e workspace Langflow.

## 3. Success metrics

| Metric | Target |
|--------|--------|
| Signup → tenant provisionado (end-to-end) | < 30s incluindo schema migration |
| Form submission errors por validação client-side | < 5% de submissões |
| Signup abandonment rate | Baseline (não há dados atuais) |

## 4. User stories

### US-1: Cadastro empresarial (P0 — must have)
**Como** dono de empresa,  
**Quero** me cadastrar informando o nome da minha empresa, email e telefone,  
**Para que** meu workspace seja criado automaticamente e eu possa começar a usar a plataforma.

**Critérios de aceite:**
1. Form de signup exibe: Nome da Empresa, Email, Telefone, Senha, Confirmar Senha
2. Nome da Empresa é validado: mínimo 3 caracteres, somente letras/números/espaços, unicidade
3. Telefone aceita formato brasileiro: (XX) XXXXX-XXXX ou +55XXXXXXXXXXX
4. Após submit, allauth cria TenantUser e envia email de verificação
5. Paralelamente, Customer + Domain + TenantMembership(role=owner) são criados
6. Signal post_save existente provisiona schema + Langflow em background
7. Após verificar email, usuário é redirecionado para `/app/`

### US-2: Validação inline de nome da empresa (P1 — should have)
**Como** usuário preenchendo o cadastro,  
**Quero** saber imediatamente se o nome da empresa já está em uso,  
**Para que** eu não perca tempo preenchendo o resto do formulário.

**Critérios de aceite:**
1. Ao sair do campo "Nome da Empresa" (blur), uma requisição AJAX verifica unicidade
2. Feedback visual: verde se disponível, vermelho com mensagem se já existe
3. Endpoint: `GET /accounts/check-name/?q=<nome>` retorna `{"available": bool}`

### US-3: Feedback pós-signup (P1 — should have)
**Como** usuário que acabou de se cadastrar,  
**Quero** ver uma mensagem clara sobre os próximos passos,  
**Para que** eu saiba que preciso verificar meu email.

**Critérios de aceite:**
1. Após signup, página de verificação mostra: "Enviamos um email para {email}. Verifique sua caixa de entrada."
2. Se o tenant ainda estiver sendo provisionado, não bloqueia o fluxo

## 5. Scope

### In scope
- Custom signup form (`SignupExtraForm`) com tenant_name + phone_number
- Settings: `ACCOUNT_SIGNUP_FORM_CLASS`
- `signup()` method que cria Customer + Domain + TenantMembership
- Template de signup customizado (`templates/account/signup.html`)
- Validação server-side (clean methods) + client-side (JS on blur para uniqueness)
- Campo `phone_number` no model TenantUser (migration)
- Simplificação do adapter (remover lógica de session — provisioning direto no form)
- Testes unitários para form validation + provisioning flow

### Out of scope
- Redesign visual completo da landing page
- OAuth/social signup (mantém allauth default)
- Fluxo de convite de membros (TenantMembership invite)
- Billing/Stripe durante signup
- Customização do email de verificação
- i18n (apenas pt-BR por agora)

## 6. Technical constraints

| Constraint | Detail |
|------------|--------|
| allauth v65+ | Usa `ACCOUNT_SIGNUP_FIELDS` — campos custom via `ACCOUNT_SIGNUP_FORM_CLASS` |
| Schema creation assíncrona | `auto_create_schema = False` no Customer; post_save signal cria em thread |
| Users no schema público | TenantUser em SHARED_APPS — não migra para schema do tenant |
| Email verification mandatory | `ACCOUNT_EMAIL_VERIFICATION = "mandatory"` — user só pode logar após verificar |
| Login por email | `ACCOUNT_LOGIN_METHODS = {"email"}` — sem username no signup |

## 7. Data flow

```
[Browser]                    [Django/allauth]                    [Background]
    │                              │                                  │
    │ POST /accounts/signup/       │                                  │
    │ {tenant_name, email,         │                                  │
    │  phone, password}            │                                  │
    │─────────────────────────────>│                                  │
    │                              │ 1. Validate form                 │
    │                              │ 2. adapter.save_user()           │
    │                              │    → TenantUser.save()           │
    │                              │ 3. form.signup()                 │
    │                              │    → Customer.save()             │
    │                              │    → Domain.save()     ─────────>│ post_save signal
    │                              │    → TenantMembership.save()     │ → thread: migrate_schemas
    │                              │ 4. setup_user_email()            │ → thread: Langflow provision
    │                              │    → send verification email     │
    │                              │                                  │
    │ 302 → /accounts/confirm/     │                                  │
    │<─────────────────────────────│                                  │
    │                              │                                  │
    │ GET /accounts/confirm/{key}/ │                                  │
    │─────────────────────────────>│                                  │
    │                              │ 5. Verify email                  │
    │                              │ 6. Login user                    │
    │ 302 → /app/                  │                                  │
    │<─────────────────────────────│                                  │
```

## 8. Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| `Customer` model | Existe | `apps/tenants/models.py` |
| `Domain` model | Existe | `apps/tenants/models.py` |
| `TenantUser` model | Existe | `apps/accounts/models.py` — precisa adicionar `phone_number` |
| `TenantMembership` model | Existe | `apps/accounts/models.py` |
| `provision_tenant_for_user` | Existe | `apps/tenants/services.py:50` |
| `post_save` signal | Existe | `apps/tenants/signals.py` — schema + Langflow |
| `TenantAwareAccountAdapter` | Existe | `core/adapters.py` — precisa simplificar |
| Signup template | NÃO existe | Precisa criar |
| `ACCOUNT_SIGNUP_FORM_CLASS` | NÃO configurado | Precisa adicionar ao settings |

## 9. Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| `signup()` falha após user criado | Low | High — user sem tenant | Wrap em try/except; log error; admin pode re-provisionar |
| Schema migration lenta bloqueia UX | Medium | Medium — user espera | Já é assíncrono (thread); UX não bloqueia |
| Nome de empresa com caracteres especiais | Medium | Low — schema inválido | `_normalize_schema_name()` já faz slugify |
| Duplo submit cria dois tenants | Low | Medium | `get_or_create` no service + unique constraint no DB |
