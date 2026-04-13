---
feature: custom-signup-tenant-provisioning
gate: 1
document: user-flows
date: 2026-04-06
author: ring:product-designer
ux_criteria_ref: docs/pre-dev/custom-signup-tenant-provisioning/ux-criteria.md
---

# User flows — Cadastro empresarial com provisionamento de tenant

---

## Flow 1: Cadastro completo (happy path)

### Entry points
- Utilizador clica em "Criar conta" ou "Cadastre-se" na landing page ou pagina de login.
- Utilizador acede directamente a `/accounts/signup/` via link partilhado.

### Happy path

```mermaid
flowchart TD
    A["Utilizador acede /accounts/signup/"] --> B["Formulario carrega (estado default)"]
    B --> C["Preenche Nome da Empresa"]
    C --> D["Blur: fetch verifica unicidade"]
    D --> E["Unicidade OK"]
    E --> F["Preenche Email"]
    F --> G["Blur: fetch verifica unicidade"]
    G --> H["Email disponivel"]
    H --> I["Preenche Telefone (mascara aplica-se)"]
    I --> J["Preenche Senha"]
    J --> K["Preenche Confirmar Senha"]
    K --> L["Clica: Criar conta da empresa"]
    L --> M["Botao: loading 'Criando...'"]
    M --> N["Django: cria TenantUser"]
    N --> O["signup: cria Customer + Domain + TenantMembership"]
    O --> P["post_save signal: thread provisiona schema + Langflow"]
    P --> Q["allauth envia email de verificacao"]
    Q --> R["Redirect: /accounts/confirm-email/"]
    R --> S["Utilizador ve: Verifique seu email"]
    S --> T["Utilizador abre email, clica link"]
    T --> U["allauth confirma email"]
    U --> V["Redirect: /app/ (dashboard)"]
```

### Steps (detalhe)

1. Utilizador acede a `/accounts/signup/`.
2. Sistema renderiza formulario com 5 campos vazios + labels + help text.
3. Utilizador preenche "Nome da Empresa" e sai do campo (blur).
4. Sistema faz fetch para `/accounts/check-company/?name=X` — responde OK.
5. Utilizador preenche "Email" e sai do campo (blur).
6. Sistema faz fetch para `/accounts/check-email/?email=X` — responde OK.
7. Utilizador preenche "Telefone" — mascara formata automaticamente.
8. Utilizador preenche "Senha" e "Confirmar Senha".
9. Utilizador clica "Criar conta da empresa".
10. Sistema desabilita formulario, botao mostra "Criando...".
11. Django/allauth cria TenantUser (schema publico).
12. `SignupExtraForm.signup()` cria Customer + Domain + TenantMembership(role=owner).
13. Signal `post_save` dispara thread de provisionamento (schema + Langflow).
14. allauth envia email de verificacao.
15. Redirect para pagina de confirmacao de email.
16. Utilizador verifica email via link.
17. Redirect para `/app/`.

---

## Flow 2: Erro de validacao inline — empresa ja existe

```mermaid
flowchart TD
    A["Preenche Nome da Empresa: 'Acme'"] --> B["Blur: fetch /check-company/?name=Acme"]
    B --> C{"Empresa existe?"}
    C -->|Sim| D["Exibe erro: 'Ja existe uma empresa com este nome.'"]
    D --> E["Borda vermelha + mensagem abaixo do campo"]
    E --> F["Utilizador corrige o nome"]
    F --> G["Blur: fetch com novo nome"]
    G --> H{"Existe?"}
    H -->|Nao| I["Erro removido, campo normal"]
    I --> J["Continua preenchimento"]
    C -->|Nao| J
```

---

## Flow 3: Erro de validacao inline — email ja cadastrado

```mermaid
flowchart TD
    A["Preenche Email: 'carlos@acme.com.br'"] --> B["Blur: fetch /check-email/?email=..."]
    B --> C{"Email existe?"}
    C -->|Sim| D["Exibe: 'Este email ja esta cadastrado. Deseja entrar?'"]
    D --> E{"Utilizador clica 'entrar'?"}
    E -->|Sim| F["Redirect: /accounts/login/"]
    E -->|Nao| G["Utilizador altera o email"]
    G --> H["Blur: novo fetch"]
    C -->|Nao| I["Continua preenchimento"]
    H --> I
```

---

## Flow 4: Erro de validacao server-side (submit)

```mermaid
flowchart TD
    A["Utilizador clica 'Criar conta da empresa'"] --> B["POST /accounts/signup/"]
    B --> C{"Validacao Django OK?"}
    C -->|Nao| D["Pagina recarrega com erros"]
    D --> E["Valores preservados em todos os campos"]
    E --> F["Erros exibidos abaixo dos campos invalidos"]
    F --> G["Foco move para primeiro campo com erro"]
    G --> H["Utilizador corrige e re-submete"]
    H --> B
    C -->|Sim| I["Signup prossegue (happy path)"]
```

