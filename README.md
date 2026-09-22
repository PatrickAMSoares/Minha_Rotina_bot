# Rotina Bot

Bot de Telegram que lembra suas atividades de manhã, registra o que você marcou
como feito ao longo do dia e monta um painel web com os gráficos de desempenho.

Roda inteiramente de graça no GitHub Actions. Não precisa de servidor, não
precisa deixar o computador ligado e não tem nada para pagar.

**Como funciona no dia a dia**

- 07:00 — o bot manda a lista do dia com um botão por atividade.
- Durante o dia — você toca no botão assim que conclui. A própria mensagem se
  atualiza com o ✅ e o horário.
- 21:00 — o bot lista o que ficou em aberto e fecha o dia.
- Quando quiser — `/resumo` no chat ou o painel web com os gráficos.

---

## Instalação (uma vez, cerca de 15 minutos)

### 1. Criar o bot no Telegram

1. No Telegram, procure por **@BotFather** e mande `/newbot`.
2. Escolha um nome (ex.: `Minha Rotina`) e um usuário terminado em `bot`
   (ex.: `patrick_rotina_bot`).
3. O BotFather devolve um **token** parecido com
   `8123456789:AAF-abcDEFghblablaiJKLmnoPQRstuVWXyz12345`. Guarde.
4. Abra a conversa com o seu bot e mande qualquer mensagem, por exemplo `oi`.
   Isso é necessário para o próximo passo.

### 2. Descobrir o seu chat_id

No navegador, abra (trocando `SEU_TOKEN` pelo token do passo anterior):

```
https://api.telegram.org/botSEU_TOKEN/getUpdates
```

Procure por `"chat":{"id":123456789` — esse número é o seu **chat_id**.

### 3. Criar o repositório

1. Em <https://github.com/new>, crie um repositório chamado `rotina-bot`.
2. Marque **Public**. Isso importa: no plano gratuito, só repositório público
   tem GitHub Pages e minutos de Actions ilimitados. Como o repositório fica
   visível, não use nomes de atividade com informação sensível.
3. Envie todos os arquivos desta pasta para o repositório. Se preferir pelo
   site: **Add file → Upload files**, arraste tudo e confirme.

### 4. Guardar o token e o chat_id

No repositório: **Settings → Secrets and variables → Actions → New repository
secret**. Crie os dois:

| Nome | Valor |
| --- | --- |
| `TELEGRAM_TOKEN` | o token do BotFather |
| `TELEGRAM_CHAT_ID` | o número do passo 2 |

Secrets ficam criptografados e não aparecem para quem visita o repositório.

### 5. Deixar as automações gravarem os dados

**Settings → Actions → General → Workflow permissions** → marque
**Read and write permissions** → **Save**.

Sem isso o bot manda as mensagens mas não consegue salvar o histórico.

### 6. Ligar o painel web

**Settings → Pages → Build and deployment**: em *Source* escolha
**Deploy from a branch**, branch **main**, pasta **/ (root)** e salve.

Em um ou dois minutos o painel fica no ar em
`https://SEU-USUARIO.github.io/rotina-bot/`.

Abra `dados/atividades.json` e troque o campo `painel` por esse endereço, para
o comando `/painel` funcionar.

### 7. Testar

Vá em **Actions → Lembrete da manhã → Run workflow**. Em alguns segundos a
lista deve chegar no Telegram. Toque em um botão e espere alguns minutos: o
registro aparece na mensagem e no painel.

> Se a aba Actions pedir para habilitar os workflows, clique em
> **I understand my workflows, go ahead and enable them**.

---

## Configurar as atividades

Dá para fazer tudo pelo chat, sem mexer em arquivo:

```
/fixa Treino | seg,ter,qua,qui,sex
/fixa Ler 30min | todos
/fixa Revisar orçamento | dom
/fixas
/pausar ler-30min
/remover ler-30min
```

Ou editar `dados/atividades.json` direto no GitHub:

```json
{
  "fuso": "America/Sao_Paulo",
  "painel": "https://SEU-USUARIO.github.io/rotina-bot/",
  "atividades": [
    { "id": "treino", "nome": "Treino", "dias": ["seg", "ter", "qua", "qui", "sex"] },
    { "id": "ler", "nome": "Ler 30min", "dias": ["seg", "ter", "qua", "qui", "sex", "sab", "dom"] }
  ]
}
```

Dias aceitos: `seg`, `ter`, `qua`, `qui`, `sex`, `sab`, `dom`.

## Comandos do chat

| Comando | O que faz |
| --- | --- |
| `2` (só o número) | marca a tarefa 2 como feita |
| `/hoje` | manda a lista de hoje de novo |
| `/feito 2` · `/desfazer 2` | marca e desmarca pelo número |
| `/add pagar boleto` | tarefa avulsa, só para hoje |
| `/resumo` · `/resumo 30` | desempenho dos últimos 7 ou 30 dias |
| `/painel` | link dos gráficos |
| `/fixas` · `/fixa` · `/pausar` · `/voltar` · `/remover` | gerenciam as atividades recorrentes |
| `/ajuda` | lista tudo isso |

## Mudar os horários

Os agendamentos ficam em `.github/workflows/`, em **UTC**. Brasília é UTC-3,
então some 3 horas ao horário que você quer:

| Horário desejado | `cron` |
| --- | --- |
| 06:00 | `0 9 * * *` |
| 07:00 | `0 10 * * *` |
| 08:00 | `0 11 * * *` |
| 21:00 | `0 0 * * *` |
| 22:00 | `0 1 * * *` |

`manha.yml` é o lembrete, `noite.yml` é o fechamento do dia.

---

## O que esperar (e as limitações)

- **As respostas não são instantâneas.** O GitHub verifica as mensagens a cada
  5 minutos e costuma atrasar mais alguns minutos em horários de pico. Para
  marcar hábitos isso não atrapalha, mas não espere uma resposta imediata.
- **O horário do lembrete também varia.** Agendamento no GitHub Actions pode
  sair alguns minutos depois do previsto.
- **Só você conversa com o bot.** Mensagens de qualquer outro chat_id são
  ignoradas.
- **Repositório público.** O histórico (nomes das atividades e os ✅) fica
  visível. O token e o chat_id, não — estão nos secrets.
- **Workflows agendados hibernam após 60 dias sem commits no repositório.**
  Como o bot grava os dados todo dia, isso não deve acontecer; se acontecer,
  basta abrir a aba Actions e reativar.

Se um dia quiser respostas instantâneas, o mesmo código roda em qualquer
serviço que fique ligado 24/7 (Fly.io, Oracle Cloud Free Tier, Render), com o
bot em modo de escuta contínua em vez do agendamento.

## Estrutura dos arquivos

```
bot/telegram.py     comunicação com a API do Telegram
bot/dados.py        leitura, escrita e estatísticas
bot/manha.py        lembrete das 07:00
bot/processar.py    lê as mensagens novas e aplica os comandos
bot/noite.py        fechamento das 21:00
dados/atividades.json   suas atividades recorrentes
dados/registros.json    o histórico (o bot escreve aqui)
dados/estado.json       controle interno de mensagens já lidas
index.html          o painel web
.github/workflows/  os agendamentos
.github/salvar.sh   grava os dados de volta no repositório
```
