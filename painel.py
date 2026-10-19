import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
import os
import sqlite3

# Garante que se o banco não existir (ex: no Streamlit Cloud), ele é gerado automaticamente
if not os.path.exists("auditsaude.db"):
    from auditor_nacional import executar_varredura_nacional
    executar_varredura_nacional()

# Configuração da Página
st.set_page_config(
    page_title="AuditSaúde-BR | Plataforma Acessível de Inteligência Acadêmica",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS E ARIA PARA ACESSIBILIDADE WCAG / eMAG ---
st.markdown("""
<style>
    *:focus-visible {
        outline: 3px solid #005f73 !important;
        outline-offset: 2px !important;
    }
    
    .header-container {
        background: linear-gradient(135deg, #0d3b66 0%, #005f73 100%);
        padding: 26px 32px;
        border-radius: 16px;
        color: #ffffff !important;
        margin-bottom: 25px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }
    .header-container h1, .header-container p {
        color: #ffffff !important;
        margin: 0;
    }
    
    .kpi-card {
        background-color: var(--secondary-background-color);
        border: 2px solid rgba(128, 128, 128, 0.25);
        border-radius: 14px;
        padding: 20px 22px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .kpi-label {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: var(--text-color);
    }
    .kpi-value {
        font-size: 2.1rem;
        font-weight: 800;
        margin-top: 6px;
        color: var(--text-color);
    }
    .kpi-sub {
        font-size: 0.85rem;
        opacity: 0.85;
        margin-top: 4px;
        color: var(--text-color);
    }

    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

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

MAPA_INDICADORES_LEGIVEIS = {
    'tec_01_atualizacao': 'Atualização Recente',
    'tec_02_identificacao_responsavel': 'Órgão Responsável',
    'tec_03_datas_criacao_revisao': 'Data Criação/Revisão',
    'tec_04_correcao_ortografica': 'Idioma PT-BR',
    'tec_05_referencias_bibliograficas': 'Citação Fontes/SUS',
    'tec_06_conexao_segura_https': 'Conexão HTTPS',
    'tec_07_disponibilidade_uptime': 'Status HTTP 200',
    'tec_08_dominio_oficial_gov': 'Domínio .gov.br',
    'int_01_compreensao_linguagem': 'Linguagem Compreensível',
    'int_02_clareza_apresentacao': 'Estrutura Títulos (H1-H3)',
    'int_03_unidades_medida': 'Métricas Epidemiológicas',
    'int_04_ausencia_dificuldade': 'Acesso Sem Barreiras',
    'int_05_indice_legibilidade_flesch': 'Índice Legibilidade Flesch',
    'ace_01_facilidade_localizacao': 'Estrutura de Navegação',
    'ace_02_disponibilidade_publica': 'Acesso Público Direto',
    'ace_03_carregamento_movel': 'Suporte Mobile / Viewport',
    'ace_04_descricao_imagens_alt': 'Descrição Imagens (ALT)',
    'ita_01_canais_contato': 'Contatos Institucionais',
    'ita_02_menus_navegacao': 'Menus de Navegação',
    'ita_03_redes_sociais': 'Redes Sociais Oficiais',
    'ita_04_mecanismo_busca': 'Barra de Pesquisa',
    'ita_05_recursos_acessibilidade': 'Atalhos Acessibilidade',
    'ita_06_organizacao_visual': 'Layout Organizado',
    'ita_07_ouvidoria_fale_conosco': 'Ouvidoria / Fale Conosco',
    'ita_08_formularios_servicos': 'Formulários Interativos',
    'abr_01_prevencao': 'Conteúdo: Prevenção',
    'abr_02_sintomas': 'Conteúdo: Sintomas',
    'abr_03_transmissao': 'Conteúdo: Transmissão',
    'abr_04_diagnostico': 'Conteúdo: Diagnóstico',
    'abr_05_campanhas': 'Conteúdo: Campanhas',
    'abr_06_vacinacao': 'Conteúdo: Vacinação',
    'abr_07_promocao_saude': 'Conteúdo: Promoção da Saúde',
    'leg_01_explicacao_termos_tecnicos': 'Explicação Termos Médicos',
    'leg_02_recursos_visuais': 'Infográficos e Vídeos',
    'leg_03_tamanho_fonte_contraste': 'Alto Contraste / Fonte',
    'leg_04_vlibras_audiodescricao': 'Widget VLibras',
    'apo_01_materiais_campanha': 'Materiais para Download',
    'apo_02_informacoes_profissionais': 'Notas Técnicas / Boletins'
}

DIMENSOES = {
    'Dimensão 1: Técnico (8)': [c for c in COLUNAS_38 if c.startswith('tec_')],
    'Dimensão 2: Interpretabilidade (5)': [c for c in COLUNAS_38 if c.startswith('int_')],
    'Dimensão 3: Acessibilidade (4)': [c for c in COLUNAS_38 if c.startswith('ace_')],
    'Dimensão 4: Interatividade (8)': [c for c in COLUNAS_38 if c.startswith('ita_')],
    'Dimensão 5: Abrangência (7)': [c for c in COLUNAS_38 if c.startswith('abr_')],
    'Dimensão 6: Legibilidade (4)': [c for c in COLUNAS_38 if c.startswith('leg_')],
    'Dimensão 7: Apoio a Gestores (2)': [c for c in COLUNAS_38 if c.startswith('apo_')]
}

MAPA_REGIOES = {
    'AC': 'Norte', 'AP': 'Norte', 'AM': 'Norte', 'PA': 'Norte', 'RO': 'Norte', 'RR': 'Norte', 'TO': 'Norte',
    'AL': 'Nordeste', 'BA': 'Nordeste', 'CE': 'Nordeste', 'MA': 'Nordeste', 'PB': 'Nordeste', 'PE': 'Nordeste', 'PI': 'Nordeste', 'RN': 'Nordeste', 'SE': 'Nordeste',
    'DF': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'MS': 'Centro-Oeste',
    'ES': 'Sudeste', 'MG': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
    'PR': 'Sul', 'RS': 'Sul', 'SC': 'Sul'
}

CORES_CATEGORIA_ACESSIVEIS = {
    'Excelente': '#1b7837',
    'Boa': '#2b83ba',
    'Regular': '#d95f02',
    'Insuficiente': '#7570b3'
}

@st.cache_data(ttl=5)
def carregar_dados():
    try:
        conexao = sqlite3.connect("auditsaude.db")
        df = pd.read_sql("SELECT * FROM auditoria_estados ORDER BY iqi_estimado DESC", conexao)
        conexao.close()
        df['Região'] = df['uf'].map(MAPA_REGIOES)
        return df
    except Exception:
        return pd.DataFrame()

df = carregar_dados()

st.markdown("""
<header class="header-container" role="banner">
    <h1>🏥 AuditSaúde-BR | Sistema de Auditoria de Informação em Saúde</h1>
    <p>Plataforma Acessível de Avaliação Científica dos Portais das Secretarias de Saúde — <b>Metodologia TCC UnB</b></p>
</header>
""", unsafe_allow_html=True)

if df.empty or 'tec_01_atualizacao' not in df.columns:
    st.error("⚠️ Base de dados ausente ou antiga. Execute o comando `python auditor_nacional.py` no terminal!")
else:
    df['Posição'] = range(1, len(df) + 1)

    tab_rank, tab_radar, tab_matriz, tab_curadoria, tab_export = st.tabs([
        "🏆 Ranking e Regiões", 
        "🕸️ Análise por Dimensão", 
        "🔍 Matriz dos 38 Indicadores", 
        "✏️ Central de Curadoria TCC",
        "📄 Exportação e Texto TCC"
    ])

    # --- TAB 1: RANKING NACIONAL E ANÁLISE REGIONAL ---
    with tab_rank:
        st.markdown("### 📊 Visão Geral e Desempenho por Macrorregião do Brasil")
        
        media_nacional = df['iqi_estimado'].mean()
        campeao = df.iloc[0]
        df_df = df[df['uf'] == 'DF']
        pos_df = df_df.iloc[0]['Posição'] if not df_df.empty else "-"
        iqi_df = df_df.iloc[0]['iqi_estimado'] if not df_df.empty else 0.0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <article class="kpi-card">
                <div class="kpi-label">Amostra Auditada</div>
                <div class="kpi-value">{len(df)} UFs</div>
                <div class="kpi-sub">26 Estados + DF</div>
            </article>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <article class="kpi-card">
                <div class="kpi-label">Média Nacional IQI</div>
                <div class="kpi-value">{media_nacional:.1f}%</div>
                <div class="kpi-sub">Média dos 38 Indicadores</div>
            </article>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <article class="kpi-card">
                <div class="kpi-label">1º Lugar Geral</div>
                <div class="kpi-value">{campeao['estado']}</div>
                <div class="kpi-sub">IQI: {campeao['iqi_estimado']:.1f}%</div>
            </article>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <article class="kpi-card">
                <div class="kpi-label">Desempenho do DF</div>
                <div class="kpi-value">{pos_df}º Lugar</div>
                <div class="kpi-sub">IQI: {iqi_df:.1f}%</div>
            </article>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Visão por Região
        col_reg, col_donut = st.columns(2)

        with col_reg:
            st.markdown("#### 🌍 Desempenho Médio por Macrorregião")
            df_regiao = df.groupby('Região')['iqi_estimado'].mean().reset_index().sort_values(by='iqi_estimado', ascending=False)
            fig_reg = px.bar(
                df_regiao, x='Região', y='iqi_estimado', text='iqi_estimado',
                title="Média do IQI (%) por Região Geográfica",
                color='iqi_estimado', color_continuous_scale='Teal'
            )
            fig_reg.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_reg.update_layout(height=340, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_reg, use_container_width=True)

        with col_donut:
            df_cat = df['classificacao'].value_counts().reset_index()
            df_cat.columns = ['Categoria', 'Quantidade']
            fig_donut = px.pie(
                df_cat, names='Categoria', values='Quantidade', hole=0.6,
                title="<b>Distribuição por Categoria TCC</b>",
                color='Categoria', color_discrete_map=CORES_CATEGORIA_ACESSIVEIS
            )
            fig_donut.update_layout(height=340, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"))
            st.plotly_chart(fig_donut, use_container_width=True)

        st.divider()

        fig_bar = px.bar(
            df, x='iqi_estimado', y='uf', color='classificacao', text='iqi_estimado', orientation='h',
            custom_data=['estado', 'Posição', 'classificacao', 'Região'],
            title="<b>Ranking Geral do IQI (%) por Unidade Federativa</b>",
            labels={'uf': 'UF', 'iqi_estimado': 'IQI (%)', 'classificacao': 'Categoria'},
            color_discrete_map=CORES_CATEGORIA_ACESSIVEIS
        )
        fig_bar.add_vline(x=85, line_dash="dash", line_color="#1b7837", annotation_text="Excelente (≥85%)", annotation_position="bottom left")
        fig_bar.add_vline(x=70, line_dash="dash", line_color="#2b83ba", annotation_text="Boa (≥70%)", annotation_position="bottom left")
        fig_bar.add_vline(x=50, line_dash="dash", line_color="#d95f02", annotation_text="Regular (≥50%)", annotation_position="bottom left")
        
        fig_bar.update_traces(
            texttemplate='<b>%{text:.1f}%</b>', textposition='outside',
            hovertemplate='<b>%{customdata[1]}º Lugar: %{customdata[0]} (%{y} - Região %{customdata[3]})</b><br>IQI: <b>%{x:.1f}%</b><extra></extra>',
            marker=dict(cornerradius=6)
        )
        fig_bar.update_layout(xaxis_range=[0, 118], yaxis=dict(autorange="reversed"), height=750, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(size=12))
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- TAB 2: ANÁLISE POR DIMENSÃO ---
    with tab_radar:
        st.markdown("### 🕸️ Comparativo das 7 Dimensões do TCC")
        uf_selecionada = st.selectbox("Selecione o Estado para comparar com a Média Nacional:", df['uf'].tolist(), index=df['uf'].tolist().index('DF') if 'DF' in df['uf'].tolist() else 0)
        row_uf = df[df['uf'] == uf_selecionada].iloc[0]

        dim_labels = ["Técnico", "Interpretabilidade", "Acessibilidade", "Interatividade", "Abrangência", "Legibilidade", "Apoio Gestores"]
        valores_uf, valores_brasil = [], []
        for dim, cols in DIMENSOES.items():
            valores_uf.append(round((sum(row_uf[col] for col in cols) / len(cols)) * 100, 1))
            valores_brasil.append(round((df[cols].sum().sum() / (len(cols) * len(df))) * 100, 1))

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=valores_uf, theta=dim_labels, fill='toself', name=f"{uf_selecionada} ({row_uf['estado']})", line_color='#0d3b66', fillcolor='rgba(13, 59, 102, 0.35)'))
        fig_radar.add_trace(go.Scatterpolar(r=valores_brasil, theta=dim_labels, fill='toself', name="Média Brasil", line_color='#d95f02', fillcolor='rgba(217, 95, 2, 0.25)'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, height=540, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', title=f"<b>Desempenho Dimensional: {uf_selecionada} vs Média do Brasil</b>")
        st.plotly_chart(fig_radar, use_container_width=True)

    # --- TAB 3: MATRIZ DOS 38 INDICADORES ---
    with tab_matriz:
        st.markdown("### 🔍 Matriz de Atendimento aos 38 Indicadores")
        cols_display = ['Posição', 'uf', 'estado', 'iqi_estimado', 'classificacao'] + COLUNAS_38
        config_colunas = {"Posição": st.column_config.NumberColumn("º", format="%d"), "uf": "UF", "estado": "Estado", "iqi_estimado": st.column_config.NumberColumn("IQI (%)", format="%.1f%%"), "classificacao": "Categoria TCC"}
        for col_db, nome_amigavel in MAPA_INDICADORES_LEGIVEIS.items():
            config_colunas[col_db] = st.column_config.CheckboxColumn(nome_amigavel)
        st.dataframe(df[cols_display], use_container_width=True, column_config=config_colunas)

    # --- TAB 4: CENTRAL DE CURADORIA TCC ---
    with tab_curadoria:
        st.markdown("### ✏️ Central de Ajuste e Validação do TCC")
        uf_edit = st.selectbox("Escolha o Estado para Auditar/Editar:", df['uf'].tolist(), key="curadoria_uf")
        dados_uf = df[df['uf'] == uf_edit].iloc[0]
        with st.form("form_curadoria"):
            novas_respostas = {}
            for dim_nome, cols in DIMENSOES.items():
                with st.expander(f"📌 {dim_nome}", expanded=False):
                    c1, c2 = st.columns(2)
                    for idx_ind, col_ind in enumerate(cols):
                        target = c1 if idx_ind % 2 == 0 else c2
                        novas_respostas[col_ind] = target.checkbox(MAPA_INDICADORES_LEGIVEIS.get(col_ind, col_ind), value=bool(dados_uf[col_ind]), key=f"chk_{uf_edit}_{col_ind}")
            if st.form_submit_button("💾 Salvar Alterações e Recalcular IQI"):
                novo_iqi = round((sum(1 for v in novas_respostas.values() if v) / 38) * 100, 2)
                nova_classe = "Excelente" if novo_iqi >= 85 else ("Boa" if novo_iqi >= 70 else ("Regular" if novo_iqi >= 50 else "Insuficiente"))
                conexao = sqlite3.connect("auditsaude.db")
                cursor = conexao.cursor()
                set_clause = ", ".join([f"{k} = ?" for k in novas_respostas.keys()])
                cursor.execute(f"UPDATE auditoria_estados SET {set_clause}, iqi_estimado = ?, classificacao = ? WHERE uf = ?", [1 if v else 0 for v in novas_respostas.values()] + [novo_iqi, nova_classe, uf_edit])
                conexao.commit()
                conexao.close()
                st.success("✅ Atualizado com sucesso!")
                st.cache_data.clear()
                st.rerun()

    # --- TAB 5: EXPORTAÇÃO E TEXTO ACADÊMICO AUTOMÁTICO ---
    with tab_export:
        st.markdown("### 📄 Exportação e Parágrafo de Síntese para a Tese")
        st.markdown("Copie o texto de resultados gerado automaticamente abaixo para colar diretamente no capítulo de discussão do seu TCC:")

        # Gerador Automático do Parágrafo de Síntese
        total_ufs = len(df)
        media_geral = df['iqi_estimado'].mean()
        desvio_padrao = df['iqi_estimado'].std()
        primeiro_lugar = df.iloc[0]
        df_distrito = df[df['uf'] == 'DF']
        pos_df_val = df_distrito.iloc[0]['Posição'] if not df_distrito.empty else 0
        iqi_df_val = df_distrito.iloc[0]['iqi_estimado'] if not df_distrito.empty else 0

        paragrafo_sintese = (
            f"A auditoria realizada em {total_ufs} portais eletrônicos das Secretarias Estaduais de Saúde "
            f"revelou uma média nacional do Índice de Qualidade da Informação (IQI) de {media_geral:.1f}% "
            f"(desvio-padrão de {desvio_padrao:.1f}%). Destacou-se na primeira colocação o estado de "
            f"{primeiro_lugar['estado']} ({primeiro_lugar['iqi_estimado']:.1f}%), enquanto o Distrito Federal "
            f"alcançou a {pos_df_val}ª posição com IQI de {iqi_df_val:.1f}%. Os resultados evidenciam "
            f"heterogeneidade significativa na infraestrutura digital e na transparência pública em saúde entre as Unidades Federativas."
        )

        st.text_area("📋 Parágrafo de Resultados Gerado Automaticamente:", value=paragrafo_sintese, height=120)

        st.divider()

        c_exp1, c_exp2 = st.columns(2)
        with c_exp1:
            st.download_button("📥 Baixar Matriz Completa (CSV)", data=df.to_csv(index=False).encode('utf-8'), file_name='matriz_completa_tcc.csv', mime='text/csv')
        with c_exp2:
            uf_pdf = st.selectbox("Gerar Apêndice PDF do Estado:", df['uf'].tolist(), key="pdf_uf")
            if st.button("⚙️ Gerar PDF"):
                from gerar_apendices_pdf import gerar_pdf_estado
                gerar_pdf_estado(df[df['uf'] == uf_pdf].iloc[0])
                st.success("✅ Relatório PDF gerado na pasta `relatorios_pdf/`!")

# WIDGET VLIBRAS FLUTUANTE
components.html("""
<script>
    (function() {
        const parentDoc = window.parent.document;
        if (!parentDoc.getElementById('vlibras-script')) {
            const script = parentDoc.createElement('script');
            script.id = 'vlibras-script';
            script.src = "https://vlibras.gov.br/app/vlibras-plugin.js";
            script.onload = function() {
                if (!parentDoc.querySelector('[vw]')) {
                    const div = parentDoc.createElement('div');
                    div.setAttribute('vw', '');
                    div.className = 'enabled';
                    div.innerHTML = '<div vw-access-button class="active"></div><div vw-plugin-wrapper><div class="vw-plugin-top-wrapper"></div></div>';
                    parentDoc.body.appendChild(div);
                    new window.parent.VLibras.Widget('https://vlibras.gov.br/app');
                }
            };
            parentDoc.head.appendChild(script);
        }
    })();
</script>
""", height=0)