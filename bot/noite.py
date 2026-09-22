"""Fechamento do dia: cobra o que ficou pendente e fecha o registro."""

import dados
import telegram


def main():
    data_iso = dados.hoje()
    dia = dados.montar_dia(data_iso)
    tarefas = dia["tarefas"]

    if not tarefas:
        print("sem tarefas hoje")
        return

    pendentes = [t for t in tarefas if not t["feito"]]
    feitas = len(tarefas) - len(pendentes)

    if not pendentes:
        texto = "<b>Dia fechado</b>\n%s\n\nTudo concluído: %d de %d. Excelente." % (
            dados.data_por_extenso(data_iso),
            feitas,
            len(tarefas),
        )
        telegram.enviar(texto)
        print("dia completo")
        return

    linhas = [
        "<b>Fechando o dia</b>",
        dados.data_por_extenso(data_iso),
        "",
        "Concluídas: %d de %d" % (feitas, len(tarefas)),
        "",
        "Ainda em aberto:",
    ]
    for tarefa in pendentes:
        linhas.append("⬜ %s" % tarefa["nome"])
    linhas.append("")
    linhas.append("Se fez alguma, toque no botão. O que ficar em branco entra como não feito.")

    telegram.enviar("\n".join(linhas), dados.teclado_do_dia(data_iso, dia))
    print("cobranca enviada (%d pendentes)" % len(pendentes))


if __name__ == "__main__":
    main()
