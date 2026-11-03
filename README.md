# Cursos do Senac Sobral

Scripts em Python que usam Selenium para consultar o catálogo do Senac Ceará
na unidade Senac Sobral e exportar os dados para CSV e Markdown:

- `app.py` coleta os **cursos** da unidade;
- `app_psg.py` coleta as **oportunidades de bolsas** do Programa Senac de
  Gratuidade (PSG) da mesma unidade;
- `comum.py` reúne o código compartilhado pelos dois (driver, leitura das abas,
  conversão de datas, tolerância a falhas e gravação dos arquivos).

Os três arquivos precisam ficar na mesma pasta.

## O que é coletado

Para cada curso (ou oportunidade) listado, o script abre a página individual e
coleta nome, endereço, descrição, datas, horário, carga horária, unidade e as
informações das abas de detalhes (requisitos, período, conteúdo, formas de
pagamento, prazos, vagas etc.).

Arquivos gerados na mesma pasta dos scripts, criados ou substituídos a cada
execução:

| Script       | CSV                           | Markdown                     |
| ------------ | ----------------------------- | ---------------------------- |
| `app.py`     | `cursos_senac_sobral.csv`     | `cursos_senac_sobral.md`     |
| `app_psg.py` | `cursos_senac_sobral_psg.csv` | `cursos_senac_sobral_psg.md` |

- **CSV:** UTF-8 com BOM, para abrir direto no Excel e filtrar em planilhas.
  Campos indisponíveis ficam vazios.
- **Markdown:** frontmatter YAML (`tags`, `unidade`, `coletado_em`), uma tabela
  de resumo com links no topo e, para cada item, **um único callout compacto**
  (compatível com Obsidian e Quartz). O título do callout traz período, horário
  e carga horária, e as linhas de destaque trazem preço, requisitos e prazos.
  Os textos longos (descrição, conteúdo programático, formas de pagamento e
  avisos) ficam em callouts internos recolhíveis. Campos vazios são omitidos. O
  texto é o publicado no site, e as datas aparecem como dd/mm/aaaa.

## Requisitos

- Python 3.10 ou superior;
- Google Chrome instalado;
- conexão com a internet para acessar o catálogo e, na primeira execução,
  baixar o ChromeDriver compatível.

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
python app.py        # cursos
python app_psg.py    # oportunidades PSG
```

Ou, sem ativá-lo:

```powershell
.\.venv\Scripts\python.exe app.py
.\.venv\Scripts\python.exe app_psg.py
```

Por padrão o Chrome roda em modo **headless** (sem janela). Para acompanhar a
coleta ou depurar, use a opção `--visivel`:

```powershell
python app.py --visivel
```

A saída do terminal mostra o progresso (`[2/6] Coletando: ...`) e, ao final,
quantos itens foram salvos. Se uma página falhar (por exemplo, por timeout), o
script registra um aviso, segue para as demais e lista no fim o que não foi
coletado. Só aborta se nenhum item for coletado.

O `app_psg.py` seleciona **Senac Sobral** no filtro de unidades do catálogo PSG
e visita a página de cada oportunidade filtrada. A quantidade de oportunidades
muda conforme o catálogo é atualizado. Os dois scripts são independentes: um
não altera os arquivos do outro.

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

### Formato das datas

Nos dois CSVs, as colunas de data usam o formato ISO `AAAA-MM-DD`, que ordena
corretamente em planilhas e no pandas:

- `app.py`: `data`, `data_inicio`, `data_fim`;
- `app_psg.py`: `data`, `data_inicio`, `data_fim`, `prazo_inscricao`,
  `prazo_entrega_documentos`.

Quando o texto do site traz horário junto (`09/11/2026 ( 13:00 - 17:00 )`), o
CSV guarda só a data, e o horário continua na coluna `horario`. Se um campo de
data não puder ser reconhecido, ele fica vazio e o script emite um aviso. O
relatório Markdown mantém sempre o texto original do site.

## Observações

- A coleta depende da estrutura atual do site do Senac Ceará; mudanças na página
  podem exigir ajustes nos seletores dos scripts.
- Os detalhes refletem o conteúdo publicado pelo Senac no momento da execução
  (veja `coletado_em`). Consulte a página oficial do curso para confirmar
  disponibilidade, valores e condições antes de tomar decisões.
- Se a coleta em modo headless trouxer menos dados que o esperado, rode com
  `--visivel` para comparar.
- Execute a coleta de forma moderada e respeite os termos de uso e as regras de
  acesso do site.
  