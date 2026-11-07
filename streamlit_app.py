import streamlit as st
from agent.assistant import chat

st.set_page_config(page_title="SPTrans Assistant", page_icon="🚌")
st.title("SPTrans Assistant")
st.caption("Assistente de mobilidade urbana de São Paulo")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Como posso te ajudar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            response = chat(st.session_state.messages)
        st.write(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
