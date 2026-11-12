"""Captura as vagas de emprego do Senac Ceará para a cidade de Sobral."""

import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from comum import (
    Secao,
    coletar_com_tolerancia,
    compactar,
    configurar_log,
    criar_driver,
    datas_para_iso,
    ler_argumentos,
    normalizar_rotulo,
    relatar_falhas,
    salvar_csv,
    salvar_markdown,
    texto,
)

URL = "https://carreiras.ce.senac.br/vagas"
CIDADE = "Sobral"
PASTA = Path(__file__).resolve().parent
ARQUIVO_CSV = PASTA / "vagas_senac_sobral.csv"
ARQUIVO_MARKDOWN = PASTA / "Vagas em Sobral.md"  # Nome modificado conforme modelo
ARQUIVO_DEBUG_HTML = PASTA / "debug_vagas.html"
ARQUIVO_DEBUG_PNG = PASTA / "debug_vagas.png"

SELETOR_LINKS_VAGAS = 'a[href*="/vaga/"]'
TEXTO_CARREGANDO = "Buscando vagas"
XPATH_CARREGAR_MAIS = (
    "//button[contains(., 'Carregar mais') or contains(., 'Ver mais') "
    "or contains(., 'Mostrar mais')]"
)
TEXTOS_SEM_VAGAS = ("nenhuma vaga", "não encontramos", "sem vagas")
SELETOR_DETALHES = "main"

CAMPOS = [
    "curso",  # 'curso' é usado pelo comum.py como título/cargo principal
    "url",
    "empresa",
    "cidade",
    "area",
    "tipo_contrato",
    "modalidade",
    "salario",
    "escolaridade",
    "carga_horaria",
    "quantidade_vagas",
    "data_publicacao",
    "data_encerramento",
    "descricao",
    "atividades_exigencias",
    "requisitos_curtos",
    "beneficios",
    "mais_informacoes",
    "coletado_em",
]

ROTULOS_CAMPOS = {
    "empresa": "empresa",
    "cidade": "cidade",
    "local": "cidade",
    "localidade": "cidade",
    "área": "area",
    "area": "area",
    "departamento": "area",
    "tipo de contratação": "tipo_contrato",
    "tipo de contrato": "tipo_contrato",
    "contrato": "tipo_contrato",
    "regime de contratação": "tipo_contrato",
    "modalidade": "modalidade",
    "salário": "salario",
    "salario": "salario",
    "remuneração": "salario",
    "escolaridade": "escolaridade",
    "formação": "escolaridade",
    "carga horária": "carga_horaria",
    "horário": "carga_horaria",
    "jornada": "carga_horaria",
    "quantidade de vagas": "quantidade_vagas",
    "vagas": "quantidade_vagas",
    "data de publicação": "data_publicacao",
    "publicada em": "data_publicacao",
    "data de encerramento": "data_encerramento",
    "encerra em": "data_encerramento",
    "descrição": "descricao",
    "descrição da vaga": "descricao",
    "atividades e exigências": "atividades_exigencias",
    "atividades": "atividades_exigencias",
    "responsabilidades": "atividades_exigencias",
    "requisitos": "requisitos_curtos",
    "benefícios": "beneficios",
    "beneficios": "beneficios",
    "mais informações": "mais_informacoes",
}

CAMPOS_DATA = ("data_publicacao", "data_encerramento")

# Adaptado para refletir exatamente os callouts internos do Markdown
SECOES = [
    Secao("descricao", "Descrição", "abstract", aberta=True),
    Secao("atividades_exigencias", "Atividades e Exigências", "example"),
    Secao("beneficios", "Benefícios", "tip"),
    Secao("mais_informacoes", "Mais informações", "warning"),
]

# Modificado para refletir as colunas: Empresa, Contratação, Salário, Carga horária
RESUMO_MARKDOWN = [
    ("empresa", "Empresa"),
    ("tipo_contrato", "Contratação"),
    ("salario", "Salário"),
    ("carga_horaria", "Carga horária"),
]

