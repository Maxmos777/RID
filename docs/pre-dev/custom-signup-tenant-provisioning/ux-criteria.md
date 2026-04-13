---
feature: custom-signup-tenant-provisioning
gate: 1
document: ux-criteria
date: 2026-04-06
author: ring:product-designer
research_ref: docs/pre-dev/custom-signup-tenant-provisioning/research.md
---

# UX Acceptance Criteria — Cadastro empresarial com provisionamento de tenant

## Problem validation

### Problem statement

**Who:** Donos de empresa (consultoria/franquia) que querem registar a sua organizacao na plataforma RID.

**What:** O formulario de signup actual e generico do allauth pede apenas email + senha. Nao recolhe informacoes empresariais (nome da empresa, telefone) necessarias para criar o tenant e identificar o cliente como organizacao B2B. O dono de empresa nao consegue criar a conta da sua empresa num unico passo.

**When:** No primeiro contacto com a plataforma — momento de conversao de visitante para cliente.

**Impact:**
- Impossibilidade de criar tenants no signup: sem campo `tenant_name`, o tenant nao e provisionado.
- Sem telefone, a equipa comercial nao tem canal de contacto directo para onboarding.
- Formulario generico nao transmite confianca para um produto B2B — parece app pessoal, nao plataforma empresarial.
- Cada signup incompleto exige intervencao manual para recolher dados em falta.

### Evidence

- **Analise de codigo:** `ACCOUNT_SIGNUP_FIELDS` tem apenas `["email*", "password1*", "password2*"]` — zero campos empresariais (settings.py:182).
- **Adapter existente:** `TenantAwareAccountAdapter.save_user()` ja tenta ler `tenant_name` do form, mas nunca encontra porque o form nao tem o campo (adapters.py:37-40).
- **Service existente:** `provision_tenant_for_user()` esta pronto e testado mas nunca e chamado no fluxo de signup (services.py:50).
- **Modelo existente:** `TenantMembership` com role system (owner/admin/member/viewer) esta pronto mas signup nao cria membership (accounts/models.py:28).
- **Padrao de mercado:** SaaS B2B (Slack, Notion, Linear) recolhem nome da organizacao no signup como campo primario.

### Validation status

**VALIDATED.** Infraestrutura backend existe (models, services, signals, adapter) mas o formulario e template estao em falta — gap puramente de frontend/form. Evidencia directa no codigo.

---

## Personas

### Persona 1: Carlos — Dono de consultoria

**Role:** Socio-fundador de consultoria de gestao com 10-50 colaboradores. Responsavel por decisoes de ferramentas e plataformas.

**Experience:** Gere empresas ha 10+ anos. Usa ferramentas SaaS diariamente (Google Workspace, Slack, CRMs). Nao e tecnico mas espera interfaces profissionais e intuitivas.

**Goals:**
1. Criar a conta da empresa na plataforma em menos de 2 minutos sem precisar de ajuda tecnica.
2. Comecar a configurar a plataforma imediatamente apos verificar o email.
3. Depois convidar a equipa com diferentes niveis de acesso.

**Pain points:**
1. Formularios longos ou confusos fazem-no desistir — tempo e dinheiro.
2. Falta de feedback claro quando algo da errado gera desconfianca na plataforma.
3. Receber email generico "confirm your email" em vez de algo profissional e em portugues.

### Persona 2: Marina — Gestora de franquia

**Role:** Responsavel pela operacao de uma unidade de franquia. Recebe indicacao da franqueadora para usar o RID.

**Experience:** 3-8 anos em gestao de franquias. Habilidade tecnica basica — usa WhatsApp, planilhas, sistemas de ponto. Nao instala software, apenas usa o que recebe.

**Goals:**
1. Seguir o passo-a-passo indicado pela franqueadora sem erros.
2. Registar a unidade com o nome exacto exigido pela rede de franquias.
3. Confirmar que o cadastro deu certo e que a plataforma esta pronta.

**Pain points:**
1. Mensagens de erro tecnicas (em ingles ou codigos) fazem-na sentir que errou algo grave.
2. Nao saber se o cadastro foi concluido com sucesso ou se falta algum passo.
3. Campos sem explicacao clara — "o que devo escrever aqui?"

---

## Jobs to be done

### Job 1: Registar a empresa na plataforma

**Statement:** Quando decido usar a plataforma RID para a minha empresa, quero criar a conta da organizacao de forma rapida e clara, para que possa comecar a configurar o ambiente e convidar a equipa.

