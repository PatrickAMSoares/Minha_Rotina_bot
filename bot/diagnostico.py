"""Mostra o estado real da ligacao com o Telegram, sem alterar nada.

Rode pelo workflow "Diagnostico" e leia o log. Nada aqui confirma
mensagens, entao o diagnostico nao consome a fila do bot.
"""

import json

import dados
import telegram


def linha(titulo):
    print("\n" + "=" * 8 + " " + titulo + " " + "=" * 8)


def descrever(atualizacao):
    tipo = "desconhecido"
    detalhe = ""
    if "callback_query" in atualizacao:
        cb = atualizacao["callback_query"]
        tipo = "toque em botao"
        detalhe = "dado=%s  mensagem=%s" % (
            cb.get("data"),
            cb.get("message", {}).get("message_id"),
        )
    elif "message" in atualizacao:
        m = atualizacao["message"]
        tipo = "mensagem de texto"
        detalhe = "chat=%s  texto=%r" % (
            m.get("chat", {}).get("id"),
            (m.get("text") or "")[:40],
        )
    return "  id=%s  %s  %s" % (atualizacao.get("update_id"), tipo, detalhe)


def main():
    linha("1. O token funciona?")
    eu = telegram.chamar("getMe")
    if eu.get("ok"):
        r = eu["result"]
        print("  OK - bot @%s (%s)" % (r.get("username"), r.get("first_name")))
    else:
        print("  FALHOU - o secret TELEGRAM_TOKEN esta errado")
        print("  resposta: %s" % eu.get("erro"))
        return

    print("  TELEGRAM_CHAT_ID configurado: %r" % telegram.CHAT_ID)

    linha("2. Existe webhook atrapalhando?")
    wh = telegram.chamar("getWebhookInfo")
    info = wh.get("result", {}) if wh.get("ok") else {}
    if info.get("url"):
        print("  PROBLEMA - ha um webhook ativo em %s" % info["url"])
        print("  Com webhook ativo o getUpdates nunca recebe nada.")
    else:
        print("  OK - nenhum webhook ativo")
    print("  mensagens esperando na fila do Telegram: %s"
          % info.get("pending_update_count"))

    linha("3. Qual o ponto de leitura guardado?")
    estado = dados.ler_estado()
    print("  offset em dados/estado.json: %s" % estado.get("offset"))

    linha("4. Qual foi a ultima coisa que o bot recebeu?")
    ultima = telegram.chamar("getUpdates", offset=-1, timeout=0)
    itens = ultima.get("result", []) if ultima.get("ok") else []
    if itens:
        for a in itens:
            print(descrever(a))
        ultimo_id = itens[-1]["update_id"]
        if ultimo_id < estado.get("offset", 0):
            print("  -> Esse item ja foi processado antes (id menor que o offset).")
            print("     Ou seja: nada novo chegou desde entao.")
    else:
        print("  nenhuma atualizacao guardada no Telegram")
        print("  (o Telegram guarda por 24h; depois disso some)")

    linha("5. O que esta esperando para ser processado?")
    pendentes = telegram.chamar(
        "getUpdates", offset=estado.get("offset", 0), timeout=0
    )
    fila = pendentes.get("result", []) if pendentes.get("ok") else []
    if not pendentes.get("ok"):
        print("  FALHOU ao consultar: %s" % pendentes.get("erro"))
    elif not fila:
        print("  fila vazia - nada novo chegou desde o ultimo processamento")
    else:
        print("  %d item(ns) esperando:" % len(fila))
        for a in fila:
            print(descrever(a))

    linha("6. Como esta o registro de hoje")
    dia = dados.ler_registros().get(dados.hoje())
    if not dia:
        print("  ainda nao ha registro para hoje")
    else:
        print("  mensagem do dia: %s" % dia.get("message_id"))
        for i, t in enumerate(dia["tarefas"], start=1):
            print("  %d. [%s] %s" % (i, "x" if t["feito"] else " ", t["nome"]))

    linha("Leitura do resultado")
    print("""
  - Se o item 2 acusou webhook: e essa a causa.
  - Se o item 5 mostra toques esperando: o problema esta no processamento.
  - Se o item 4 nao mostra nenhum "toque em botao": os toques nao estao
    virando atualizacao, ou a mensagem no Telegram esta sem os botoes.
""")


if __name__ == "__main__":
    main()
