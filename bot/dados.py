"""Leitura, escrita e montagem do dia de atividades."""

import json
import os
import unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "dados")
ARQ_ATIVIDADES = os.path.join(PASTA, "atividades.json")
ARQ_REGISTROS = os.path.join(PASTA, "registros.json")
ARQ_ESTADO = os.path.join(PASTA, "estado.json")

DIAS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
DIAS_LONGOS = [
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
]


# ---------------------------------------------------------------- arquivos


def _ler(caminho, padrao):
    if not os.path.exists(caminho):
        return padrao
    with open(caminho, "r", encoding="utf-8") as arq:
        conteudo = arq.read().strip()
    if not conteudo:
        return padrao
    return json.loads(conteudo)


def _gravar(caminho, conteudo):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arq:
        json.dump(conteudo, arq, ensure_ascii=False, indent=2, sort_keys=True)
        arq.write("\n")


def ler_atividades():
    return _ler(ARQ_ATIVIDADES, {"fuso": "America/Sao_Paulo", "atividades": []})


def gravar_atividades(conteudo):
    _gravar(ARQ_ATIVIDADES, conteudo)


def ler_registros():
    return _ler(ARQ_REGISTROS, {})


def gravar_registros(conteudo):
    _gravar(ARQ_REGISTROS, conteudo)


def ler_estado():
    return _ler(ARQ_ESTADO, {"offset": 0})


def gravar_estado(conteudo):
    _gravar(ARQ_ESTADO, conteudo)


# ------------------------------------------------------------------ tempo


def fuso():
    return ZoneInfo(ler_atividades().get("fuso", "America/Sao_Paulo"))


def agora():
    return datetime.now(fuso())


def hoje():
    return agora().strftime("%Y-%m-%d")


def data_por_extenso(iso):
    d = datetime.strptime(iso, "%Y-%m-%d")
    return "%s, %s" % (DIAS_LONGOS[d.weekday()], d.strftime("%d/%m"))


# ------------------------------------------------------------- utilitarios


def sem_acento(texto):
    normal = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normal if unicodedata.category(c) != "Mn").lower()


def gerar_id(nome, usados):
    base = "".join(c if c.isalnum() else "-" for c in sem_acento(nome)).strip("-")
    base = "-".join(p for p in base.split("-") if p)[:24] or "item"
    novo, n = base, 2
    while novo in usados:
        novo = "%s-%d" % (base, n)
        n += 1
    return novo


# ------------------------------------------------------------- monta o dia


def montar_dia(data_iso=None):
    """Garante que o dia existe em registros.json e devolve o dia.

    Atividades fixas novas sao adicionadas ao dia; tarefas ja marcadas
    nunca sao removidas.
    """
    data_iso = data_iso or hoje()
    config = ler_atividades()
    registros = ler_registros()
    dia = registros.get(data_iso) or {"tarefas": [], "message_id": None}

    semana = DIAS[datetime.strptime(data_iso, "%Y-%m-%d").weekday()]
    existentes = {t["ref"] for t in dia["tarefas"]}

    for atividade in config.get("atividades", []):
        if atividade.get("pausada"):
            continue
        dias = atividade.get("dias", DIAS)
        if semana not in dias:
            continue
        if atividade["id"] in existentes:
            continue
        dia["tarefas"].append(
            {
                "ref": atividade["id"],
                "nome": atividade["nome"],
                "tipo": "fixa",
                "feito": False,
                "hora": None,
            }
        )

    registros[data_iso] = dia
    gravar_registros(registros)
    return dia


def salvar_dia(data_iso, dia):
    registros = ler_registros()
    registros[data_iso] = dia
    gravar_registros(registros)


# ------------------------------------------------------------- apresentacao


def texto_do_dia(data_iso, dia, cabecalho=None):
    total = len(dia["tarefas"])
    feitas = sum(1 for t in dia["tarefas"] if t["feito"])
    linhas = []
    if cabecalho:
        linhas.append("<b>%s</b>" % cabecalho)
    linhas.append("%s" % data_por_extenso(data_iso))
    linhas.append("")

    if not total:
        linhas.append("Nenhuma atividade para hoje.")
        linhas.append("Use <code>/add tarefa</code> para incluir uma.")
        return "\n".join(linhas)

    for i, tarefa in enumerate(dia["tarefas"], start=1):
        marca = "✅" if tarefa["feito"] else "⬜"
        extra = ""
        if tarefa["feito"] and tarefa.get("hora"):
            extra = "  <i>%s</i>" % tarefa["hora"]
        if tarefa["tipo"] == "avulsa" and not tarefa["feito"]:
            extra = "  <i>avulsa</i>"
        linhas.append("%s <b>%d.</b> %s%s" % (marca, i, tarefa["nome"], extra))

    linhas.append("")
    barra_cheia = int(round(feitas / total * 10))
    barra = "█" * barra_cheia + "░" * (10 - barra_cheia)
    linhas.append("%s  %d/%d (%d%%)" % (barra, feitas, total, round(feitas / total * 100)))
    return "\n".join(linhas)


def teclado_do_dia(data_iso, dia):
    """Botoes: um por tarefa pendente, duas colunas."""
    botoes, linha = [], []
    for i, tarefa in enumerate(dia["tarefas"]):
        rotulo = tarefa["nome"]
        if len(rotulo) > 22:
            rotulo = rotulo[:21] + "…"
        prefixo = "✅ " if tarefa["feito"] else ""
        linha.append(
            {
                "text": "%s%s" % (prefixo, rotulo),
                "callback_data": "m:%s:%d" % (data_iso, i),
            }
        )
        if len(linha) == 2:
            botoes.append(linha)
            linha = []
    if linha:
        botoes.append(linha)
    botoes.append([{"text": "↻ Atualizar", "callback_data": "r:%s:0" % data_iso}])
    return botoes


# ------------------------------------------------------------- estatisticas


def resumo_periodo(dias=7):
    """Texto com a taxa de conclusao por atividade nos ultimos N dias."""
    registros = ler_registros()
    limite = agora().date() - timedelta(days=dias - 1)
    contagem = {}
    for data_iso, dia in registros.items():
        d = datetime.strptime(data_iso, "%Y-%m-%d").date()
        if d < limite or d > agora().date():
            continue
        for tarefa in dia.get("tarefas", []):
            if tarefa["tipo"] != "fixa":
                continue
            item = contagem.setdefault(tarefa["nome"], [0, 0])
            item[1] += 1
            if tarefa["feito"]:
                item[0] += 1

    if not contagem:
        return "Ainda não há registros suficientes para um resumo."

    linhas = ["<b>Últimos %d dias</b>" % dias, ""]
    ordenado = sorted(contagem.items(), key=lambda x: x[1][0] / max(x[1][1], 1))
    for nome, (feitas, total) in ordenado:
        pct = round(feitas / total * 100)
        cheio = int(round(pct / 10))
        barra = "█" * cheio + "░" * (10 - cheio)
        linhas.append("%s %3d%%  %s" % (barra, pct, nome))
    linhas.append("")
    pior = ordenado[0]
    if pior[1][0] / pior[1][1] < 1:
        linhas.append("Ponto de atenção: <b>%s</b>." % pior[0])
    else:
        linhas.append("Semana completa. Muito bom.")
    return "\n".join(linhas)