log = logging.getLogger(__name__)


def gerar_ancora(texto_vaga: str) -> str:
    """Gera link âncora a partir do nome da vaga para a tabela de resumo."""
    texto_limpo = (
        unicodedata.normalize("NFKD", texto_vaga.lower())
        .encode("ASCII", "ignore")
        .decode("utf-8")
    )
    texto_limpo = re.sub(r"[^\w\s-]", "", texto_limpo)
    return re.sub(r"[-\s]+", "-", texto_limpo).strip("-")


def extrair_campos(conteudo: str) -> dict[str, str]:
    campos: dict[str, list[str]] = {}
    atual: str | None = None

    for linha in (l.strip() for l in conteudo.splitlines()):
        if not linha:
            continue
        rotulo, separador, valor = linha.partition(":")
        chave = ROTULOS_CAMPOS.get(normalizar_rotulo(rotulo)) if separador else None
        if chave is None:
            chave = ROTULOS_CAMPOS.get(normalizar_rotulo(linha))
            valor = ""
        if chave:
            atual = chave
            campos.setdefault(atual, [])
            if valor.strip():
                campos[atual].append(valor.strip())
        elif atual:
            campos[atual].append(linha)

    return {chave: "\n".join(linhas) for chave, linhas in campos.items() if linhas}


def esperar_lista_carregar(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    xpath = f"//*[contains(normalize-space(text()), '{TEXTO_CARREGANDO}')]"
    wait.until(lambda navegador: not navegador.find_elements(By.XPATH, xpath))


def expandir_lista(driver: webdriver.Chrome, limite: int = 50) -> None:
    for _ in range(limite):
        botoes = driver.find_elements(By.XPATH, XPATH_CARREGAR_MAIS)
        if not botoes:
            return
        antes = len(driver.find_elements(By.CSS_SELECTOR, SELETOR_LINKS_VAGAS))
        driver.execute_script("arguments[0].click()", botoes[0])
        try:
            WebDriverWait(driver, 5).until(
                lambda navegador: (
                    len(navegador.find_elements(By.CSS_SELECTOR, SELETOR_LINKS_VAGAS))
                    > antes
                )
            )
        except TimeoutException:
            return


def listar_vagas(driver: webdriver.Chrome, wait: WebDriverWait) -> dict[str, str]:
    # Adicionando filtro de cidade na URL principal
    driver.get(f"{URL}?cidade={CIDADE}")

    try:
        esperar_lista_carregar(driver, wait)
    except TimeoutException:
        pass

    try:
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELETOR_LINKS_VAGAS))
        )
    except TimeoutException:
        pagina = texto(driver, "body").casefold()
        if any(frase in pagina for frase in TEXTOS_SEM_VAGAS):
            return {}
        raise RuntimeError("Nenhum link de vaga foi encontrado.") from None

    expandir_lista(driver)

    vagas: dict[str, str] = {}
    for link in driver.find_elements(By.CSS_SELECTOR, SELETOR_LINKS_VAGAS):
        url_vaga = (link.get_attribute("href") or "").split("#")[0]
        titulo = compactar(link.text) or compactar(link.get_attribute("title") or "")
        if url_vaga and url_vaga not in vagas:
            vagas[url_vaga] = titulo
    return vagas


def capturar_detalhes(
    driver: webdriver.Chrome, wait: WebDriverWait, url: str, titulo: str
) -> dict[str, str]:
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELETOR_DETALHES)))

    try:
        esperar_lista_carregar(driver, wait)
    except TimeoutException:
        pass

    vaga = texto(driver, "h1") or titulo or compactar(driver.title.split("|")[0])

    # O módulo comum.py usa a chave "curso" de forma fixa para gerar os títulos Markdown `##`
    detalhes = {"curso": vaga, "url": url}
    detalhes.update(extrair_campos(texto(driver, SELETOR_DETALHES)))

    detalhes.setdefault("cidade", CIDADE)
    detalhes.setdefault("empresa", "Senac / Parceiro")  # Fallback caso não encontre
    detalhes.setdefault("tipo_contrato", "Efetiva (CLT)")
    detalhes.setdefault("salario", "A combinar")

    return detalhes


