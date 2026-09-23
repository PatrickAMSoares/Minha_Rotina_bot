"""Mostra o estado real da ligacao com o Telegram.

Rode pelo workflow "Diagnostico" e leia o log. Nada aqui confirma
mensagens, entao o diagnostico nao consome a fila do bot.

Com a opcao "enviar teste" marcada, manda uma mensagem com um botao
para voce tocar. E a forma de descobrir se o toque vira atualizacao.
"""

import os

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

    linha("1b. O chat_id aponta para a sua conversa?")
    chat = telegram.chamar("getChat", chat_id=telegram.CHAT_ID)
    if chat.get("ok"):
        c = chat["result"]
        print("  OK - conversa privada com: %s %s (@%s)"
              % (c.get("first_name", ""), c.get("last_name", ""),
                 c.get("username", "sem usuario")))
        print("  tipo: %s" % c.get("type"))
        print("  -> Confira se esse e voce. Se for outra pessoa ou um grupo,")
        print("     o TELEGRAM_CHAT_ID esta errado.")
    else:
        print("  FALHOU - o TELEGRAM_CHAT_ID nao corresponde a nenhuma conversa")
        print("  resposta: %s" % chat.get("erro"))

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

    if os.environ.get("ENVIAR_TESTE") == "true":
        linha("7. Mandando uma mensagem de teste com botao")
        teclado = [[
            {"text": "✅ Tocar aqui", "callback_data": "teste:tocou"},
        ]]
        envio = telegram.enviar(
            "<b>Teste de botao</b>\n\n"
            "Toque no botao abaixo e depois rode o Diagnostico de novo "
            "(sem marcar a opcao de teste).\n\n"
            "Se o toque aparecer no item 4 ou 5, os botoes funcionam.",
            teclado,
        )
        if envio.get("ok"):
            print("  enviada - mensagem %s" % envio["result"]["message_id"])
            tem_botao = "reply_markup" in envio["result"]
            print("  o Telegram confirmou os botoes na mensagem: %s"
                  % ("SIM" if tem_botao else "NAO"))
            if not tem_botao:
                print("  -> Se veio NAO, a mensagem chegou sem botao nenhum.")
        else:
            print("  FALHOU: %s" % envio.get("erro"))

    linha("Leitura do resultado")
    print("""
  - Se o item 1b nao mostrar o seu nome: o chat_id esta errado.
  - Se o item 2 acusou webhook: e essa a causa.
  - Se o item 5 mostra toques esperando: o problema esta no processamento.
  - Se o item 4 nao mostra nenhum "toque em botao": os toques nao estao
    virando atualizacao. Use a opcao de teste para confirmar.
""")


if __name__ == "__main__":
    main()
