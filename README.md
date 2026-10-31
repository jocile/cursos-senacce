# Cursos do Senac Sobral

Script em Python que usa Selenium para consultar os cursos disponíveis na
unidade Senac Sobral e exportar informações de cada curso para um arquivo CSV.
O script `app_psg.py` também consulta as oportunidades de bolsas do Programa
Senac de Gratuidade (PSG) da mesma unidade.

## O que é coletado

Para cada curso listado na página da unidade, o script abre a página individual
e tenta coletar:

- nome e endereço da página do curso;
- descrição e preço;
- data, horário, carga horária e unidade;
- requisitos, período, conteúdo programático, formas de pagamento e outras
  informações exibidas nas abas de detalhes.

Os dados são salvos em dois arquivos:

- `cursos_senac_sobral.csv`, para abrir e filtrar os dados em uma planilha;
- `cursos_senac_sobral.md`, com os detalhes em callouts compatíveis com o
  Obsidian, para leitura em editores e visualizadores de Markdown.

Campos que não estiverem disponíveis na página podem ficar vazios no CSV e são
omitidos do relatório Markdown. O CSV é gravado em UTF-8 com BOM para facilitar
a abertura em planilhas, como o Microsoft Excel.

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

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação do ambiente, execute o script diretamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Execução

Com o ambiente virtual ativado:

```powershell
python app.py
```

Ou, sem ativá-lo:

```powershell
.\.venv\Scripts\python.exe app.py
```

O Chrome será aberto durante a coleta e fechado ao final. Os arquivos
`cursos_senac_sobral.csv` e `cursos_senac_sobral.md` serão criados ou
substituídos na pasta atual. A saída do terminal informa quantos cursos foram
salvos.

### Oportunidades PSG

Para capturar as oportunidades do PSG disponíveis na unidade Senac Sobral,
execute:

```powershell
python app_psg.py
```

Ou, sem ativar o ambiente virtual:

```powershell
.\.venv\Scripts\python.exe app_psg.py
```

Esse script seleciona **Senac Sobral** no filtro de unidades do catálogo PSG e
visita a página de cada oportunidade filtrada para coletar detalhes adicionais,
como descrição, datas, carga horária, vagas, pré-requisitos e prazos. A
quantidade de oportunidades pode mudar conforme o catálogo é atualizado. Ele
cria ou substitui
`cursos_senac_sobral_psg.csv` e `cursos_senac_sobral_psg.md`, sem alterar os
arquivos produzidos por `app.py`.

## Colunas do CSV

O arquivo inclui as colunas `curso`, `url`, `descricao`, `preco`, `data`,
`horário`, `carga_horária`, `unidade`, `requisitos`, `periodo`, `conteudo`,
`formas_pagamento` e `mais_informacoes`.

## Observações

- A coleta depende da estrutura atual do site do Senac Ceará; mudanças na página
  podem exigir ajustes nos seletores do script.
- Os detalhes refletem o conteúdo publicado pelo Senac no momento da execução.
  Consulte a página oficial do curso para confirmar disponibilidade, valores e
  condições antes de tomar decisões.
- Execute a coleta de forma moderada e respeite os termos de uso e as regras de
  acesso do site.
