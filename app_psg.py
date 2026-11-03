"""Captura oportunidades de cursos PSG da unidade Senac Sobral."""

import re
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from comum import (
    Secao,
    coletar_com_tolerancia,
    compactar,
    configurar_log,
    criar_driver,
    data_br,
    datas_para_iso,
    formatar_carga,
    ler_abas,
    ler_argumentos,
    normalizar_rotulo,
    relatar_falhas,
    salvar_csv,
    salvar_markdown,
    texto,
)

URL = "https://psg.ce.senac.br/oportunidades/"
PASTA = Path(__file__).resolve().parent  # arquivos gravados ao lado do script
ARQUIVO_CSV = PASTA / "cursos_senac_sobral_psg.csv"
ARQUIVO_MARKDOWN = PASTA / "cursos_senac_sobral_psg.md"

CAMPOS = [
    "curso",
    "url",
    "categoria",
    "unidade",
    "horario",
    "data",
    "dias",
    "situacao",
    "descricao",
    "data_inicio",
    "data_fim",
    "carga_horaria",
    "quantidade_vagas",
    "periodicidade",
    "pre_requisitos",
    "escolaridade",
    "idade_minima",
    "prazo_inscricao",
    "prazo_entrega_documentos",
    "mais_informacoes",
]

# Campos de data do CSV gravados em ISO (AAAA-MM-DD); o Markdown mantém o texto do site.
CAMPOS_DATA = (
    "data",
    "data_inicio",
    "data_fim",
    "prazo_inscricao",
    "prazo_entrega_documentos",
)

# Callouts internos recolhíveis (campo, rótulo, tipo) abaixo da ficha de cada oportunidade.
SECOES = [
    Secao("descricao", "Descrição", "abstract", aberta=True),
]

# Colunas (campo do CSV, título) da tabela de resumo no topo do Markdown.
RESUMO_MARKDOWN = [
    ("categoria", "Categoria"),
    ("data_inicio", "Início"),
    ("data_fim", "Fim"),
    ("carga_horaria", "Carga horária"),
    ("prazo_inscricao", "Prazo de inscrição"),
]

CHAVES_ABAS = {
    "quantidade de vagas ofertadas": "quantidade_vagas",
    "periodicidade": "periodicidade",
    "pré-requisitos": "pre_requisitos",
    "pre-requisitos": "pre_requisitos",
    "escolaridade": "escolaridade",
    "idade mínima": "idade_minima",
    "prazo para inscrição": "prazo_inscricao",
    "prazo para entrega dos documentos na unidade": "prazo_entrega_documentos",
    "mais informações": "mais_informacoes",
}

CHAVES_DADOS = {
    "data início": "data_inicio",
    "data final": "data_fim",
    "carga horária": "carga_horaria",
    "unidade": "unidade",
}


def ficha_oportunidade(curso: dict[str, str]) -> tuple[str, list[str]]:
    """Título e linhas de destaque do callout principal da oportunidade."""
    inicio = data_br(curso.get("data_inicio", ""))
    fim = data_br(curso.get("data_fim", ""))
    periodo = f"{inicio} a {fim}" if inicio and fim and inicio != fim else inicio
    titulo = " · ".join(
        parte
        for parte in (
            periodo,
            compactar(curso.get("horario", "")),
            formatar_carga(curso.get("carga_horaria", "")),
        )
        if parte
    )

    linhas = []
    if categoria := compactar(curso.get("categoria", "")):
        linhas.append(f"**Categoria:** {categoria}")

    # Prazos em destaque: são o que mais pesa na decisão.
    inscricao = data_br(curso.get("prazo_inscricao", ""))
    documentos = data_br(curso.get("prazo_entrega_documentos", ""))
    partes = [compactar(curso.get("situacao", ""))]
    if inscricao and inscricao == documentos:
        partes.append(f"inscrição e documentos até {inscricao}")
    else:
        if inscricao:
            partes.append(f"inscrição até {inscricao}")
        if documentos:
            partes.append(f"documentos até {documentos}")
    if prazos := " · ".join(parte for parte in partes if parte):
        linhas.append(f"**Prazos:** {prazos}")

    vagas = re.search(r"\d+", curso.get("quantidade_vagas", ""))
    periodicidade = compactar(curso.get("periodicidade", ""))
    detalhes = [
        f"{vagas.group()} vagas" if vagas else "",
        # Intervalos de datas repetem o título; só dias da semana interessam.
        "" if re.search(r"\d{2}/\d{2}", periodicidade) else periodicidade,
    ]
    if oferta := " · ".join(parte for parte in detalhes if parte):
        linhas.append(f"**Oferta:** {oferta}")

    requisitos = [
        " · ".join(
            compactar(linha).rstrip(".")
            for linha in curso.get(campo, "").splitlines()
            if linha.strip()
        )
        for campo in ("escolaridade", "idade_minima", "pre_requisitos")
    ]
    if texto := " · ".join(parte for parte in requisitos if parte):
        linhas.append(f"**Requisitos:** {texto}")

    if contato := compactar(curso.get("mais_informacoes", "")):
        linhas.append(f"**Contato:** {contato}")
    return titulo, linhas


