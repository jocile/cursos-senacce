# Cursos, bolsas e vagas do Senac Sobral

Scripts em Python que usam Selenium para consultar o Senac Ceará (unidade
Senac Sobral) e exportar os dados para Markdown e, opcionalmente, CSV:

- `app.py` coleta os **cursos** da unidade;
- `app_psg.py` coleta as **oportunidades de bolsas** do Programa Senac de
  Gratuidade (PSG) da mesma unidade;
- `app_vagas.py` coleta as **vagas de emprego** de Sobral no portal Carreiras
  do Senac Ceará;
- `comum.py` reúne o código compartilhado pelos três (driver, leitura das abas,
  conversão de datas, tolerância a falhas e gravação dos arquivos).

Os quatro arquivos precisam ficar na mesma pasta.

## O que é coletado

Para cada curso, oportunidade ou vaga listada, o script abre a página
individual e coleta nome, link, descrição, datas, horário, carga horária e as
demais informações disponíveis (requisitos, período, conteúdo, formas de
pagamento, prazos, vagas, salário, benefícios etc.).

Arquivos gerados na mesma pasta dos scripts, criados ou substituídos a cada
execução:

| Script         | Markdown (sempre)            | CSV (só com `--csv`)          |
| -------------- | ---------------------------- | ----------------------------- |
| `app.py`       | `cursos_senac_sobral.md`     | `cursos_senac_sobral.csv`     |
| `app_psg.py`   | `cursos_senac_sobral_psg.md` | `cursos_senac_sobral_psg.csv` |
| `app_vagas.py` | `Vagas em Sobral.md`         | `vagas_senac_sobral.csv`      |

- **Markdown (padrão):** frontmatter YAML (`tags`, `unidade`, `coletado_em`),
  uma tabela de resumo com links no topo e, para cada item, **um único callout
  compacto** (compatível com Obsidian e Quartz). O título do callout traz
  período, horário e carga horária (ou local e área, no caso das vagas), e as
  linhas de destaque trazem preço ou salário, requisitos e prazos. Os textos
  longos (descrição, conteúdo programático, formas de pagamento, atividades,
  benefícios e avisos) ficam em callouts internos recolhíveis. Campos vazios
  são omitidos. O texto é o publicado no site, e as datas aparecem como
  dd/mm/aaaa.
- **CSV (opcional):** gerado apenas com `--csv`. UTF-8 com BOM, para abrir
  direto no Excel e filtrar em planilhas. Campos indisponíveis ficam vazios.

### Cifrão (`$`) no Markdown

No Quartz, o `$` é delimitador de fórmula matemática (KaTeX). Textos como
`R$ 280,00 ... R$ 49,00` na mesma linha faziam o trecho entre os dois cifrões
ser interpretado como fórmula e geravam avisos como `unicodeTextInMathMode`.
Por isso o `comum.py` grava todo `$` do conteúdo como `\$` no Markdown (ficha,
seções e tabela de resumo). O Quartz exibe normalmente "R$ 280,00". Frontmatter
e URLs não são alterados, e o CSV mantém o texto original, sem escape.

## Requisitos

- Python 3.10 ou superior;
- Google Chrome instalado;
- conexão com a internet para acessar os sites e, na primeira execução, baixar
  o ChromeDriver compatível.

## Instalação

No PowerShell, na pasta do projeto, crie e ative um ambiente virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências (`selenium` e `webdriver-manager`):