- **Functional:** Preencher dados da empresa (nome, email, telefone) e criar credenciais num unico formulario.
- **Emotional:** Sentir confianca de que a plataforma e profissional e que os dados estao seguros.
- **Social:** Apresentar a plataforma a equipa com confianca — "ja criei a nossa conta".

**Priority:** Must Have.

### Job 2: Confirmar que o cadastro foi bem sucedido

**Statement:** Quando submeto o formulario de cadastro, quero receber confirmacao clara do proximo passo (verificar email), para que nao fique na duvida se deu certo ou nao.

- **Functional:** Ver pagina de confirmacao e receber email de verificacao em portugues.
- **Emotional:** Sentir que o processo esta sob controlo — sei o que vai acontecer a seguir.

**Priority:** Must Have.

---

## UX acceptance criteria

### Functional criteria

#### FC-001 — Formulario de cadastro empresarial

- [ ] O formulario de signup exibe 5 campos na seguinte ordem: Nome da Empresa, Email, Telefone, Senha, Confirmar Senha.
- [ ] O campo "Nome da Empresa" e o primeiro campo do formulario (acima do email).
- [ ] Todos os campos obrigatorios estao marcados com asterisco visual (*).
- [ ] O formulario submete via POST para o endpoint allauth de signup (`/accounts/signup/`).
- [ ] Apos submit bem sucedido, o sistema cria: TenantUser + Customer + Domain + TenantMembership(role=owner).
- [ ] Apos submit bem sucedido, o utilizador e redirecionado para a pagina de verificacao de email.
- [ ] O campo de telefone aceita formato brasileiro: `(XX) XXXXX-XXXX` ou `(XX) XXXX-XXXX`.
- [ ] O campo "Nome da Empresa" gera o `schema_name` via slugify (apenas letras minusculas, numeros e underscore).

#### FC-002 — Validacao de campos

- [ ] Validacao server-side obrigatoria em TODOS os campos (nao depender apenas de JS).
- [ ] Validacao inline (on blur via fetch) para: email (unicidade) e nome da empresa (unicidade + formato).
- [ ] Erros de validacao aparecem imediatamente abaixo do campo com erro, em vermelho, em portugues.
- [ ] O formulario preserva todos os valores preenchidos quando recarregado apos erro de validacao server-side.
- [ ] O campo "Nome da Empresa" valida: minimo 3 caracteres, apenas letras/numeros/espacos, unicidade.
- [ ] O campo "Telefone" valida formato brasileiro (10-11 digitos apos remover mascara).
- [ ] Erros de unicidade (email ou empresa ja cadastrados) mostram mensagem especifica, nao generica.

#### FC-003 — Pos-signup: verificacao de email

- [ ] Apos signup, o utilizador ve pagina com mensagem: "Enviamos um email de verificacao para [email]. Verifique sua caixa de entrada."
- [ ] O email de verificacao e enviado em portugues (pt-BR).
- [ ] Apos clicar no link de verificacao, o tenant schema e Langflow workspace sao provisionados assincronamente (via signal existente).
- [ ] Apos verificacao, o utilizador e redirecionado para `/app/` (LOGIN_REDIRECT_URL).

#### FC-004 — Link para login existente

- [ ] O formulario exibe link "Ja tem uma conta? Entre aqui" acima ou abaixo do formulario.
- [ ] O link direciona para `/accounts/login/`.

---

### Usability criteria

- [ ] O formulario e completavel em menos de 90 segundos por um utilizador que sabe os dados da sua empresa.
- [ ] O campo "Nome da Empresa" tem placeholder ou help text que explica o que preencher.
- [ ] Cada campo tem label visivel permanente (nao apenas placeholder que desaparece ao focar).
- [ ] O botao de submit esta claramente identificado como acao primaria: "Criar conta da empresa".
- [ ] O formulario usa uma unica coluna — sem layout multi-coluna que confunde a ordem de preenchimento.
- [ ] Apos erro de validacao, o foco do teclado move para o primeiro campo com erro.
- [ ] O campo de telefone aplica mascara visual automatica conforme o utilizador digita.
- [ ] Help text e visivel sem hover — exibido permanentemente abaixo do campo.

---

### Accessibility criteria

Nivel exigido: **WCAG 2.1 AA**

