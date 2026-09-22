"""Lembrete da manha: monta o dia e envia a lista com botoes."""

import dados
import telegram


def main():
    data_iso = dados.hoje()
    dia = dados.montar_dia(data_iso)

    if not dia["tarefas"]:
        print("sem tarefas hoje, nada a enviar")
        return

    texto = dados.texto_do_dia(data_iso, dia, cabecalho="Bom dia, Patrick")
    texto += "\n\nToque no botão assim que concluir cada uma."

    resposta = telegram.enviar(texto, dados.teclado_do_dia(data_iso, dia))
    if resposta.get("ok"):
        dia["message_id"] = resposta["result"]["message_id"]
        dados.salvar_dia(data_iso, dia)
        print("lembrete enviado (%d tarefas)" % len(dia["tarefas"]))
    else:
        print("falha ao enviar o lembrete")


if __name__ == "__main__":
    main()