def unidade_do_cartao(cartao: WebElement) -> str:
    informacoes = cartao.find_elements(By.CSS_SELECTOR, ".opportunities__info")
    return " ".join(informacoes[2].text.split()) if len(informacoes) >= 3 else ""


def listar_cursos_sobral(
    driver: webdriver.Chrome, wait: WebDriverWait
) -> list[dict[str, str]]:
    driver.get(URL)
    wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".opportunities__box"))
    )

    driver.find_element(By.ID, "dropdownMenuLink").click()
    wait.until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".dropdown-menu .filter__checkbox_unity")
        )
    )
    opcao_sobral = next(
        (
            item
            for item in driver.find_elements(
                By.CSS_SELECTOR, ".dropdown-menu .filter__item"
            )
            if " ".join(item.text.split()).casefold() == "senac sobral"
        ),
        None,
    )
    if opcao_sobral is None:
        raise RuntimeError("A opção Senac Sobral não foi encontrada no filtro.")

    checkbox_sobral = opcao_sobral.find_element(
        By.CSS_SELECTOR, ".filter__checkbox_unity"
    )
    if not checkbox_sobral.is_selected():
        checkbox_sobral.click()

    wait.until(
        lambda navegador: (
            (cartoes := navegador.find_elements(By.CSS_SELECTOR, ".opportunities__box"))
            and all(
                "sobral" in unidade_do_cartao(cartao).casefold() for cartao in cartoes
            )
        )
    )

    cursos = []
    for cartao in driver.find_elements(By.CSS_SELECTOR, ".opportunities__box"):
        informacoes = [
            " ".join(item.text.split())
            for item in cartao.find_elements(By.CSS_SELECTOR, ".opportunities__info")
        ]
        unidade = unidade_do_cartao(cartao)

        titulo = texto(cartao, "h5")
        links = cartao.find_elements(By.CSS_SELECTOR, 'a[href*="/oportunidade/"]')
        if not titulo or not links:
            continue

        cursos.append(
            {
                "curso": titulo,
                "url": links[0].get_attribute("href") or "",
                "categoria": texto(cartao, "small"),
                "unidade": unidade,
                "horario": informacoes[0] if informacoes else "",
                "data": informacoes[1] if len(informacoes) > 1 else "",
                "dias": informacoes[3] if len(informacoes) > 3 else "",
                "situacao": links[0].text.strip(),
            }
        )

    if not cursos:
        raise RuntimeError(
            "Nenhuma oportunidade da unidade Senac Sobral foi encontrada."
        )
    return cursos


def capturar_detalhes(
    driver: webdriver.Chrome, wait: WebDriverWait, curso: dict[str, str]
) -> dict[str, str]:
    driver.get(curso["url"])
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".content__description"))
    )

    detalhes = curso.copy()
    detalhes["descricao"] = texto(driver, ".content__description")

    for item in driver.find_elements(By.CSS_SELECTOR, ".bar-item-content"):
        rotulos = item.find_elements(By.CSS_SELECTOR, ".item-content__label")
        valores = item.find_elements(By.CSS_SELECTOR, ".item-content__info")
        for rotulo, valor in zip(rotulos, valores):
            chave = CHAVES_DADOS.get(normalizar_rotulo(rotulo.text))
            if chave:
                detalhes[chave] = valor.text.strip()

    detalhes.update(ler_abas(driver, wait, CHAVES_ABAS))

    return detalhes


def main() -> None:
    args = ler_argumentos(__doc__)
    configurar_log()
    driver = criar_driver(visivel=args.visivel)

    try:
        wait = WebDriverWait(driver, 20)
        oportunidades = listar_cursos_sobral(driver, wait)
        cursos, falhas = coletar_com_tolerancia(
            oportunidades,
            coletar=lambda curso: capturar_detalhes(driver, wait, curso),
            descrever=lambda curso: (curso["curso"], curso["url"]),
        )
        if not cursos:
            raise RuntimeError("Nenhuma oportunidade foi coletada com sucesso.")

        cursos_csv = [datas_para_iso(curso, CAMPOS_DATA) for curso in cursos]
        salvar_csv(ARQUIVO_CSV, CAMPOS, cursos_csv)
        salvar_markdown(
            ARQUIVO_MARKDOWN,
            cabecalho=[
                "# Cursos PSG do Senac Sobral",
                "",
                f"**Catálogo:** [Senac Ceará PSG]({URL})",
                "",
            ],
            rotulo_link="Abrir oportunidade",
            registros=cursos,
            ficha=ficha_oportunidade,
            secoes=SECOES,
            resumo=RESUMO_MARKDOWN,
            registros_resumo=cursos_csv,
            rotulo_resumo="Oportunidade",
            frontmatter={
                "tags": ["senac", "psg"],
                "unidade": "Senac Sobral",
                "coletado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
            },
        )
        print(
            f"{len(cursos)} oportunidades PSG do Senac Sobral salvas em "
            f"{ARQUIVO_CSV} e {ARQUIVO_MARKDOWN}"
        )
        relatar_falhas(falhas)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
