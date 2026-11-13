"""Captura os cursos disponíveis na unidade Senac Sobral."""

import logging
import re
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from comum import (
    Secao,
    brl,
    coletar_com_tolerancia,
    compactar,
    configurar_log,
    criar_driver,
    data_br,
    data_iso,
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

URL = "https://cursos.ce.senac.br/unidade/senac-sobral/"
PASTA = Path(__file__).resolve().parent  # arquivos gravados ao lado do script
ARQUIVO_CSV = PASTA / "cursos_senac_sobral.csv"
ARQUIVO_MARKDOWN = PASTA / "cursos_senac_sobral.md"

SELETOR_LINKS_CURSOS = 'a.content__title[href*="/produto/"]'

# 1.1 - Lista de colunas do CSV centralizada (ordem idêntica à anterior).
CAMPOS = [
    "curso",
    "url",
    "descricao",
    "preco",
    "data",
    "horario",
    "carga_horaria",
    "unidade",
    "requisitos",
    "periodo",
    "conteudo",
    "formas_pagamento",
    "mais_informacoes",
    # Fase 2 - colunas derivadas (as originais acima permanecem intactas).
    "preco_de",
    "preco_por",
    "parcelas",
    "valor_parcela",
    "data_inicio",
    "data_fim",
    "dias_semana",
    "idade_minima",
    "escolaridade",
    "coletado_em",
]

ABAS_DETALHES = {
    "requisitos": "requisitos",
    "periodo": "periodo",
    "período": "periodo",
    "conteúdo": "conteudo",
    "formas de pagamento": "formas_pagamento",
    "mais informações": "mais_informacoes",
}
# Callouts internos recolhíveis (campo, rótulo, tipo) abaixo da ficha de cada curso.
SECOES = [
    Secao("descricao", "Descrição", "abstract", aberta=True),
    Secao("conteudo", "Conteúdo programático", "example", lista=True),
    Secao("formas_pagamento", "Formas de pagamento", "tip"),
    Secao("mais_informacoes", "Mais informações", "warning"),
]

# Colunas (campo do CSV, título) da tabela de resumo no topo do Markdown.
RESUMO_MARKDOWN = [
    ("data_inicio", "Início"),
    ("data_fim", "Fim"),
    ("dias_semana", "Dias"),
    ("horario", "Horário"),
    ("carga_horaria", "Carga horária"),
    ("preco_por", "Preço (R$)"),
    ("idade_minima", "Idade mín."),
]

# 4.4 - Rótulos da barra de dados do site -> colunas sem acento.
CHAVES_DADOS = {
    "data": "data",
    "horário": "horario",
    "carga horária": "carga_horaria",
    "unidade": "unidade",
}

# Campos de data do CSV gravados em ISO (AAAA-MM-DD); o Markdown mantém o texto do site.
CAMPOS_DATA = ("data",)

log = logging.getLogger(__name__)

# 2.1 - Linhas de traços usadas pelo site como divisor dentro de uma mesma aba.
SEPARADOR = re.compile(r"\s*[—―]{3,}\s*")
CAMPOS_COM_SEPARADOR = {"conteudo", "formas_pagamento"}

VALOR = r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2})"
DATA = r"(\d{2}/\d{2}/\d{2,4})"


def chave_do_rotulo(rotulo: str) -> str:
    """Rótulo do site -> nome da coluna; rótulos novos viram snake_case."""
    normalizado = normalizar_rotulo(rotulo)
    return CHAVES_DADOS.get(normalizado, normalizado.replace(" ", "_"))


def formatar_preco(curso: dict[str, str]) -> str:
    """'~~R$ 280,00~~ **R$ 196,00** (até 4x de R$ 49,00)'; cai no texto cru se faltar dado."""
    de, por = curso.get("preco_de", ""), curso.get("preco_por", "")
    if not por:
        return " · ".join(
            compactar(linha) for linha in curso.get("preco", "").splitlines()
        )
    texto = f"~~{brl(de)}~~ **{brl(por)}**" if de and de != por else f"**{brl(por)}**"
    if curso.get("parcelas") and curso.get("valor_parcela"):
        texto += f" (até {curso['parcelas']}x de {brl(curso['valor_parcela'])})"
    return texto


def ficha_curso(curso: dict[str, str]) -> tuple[str, list[str]]:
    """Título e linhas de destaque do callout principal do curso."""
    inicio = data_br(curso.get("data_inicio") or curso.get("data", ""))
    fim = data_br(curso.get("data_fim", ""))
    periodo = f"{inicio} a {fim}" if inicio and fim and inicio != fim else inicio
    titulo = " · ".join(
        parte
        for parte in (
            periodo or compactar(curso.get("periodo", "")),
            formatar_carga(curso.get("carga_horaria", "")),
        )
        if parte
    )

    horario = " · ".join(
        parte
        for parte in (curso.get("dias_semana", ""), compactar(curso.get("horario", "")))
        if parte
    )
    linhas = []
    if horario:
        linhas.append(f"**Horário:** {horario}")
    if preco := formatar_preco(curso):
        linhas.append(f"**Preço:** {preco}")
    if requisitos := compactar(curso.get("requisitos", "")):
        linhas.append(f"**Requisitos:** {requisitos}")
    return titulo, linhas


def limpar_separadores(valor: str) -> str:
    """2.1 - Troca '———' por quebra de linha."""
    return SEPARADOR.sub("\n", valor).strip()


def limpar_preco(preco: str) -> str:
    """2.3 - Remove o rótulo 'MATRICULE-SE' que vem misturado ao preço."""
    linhas = (linha.strip() for linha in preco.splitlines())
    return "\n".join(l for l in linhas if l and l.upper() != "MATRICULE-SE")


