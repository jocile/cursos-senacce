"""Funções compartilhadas pelos scripts de coleta do Senac Ceará."""

import argparse
import csv
import json
import logging
import re
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import TypeVar

from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

T = TypeVar("T")

# Erros que justificam pular um item sem abortar a coleta inteira.
ERROS_TOLERADOS = (TimeoutException, StaleElementReferenceException)

SELETOR_CABECALHOS = ".tab-header-item"
SELETOR_PAINEIS = ".tab-content-item"

log = logging.getLogger(__name__)


def configurar_log() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def ler_argumentos(descricao: str | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=descricao)
    parser.add_argument(
        "--visivel",
        action="store_true",
        help="abre o Chrome com janela (por padrão roda em modo headless)",
    )
    return parser.parse_args()


def criar_driver(visivel: bool = False) -> webdriver.Chrome:
    opcoes = webdriver.ChromeOptions()
    if not visivel:
        opcoes.add_argument("--headless=new")
        opcoes.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opcoes)


def texto(elemento: webdriver.Chrome | WebElement, seletor: str) -> str:
    """Texto do primeiro elemento que casa com o seletor CSS, ou ''."""
    elementos = elemento.find_elements(By.CSS_SELECTOR, seletor)
    return elementos[0].text.strip() if elementos else ""


def normalizar_rotulo(rotulo: str) -> str:
    return re.sub(r"\s+", " ", rotulo).strip().rstrip(":").casefold()


def data_iso(texto: str) -> str:
    """'10/11/2026' ou '10/11/26' -> '2026-11-10'; '' se o formato não bater."""
    formato = "%d/%m/%Y" if len(texto.rsplit("/", 1)[-1]) == 4 else "%d/%m/%y"
    try:
        return datetime.strptime(texto, formato).strftime("%Y-%m-%d")
    except ValueError:
        return ""


def datas_para_iso(registro: dict[str, str], campos: Sequence[str]) -> dict[str, str]:
    """Cópia do registro com `campos` convertidos para ISO (AAAA-MM-DD).

    Usa a primeira data dd/mm/aaaa encontrada no texto (ex.: 'Até 10/11/2026'
    ou '09/11/2026 ( 13:00 - 17:00 )'). Se não houver data reconhecível, o campo
    fica vazio e um aviso é registrado. O registro original não é alterado, de
    modo que o relatório Markdown continue mostrando o texto do site.
    """
    convertido = dict(registro)
    for campo in campos:
        valor = registro.get(campo, "")
        if not valor:
            continue
        achado = re.search(r"\d{1,2}/\d{1,2}/(?:\d{4}|\d{2})\b", valor)
        convertido[campo] = data_iso(achado.group()) if achado else ""
        if not convertido[campo]:
            log.warning(
                "Data não reconhecida em %r (campo %s, %s)",
                valor,
                campo,
                registro.get("curso", "?"),
            )
    return convertido


def coletar_com_tolerancia(
    itens: Sequence[T],
    coletar: Callable[[T], dict[str, str]],
    descrever: Callable[[T], tuple[str, str]],
) -> tuple[list[dict[str, str]], list[tuple[str, str]]]:
    """Coleta cada item; uma falha tolerada não derruba os demais.

    `descrever` devolve (título, url) para o log. Retorna (coletados, falhas).
    """
    coletados: list[dict[str, str]] = []
    falhas: list[tuple[str, str]] = []
    for posicao, item in enumerate(itens, start=1):
        titulo, url = descrever(item)
        log.info("[%d/%d] Coletando: %s", posicao, len(itens), titulo)
        try:
            coletados.append(coletar(item))
        except ERROS_TOLERADOS as erro:
            log.warning("Falha em %s (%s): %s", titulo, url, type(erro).__name__)
            falhas.append((titulo, url))
    return coletados, falhas


def relatar_falhas(falhas: list[tuple[str, str]]) -> None:
    if falhas:
        print(f"Atenção: {len(falhas)} item(ns) não coletado(s):")
        for titulo, url in falhas:
            print(f"  - {titulo}: {url}")


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
    caminho: str | Path, campos: list[str], registros: list[dict[str, str]]
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


def _yaml(valor: str) -> str:
    """Texto entre aspas duplas (JSON é YAML válido), seguro para ':' e '#'."""
    return json.dumps(valor, ensure_ascii=False)


def _frontmatter(dados: dict[str, str | list[str]]) -> list[str]:
    linhas = ["---"]
    for chave, valor in dados.items():
        if isinstance(valor, list):
            linhas.append(f"{chave}:")
            linhas.extend(f"  - {_yaml(item)}" for item in valor)
        else:
            linhas.append(f"{chave}: {_yaml(valor)}")
    linhas.extend(["---", ""])
    return linhas


def salvar_markdown(
    caminho: str | Path,
    cabecalho: list[str],
    rotulo_link: str,
    registros: list[dict[str, str]],
    rotulos: dict[str, str],
    *,
    tipos: dict[str, str] | None = None,
    frontmatter: dict[str, str | list[str]] | None = None,
) -> None:
    """Gera o relatório com um callout por campo preenchido.

    `tipos` mapeia campo -> tipo do callout (padrão: info); `frontmatter`,
    se dado, é gravado como bloco YAML no topo do arquivo.
    """
    tipos = tipos or {}
    linhas = _frontmatter(frontmatter) if frontmatter else []
    linhas.extend(cabecalho)

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
                linhas.append(f"> [!{tipos.get(campo, 'info')}] {rotulo}")
                linhas.extend(
                    f"> {linha}" if linha else ">" for linha in valor.splitlines()
                )
                linhas.append("")

    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas).rstrip() + "\n")
