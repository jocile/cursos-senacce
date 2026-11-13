# Relatório de Avisos LaTeX no Quartz

- **Total de arquivos analisados:** 20
- **Arquivos com problemas:** 2
- **Total de avisos:** 148

## Tipos de avisos

| Código | Descrição |
|--------|-----------|
| `unicodeTextInMathMode` | Caractere acentuado usado dentro de `$...$` |
| `unknownSymbol` | Caractere Unicode não reconhecido pelo KaTeX |
| `commentAtEnd` | `%` interpretado como comentário LaTeX dentro de fórmula |

## Arquivos com avisos

### 1. `Vagas em Sobral.md`

| Linha | Trecho | Avisos |
|------:|--------|--------|
| 18 | `1621.00 Horários 12X36 Modelo de trabalho Presencial Compartilhe Compartilhe ...` | `á` (unicodeTextInMathMode) |
| 20 | `1760.00 Horários 16:00 às 00:00 Modelo de trabalho Presencial Compartilhe Com...` | `á` (unicodeTextInMathMode), `à` (unicodeTextInMathMode), `Ç` (unicodeTextInMathMode), `Õ` (unicodeTextInMathMode) |
| 22 | `1900.00 Horários 17:00 às 01:00 Modelo de trabalho Presencial Compartilhe Com...` | `á` (unicodeTextInMathMode), `à` (unicodeTextInMathMode), `Á` (unicodeTextInMathMode) |
| 24 | `800.00 Horários Comercial Modelo de trabalho Presencial Compartilhe Compartil...` | `á` (unicodeTextInMathMode), `Ó` (unicodeTextInMathMode), `Á` (unicodeTextInMathMode) |
| 26 | `700.00 Horários Comercial Modelo de trabalho Presencial Compartilhe Compartil...` | `ã` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `Ê` (unicodeTextInMathMode) |
| 53 | `1621.00 Horários Comercial Modelo de trabalho Presencial Compartilhe Comparti...` | `ã` (unicodeTextInMathMode), `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `í` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `ê` (unicodeTextInMathMode) |
| 91 | `1670.00 Horários 16:00 às 00:00 Modelo de trabalho Presencial Compartilhe Com...` | `ã` (unicodeTextInMathMode), `é` (unicodeTextInMathMode), `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `í` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `õ` (unicodeTextInMathMode), `ê` (unicodeTextInMathMode), `à` (unicodeTextInMathMode) |
| 129 | `800.00 Horários Comercial Modelo de trabalho Presencial Compartilhe Compartil...` | `ã` (unicodeTextInMathMode), `é` (unicodeTextInMathMode), `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `í` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `õ` (unicodeTextInMathMode), `ê` (unicodeTextInMathMode), `à` (unicodeTextInMathMode), `Á` (unicodeTextInMathMode) |
| 153 | `800.00 Horários Comercial Modelo de trabalho Presencial Compartilhe Compartil...` | `ã` (unicodeTextInMathMode), `é` (unicodeTextInMathMode), `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `õ` (unicodeTextInMathMode), `ú` (unicodeTextInMathMode), `ê` (unicodeTextInMathMode), `Ã` (unicodeTextInMathMode), `Á` (unicodeTextInMathMode), `Ç` (unicodeTextInMathMode) |

### 2. `cursos_senac_sobral.md`

