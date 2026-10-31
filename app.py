"""Captura os cursos disponíveis na unidade Senac Sobral."""

import csv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://cursos.ce.senac.br/unidade/senac-sobral/"
ARQUIVO_CSV = "cursos_senac_sobral.csv"
ARQUIVO_MARKDOWN = "cursos_senac_sobral.md"
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


def texto_do_primeiro_elemento(
    driver: webdriver.Chrome | WebElement, seletor: str
) -> str:
    elementos = driver.find_elements(By.CSS_SELECTOR, seletor)
    return elementos[0].text.strip() if elementos else ""


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

    cabecalhos = driver.find_elements(By.CSS_SELECTOR, ".tab-header-item")
    for indice, cabecalho in enumerate(cabecalhos):
        driver.execute_script("arguments[0].click()", cabecalho)
        wait.until(
            lambda navegador, i=indice: "is-active"
            in navegador.find_elements(By.CSS_SELECTOR, ".tab-content-item")[i].get_attribute(
                "class"
            )
        )
        nome = cabecalho.text.strip()
        chave = ABAS_DETALHES.get(
            nome.casefold(), nome.casefold().replace(" ", "_")
        )
        paineis = driver.find_elements(By.CSS_SELECTOR, ".tab-content-item")
        detalhes[chave] = paineis[indice].text.strip()

    return detalhes


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
                linhas.extend(f"> {linha}" if linha else ">" for linha in valor.splitlines())
                linhas.append("")

    with open(ARQUIVO_MARKDOWN, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas).rstrip() + "\n")


def main() -> None:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)
        wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'a.content__title[href*="/produto/"]')
            )
        )

        cursos_por_url: dict[str, str] = {}
        for link in driver.find_elements(
            By.CSS_SELECTOR, 'a.content__title[href*="/produto/"]'
        ):
            titulo = link.text.strip()
            url = link.get_attribute("href")
            if titulo and url:
                cursos_por_url[url] = titulo

        if not cursos_por_url:
            raise RuntimeError("A página carregou, mas nenhum curso foi encontrado.")

        campos = [
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
        cursos = [
            capturar_detalhes(driver, wait, url, titulo)
            for url, titulo in cursos_por_url.items()
        ]

        with open(ARQUIVO_CSV, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(cursos)

        salvar_markdown(cursos)
        print(
            f"{len(cursos)} cursos salvos em {ARQUIVO_CSV} e {ARQUIVO_MARKDOWN}"
        )
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
