# 🏆 Copa 2026 Tracker — Guia de Configuração

Sistema de notificações em tempo real para jogos da Copa do Mundo 2026.
Você receberá um push no celular a cada início de jogo, gol e fim de partida — **grátis**.

---

## Visão geral

```
football-data.org  →  tracker.py (Railway)  →  ntfy.sh  →  📱 seu celular
    (dados ao vivo)      (roda 24/7)           (push free)
```

---

## Passo 1 — Instale o app Ntfy no celular (2 min)

1. **Android**: [Play Store → Ntfy](https://play.google.com/store/apps/details?id=io.heckel.ntfy)  
   **iPhone**: [App Store → Ntfy](https://apps.apple.com/app/ntfy/id1625396347)

2. Abra o app → toque em **"+"** → adicione um tópico com nome único, ex:  
   `copa2026-joaosilva`  
   *(qualquer nome, só precisa ser único — é como um canal privado)*

3. Pronto! Você já pode receber notificações nesse tópico.

> **Dica:** Teste agora abrindo no navegador:  
> `https://ntfy.sh/copa2026-joaosilva` e enviando uma mensagem de teste.

---

## Passo 2 — Crie sua chave na football-data.org (2 min)

1. Acesse [football-data.org](https://www.football-data.org/client/register)
2. Crie uma conta gratuita
3. Confirme o e-mail
4. Acesse seu painel e copie o **API Token** (parece com: `abc123def456...`)

> O plano gratuito inclui dados da Copa do Mundo com atualização a cada ~1 minuto.

---

## Passo 3 — Suba o tracker no Railway (5 min)

O Railway roda seu script 24/7 gratuitamente (500h/mês no plano free).

### 3a. Crie o repositório no GitHub

1. Acesse [github.com](https://github.com) → **New repository**
2. Nome: `copa2026-tracker` → **Create repository**
3. Faça upload dos arquivos:
   - `tracker.py`
   - `requirements.txt`
   - `railway.toml`

### 3b. Deploy no Railway

1. Acesse [railway.app](https://railway.app) e entre com sua conta GitHub
2. Clique em **"New Project"** → **"Deploy from GitHub repo"**
3. Selecione `copa2026-tracker`
4. Railway detecta automaticamente o `railway.toml` e instala tudo

### 3c. Configure as variáveis de ambiente

No painel do Railway, vá em **Variables** e adicione:

| Variável | Valor |
|----------|-------|
| `FOOTBALL_API_KEY` | sua chave da football-data.org |
| `NTFY_TOPIC` | `copa2026-joaosilva` (seu tópico) |
| `CHECK_INTERVAL` | `60` (verifica a cada 60 segundos) |

Clique em **Deploy** — pronto!

---

## Passo 4 — Teste

Assim que o deploy terminar, você receberá uma notificação no celular:

> 🏆 **Copa 2026 Tracker ativo!**  
> Você receberá notificações de início, gols e fim de cada partida.

Se chegou, tá tudo funcionando. ✅

---

## O que você receberá

| Evento | Exemplo |
|--------|---------|
| Início do jogo | 🟢 **Começa agora! Brasil vs Argentina** |
| Gol | ⚽ **GOL DE BRASIL!** Vini Jr 34' — Brasil 1 × 0 Argentina |
| Fim do jogo | 🏁 **Fim de jogo: Brasil 2 × 1 Argentina** — Vitória do Brasil! |

---

## Alternativa: rodar local (sem Railway)

Se preferir rodar no seu próprio computador:

```bash
# Clone/copie os arquivos, entre na pasta e:
pip install -r requirements.txt

# Configure as variáveis:
export FOOTBALL_API_KEY="sua_chave_aqui"
export NTFY_TOPIC="copa2026-joaosilva"

# Rode:
python tracker.py
```

O script fica rodando em segundo plano enquanto o computador estiver ligado.

---

## Dúvidas frequentes

**"O plano gratuito do Railway é suficiente?"**  
Sim. 500 horas/mês gratuitas — a Copa dura ~30 dias, são ~720h, mas jogos não são 24h então sobra folgado. Você pode também usar o [Render.com](https://render.com) como alternativa (plano free tem limitações de sleep, prefira Railway).

**"Posso receber no WhatsApp em vez do Ntfy?"**  
O Ntfy é o mais simples e gratuito. Para WhatsApp você precisaria de uma conta Twilio (tem custo). Para Telegram, há uma opção via bot — me peça que adiciono.

**"E se a API demorar a atualizar o gol?"**  
A football-data.org no plano gratuito atualiza com ~1-2 min de delay. É o tradeoff do plano free. O plano pago (~€10/mês) tem dados em tempo real.