def ficha_vaga(vaga: dict[str, str]) -> tuple[str, list[str]]:
    """Gera o bloco superior do callout igual ao template modelo."""
    cidade = compactar(vaga.get("cidade", CIDADE))
    area = compactar(vaga.get("area", ""))

    titulo = f"{cidade}, CE"
    if area:
        titulo += f" · {area}"

    linhas = []
    if tc := compactar(vaga.get("tipo_contrato", "")):
        linhas.append(f"**Tipo de contratação:** {tc}")
    if sal := compactar(vaga.get("salario", "")):
        linhas.append(f"**Salário:** {sal}")
    if ch := compactar(vaga.get("carga_horaria", "")):
        linhas.append(f"**Horário:** {ch}")
    if req := compactar(vaga.get("requisitos_curtos", vaga.get("escolaridade", ""))):
        # Exibe os requisitos de forma mais resumida no cabeçalho
        linhas.append(f"**Requisitos:** {req.split(chr(10))[0]}")

    return titulo, linhas


def main() -> None:
    args = ler_argumentos(__doc__)
    configurar_log()
    driver = criar_driver(visivel=args.visivel)

    try:
        wait = WebDriverWait(driver, 20)

        vagas_por_url = listar_vagas(driver, wait)
        if not vagas_por_url:
            print(f"Nenhuma vaga para {CIDADE} no momento.")
            return

        coletado_em = datetime.now().strftime("%Y-%m-%d %H:%M")
        vagas, falhas = coletar_com_tolerancia(
            list(vagas_por_url.items()),
            coletar=lambda item: capturar_detalhes(driver, wait, item[0], item[1]),
            descrever=lambda item: (item[1] or item[0], item[0]),
        )
        if not vagas:
            raise RuntimeError("Nenhuma vaga foi coletada.")

        for vaga in vagas:
            vaga["coletado_em"] = coletado_em

        vagas_csv = [datas_para_iso(vaga, CAMPOS_DATA) for vaga in vagas]
        salvar_csv(ARQUIVO_CSV, CAMPOS, vagas_csv)

        # Modifica a URL apenas na tabela de resumo para criar links âncoras locais
        vagas_resumo_ancora = []
        for vaga in vagas_csv:
            vaga_resumo = dict(vaga)
            vaga_resumo["url"] = f"#{gerar_ancora(vaga_resumo['curso'])}"
            vagas_resumo_ancora.append(vaga_resumo)

        salvar_markdown(
            ARQUIVO_MARKDOWN,
            cabecalho=[
                f"# Vagas do Senac Ceará - {CIDADE}",
                "",
                f"Catálogo consultado em [Carreiras Senac Ceará]({URL}).",
                "",
                f"**Coletado em:** {coletado_em}",
                "",
            ],
            rotulo_link="Abrir página da vaga",
            registros=vagas,  # Mantém os dados originais para as descrições
            ficha=ficha_vaga,
            secoes=SECOES,
            resumo=RESUMO_MARKDOWN,
            registros_resumo=vagas_resumo_ancora,  # Usa a variação com links âncora na tabela
            rotulo_resumo="Cargo",
            frontmatter={
                "tags": ["senac", "vagas", CIDADE.lower()],
                "unidade": f"Senac {CIDADE}",
                "coletado_em": coletado_em,
            },
        )
        print(f"{len(vagas)} vagas salvas em {ARQUIVO_CSV} e {ARQUIVO_MARKDOWN}")
        relatar_falhas(falhas)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
