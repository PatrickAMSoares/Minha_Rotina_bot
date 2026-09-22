"""Le as mensagens novas do Telegram e aplica os comandos.

Roda a cada poucos minutos pelo GitHub Actions. Usa getUpdates com offset
guardado em dados/estado.json, então nenhuma mensagem é processada duas vezes.
"""

import dados
import telegram

AJUDA = """<b>Como usar</b>

<b>Durante o dia</b>
Toque nos botões da lista da manhã para marcar o que já fez.
Ou mande só o número da tarefa (ex.: <code>2</code>).

<b>Comandos</b>
<code>/hoje</code> - manda a lista de hoje de novo
<code>/feito 2</code> - marca a tarefa 2
<code>/desfazer 2</code> - desmarca a tarefa 2
<code>/add pagar boleto</code> - tarefa avulsa só para hoje
<code>/resumo</code> - desempenho dos últimos 7 dias
<code>/resumo 30</code> - dos últimos 30 dias
<code>/painel</code> - link dos gráficos

<b>Atividades fixas</b>
<code>/fixas</code> - lista as atividades recorrentes
<code>/fixa Ler 30min | seg,ter,qua,qui,sex</code> - cria uma
<code>/fixa Correr | todos</code> - todos os dias
<code>/pausar ler-30min</code> - suspende sem apagar o histórico
<code>/voltar ler-30min</code> - reativa
<code>/remover ler-30min</code> - apaga a atividade fixa"""


# --------------------------------------------------------------- auxiliares


def atualizar_mensagem(data_iso, dia):
    """Reescreve a mensagem do dia, se ela existir."""
    if not dia.get("message_id"):
        return
    telegram.editar(
        dia["message_id"],
        dados.texto_do_dia(data_iso, dia),
        dados.teclado_do_dia(data_iso, dia),
    )


def marcar(data_iso, indice, feito=True):
    dia = dados.montar_dia(data_iso)
    if indice < 0 or indice >= len(dia["tarefas"]):
        return None, dia
    tarefa = dia["tarefas"][indice]
    tarefa["feito"] = feito
    tarefa["hora"] = dados.agora().strftime("%H:%M") if feito else None
    dados.salvar_dia(data_iso, dia)
    return tarefa, dia


def enviar_lista(data_iso=None):
    data_iso = data_iso or dados.hoje()
    dia = dados.montar_dia(data_iso)
    resposta = telegram.enviar(
        dados.texto_do_dia(data_iso, dia), dados.teclado_do_dia(data_iso, dia)
    )
    if resposta.get("ok"):
        dia["message_id"] = resposta["result"]["message_id"]
        dados.salvar_dia(data_iso, dia)


# ----------------------------------------------------------------- comandos


def comando_add(argumento):
    if not argumento:
        telegram.enviar("Escreva a tarefa. Ex.: <code>/add pagar boleto</code>")
        return
    data_iso = dados.hoje()
    dia = dados.montar_dia(data_iso)
    usados = {t["ref"] for t in dia["tarefas"]}
    dia["tarefas"].append(
        {
            "ref": dados.gerar_id(argumento, usados),
            "nome": argumento,
            "tipo": "avulsa",
            "feito": False,
            "hora": None,
        }
    )
    dados.salvar_dia(data_iso, dia)
    atualizar_mensagem(data_iso, dia)
    telegram.enviar("Adicionado para hoje: <b>%s</b>" % argumento)


def comando_fixa(argumento):
    if "|" in argumento:
        nome, dias_txt = [p.strip() for p in argumento.split("|", 1)]
    else:
        nome, dias_txt = argumento.strip(), "todos"
    if not nome:
        telegram.enviar("Formato: <code>/fixa Ler 30min | seg,qua,sex</code>")
        return

    dias_txt = dados.sem_acento(dias_txt)
    if dias_txt in ("todos", "todo dia", "diario", "sempre"):
        dias = list(dados.DIAS)
    elif dias_txt in ("util", "uteis", "dias uteis", "semana"):
        dias = dados.DIAS[:5]
    else:
        dias = [d.strip()[:3] for d in dias_txt.replace(" ", ",").split(",")]
        dias = [d for d in dias if d in dados.DIAS]
    if not dias:
        telegram.enviar(
            "Não entendi os dias. Use seg, ter, qua, qui, sex, sab, dom, "
            "<code>todos</code> ou <code>uteis</code>."
        )
        return

    config = dados.ler_atividades()
    usados = {a["id"] for a in config["atividades"]}
    novo_id = dados.gerar_id(nome, usados)
    config["atividades"].append({"id": novo_id, "nome": nome, "dias": dias})
    dados.gravar_atividades(config)

    data_iso = dados.hoje()
    dia = dados.montar_dia(data_iso)
    atualizar_mensagem(data_iso, dia)
    telegram.enviar(
        "Atividade fixa criada: <b>%s</b>\nDias: %s\nIdentificador: <code>%s</code>"
        % (nome, ", ".join(dias), novo_id)
    )


def comando_fixas():
    config = dados.ler_atividades()
    if not config["atividades"]:
        telegram.enviar(
            "Nenhuma atividade fixa ainda.\n"
            "Crie com <code>/fixa Ler 30min | seg,qua,sex</code>"
        )
        return
    linhas = ["<b>Atividades fixas</b>", ""]
    for atividade in config["atividades"]:
        estado = " <i>(pausada)</i>" if atividade.get("pausada") else ""
        linhas.append(
            "• <b>%s</b>%s\n  %s\n  <code>%s</code>"
            % (atividade["nome"], estado, ", ".join(atividade["dias"]), atividade["id"])
        )
    telegram.enviar("\n".join(linhas))


