name: Processar mensagens

on:
  schedule:
    # De hora em hora. O GitHub trata agendamento como "melhor esforco",
    # entao pode sair alguns minutos depois do previsto.
    - cron: "0 * * * *"
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: dados-rotina
  cancel-in-progress: false

jobs:
  processar:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Ler e aplicar as mensagens novas
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python bot/processar.py

      - name: Salvar os dados
        run: |
          git config user.name "rotina-bot"
          git config user.email "rotina-bot@users.noreply.github.com"
          if git diff --quiet -- dados/; then
            echo "nada mudou"
            exit 0
          fi
          git add dados/
          git commit -m "dados: registro de atividades"
          for i in 1 2 3 4 5; do
            if git push; then
              echo "dados salvos"
              exit 0
            fi
            echo "push falhou (tentativa $i), sincronizando..."
            git pull --rebase --autostash || true
            sleep $((i * 3))
          done
          echo "nao foi possivel salvar os dados"
          exit 1
