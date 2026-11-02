"""Captura os cursos disponíveis na unidade Senac Sobral."""

import csv
import logging

from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://cursos.ce.senac.br/unidade/senac-sobral/"
ARQUIVO_CSV = "cursos_senac_sobral.csv"
ARQUIVO_MARKDOWN = "cursos_senac_sobral.md"

SELETOR_LINKS_CURSOS = 'a.content__title[href*="/produto/"]'
SELETOR_CABECALHOS = ".tab-header-item"
SELETOR_PAINEIS = ".tab-content-item"

# 1.1 - Lista de colunas do CSV centralizada (ordem idêntica à anterior).
CAMPOS = [
    "curso",
    "url",
    "descricao",
    "preco",
    "data",
    "horário",
    "carga_horária",
    "unidade",
    "requisitos",
    "periodo",
    "conteudo",
    "formas_pagamento",
    "mais_informacoes",
]

ABAS_DETALHES = {
    "requisitos": "requisitos",
    "periodo": "periodo",
    "período": "periodo",
    "conteúdo": "conteudo",
    "formas de pagamento": "formas_pagamento",
    "mais informações": "mais_informacoes",
}
ROTULOS_MARKDOWN = {
    "descricao": "Descrição",
    "preco": "Preço",
    "data": "Data",
    "horário": "Horário",
    "carga_horária": "Carga horária",
    "unidade": "Unidade",
    "requisitos": "Requisitos",
    "periodo": "Período",
    "conteudo": "Conteúdo programático",
    "formas_pagamento": "Formas de pagamento",
    "mais_informacoes": "Mais informações",
}

# 1.2 - Erros que justificam pular um curso sem abortar a coleta inteira.
ERROS_TOLERADOS = (TimeoutException, StaleElementReferenceException)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def texto_do_primeiro_elemento(
    driver: webdriver.Chrome | WebElement, seletor: str
) -> str:
    elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
    return elementos[0].text.strip() if elementos else ""


def painel_ativo(navegador: webdriver.Chrome, indice: int) -> bool:
    """1.3 - Só consulta o painel se ele já existir no DOM."""
    paineis = navegador.find_elements(By.CSS_SELECTOR, SELETOR_PAINEIS)
    return len(paineis) > indice and "is-active" in (
        paineis[indice].get_attribute("class") or ""
    )


def capturar_detalhes(
    driver: webdriver.Chrome, wait: WebDriverWait, url: str, titulo: str
) -> dict[str, str]:
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3.content__title")))

    detalhes = {
        "curso": titulo,
        "url": url,
        "descricao": texto_do_primeiro_elemento(driver, ".content__description"),
        "preco": texto_do_primeiro_elemento(driver, ".item-prices"),
    }

    for item in driver.find_elements(By.CSS_SELECTOR, ".bar-item-content"):
        rotulo = texto_do_primeiro_elemento(item, ".item-content__label").rstrip(":")
        valor = texto_do_primeiro_elemento(item, ".item-content__info")
        if rotulo:
            detalhes[rotulo.lower().replace(" ", "_")] = valor

    total_abas = len(driver.find_elements(By.CSS_SELECTOR, SELETOR_CABECALHOS))
    for indice in range(total_abas):
        # 1.3 - Reconsulta o cabeçalho a cada volta para evitar elemento "stale".
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, SELETOR_CABECALHOS)
        if indice >= len(cabecalhos):
            break
        cabecalho = cabecalhos[indice]

        nome = cabecalho.text.strip()
        driver.execute_script("arguments[0].click()", cabecalho)
        wait.until(lambda navegador, i=indice: painel_ativo(navegador, i))

        chave = ABAS_DETALHES.get(nome.casefold(), nome.casefold().replace(" ", "_"))
        paineis = driver.find_elements(By.CSS_SELECTOR, SELETOR_PAINEIS)
        detalhes[chave] = paineis[indice].text.strip()

    return detalhes


def salvar_csv(cursos: list[dict[str, str]]) -> None:
    # 1.1 - Chaves fora de CAMPOS são ignoradas, mas avisadas no log.
    extras = {chave for curso in cursos for chave in curso} - set(CAMPOS)
    if extras:
        log.warning("Campos novos ignorados no CSV: %s", ", ".join(sorted(extras)))

    with open(ARQUIVO_CSV, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(
            arquivo, fieldnames=CAMPOS, extrasaction="ignore", restval=""
        )
        escritor.writeheader()
        escritor.writerows(cursos)


def salvar_markdown(cursos: list[dict[str, str]]) -> None:
    linhas = [
        "# Cursos do Senac Sobral",
        "",
        f"Catálogo consultado em [Senac Ceará]({URL}).",
        "",
    ]

    for curso in cursos:
        linhas.extend(
            [
                f"## {curso['curso']}",
                "",
                f"[Abrir página do curso]({curso['url']})",
                "",
            ]
        )
        for campo, rotulo in ROTULOS_MARKDOWN.items():
            valor = curso.get(campo, "").strip()
            if valor:
                linhas.append(f"> [!info] {rotulo}")
                linhas.extend(
                    f"> {linha}" if linha else ">" for linha in valor.splitlines()
                )
                linhas.append("")

    with open(ARQUIVO_MARKDOWN, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas).rstrip() + "\n")


def listar_cursos(driver: webdriver.Chrome, wait: WebDriverWait) -> dict[str, str]:
    driver.get(URL)
    wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, SELETOR_LINKS_CURSOS))
    )

    cursos_por_url: dict[str, str] = {}
    for link in driver.find_elements(By.CSS_SELECTOR, SELETOR_LINKS_CURSOS):
        titulo = link.text.strip()
        url = link.get_attribute("href")
        if titulo and url:
            cursos_por_url[url] = titulo

    if not cursos_por_url:
        raise RuntimeError("A página carregou, mas nenhum curso foi encontrado.")

    # 1.4 - Log da contagem para detectar mudanças (ex.: paginação) ao longo do tempo.
    log.info("%d cursos encontrados na listagem.", len(cursos_por_url))
    return cursos_por_url


def main() -> None:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    try:
        wait = WebDriverWait(driver, 20)
        cursos_por_url = listar_cursos(driver, wait)

        cursos: list[dict[str, str]] = []
        falhas: list[tuple[str, str]] = []
        total = len(cursos_por_url)

        # 1.2 - Falha em um curso não derruba os demais.
        for posicao, (url, titulo) in enumerate(cursos_por_url.items(), start=1):
            log.info("[%d/%d] Coletando: %s", posicao, total, titulo)
            try:
                cursos.append(capturar_detalhes(driver, wait, url, titulo))
            except ERROS_TOLERADOS as erro:
                log.warning("Falha em %s (%s): %s", titulo, url, type(erro).__name__)
                falhas.append((titulo, url))

        if not cursos:
            raise RuntimeError("Nenhum curso foi coletado com sucesso.")

        salvar_csv(cursos)
        salvar_markdown(cursos)
        print(f"{len(cursos)} cursos salvos em {ARQUIVO_CSV} e {ARQUIVO_MARKDOWN}")

        if falhas:
            print(f"Atenção: {len(falhas)} curso(s) não coletado(s):")
            for titulo, url in falhas:
                print(f"  - {titulo}: {url}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