### Cenarios de erro server-side

| Cenario | Causa | Mensagem | Acao de recuperacao |
|---------|-------|----------|---------------------|
| Race condition: empresa criada entre fetch e submit | Dois signups simultaneos | "Ja existe uma empresa com este nome. Escolha outro." | Alterar nome e re-submeter |
| Race condition: email registado entre fetch e submit | Dois signups simultaneos | "Este email ja esta cadastrado." | Alterar email ou ir para login |
| Senha demasiado curta | Validacao allauth | "A senha deve ter pelo menos 8 caracteres." | Corrigir senha |
| Senha demasiado comum | Validacao allauth | "Esta senha e muito comum. Escolha outra." | Escolher senha diferente |
| Senhas nao conferem | password1 != password2 | "As senhas nao conferem." | Corrigir confirmacao |
| Schema name reservado | "langflow", "public", etc. | "Este nome nao pode ser utilizado." | Escolher outro nome |

---

## Flow 5: Erro de servidor (500)

```mermaid
flowchart TD
    A["Utilizador clica 'Criar conta'"] --> B["POST /accounts/signup/"]
    B --> C{"Servidor responde?"}
    C -->|500| D["Banner de erro topo: 'Erro ao criar a conta...'"]
    D --> E["Formulario com valores preservados"]
    E --> F["Botao re-habilitado"]
    F --> G["Utilizador tenta novamente"]
    G --> B
    C -->|200/302| H["Happy path continua"]
```

---

## Flow 6: Navegacao para login (utilizador ja tem conta)

```mermaid
flowchart TD
    A["Utilizador acede /accounts/signup/"] --> B["Ve: 'Ja tem uma conta? Entre aqui.'"]
    B --> C["Clica link 'Entre aqui'"]
    C --> D["Redirect: /accounts/login/"]
```

---

## Flow 7: Reenvio de email de verificacao

```mermaid
flowchart TD
    A["Pagina: 'Verifique seu email'"] --> B{"Email recebido?"}
    B -->|Nao| C["Utilizador clica 'Reenviar email'"]
    C --> D["Sistema reenvia email"]
    D --> E["Mensagem: 'Email reenviado'"]
    E --> B
    B -->|Sim| F["Utilizador clica link no email"]
    F --> G["Email confirmado"]
    G --> H["Redirect: /app/"]
```

---

## State machine — Formulario de signup

```mermaid
stateDiagram-v2
    [*] --> Default: pagina carrega

    Default --> Filling: utilizador digita

    Filling --> InlineChecking: blur em email ou empresa
    InlineChecking --> InlineError: unicidade falhou
    InlineChecking --> InlineSuccess: unicidade OK
    InlineError --> Filling: utilizador corrige
    InlineSuccess --> Filling: continua preenchimento

    Filling --> Submitting: clica Criar conta
    InlineSuccess --> Submitting: clica Criar conta

    Submitting --> ValidationError: erros de validacao
    Submitting --> ServerError: erro 500
    Submitting --> Success: signup OK

    ValidationError --> Filling: utilizador corrige
    ServerError --> Filling: utilizador tenta novamente

    Success --> EmailVerification: redirect

    EmailVerification --> EmailResent: clica reenviar
    EmailResent --> EmailVerification: volta a esperar
    EmailVerification --> Verified: clica link no email

    Verified --> Dashboard: redirect /app/
```

---

## Decisoes de design documentadas

| Decisao | Alternativa descartada | Justificativa |
|---------|----------------------|---------------|
| Formulario single-page | Wizard multi-step | 5 campos nao justificam wizard. Single page reduz percepcao de complexidade. |
| Validacao inline + server-side | Apenas server-side | Inline reduz erros no submit e melhora percepcao de responsividade. Server-side e fonte de verdade. |
| "Nome da Empresa" primeiro | Email primeiro (padrao allauth) | Comunica contexto B2B imediatamente. Diferencia de signup pessoal. |
| Mascara de telefone | Campo livre | Reduz erros de formato. Padrao esperado em sites brasileiros. |
| Provisioning no signup() | Provisioning via session + signal | Directo, atomico, testavel. Elimina fragilidade de dados na session. |
| Link para login no formulario | Apenas na navbar | Reduz abandono de utilizadores que ja tem conta. Padrao universal. |
| Help text permanente | Help text on hover/focus | Visivel para todos sem interaccao. Essencial para persona Marina. |