| Linha | Trecho | Avisos |
|------:|--------|--------|
| 15 | `) \| Idade mín. \| \| --- \| --- \| --- \| --- \| --- \| --- \| --- \| --- \| \| [ALFAIAT...` | `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `í` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `à` (unicodeTextInMathMode), `Ã` (unicodeTextInMathMode), `É` (unicodeTextInMathMode), `Ó` (unicodeTextInMathMode), `Á` (unicodeTextInMathMode), `Ç` (unicodeTextInMathMode) |
| 32 | `420,00** (até 10x de R` | `é` (unicodeTextInMathMode) |
| 42 | `600,00 > > Cartão de Crédito em até 12x de R` | `ã` (unicodeTextInMathMode), `é` (unicodeTextInMathMode) |
| 44 | `600,00 (Para essa forma de pagamento entrar em contato pelo número (85) 3270 ...` | `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `í` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `õ` (unicodeTextInMathMode), `ú` (unicodeTextInMathMode), `à` (unicodeTextInMathMode), `Á` (unicodeTextInMathMode) |
| 55 | `185,50** (até 4x de R` | `é` (unicodeTextInMathMode) |
| 65 | `265,00 > > Cartão de Crédito em até 6x de R` | `ã` (unicodeTextInMathMode), `é` (unicodeTextInMathMode) |
| 67 | `265,00 (Para essa forma de pagamento entrar em contato pelo número (85) 3270 ...` | `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `í` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `õ` (unicodeTextInMathMode), `ú` (unicodeTextInMathMode), `à` (unicodeTextInMathMode), `Á` (unicodeTextInMathMode) |
| 78 | `185,50** (até 4x de R` | `é` (unicodeTextInMathMode) |
| 88 | `265,00 > > Cartão de Crédito em até 6x de R` | `ã` (unicodeTextInMathMode), `é` (unicodeTextInMathMode) |
| 90 | `265,00 (Para essa forma de pagamento entrar em contato pelo número (85) 3270 ...` | `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `í` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `õ` (unicodeTextInMathMode), `ú` (unicodeTextInMathMode), `à` (unicodeTextInMathMode) |
| 101 | `266,00** (até 6x de R` | `é` (unicodeTextInMathMode) |
| 112 | `42,22 > > Depósito Bancário em até 1x de R` | `é` (unicodeTextInMathMode), `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode) |
| 124 | `82,98) > **Requisitos:** Idade mínima: 16 anos e cursando, no mínimo, o 2º an...` | `ã` (unicodeTextInMathMode), `é` (unicodeTextInMathMode), `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `í` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `õ` (unicodeTextInMathMode), `ú` (unicodeTextInMathMode), `ê` (unicodeTextInMathMode), `à` (unicodeTextInMathMode), `É` (unicodeTextInMathMode), `Ó` (unicodeTextInMathMode), `– (en dash, U+2013)` (unknownSymbol) |
| 145 | `1.991,52 > > Cartão de Crédito em até 12x de R` | `ã` (unicodeTextInMathMode), `é` (unicodeTextInMathMode) |
| 147 | `1.991,52 (Para esta forma de pagamento, entre em contato pelo número (85) 327...` | `ó` (unicodeTextInMathMode), `ú` (unicodeTextInMathMode), `– (en dash, U+2013)` (unknownSymbol) |
| 149 | `1.981,08 – Pagamento no ato da rematrícula (Para mais informações sobre as fo...` | `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `í` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `õ` (unicodeTextInMathMode), `ú` (unicodeTextInMathMode), `à` (unicodeTextInMathMode), `– (en dash, U+2013)` (unknownSymbol) |
| 160 | `196,00** (até 4x de R` | `é` (unicodeTextInMathMode) |
| 182 | `280,00 > > Cartão de Crédito em até 7x de R` | `ã` (unicodeTextInMathMode), `é` (unicodeTextInMathMode) |
| 184 | `280,00 (Para essa forma de pagamento entrar em contato pelo número (85) 3270-...` | `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `í` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `õ` (unicodeTextInMathMode), `ú` (unicodeTextInMathMode), `à` (unicodeTextInMathMode), `Ã` (unicodeTextInMathMode), `Ç` (unicodeTextInMathMode) |
| 195 | `319,20** (até 7x de R` | `é` (unicodeTextInMathMode) |
| 211 | `456,00 > > Cartão de Crédito em até 10x de R` | `ã` (unicodeTextInMathMode), `é` (unicodeTextInMathMode) |
| 213 | `456,00 (Para essa forma de pagamento entrar em contato pelo número (85) 3270 ...` | `ó` (unicodeTextInMathMode), `á` (unicodeTextInMathMode), `í` (unicodeTextInMathMode), `ç` (unicodeTextInMathMode), `õ` (unicodeTextInMathMode), `ú` (unicodeTextInMathMode), `à` (unicodeTextInMathMode) |
| 224 | `170,10** (até 4x de R` | `é` (unicodeTextInMathMode) |
| 238 | `243,00 > > Cartão de Crédito em até 6x de R` | `ã` (unicodeTextInMathMode), `é` (unicodeTextInMathMode) |