```powershell
python -m pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente, use o Python do ambiente
diretamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

> O `ipykernel` não faz mais parte do `requirements.txt`. Se você usa
> notebooks, instale-o à parte.

## Execução

Com o ambiente virtual ativado:

```powershell
python app.py          # cursos
python app_psg.py      # oportunidades PSG
python app_vagas.py    # vagas de emprego em Sobral
```

Ou, sem ativá-lo:

```powershell
.\.venv\Scripts\python.exe app.py
.\.venv\Scripts\python.exe app_psg.py
.\.venv\Scripts\python.exe app_vagas.py
```

### Opções

Valem para os três scripts e podem ser combinadas:

| Opção       | Efeito                                                                  |
| ----------- | ----------------------------------------------------------------------- |
| `--csv`     | grava também o CSV (por padrão só o Markdown é gerado)                  |
| `--visivel` | abre o Chrome com janela (por padrão roda em modo headless, sem janela) |

```powershell
python app.py                   # só Markdown
python app.py --csv             # Markdown + CSV
python app.py --csv --visivel   # Markdown + CSV, acompanhando no navegador
```

A saída do terminal mostra o progresso (`[2/6] Coletando: ...`) e, ao final,
quantos itens foram salvos e em quais arquivos. Se uma página falhar (por
exemplo, por timeout), o script registra um aviso, segue para as demais e lista
no fim o que não foi coletado. Só aborta se nenhum item for coletado.

Particularidades de cada script:

- `app_psg.py` seleciona **Senac Sobral** no filtro de unidades do catálogo PSG
  e visita a página de cada oportunidade filtrada;
- `app_vagas.py` filtra a listagem por `cidade=Sobral`, clica em "Carregar
  mais" até a lista parar de crescer e visita cada vaga. Se não houver vagas, o
  script informa e não gera arquivos. Se a lista não crescer após um clique, um
  aviso indica que ela pode estar incompleta.

A quantidade de itens muda conforme os catálogos são atualizados. Os scripts
são independentes: um não altera os arquivos do outro.

## Colunas do CSV

### `cursos_senac_sobral.csv`

| Grupo                | Colunas                                                                                                                                          |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Identificação        | `curso`, `url`                                                                                                                                   |
| Texto do site        | `descricao`, `preco`, `data`, `horario`, `carga_horaria`, `unidade`, `requisitos`, `periodo`, `conteudo`, `formas_pagamento`, `mais_informacoes` |
| Preço estruturado    | `preco_de`, `preco_por`, `parcelas`, `valor_parcela` (números com ponto decimal, ex.: `1656.90`)                                                 |
| Período e requisitos | `data_inicio`, `data_fim`, `dias_semana`, `idade_minima` (número), `escolaridade`                                                                |
| Coleta               | `coletado_em` (`AAAA-MM-DD HH:MM`)                                                                                                               |

As colunas estruturadas são extraídas do texto por expressões regulares. Se o
site mudar o formato, o campo derivado fica vazio e a coluna de texto original
continua preenchida. Nas colunas `conteudo` e `formas_pagamento`, os divisores
`———` do site viram quebras de linha.

### `cursos_senac_sobral_psg.csv`

`curso`, `url`, `categoria`, `unidade`, `horario`, `data`, `dias`, `situacao`,
`descricao`, `data_inicio`, `data_fim`, `carga_horaria`, `quantidade_vagas`,
`periodicidade`, `pre_requisitos`, `escolaridade`, `idade_minima`,
`prazo_inscricao`, `prazo_entrega_documentos` e `mais_informacoes`.

### `vagas_senac_sobral.csv`

`curso` (título da vaga), `url`, `empresa`, `cidade`, `area`, `tipo_contrato`,
`modalidade`, `salario`, `escolaridade`, `carga_horaria`, `quantidade_vagas`,
`data_publicacao`, `data_encerramento`, `descricao`, `atividades_exigencias`,
`requisitos_curtos`, `beneficios`, `mais_informacoes` e `coletado_em`.

A coluna se chama `curso` por compatibilidade com o `comum.py`, que usa esse
nome como título de cada registro. Quando o site não informa empresa, tipo de
contrato ou salário, o script preenche `Senac / Parceiro`, `Efetiva (CLT)` e
`A combinar`. O prefixo "Senac Ceará - Detalhes da Vaga:" é removido do título,
e textos de rodapé da página (compartilhar, candidatar-se, login) são
descartados antes da extração dos campos.

### Formato das datas

Nos CSVs, as colunas de data usam o formato ISO `AAAA-MM-DD`, que ordena
corretamente em planilhas e no pandas:

- `app.py`: `data`, `data_inicio`, `data_fim`;
- `app_psg.py`: `data`, `data_inicio`, `data_fim`, `prazo_inscricao`,
  `prazo_entrega_documentos`;
- `app_vagas.py`: `data_publicacao`, `data_encerramento`.

Quando o texto do site traz horário junto (`09/11/2026 ( 13:00 - 17:00 )`), o
CSV guarda só a data, e o horário continua na coluna `horario`. Se um campo de
data não puder ser reconhecido, ele fica vazio e o script emite um aviso. O
relatório Markdown mantém sempre o texto original do site.

## Verificação no Quartz

O script `find_latex_warnings.py` varre os arquivos `.md` de uma pasta e gera
`latex_warnings.md` com os trechos que o KaTeX interpretaria como fórmula
(acentos, travessões e `%` entre cifrões). Depois do escape do `$` feito pelo
`comum.py`, os arquivos gerados por estes scripts não devem mais aparecer no
relatório.

O `fix_latex_warnings.py` corrige manualmente uma lista fixa de arquivos
antigos e **não é necessário** para os Markdown gerados por estes scripts.

## Observações

- A coleta depende da estrutura atual dos sites do Senac Ceará; mudanças nas
  páginas podem exigir ajustes nos seletores dos scripts.
- Os detalhes refletem o conteúdo publicado pelo Senac no momento da execução
  (veja `coletado_em`). Consulte a página oficial para confirmar

## Referências

- [Site do Senac Ceará](https://www.senac.ce.gov.br/)
- [Vagas disponíveis no Senac Ceará](https://www.senac.ce.gov.br/vagas)
- [Programa Senac de Gratuidade (PSG)](https://www.senac.ce.gov.br/psg)
- [Catálogo de cursos do Senac Ceará](https://www.senac.ce.gov.br/cursos)
- [Quartz](https://quartz.obsidian.md/) (Obsidian) e [KaTeX](https://katex.org/)
- [KaTeX warnings](https://katex.org/docs/faq.html#warnings)
- [Instrutor Jocile Serra](https://jocile.com)
