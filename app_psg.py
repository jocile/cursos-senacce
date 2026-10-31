"""Captura oportunidades de cursos PSG da unidade Senac Sobral."""

import csv
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://psg.ce.senac.br/oportunidades/"
ARQUIVO_CSV = "cursos_senac_sobral_psg.csv"
ARQUIVO_MARKDOWN = "cursos_senac_sobral_psg.md"

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
    "data_final",
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

ROTULOS_MARKDOWN = {
    "categoria": "Categoria",
    "unidade": "Unidade",
    "horario": "Horário",
    "data": "Datas anunciadas",
    "dias": "Dias da semana",
    "situacao": "Inscrições",
    "descricao": "Descrição",
    "data_inicio": "Data de início",
    "data_final": "Data final",
    "carga_horaria": "Carga horária",
    "quantidade_vagas": "Quantidade de vagas ofertadas",
    "periodicidade": "Periodicidade",
    "pre_requisitos": "Pré-requisitos",
    "escolaridade": "Escolaridade",
    "idade_minima": "Idade mínima",
    "prazo_inscricao": "Prazo para inscrição",
    "prazo_entrega_documentos": "Prazo para entrega dos documentos",
    "mais_informacoes": "Mais informações",
}

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
    "data final": "data_final",
    "carga horária": "carga_horaria",
    "unidade": "unidade",
}


def texto(elemento: WebElement, seletor: str) -> str:
    elementos = elemento.find_elements(By.CSS_SELECTOR, seletor)
    return elementos[0].text.strip() if elementos else ""


def normalizar_rotulo(rotulo: str) -> str:
    return re.sub(r"\s+", " ", rotulo).strip().rstrip(":").casefold()


def unidade_do_cartao(cartao: WebElement) -> str:
    informacoes = cartao.find_elements(By.CSS_SELECTOR, ".opportunities__info")
    return " ".join(informacoes[2].text.split()) if len(informacoes) >= 3 else ""


def listar_cursos_sobral(
    driver: webdriver.Chrome, wait: WebDriverWait
) -> list[dict[str, str]]:
    driver.get(URL)
    wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".opportunities__box")
        )
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
            (
                cartoes := navegador.find_elements(
                    By.CSS_SELECTOR, ".opportunities__box"
                )
            )
            and all(
                "sobral" in unidade_do_cartao(cartao).casefold()
                for cartao in cartoes
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
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".content__description")))

    detalhes = curso.copy()
    detalhes["descricao"] = texto(driver, ".content__description")

    for item in driver.find_elements(By.CSS_SELECTOR, ".bar-item-content"):
        rotulos = item.find_elements(By.CSS_SELECTOR, ".item-content__label")
        valores = item.find_elements(By.CSS_SELECTOR, ".item-content__info")
        for rotulo, valor in zip(rotulos, valores):
            chave = CHAVES_DADOS.get(normalizar_rotulo(rotulo.text))
            if chave:
                detalhes[chave] = valor.text.strip()

    cabecalhos = driver.find_elements(By.CSS_SELECTOR, ".tab-header-item")
    for indice, cabecalho in enumerate(cabecalhos):
        paineis = driver.find_elements(By.CSS_SELECTOR, ".tab-content-item")
        if indice >= len(paineis):
            continue

        driver.execute_script("arguments[0].click()", cabecalho)
        wait.until(
            lambda navegador, i=indice: len(
                navegador.find_elements(By.CSS_SELECTOR, ".tab-content-item")
            )
            > i
            and "is-active"
            in navegador.find_elements(By.CSS_SELECTOR, ".tab-content-item")[
                i
            ].get_attribute("class")
        )

        rotulo = normalizar_rotulo(cabecalho.text)
        chave = CHAVES_ABAS.get(rotulo)
        if chave:
            paineis = driver.find_elements(By.CSS_SELECTOR, ".tab-content-item")
            detalhes[chave] = paineis[indice].text.strip()

    return detalhes


def salvar_markdown(cursos: list[dict[str, str]]) -> None:
    linhas = [
        "# Cursos PSG do Senac Sobral",
        "",
        f"**Catálogo:** [Senac Ceará PSG]({URL})",
        "",
    ]

    for curso in cursos:
        linhas.extend(
            [
                f"## {curso['curso']}",
                "",
                f"[Abrir oportunidade]({curso['url']})",
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


def main() -> None:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    try:
        wait = WebDriverWait(driver, 20)
        oportunidades = listar_cursos_sobral(driver, wait)
        cursos = [
            capturar_detalhes(driver, wait, curso) for curso in oportunidades
        ]

        with open(ARQUIVO_CSV, "w", newline="", encoding="utf-8-sig") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
            escritor.writeheader()
            escritor.writerows(cursos)

        salvar_markdown(cursos)
        print(
            f"{len(cursos)} oportunidades PSG do Senac Sobral salvas em "
            f"{ARQUIVO_CSV} e {ARQUIVO_MARKDOWN}"
        )
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
