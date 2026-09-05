# Ylookup deterministic tools

The Ylookup hackathon datasets are deliberately imperfect. These tools are designed to surface those imperfections deterministically; they do not use an LLM and never silently repair source data.

## Registered tools

| Tool | Input | Purpose |
|---|---|---|
| `ylookup_workbook_summary` | base64 Excel | Sheet/header/row inventory |
| `ylookup_bank_statement_review` | base64 bank-statement PDF | Parse statement transactions and check debit/credit integrity, duplicate references and balance roll-forward |
| `ylookup_bank_workbook_control` | base64 working workbook | Validate account/entity/counterparty/project/related-party references and source amount columns |
| `ylookup_journal_entry_control` | base64 working workbook | Validate DIU double-entry balance, completeness and transaction-reference consistency |
| `ylookup_investor_loader_control` | base64 investor GL + reference workbook | Validate legal-entity/currency, investor, deal/currency, CoA mappings and JE balancing |
| `ylookup_mapping_gap_control` | base64 verified loader | Extract unresolved mapping gaps for human review |
| `ylookup_movements_control` | base64 verified loader | Validate debit - credit = net movement |

## Design rules

1. **Decimal arithmetic** is used for monetary controls.
2. Default materiality/tolerance for dataset integrity checks is **0.01** in source currency.
3. Exceptions are returned as structured records with stable error codes.
4. Mapping gaps are surfaced, not guessed.
5. These tools are safe to call from an agent because they are deterministic and side-effect free.
6. LLM agents should interpret and explain these results, not perform accounting arithmetic themselves.

## Intended next layer

After these controls are stable, add deterministic transformation tools:

- bank statement PDF -> canonical bank transactions
- canonical bank transactions + reference mappings -> journal-entry lines
- investor-level GL + mapping workbook -> Phase I loader rows
- loader output -> reconciliation/evidence package

Those transformations should remain separate from validation so that the system can distinguish **what was received**, **what was derived**, and **what failed control**.
