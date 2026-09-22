"""Comunicacao com a API do Telegram usando apenas a biblioteca padrao."""

import json
import os
import urllib.error
import urllib.request

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
API = "https://api.telegram.org/bot%s" % TOKEN


def chamar(metodo, **parametros):
    """Chama um metodo da API. Devolve o dicionario de resposta."""
    corpo = json.dumps(parametros).encode("utf-8")
    req = urllib.request.Request(
        "%s/%s" % (API, metodo),
        data=corpo,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", "replace")
        print("[telegram] erro em %s: %s %s" % (metodo, erro.code, detalhe))
        return {"ok": False, "erro": detalhe}
    except Exception as erro:  # rede instavel, timeout etc.
        print("[telegram] falha em %s: %s" % (metodo, erro))
        return {"ok": False, "erro": str(erro)}


def enviar(texto, teclado=None, chat_id=None):
    parametros = {
        "chat_id": chat_id or CHAT_ID,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if teclado:
        parametros["reply_markup"] = {"inline_keyboard": teclado}
    return chamar("sendMessage", **parametros)


def editar(message_id, texto, teclado=None, chat_id=None):
    parametros = {
        "chat_id": chat_id or CHAT_ID,
        "message_id": message_id,
        "text": texto,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if teclado is not None:
        parametros["reply_markup"] = {"inline_keyboard": teclado}
    return chamar("editMessageText", **parametros)


def responder_botao(callback_id, aviso=""):
    return chamar("answerCallbackQuery", callback_query_id=callback_id, text=aviso)


def buscar_atualizacoes(offset):
    return chamar(
        "getUpdates",
        offset=offset,
        timeout=0,
        allowed_updates=["message", "callback_query"],
    )
