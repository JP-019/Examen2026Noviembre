"""Interfaz conversacional para el asistente de ventas."""

from __future__ import annotations

from typing import Any

import streamlit as st

from genai_client import GenAiClient, GenAiClientError
from ollama_client import OllamaClient, OllamaClientError

st.set_page_config(
    page_title="Asistente de ventas",
    page_icon=":speech_balloon:",
    layout="wide",
)

CHAT_KEY = "asistente_ventas_mensajes"
client = GenAiClient()
ollama_client = OllamaClient()


def _mostrar_respuesta(message: dict[str, Any]) -> None:
    st.markdown(message["content"])
    if message.get("provider") == "ollama":
        st.caption("Respuesta general de Ollama local; no es un dato de ventas verificado.")
    elif message.get("grounded"):
        st.caption("Respuesta respaldada por datos de la plataforma.")
    else:
        st.caption("Sin respaldo de datos: pregunta fuera del catálogo o sin resultados.")

    sources = message.get("fuentes", [])
    if not sources:
        return
    with st.expander("Fuentes"):
        for source in sources:
            if not isinstance(source, dict):
                continue
            servicio = source.get("servicio", "servicio")
            endpoint = source.get("endpoint", "endpoint")
            st.markdown(f"- `{servicio}` · `{endpoint}`")
            actualizado = source.get("data_updated_at")
            if actualizado:
                st.caption(f"Datos actualizados: {actualizado}")


def _historial_general(messages: list[dict[str, Any]]) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    for index, message in enumerate(messages[:-1]):
        if (
            message.get("role") == "user"
            and messages[index + 1].get("role") == "assistant"
            and messages[index + 1].get("provider") == "ollama"
        ):
            history.extend(
                [
                    {"role": "user", "content": message["content"]},
                    {"role": "assistant", "content": messages[index + 1]["content"]},
                ]
            )
    return history[-6:]


st.title("Asistente de ventas")
modo = st.radio(
    "Modo de conversación",
    ["Ventas verificadas", "Asistente general (Ollama)"],
    horizontal=True,
)
if modo == "Ventas verificadas":
    st.caption(
        "GenAI responde con datos verificados de ventas, fuentes declaradas "
        "y sin ejecutar SQL libre."
    )
    st.info(
        "Prueba con: «¿Cuánto vendimos en total?», «ventas por local» "
        "o «¿cuál es el ticket promedio?»."
    )
else:
    st.caption(
        "Ollama local responde consultas generales. No tiene acceso a los datos "
        "de ventas ni debe usarse para cifras del negocio."
    )

if CHAT_KEY not in st.session_state:
    st.session_state[CHAT_KEY] = []

if st.button("Nueva conversación", key="nueva_conversacion"):
    st.session_state[CHAT_KEY] = []
    st.rerun()

for message in st.session_state[CHAT_KEY]:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            _mostrar_respuesta(message)
        else:
            st.markdown(message["content"])

question = st.chat_input("Escribe tu pregunta...", max_chars=500)
if question is not None:
    question = question.strip()
    if len(question) < 3:
        st.error("La pregunta debe tener al menos 3 caracteres.")
    else:
        st.session_state[CHAT_KEY].append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            if modo == "Ventas verificadas":
                with st.spinner("Consultando datos aprobados..."):
                    try:
                        result = client.ask(question)
                    except GenAiClientError as exc:
                        st.error(str(exc))
                    else:
                        message = {
                            "role": "assistant",
                            "content": result["respuesta"],
                            "provider": "genai",
                            "grounded": result["grounded"],
                            "fuentes": result["fuentes"],
                        }
                        st.session_state[CHAT_KEY].append(message)
                        _mostrar_respuesta(message)
            else:
                with st.spinner("Consultando Ollama local..."):
                    try:
                        answer = ollama_client.ask(
                            question,
                            _historial_general(st.session_state[CHAT_KEY]),
                        )
                    except OllamaClientError as exc:
                        st.error(str(exc))
                    else:
                        message = {
                            "role": "assistant",
                            "content": answer,
                            "provider": "ollama",
                            "grounded": False,
                            "fuentes": [],
                        }
                        st.session_state[CHAT_KEY].append(message)
                        _mostrar_respuesta(message)