- [ ] Todos os campos `<input>` tem `<label>` associado via `for`/`id`.
- [ ] Contraste de texto/fundo >= 4.5:1 para texto normal; >= 3:1 para texto grande (18px+).
- [ ] O formulario e 100% navegavel por teclado: Tab percorre campos na ordem visual, Enter submete.
- [ ] Mensagens de erro usam `aria-describedby` ligando o campo ao texto de erro.
- [ ] Campos com erro tem `aria-invalid="true"`.
- [ ] O botao de submit tem tipo `type="submit"` (nao `type="button"` com JS).
- [ ] Help text dos campos esta ligado via `aria-describedby`.
- [ ] Formulario funciona sem JavaScript (validacao server-side como fallback).
- [ ] Foco visivel em todos os elementos interactivos (outline nao removido).

---

### Responsive criteria

- [ ] O formulario e legivel e utilizavel em viewport de 320px de largura minima sem scroll horizontal.
- [ ] Em mobile (< 768px): formulario ocupa largura total com padding lateral de 16px.
- [ ] Em desktop (>= 1024px): formulario centrado com largura maxima de 480px.
- [ ] Campos de input tem altura minima de 44px (touch target).
- [ ] Botao de submit tem largura 100% do formulario em todas as viewports.
- [ ] Texto do formulario e legivel sem zoom — minimo 16px para inputs (previne zoom automatico em iOS).

---

### Performance criteria

- [ ] Pagina de signup carrega em < 1s em conexao 3G (server-rendered, sem SPA bundle).
- [ ] Validacao inline (fetch on blur) responde em < 300ms.
- [ ] Submit do formulario processa em < 2s (criacao de user + tenant + membership).

---

## UI states inventory

### Formulario de signup

| Estado | Trigger | Comportamento | Feedback visual |
|--------|---------|---------------|-----------------|
| **Default** | Pagina carrega | Formulario vazio, todos os campos habilitados | Labels, help text, botao habilitado |
| **Filling** | Utilizador digita | Mascara de telefone aplica-se automaticamente | Caracteres aparecem; telefone formata-se |
| **Inline validation — checking** | Blur em campo de email ou empresa | Fetch para verificar unicidade | Spinner discreto ao lado do campo |
| **Inline validation — success** | Resposta positiva do fetch | Campo aceite | Check verde ao lado do campo (opcional) |
| **Inline validation — error** | Resposta negativa do fetch | Erro exibido | Borda vermelha + mensagem de erro abaixo |
| **Submitting** | Clique em "Criar conta" | Formulario desabilitado, request POST | Botao com loading spinner, texto "Criando..." |
| **Server error — validation** | POST retorna erros de validacao | Formulario recarrega com valores preservados | Campos com erro destacados, mensagens em vermelho |
| **Server error — 500** | Erro inesperado no servidor | Mensagem generica de erro | Banner de erro topo: "Erro ao criar a conta. Tente novamente." |
| **Success** | POST retorna redirect | Redirect para pagina de verificacao | Pagina de confirmacao de email |

---

## Error messages (pt-BR)

| Campo | Erro | Mensagem |
|-------|------|----------|
| Nome da Empresa | Vazio | "Informe o nome da empresa." |
| Nome da Empresa | Muito curto | "O nome deve ter pelo menos 3 caracteres." |
| Nome da Empresa | Caracteres invalidos | "Use apenas letras, numeros e espacos." |
| Nome da Empresa | Ja existe | "Ja existe uma empresa com este nome. Escolha outro." |
| Nome da Empresa | Nome reservado | "Este nome nao pode ser utilizado." |
| Email | Vazio | "Informe o email." |
| Email | Formato invalido | "Informe um email valido." |
| Email | Ja cadastrado | "Este email ja esta cadastrado. Deseja entrar?" (com link para login) |
| Telefone | Vazio | "Informe o telefone." |
| Telefone | Formato invalido | "Informe um telefone valido com DDD. Ex: (11) 99999-9999" |
| Senha | Vazio | "Informe a senha." |
| Senha | Muito curta | "A senha deve ter pelo menos 8 caracteres." |
| Senha | Muito comum | "Esta senha e muito comum. Escolha outra." |
| Confirmar Senha | Nao confere | "As senhas nao conferem." |

## Help text por campo

| Campo | Help text (permanente, abaixo do campo) |
|-------|----------------------------------------|
| Nome da Empresa | "Sera o identificador da sua empresa na plataforma." |
| Email | "Use o email principal da empresa. Sera usado para login." |
| Telefone | "Com DDD. Ex: (11) 99999-9999" |
| Senha | "Minimo 8 caracteres." |
| Confirmar Senha | — (sem help text) |
