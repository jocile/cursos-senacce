"""Captura oportunidades de cursos PSG da unidade Senac Sobral."""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from comum import (
    configurar_log,
    criar_driver,
    ler_abas,
    normalizar_rotulo,
    salvar_csv,
    salvar_markdown,
    texto,
)

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
    configurar_log()
    driver = criar_driver()

    try:
        wait = WebDriverWait(driver, 20)
        oportunidades = listar_cursos_sobral(driver, wait)
        cursos = [capturar_detalhes(driver, wait, curso) for curso in oportunidades]

        salvar_csv(ARQUIVO_CSV, CAMPOS, cursos)
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
            rotulos=ROTULOS_MARKDOWN,
        )
        print(
            f"{len(cursos)} oportunidades PSG do Senac Sobral salvas em "
            f"{ARQUIVO_CSV} e {ARQUIVO_MARKDOWN}"
        )
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