def comando_estado_fixa(identificador, acao):
    config = dados.ler_atividades()
    identificador = identificador.strip()
    for i, atividade in enumerate(config["atividades"]):
        if atividade["id"] != identificador:
            continue
        if acao == "remover":
            config["atividades"].pop(i)
            mensagem = "Removida: <b>%s</b>" % atividade["nome"]
        elif acao == "pausar":
            atividade["pausada"] = True
            mensagem = "Pausada: <b>%s</b>" % atividade["nome"]
        else:
            atividade.pop("pausada", None)
            mensagem = "Reativada: <b>%s</b>" % atividade["nome"]
        dados.gravar_atividades(config)
        telegram.enviar(mensagem)
        return
    telegram.enviar(
        "Não achei <code>%s</code>. Veja os identificadores com <code>/fixas</code>."
        % identificador
    )


def comando_painel():
    url = dados.ler_atividades().get("painel")
    if url:
        telegram.enviar("Seus gráficos: %s" % url)
    else:
        telegram.enviar(
            "O endereço do painel ainda não foi configurado em "
            "<code>dados/atividades.json</code>."
        )


# ------------------------------------------------------------- roteamento


def tratar_texto(texto):
    texto = (texto or "").strip()
    if not texto:
        return

    if texto.isdigit():
        tarefa, dia = marcar(dados.hoje(), int(texto) - 1, True)
        if tarefa:
            atualizar_mensagem(dados.hoje(), dia)
            telegram.enviar("Feito: <b>%s</b>" % tarefa["nome"])
        else:
            telegram.enviar("Não existe tarefa com esse número hoje.")
        return

    if not texto.startswith("/"):
        telegram.enviar(
            "Não entendi. Mande <code>/ajuda</code> para ver os comandos."
        )
        return

    partes = texto[1:].split(" ", 1)
    comando = partes[0].split("@")[0].lower()
    argumento = partes[1].strip() if len(partes) > 1 else ""

    if comando in ("start", "ajuda", "help"):
        telegram.enviar(AJUDA)
    elif comando == "hoje":
        enviar_lista()
    elif comando in ("feito", "desfazer"):
        if not argumento.isdigit():
            telegram.enviar("Use o número da tarefa. Ex.: <code>/feito 2</code>")
            return
        feito = comando == "feito"
        tarefa, dia = marcar(dados.hoje(), int(argumento) - 1, feito)
        if tarefa:
            atualizar_mensagem(dados.hoje(), dia)
            telegram.enviar(
                ("Feito: <b>%s</b>" if feito else "Desmarcado: <b>%s</b>")
                % tarefa["nome"]
            )
        else:
            telegram.enviar("Não existe tarefa com esse número hoje.")
    elif comando == "add":
        comando_add(argumento)
    elif comando == "fixa":
        comando_fixa(argumento)
    elif comando == "fixas":
        comando_fixas()
    elif comando in ("pausar", "voltar", "remover"):
        comando_estado_fixa(argumento, comando)
    elif comando == "resumo":
        periodo = int(argumento) if argumento.isdigit() else 7
        telegram.enviar(dados.resumo_periodo(min(periodo, 365)))
    elif comando == "painel":
        comando_painel()
    else:
        telegram.enviar("Comando desconhecido. Veja <code>/ajuda</code>.")


def tratar_botao(callback):
    acao, data_iso, indice = callback["data"].split(":")
    if acao == "r":
        dia = dados.montar_dia(data_iso)
        atualizar_mensagem(data_iso, dia)
        telegram.responder_botao(callback["id"], "Atualizado")
        return

    dia = dados.montar_dia(data_iso)
    indice = int(indice)
    if indice >= len(dia["tarefas"]):
        telegram.responder_botao(callback["id"], "Tarefa não encontrada")
        return

    tarefa = dia["tarefas"][indice]
    novo = not tarefa["feito"]
    tarefa["feito"] = novo
    tarefa["hora"] = dados.agora().strftime("%H:%M") if novo else None
    if not dia.get("message_id"):
        dia["message_id"] = callback["message"]["message_id"]
    dados.salvar_dia(data_iso, dia)

    telegram.editar(
        callback["message"]["message_id"],
        dados.texto_do_dia(data_iso, dia),
        dados.teclado_do_dia(data_iso, dia),
    )
    telegram.responder_botao(
        callback["id"], "Registrado" if novo else "Desmarcado"
    )


def main():
    estado = dados.ler_estado()
    resposta = telegram.buscar_atualizacoes(estado.get("offset", 0))
    if not resposta.get("ok"):
        print("nao foi possivel buscar atualizacoes")
        return

    atualizacoes = resposta.get("result", [])
    if not atualizacoes:
        print("nada novo")
        return

    for atualizacao in atualizacoes:
        estado["offset"] = atualizacao["update_id"] + 1
        try:
            if "callback_query" in atualizacao:
                tratar_botao(atualizacao["callback_query"])
            elif "message" in atualizacao:
                mensagem = atualizacao["message"]
                if str(mensagem["chat"]["id"]) != str(telegram.CHAT_ID):
                    continue  # ignora qualquer outra pessoa
                tratar_texto(mensagem.get("text", ""))
        except Exception as erro:
            print("erro ao tratar atualizacao %s: %s" % (atualizacao["update_id"], erro))

    dados.gravar_estado(estado)
    print("processadas %d atualizacoes" % len(atualizacoes))


if __name__ == "__main__":
    main()