def _decimal(correspondencia: re.Match | None) -> str:
    """'2.367,00' -> '2367.00'; vazio se não houve correspondência."""
    if not correspondencia:
        return ""
    return correspondencia.group(1).replace(".", "").replace(",", ".")


def parsear_preco(preco: str) -> dict[str, str]:
    """2.3 - Extrai preco_de, preco_por, parcelas e valor_parcela."""
    de = re.search(rf"De:\s*{VALOR}", preco)
    por = re.search(rf"Por:\s*{VALOR}", preco)
    parcelas = re.search(rf"(\d+)\s*x\s*de\s*{VALOR}", preco, re.IGNORECASE)

    if not por and not de:
        # Sem desconto: o preço único é o primeiro valor antes das parcelas.
        antes_das_parcelas = preco[: parcelas.start()] if parcelas else preco
        por = re.search(VALOR, antes_das_parcelas)

    return {
        "preco_de": _decimal(de),
        "preco_por": _decimal(por),
        "parcelas": parcelas.group(1) if parcelas else "",
        "valor_parcela": (
            parcelas.group(2).replace(".", "").replace(",", ".") if parcelas else ""
        ),
    }


def parsear_periodo(periodo: str) -> dict[str, str]:
    """2.4 - '10/11/26 a 03/12/26 – TER QUI' -> datas ISO e dias da semana."""
    achado = re.search(rf"{DATA}\s*a\s*{DATA}(?:\s*[–—-]\s*(.*))?", periodo)
    if not achado:
        return {"data_inicio": "", "data_fim": "", "dias_semana": ""}
    return {
        "data_inicio": data_iso(achado.group(1)),
        "data_fim": data_iso(achado.group(2)),
        "dias_semana": (achado.group(3) or "").strip(),
    }


def parsear_requisitos(requisitos: str) -> dict[str, str]:
    """2.4 - Extrai idade mínima e escolaridade do texto de requisitos."""
    idade = re.search(r"Idade mínima:\s*(\d+)", requisitos)
    escolaridade = re.search(
        r"Idade mínima:\s*\d+\s*anos?\s*(?:,|e)\s*(.+?)"
        r"(?:\s+e\s+Requisito/Conhecimento Específico:.*)?\.?\s*$",
        requisitos,
        re.DOTALL,
    )
    return {
        "idade_minima": idade.group(1) if idade else "",
        "escolaridade": escolaridade.group(1).strip() if escolaridade else "",
    }


def enriquecer(detalhes: dict[str, str]) -> None:
    """Acrescenta as colunas derivadas; as originais não são alteradas."""
    detalhes.update(parsear_preco(detalhes.get("preco", "")))
    detalhes.update(parsear_periodo(detalhes.get("periodo", "")))
    detalhes.update(parsear_requisitos(detalhes.get("requisitos", "")))


def capturar_detalhes(
    driver: webdriver.Chrome, wait: WebDriverWait, url: str, titulo: str
) -> dict[str, str]:
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3.content__title")))

    detalhes = {
        "curso": titulo,
        "url": url,
        "descricao": texto(driver, ".content__description"),
        "preco": limpar_preco(texto(driver, ".item-prices")),
    }

    for item in driver.find_elements(By.CSS_SELECTOR, ".bar-item-content"):
        rotulo = texto(item, ".item-content__label").rstrip(":")
        valor = texto(item, ".item-content__info")
        if rotulo:
            detalhes[chave_do_rotulo(rotulo)] = valor

    abas = ler_abas(driver, wait, ABAS_DETALHES, aceitar_desconhecidas=True)
    for chave, valor in abas.items():
        if chave in CAMPOS_COM_SEPARADOR:
            valor = limpar_separadores(valor)
        detalhes[chave] = valor

    enriquecer(detalhes)
    return detalhes


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
    args = ler_argumentos(__doc__)
    configurar_log()
    driver = criar_driver(visivel=args.visivel)

    try:
        wait = WebDriverWait(driver, 20)
        cursos_por_url = listar_cursos(driver, wait)

        coletado_em = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursos, falhas = coletar_com_tolerancia(
            list(cursos_por_url.items()),
            coletar=lambda item: capturar_detalhes(driver, wait, item[0], item[1]),
            descrever=lambda item: (item[1], item[0]),
        )
        if not cursos:
            raise RuntimeError("Nenhum curso foi coletado com sucesso.")
        for curso in cursos:
            curso["coletado_em"] = coletado_em

        cursos_csv = [datas_para_iso(curso, CAMPOS_DATA) for curso in cursos]
        salvar_markdown(
            ARQUIVO_MARKDOWN,
            cabecalho=[
                "# Cursos do Senac Sobral",
                "",
                f"Catálogo consultado em [Senac Ceará]({URL}).",
                "",
                f"**Coletado em:** {coletado_em}",
                "",
            ],
            rotulo_link="Abrir página do curso",
            registros=cursos,
            ficha=ficha_curso,
            secoes=SECOES,
            resumo=RESUMO_MARKDOWN,
            registros_resumo=cursos_csv,
            frontmatter={
                "tags": ["senac", "cursos"],
                "unidade": "Senac Sobral",
                "coletado_em": coletado_em,
            },
        )
        arquivos = [ARQUIVO_MARKDOWN]

        if args.csv:
            salvar_csv(ARQUIVO_CSV, CAMPOS, cursos_csv)
            arquivos.append(ARQUIVO_CSV)

        print(f"{len(cursos)} cursos salvos em " + " e ".join(map(str, arquivos)))
        relatar_falhas(falhas)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
