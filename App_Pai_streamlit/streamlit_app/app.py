import streamlit as st
import pandas as pd
from datetime import date

from database import (
    init_db,
    verificar_login,
    listar_responsaveis,
    criar_responsavel,
    inserir_pedido,
    listar_pedidos,
    aprovar_pedido,
    recusar_pedido,
    apagar_pedido,
)

st.set_page_config(
    page_title="Gestão de Ausências",
    page_icon="📅",
    layout="wide"
)

init_db()

COLABORADORES = [
    "Alisson Costa",
    "Bruno Carrulo",
    "Bruno Manuel",
    "Bruno Neves",
    "Bruno Ribeiro",
    "Bruno Santos",
    "Carla Teodósio",
    "Fernando Junior",
    "Hugo Nunes",
    "João Santos",
    "Marisa Barata",
]

if "responsavel_logado" not in st.session_state:
    st.session_state.responsavel_logado = None


# ==============================================================
# ECRÃ DE LOGIN
# ==============================================================

def tela_login():

    st.title("📅 Gestão de Ausências")
    st.subheader("Login de Responsável")

    responsaveis = listar_responsaveis()

    if responsaveis:
        with st.form("login_form"):
            nome = st.selectbox("Responsável", responsaveis)
            password = st.text_input("Palavra-passe", type="password")
            entrar = st.form_submit_button("Entrar", use_container_width=True)

            if entrar:
                if verificar_login(nome, password):
                    st.session_state.responsavel_logado = nome
                    st.rerun()
                else:
                    st.error("Nome ou palavra-passe incorretos.")
    else:
        st.info("Ainda não há responsáveis registados. Cria o primeiro abaixo.")

    st.divider()

    with st.expander("⚙️ Criar responsável (acesso restrito)"):
        st.caption(
            "Requer a chave de administração definida nos Secrets da app "
            "(ADMIN_SETUP_KEY). Usa isto para criar ou adicionar responsáveis."
        )

        admin_key_configurada = st.secrets.get("ADMIN_SETUP_KEY")

        if not admin_key_configurada:
            st.warning(
                "ADMIN_SETUP_KEY não está definida nos Secrets da app. "
                "Define-a em Settings → Secrets no Streamlit Cloud antes de continuar."
            )
        else:
            with st.form("criar_responsavel_form"):
                chave = st.text_input("Chave de administração", type="password")
                novo_nome = st.text_input("Nome do responsável")
                nova_password = st.text_input("Password inicial", type="password")
                confirmar_password = st.text_input("Confirmar password", type="password")

                criar = st.form_submit_button("Criar responsável")

                if criar:
                    if chave != admin_key_configurada:
                        st.error("Chave de administração incorreta.")
                    elif not novo_nome or not nova_password:
                        st.error("Preenche o nome e a password.")
                    elif nova_password != confirmar_password:
                        st.error("As passwords não coincidem.")
                    else:
                        criado = criar_responsavel(novo_nome, nova_password)
                        if criado:
                            st.success(f"Responsável '{novo_nome}' criado. Já podes fazer login acima.")
                            st.rerun()
                        else:
                            st.error(f"Já existe um responsável chamado '{novo_nome}'.")


# ==============================================================
# APP PRINCIPAL (após login)
# ==============================================================

def tela_principal():

    responsavel = st.session_state.responsavel_logado

    col_titulo, col_user = st.columns([5, 1])

    with col_titulo:
        st.title("📅 Gestão de Ausências")

    with col_user:
        st.write("")
        st.write(f"👤 **{responsavel}**")
        if st.button("Sair", use_container_width=True):
            st.session_state.responsavel_logado = None
            st.rerun()

    pedidos = listar_pedidos()

    df = pd.DataFrame(
        pedidos,
        columns=[
            "ID",
            "Colaborador",
            "Início",
            "Fim",
            "Período",
            "Estado",
            "Responsável",
        ],
    )

    # ----------------------------------------------------------
    # DASHBOARD
    # ----------------------------------------------------------

    total = len(df)
    aprovados = int((df["Estado"].str.lower() == "aprovado").sum()) if total else 0
    pendentes = int((df["Estado"].str.lower() == "pendente").sum()) if total else 0
    recusados = int((df["Estado"].str.lower() == "recusado").sum()) if total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", total)
    c2.metric("Aprovados", aprovados)
    c3.metric("Pendentes", pendentes)
    c4.metric("Recusados", recusados)

    st.divider()

    # ----------------------------------------------------------
    # FORMULÁRIO: NOVO PEDIDO
    # ----------------------------------------------------------

    st.subheader("Novo pedido")

    with st.form("novo_pedido", clear_on_submit=True):
        cols = st.columns([2, 1, 1, 2])

        colaborador = cols[0].selectbox("Colaborador", COLABORADORES)
        data_inicio = cols[1].date_input("Início", value=date.today())
        data_fim = cols[2].date_input("Fim", value=date.today())
        periodo = cols[3].text_input("Período")

        submeter = st.form_submit_button("Submeter", use_container_width=True)

        if submeter:
            if data_fim < data_inicio:
                st.error("A data de fim não pode ser anterior à data de início.")
            else:
                inserir_pedido(
                    colaborador,
                    data_inicio.isoformat(),
                    data_fim.isoformat(),
                    periodo,
                )
                st.success("Pedido submetido.")
                st.rerun()

    st.divider()

    # ----------------------------------------------------------
    # TABELA + PESQUISA
    # ----------------------------------------------------------

    st.subheader("Pedidos")

    pesquisa = st.text_input("🔍 Procurar colaborador...")

    df_filtrado = (
        df[df["Colaborador"].str.contains(pesquisa, case=False, na=False)]
        if pesquisa
        else df
    )

    def cor_estado(val):
        if val.lower() == "aprovado":
            return "background-color: #DCFCE7"
        if val.lower() == "pendente":
            return "background-color: #FEF3C7"
        if val.lower() == "recusado":
            return "background-color: #FEE2E2"
        return ""

    if not df_filtrado.empty:
        st.dataframe(
            df_filtrado.style.map(cor_estado, subset=["Estado"]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Sem pedidos para mostrar.")

    st.divider()

    # ----------------------------------------------------------
    # AÇÕES: APROVAR / RECUSAR / ELIMINAR
    # ----------------------------------------------------------

    st.subheader("Ações sobre um pedido")
    st.caption(f"A aprovar/recusar como: {responsavel}")

    if not df.empty:
        pedido_id = st.selectbox("ID do pedido", df["ID"].tolist())

        b1, b2, b3 = st.columns(3)

        if b1.button("✅ Aprovar", use_container_width=True):
            aprovar_pedido(pedido_id, responsavel)
            st.rerun()

        if b2.button("❌ Recusar", use_container_width=True):
            recusar_pedido(pedido_id, responsavel)
            st.rerun()

        if b3.button("🗑 Eliminar", use_container_width=True):
            apagar_pedido(pedido_id)
            st.rerun()
    else:
        st.info("Ainda não há pedidos.")


# ==============================================================
# ROTEAMENTO
# ==============================================================

if st.session_state.responsavel_logado is None:
    tela_login()
else:
    tela_principal()
