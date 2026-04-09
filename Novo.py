import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB = "chat.db"

def conectar():
    return sqlite3.connect(DB, check_same_thread=False)

if "contato_selecionado" not in st.session_state:
    st.session_state["contato_selecionado"] = None

# ─────────────────────────────
# LOGIN
# ─────────────────────────────
def login():
    st.title("Chat Interno")

    nome = st.text_input("Usuário").strip()

    if st.button("Entrar"):
        conn = conectar()
        c = conn.cursor()

        c.execute("SELECT setor FROM usuarios WHERE nome = ?", (nome,))
        resultado = c.fetchone()

        if not resultado:
            st.error("Usuário não encontrado")
            conn.close()
            return

        st.session_state["usuario"] = nome
        st.session_state["setor"] = resultado[0]
        conn.close()
        st.rerun()

# ─────────────────────────────
# CHAT
# ─────────────────────────────
def chat():

    
    usuario = st.session_state["usuario"]

    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT setor, nome FROM usuarios ORDER BY setor, nome")
    dados = c.fetchall()

    contatos_por_setor = {}
    for setor, nome in dados:
        if nome != usuario:
            contatos_por_setor.setdefault(setor, []).append(nome)

    st.sidebar.title("Contatos por Setor")

    for setor, pessoas in contatos_por_setor.items():
        with st.sidebar.expander(f"📁 {setor}", expanded=True):
            for pessoa in pessoas:
                if st.sidebar.button(
                    pessoa,
                    key=f"{setor}_{pessoa}",
                    use_container_width=True
                ):
                    st.session_state["contato_selecionado"] = pessoa

    
    contato = st.session_state["contato_selecionado"]

    if not contato:
        st.title("💬 Selecione um contato para conversar")
        st.stop()

    st.title(f"💬 Conversa com {contato}")

    # Mensagens
    c.execute("""
            SELECT remetente, mensagem, data_hora
            FROM mensagens_privadas
            WHERE
            (remetente = ? AND destinatario = ?)
            OR
            (remetente = ? AND destinatario = ?)
            ORDER BY id
        """, (usuario, contato,
            contato, usuario))

    mensagens = c.fetchall()

    for r, m, d in mensagens:
        if r == usuario:
             st.chat_message("user").write(m)
        else:
            st.chat_message("assistant").write(m)


    # Input
    msg = st.chat_input("Digite sua mensagem")

    if msg:
        c.execute("""
            INSERT INTO mensagens_privadas
            VALUES (NULL, ?, ?, '', ?, datetime('now'))
        """, (usuario, contato, msg))
        conn.commit()
        st.rerun()

    conn.close()

    if st.button("🧹 Limpar conversa"):
        conn = conectar()
        c = conn.cursor()
        c.execute("""
            DELETE FROM mensagens_privadas
            WHERE
            (remetente = ? AND destinatario = ?)
            OR
            (remetente = ? AND destinatario = ?)
        """, (usuario, contato, contato, usuario))
        conn.commit()
        conn.close()
        st.success("Conversa limpa!")
        st.rerun()
        st.warning("Essa ação não pode ser desfeita")



# ─────────────────────────────
# MAIN
# ─────────────────────────────
if "usuario" not in st.session_state:
    login()
else:
    chat()