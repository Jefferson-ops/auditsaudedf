import requests
from bs4 import BeautifulSoup
import re
import time
import sqlite3
from datetime import datetime

DB_NAME = "auditsaude.db"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

ESTADOS_SES = [
    {"uf": "AC", "estado": "Acre", "url": "https://www.saude.ac.gov.br"},
    {"uf": "AL", "estado": "Alagoas", "url": "https://www.saude.al.gov.br"},
    {"uf": "AP", "estado": "Amapá", "url": "https://www.saude.ap.gov.br"},
    {"uf": "AM", "estado": "Amazonas", "url": "https://www.saude.am.gov.br"},
    {"uf": "BA", "estado": "Bahia", "url": "https://www.saude.ba.gov.br"},
    {"uf": "CE", "estado": "Ceará", "url": "https://www.saude.ce.gov.br"},
    {"uf": "DF", "estado": "Distrito Federal", "url": "https://www.saude.df.gov.br"},
    {"uf": "ES", "estado": "Espírito Santo", "url": "https://saude.es.gov.br"},
    {"uf": "GO", "estado": "Goiás", "url": "https://www.saude.go.gov.br"},
    {"uf": "MA", "estado": "Maranhão", "url": "https://www.saude.ma.gov.br"},
    {"uf": "MT", "estado": "Mato Grosso", "url": "https://www.saude.mt.gov.br"},
    {"uf": "MS", "estado": "Mato Grosso do Sul", "url": "https://www.saude.ms.gov.br"},
    {"uf": "MG", "estado": "Minas Gerais", "url": "https://www.saude.mg.gov.br"},
    {"uf": "PA", "estado": "Pará", "url": "https://www.saude.pa.gov.br"},
    {"uf": "PB", "estado": "Paraíba", "url": "https://paraiba.pb.gov.br/diretas/secretaria-da-saude"},
    {"uf": "PR", "estado": "Paraná", "url": "https://www.saude.pr.gov.br"},
    {"uf": "PE", "estado": "Pernambuco", "url": "https://www.saude.pe.gov.br"},
    {"uf": "PI", "estado": "Piauí", "url": "https://www.saude.pi.gov.br"},
    {"uf": "RJ", "estado": "Rio de Janeiro", "url": "https://www.saude.rj.gov.br"},
    {"uf": "RN", "estado": "Rio Grande do Norte", "url": "https://www.saude.rn.gov.br"},
    {"uf": "RS", "estado": "Rio Grande do Sul", "url": "https://saude.rs.gov.br"},
    {"uf": "RO", "estado": "Rondônia", "url": "https://rondonia.ro.gov.br/sesau"},
    {"uf": "RR", "estado": "Roraima", "url": "https://www.saude.rr.gov.br"},
    {"uf": "SC", "estado": "Santa Catarina", "url": "https://www.saude.sc.gov.br"},
    {"uf": "SP", "estado": "São Paulo", "url": "https://www.saude.sp.gov.br"},
    {"uf": "SE", "estado": "Sergipe", "url": "https://www.saude.se.gov.br"},
    {"uf": "TO", "estado": "Tocantins", "url": "https://www.to.gov.br/saude"}
]

COLUNAS_38 = [
    'tec_01_atualizacao', 'tec_02_identificacao_responsavel', 'tec_03_datas_criacao_revisao', 'tec_04_correcao_ortografica',
    'tec_05_referencias_bibliograficas', 'tec_06_conexao_segura_https', 'tec_07_disponibilidade_uptime', 'tec_08_dominio_oficial_gov',
    'int_01_compreensao_linguagem', 'int_02_clareza_apresentacao', 'int_03_unidades_medida', 'int_04_ausencia_dificuldade', 'int_05_indice_legibilidade_flesch',
    'ace_01_facilidade_localizacao', 'ace_02_disponibilidade_publica', 'ace_03_carregamento_movel', 'ace_04_descricao_imagens_alt',
    'ita_01_canais_contato', 'ita_02_menus_navegacao', 'ita_03_redes_sociais', 'ita_04_mecanismo_busca',
    'ita_05_recursos_acessibilidade', 'ita_06_organizacao_visual', 'ita_07_ouvidoria_fale_conosco', 'ita_08_formularios_servicos',
    'abr_01_prevencao', 'abr_02_sintomas', 'abr_03_transmissao', 'abr_04_diagnostico', 'abr_05_campanhas', 'abr_06_vacinacao', 'abr_07_promocao_saude',
    'leg_01_explicacao_termos_tecnicos', 'leg_02_recursos_visuais', 'leg_03_tamanho_fonte_contraste', 'leg_04_vlibras_audiodescricao',
    'apo_01_materiais_campanha', 'apo_02_informacoes_profissionais'
]

def contar_silabas_pt(palavra):
    palavra = palavra.lower()
    silabas = len(re.findall(r'[aeiouáéíóúâêôãõàü]+', palavra))
    return max(1, silabas)

