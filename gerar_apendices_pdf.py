import sqlite3
import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DB_NAME = "auditsaude.db"

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

def gerar_pdf_estado(row, output_dir="relatorios_pdf"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filepath = os.path.join(output_dir, f"Relatorio_TCC_{row['uf']}_{row['estado'].replace(' ', '_')}.pdf")
    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#0d3b66'), spaceAfter=8)
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#555555'), spaceAfter=12)
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#005f73'), spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=9, leading=12)

    story = []

    # Cabeçalho
    story.append(Paragraph("<b>UNIVERSIDADE DE BRASÍLIA — UnB</b>", sub_style))
    story.append(Paragraph("Faculdade de Ciências da Saúde | Departamento de Saúde Coletiva", sub_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0d3b66'), spaceAfter=12))

    # Título do Relatório
    story.append(Paragraph(f"Ficha de Avaliação de Qualidade Informacional: <b>{row['estado']} ({row['uf']})</b>", title_style))
    story.append(Paragraph(f"<b>Portal Auditado:</b> {row['url']} | <b>Data da Coleta:</b> {row['data_verificacao']}", sub_style))

    # Tabela Resumo Executivo
    resumo_data = [
        [Paragraph("<b>Índice de Qualidade (IQI)</b>", body_style), Paragraph(f"<b>{row['iqi_estimado']:.1f}%</b>", body_style)],
        [Paragraph("<b>Classificação Metodológica</b>", body_style), Paragraph(f"<b>{row['classificacao']}</b>", body_style)],
        [Paragraph("<b>Indicadores Atendidos</b>", body_style), Paragraph(f"{sum(row[c] for c in COLUNAS_38)} de 38", body_style)],
        [Paragraph("<b>Tempo de Resposta do Servidor</b>", body_style), Paragraph(f"{row['tempo_resposta_s']} segundos", body_style)]
    ]
    t_resumo = Table(resumo_data, colWidths=[200, 300])
    t_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dee2e6')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_resumo)
    story.append(Spacer(1, 14))

    # Detalhamento dos 38 Indicadores
    story.append(Paragraph("<b>Detalhamento dos 38 Indicadores Avaliados</b>", heading_style))

    grid_data = [["Indicador", "Dimensão", "Status"]]
    for col in COLUNAS_38:
        nome_ind = col[7:].replace('_', ' ').title()
        dim_prefix = col[:3].upper()
        status_txt = "CONFORME (1)" if row[col] == 1 else "NÃO CONFORME (0)"
        grid_data.append([nome_ind, dim_prefix, status_txt])

    t_grid = Table(grid_data, colWidths=[280, 80, 140])
    t_grid.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0d3b66')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e9ecef')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_grid)

    doc.build(story)

def executar_geracao():
    conexao = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM auditoria_estados", conexao)
    conexao.close()

    print("A gerar os 27 relatórios em PDF para os Apêndices do TCC...")
    for _, row in df.iterrows():
        gerar_pdf_estado(row)
        print(f" -> Relatório gerado: {row['uf']} - {row['estado']}")

    print("\nTodos os relatórios em PDF foram guardados na pasta 'relatorios_pdf/'!")

if __name__ == "__main__":
    executar_geracao()