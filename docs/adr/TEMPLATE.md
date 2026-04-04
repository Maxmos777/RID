# ADR-{NNN} — {Título da Decisão}

**Data:** YYYY-MM-DD
**Estado:** Proposed
**Autores:** {nome ou role}
**Revisores:** {nome ou role}
**Contexto de código:** `{ficheiro(s) principais afectados — ex: api/deps.py:69}`

---

## Contexto

<!--
O que estava a acontecer no projecto que forçou esta decisão?
Descreve as forças em tensão, as restrições, e o estado antes da decisão.
Máximo 150 palavras. NÃO mencionar a solução aqui.
-->

## Decisão

<!--
A decisão tomada. Uma frase clara, afirmativa, no presente.
Exemplo: "Usamos sync_to_async com thread_sensitive=True para isolar o contexto de tenant..."
-->

## Alternativas Consideradas

| Alternativa | Motivo de rejeição |
|---|---|
| {alternativa A} | {razão concreta} |
| {alternativa B} | {razão concreta} |

## Consequências Positivas

- {consequência 1}
- {consequência 2}

## Consequências Negativas / Trade-offs

<!--
Obrigatório: mínimo 1 trade-off. ADR sem trade-offs é sinal de análise incompleta.
-->

- {trade-off 1}

## Compliance

<!--
Como verificar que esta decisão está a ser seguida.
Especificar pelo menos UM dos seguintes: test existente, comando grep, linter rule,
code comment obrigatório, ou item de PR checklist.
-->

```bash
# Exemplo de verificação
grep -n "{padrão}" {ficheiro}
```

## Referências

- `{ficheiro:linha}` — implementação de referência
- [{título}]({url}) — documentação externa relevante