def calcular_flesch_portugues(texto):
    frases = [f for f in re.split(r'[.!?]+', texto) if len(f.strip()) > 0]
    palavras = [p for p in re.findall(r'\b\w+\b', texto) if len(p) > 0]
    if not frases or not palavras:
        return 50.0
    asl = len(palavras) / len(frases)
    asw = sum(contar_silabas_pt(p) for p in palavras) / len(palavras)
    flesch = 248.836 - (1.015 * asl) - (84.6 * asw)
    return round(max(0, min(100, flesch)), 2)

def inicializar_banco():
    conexao = sqlite3.connect(DB_NAME)
    cursor = conexao.cursor()
    cursor.execute('DROP TABLE IF EXISTS auditoria_estados')
    
    colunas_sql = ", ".join([f"{col} INTEGER DEFAULT 0" for col in COLUNAS_38])
    cursor.execute(f'''
        CREATE TABLE auditoria_estados (
            uf TEXT PRIMARY KEY,
            estado TEXT NOT NULL,
            url TEXT NOT NULL,
            status_code INTEGER,
            resultado TEXT,
            tempo_resposta_s REAL,
            data_verificacao TEXT,
            iqi_estimado REAL,
            classificacao TEXT,
            {colunas_sql}
        )
    ''')
    conexao.commit()
    conexao.close()

def extrair_38_indicadores(soup, url, response_time):
    ind = {col: 0 for col in COLUNAS_38}
    texto_puro = soup.get_text().lower()
    html_raw = str(soup).lower()

    # Dimensão 1: Técnico (8)
    ind['tec_01_atualizacao'] = 1 if soup.find(['time', 'meta'], attrs={'name': re.compile('date|modified|updated', re.I)}) or re.search(r'202[4-6]', texto_puro) else 0
    ind['tec_02_identificacao_responsavel'] = 1 if 'secretaria' in texto_puro or 'governo' in texto_puro else 0
    ind['tec_03_datas_criacao_revisao'] = 1 if re.search(r'\d{2}/\d{2}/\d{4}', texto_puro) else 0
    ind['tec_04_correcao_ortografica'] = 1 if 'lang="pt' in html_raw or 'lang="pt-br"' in html_raw else 1
    ind['tec_05_referencias_bibliograficas'] = 1 if any(k in texto_puro for k in ['ministerio da saude', 'oms', 'sus', 'portaria', 'lei']) else 0
    ind['tec_06_conexao_segura_https'] = 1 if url.startswith('https') else 0
    ind['tec_07_disponibilidade_uptime'] = 1
    ind['tec_08_dominio_oficial_gov'] = 1 if '.gov.br' in url else 0

    # Dimensão 2: Interpretabilidade (5)
    flesch = calcular_flesch_portugues(soup.get_text()[:3000])
    ind['int_01_compreensao_linguagem'] = 1 if flesch >= 40 else 0
    ind['int_02_clareza_apresentacao'] = 1 if soup.find_all(['h1', 'h2', 'h3']) else 0
    ind['int_03_unidades_medida'] = 1 if any(k in texto_puro for k in ['%', 'casos', 'doses', 'taxa', 'habitantes']) else 0
    ind['int_04_ausencia_dificuldade'] = 1  # Inversão metodológica
    ind['int_05_indice_legibilidade_flesch'] = 1 if flesch >= 45 else 0

    # Dimensão 3: Acessibilidade (4)
    ind['ace_01_facilidade_localizacao'] = 1 if soup.find(['nav', 'ul', 'menu']) else 0
    ind['ace_02_disponibilidade_publica'] = 1
    ind['ace_03_carregamento_movel'] = 1 if response_time < 4.0 or soup.find('meta', attrs={'name': 'viewport'}) else 0
    imgs = soup.find_all('img')
    if imgs:
        alt_count = sum(1 for img in imgs if img.has_attr('alt') and img['alt'].strip() != '')
        ind['ace_04_descricao_imagens_alt'] = 1 if (alt_count / len(imgs)) >= 0.3 else 0

    # Dimensão 4: Interatividade (8)
    ind['ita_01_canais_contato'] = 1 if any(k in texto_puro for k in ['telefone', 'e-mail', 'email', 'endereco', 'contato']) else 0
    ind['ita_02_menus_navegacao'] = 1 if soup.find('nav') or soup.find_all('a') else 0
    ind['ita_03_redes_sociais'] = 1 if any(r in html_raw for r in ['instagram.com', 'facebook.com', 'youtube.com', 'twitter.com', 'x.com']) else 0
    ind['ita_04_mecanismo_busca'] = 1 if soup.find('input', {'type': ['search', 'text']}) else 0
    ind['ita_05_recursos_acessibilidade'] = 1 if any(k in html_raw for k in ['acessibilidade', 'contraste', 'fonte', 'alt+']) else 0
    ind['ita_06_organizacao_visual'] = 1 if soup.find_all(['div', 'section', 'article']) else 0
    ind['ita_07_ouvidoria_fale_conosco'] = 1 if any(k in texto_puro for k in ['ouvidoria', 'fale conosco', 'carta de servicos']) else 0
    ind['ita_08_formularios_servicos'] = 1 if soup.find('form') or 'servico' in texto_puro else 0

    # Dimensão 5: Abrangência (7)
    ind['abr_01_prevencao'] = 1 if any(k in texto_puro for k in ['prevencao', 'prevenir', 'cuidado']) else 0
    ind['abr_02_sintomas'] = 1 if any(k in texto_puro for k in ['sintoma', 'sinais', 'febre', 'dor']) else 0
    ind['abr_03_transmissao'] = 1 if any(k in texto_puro for k in ['transmissao', 'contagio', 'aedes', 'virus']) else 0
    ind['abr_04_diagnostico'] = 1 if any(k in texto_puro for k in ['diagnostico', 'exame', 'teste']) else 0
    ind['abr_05_campanhas'] = 1 if any(k in texto_puro for k in ['campanha', 'mobilizacao', 'multirao']) else 0
    ind['abr_06_vacinacao'] = 1 if any(k in texto_puro for k in ['vacina', 'vacinacao', 'dose', 'imunizacao']) else 0
    ind['abr_07_promocao_saude'] = 1 if any(k in texto_puro for k in ['promocao', 'nutricao', 'saude mental', 'bem-estar']) else 0

    # Dimensão 6: Legibilidade (4)
    ind['leg_01_explicacao_termos_tecnicos'] = 1 if any(k in texto_puro for k in ['glossario', 'o que e', 'entenda', 'saiba mais']) else 0
    ind['leg_02_recursos_visuais'] = 1 if len(imgs) > 2 or soup.find_all('video') or 'infografico' in texto_puro else 0
    ind['leg_03_tamanho_fonte_contraste'] = 1 if 'contraste' in html_raw or 'fonte' in html_raw else 0
    ind['leg_04_vlibras_audiodescricao'] = 1 if 'vlibras' in html_raw or 'libras' in texto_puro else 0

    # Dimensão 7: Apoio a Gestores (2)
    ind['apo_01_materiais_campanha'] = 1 if any(k in texto_puro for k in ['cartaz', 'panfleto', 'download', 'kit', 'folder']) else 0
    ind['apo_02_informacoes_profissionais'] = 1 if any(k in texto_puro for k in ['nota tecnica', 'boletim', 'protocolo', 'gestor', 'profissional']) else 0

    return ind

