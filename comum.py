"""Funções compartilhadas pelos scripts de coleta do Senac Ceará."""

import csv
import logging
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

SELETOR_CABECALHOS = ".tab-header-item"
SELETOR_PAINEIS = ".tab-content-item"

log = logging.getLogger(__name__)


def configurar_log() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def criar_driver() -> webdriver.Chrome:
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service)


def texto(elemento: webdriver.Chrome | WebElement, seletor: str) -> str:
    """Texto do primeiro elemento que casa com o seletor CSS, ou ''."""
    elementos = elemento.find_elements(By.CSS_SELECTOR, seletor)
    return elementos[0].text.strip() if elementos else ""


def normalizar_rotulo(rotulo: str) -> str:
    return re.sub(r"\s+", " ", rotulo).strip().rstrip(":").casefold()


def painel_ativo(navegador: webdriver.Chrome, indice: int) -> bool:
    """Só consulta o painel se ele já existir no DOM."""
    paineis = navegador.find_elements(By.CSS_SELECTOR, SELETOR_PAINEIS)
    return len(paineis) > indice and "is-active" in (
        paineis[indice].get_attribute("class") or ""
    )


def ler_abas(
    driver: webdriver.Chrome,
    wait: WebDriverWait,
    chaves: dict[str, str],
    *,
    aceitar_desconhecidas: bool = False,
) -> dict[str, str]:
    """Clica em cada aba de detalhes e devolve {chave: texto do painel}.

    `chaves` mapeia o rótulo normalizado (minúsculo, sem ':') para o nome do
    campo. Abas fora do mapa são ignoradas, a menos que `aceitar_desconhecidas`
    seja True; nesse caso o rótulo vira a chave (espaços -> '_').
    """
    resultado: dict[str, str] = {}
    total = len(driver.find_elements(By.CSS_SELECTOR, SELETOR_CABECALHOS))

    for indice in range(total):
        # Reconsulta a cada volta para evitar StaleElementReferenceException.
        cabecalhos = driver.find_elements(By.CSS_SELECTOR, SELETOR_CABECALHOS)
        paineis = driver.find_elements(By.CSS_SELECTOR, SELETOR_PAINEIS)
        if indice >= len(cabecalhos) or indice >= len(paineis):
            continue

        cabecalho = cabecalhos[indice]
        rotulo = normalizar_rotulo(cabecalho.text)
        chave = chaves.get(rotulo)
        if chave is None and aceitar_desconhecidas and rotulo:
            chave = rotulo.replace(" ", "_")
        if not chave:
            continue

        driver.execute_script("arguments[0].click()", cabecalho)
        wait.until(lambda navegador, i=indice: painel_ativo(navegador, i))
        paineis = driver.find_elements(By.CSS_SELECTOR, SELETOR_PAINEIS)
        resultado[chave] = paineis[indice].text.strip()

    return resultado


def salvar_csv(
    caminho: str, campos: list[str], registros: list[dict[str, str]]
) -> None:
    """Grava o CSV em UTF-8 com BOM; chaves fora de `campos` são avisadas e ignoradas."""
    extras = {chave for registro in registros for chave in registro} - set(campos)
    if extras:
        log.warning("Campos novos ignorados no CSV: %s", ", ".join(sorted(extras)))

    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(
            arquivo, fieldnames=campos, extrasaction="ignore", restval=""
        )
        escritor.writeheader()
        escritor.writerows(registros)


def salvar_markdown(
    caminho: str,
    cabecalho: list[str],
    rotulo_link: str,
    registros: list[dict[str, str]],
    rotulos: dict[str, str],
) -> None:
    """Gera o relatório com um callout `[!info]` por campo preenchido."""
    linhas = list(cabecalho)

    for registro in registros:
        linhas.extend(
            [
                f"## {registro['curso']}",
                "",
                f"[{rotulo_link}]({registro['url']})",
                "",
            ]
        )
        for campo, rotulo in rotulos.items():
            valor = registro.get(campo, "").strip()
            if valor:
                linhas.append(f"> [!info] {rotulo}")
                linhas.extend(
                    f"> {linha}" if linha else ">" for linha in valor.splitlines()
                )
                linhas.append("")

    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas).rstrip() + "\n")