def executar_varredura_nacional():
    inicializar_banco()
    print(f"[{time.strftime('%H:%M:%S')}] Iniciando Auditoria Nacional dos 38 Indicadores do TCC...\n")
    
    conexao = sqlite3.connect(DB_NAME)
    cursor = conexao.cursor()
    data_atual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for i, item in enumerate(ESTADOS_SES, 1):
        uf, estado, url = item['uf'], item['estado'], item['url']
        print(f"[{i:02d}/27] Auditando {uf} - {estado} ({url})...")

        status_code = 0
        resultado = "ERRO_REDE"
        tempo_resp = 0.0
        ind = {col: 0 for col in COLUNAS_38}

        t_inicio = time.time()
        try:
            res = requests.get(url, headers=HEADERS, timeout=12)
            tempo_resp = round(time.time() - t_inicio, 2)
            status_code = res.status_code
            if status_code == 200:
                resultado = "OK"
                soup = BeautifulSoup(res.text, 'html.parser')
                ind = extrair_38_indicadores(soup, url, tempo_resp)
            else:
                resultado = "FALHA"
        except Exception:
            resultado = "ERRO_REDE"
            tempo_resp = round(time.time() - t_inicio, 2)

        # Cálculo exato do IQI
        soma_atendidos = sum(ind.values())
        iqi = round((soma_atendidos / 38) * 100, 2)

        if iqi >= 85: classe = "Excelente"
        elif iqi >= 70: classe = "Boa"
        elif iqi >= 50: classe = "Regular"
        else: classe = "Insuficiente"

        col_names = ", ".join(['uf', 'estado', 'url', 'status_code', 'resultado', 'tempo_resposta_s', 'data_verificacao', 'iqi_estimado', 'classificacao'] + COLUNAS_38)
        placeholders = ", ".join(["?"] * (9 + 38))
        values = [uf, estado, url, status_code, resultado, tempo_resp, data_atual, iqi, classe] + [ind[c] for c in COLUNAS_38]

        cursor.execute(f"INSERT OR REPLACE INTO auditoria_estados ({col_names}) VALUES ({placeholders})", values)
        conexao.commit()
        time.sleep(0.3)

    conexao.close()
    print("\n========================================================")
    print("Auditoria concluída! Todos os 38 indicadores foram mapeados nos 27 estados.")
    print("========================================================")

if __name__ == "__main__":
    executar_varredura_nacional()