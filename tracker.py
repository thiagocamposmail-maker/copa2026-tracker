"""
Copa do Mundo 2026 - Tracker de Jogos com Notificações
Monitora jogos ao vivo e envia push notifications via Ntfy.sh
"""

import os
import time
import json
import logging
import requests
from datetime import datetime

# ─── Configuração ─────────────────────────────────────────────
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")
NTFY_TOPIC       = os.environ.get("NTFY_TOPIC", "copa2026-seu-nome")  # mude para seu tópico
NTFY_SERVER      = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
CHECK_INTERVAL   = int(os.environ.get("CHECK_INTERVAL", "60"))  # segundos entre verificações

# ID da Copa do Mundo 2026 na football-data.org
COMPETITION_ID = "WC"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# ─── Estado em memória ────────────────────────────────────────
state = {}  # {match_id: {score_home, score_away, status, notified_start, notified_end}}


# ─── Funções de notificação ───────────────────────────────────

def notify(title: str, message: str, priority: str = "default", tags: list = None):
    """Envia push notification via Ntfy.sh"""
    headers = {
        "Title": title,
        "Priority": priority,
        "Tags": ",".join(tags or ["soccer"]),
    }
    try:
        r = requests.post(
            f"{NTFY_SERVER}/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers=headers,
            timeout=10,
        )
        r.raise_for_status()
        log.info(f"Notificação enviada: {title}")
    except Exception as e:
        log.error(f"Falha ao enviar notificação: {e}")


# ─── Funções da API ───────────────────────────────────────────

def get_live_matches():
    """Busca partidas ao vivo e de hoje da Copa do Mundo"""
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    url = f"https://api.football-data.org/v4/competitions/{COMPETITION_ID}/matches"
    params = {"status": "LIVE,IN_PLAY,PAUSED,FINISHED,SCHEDULED"}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        return data.get("matches", [])
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            log.warning("Rate limit atingido. Aguardando...")
            time.sleep(60)
        else:
            log.error(f"Erro na API: {e}")
    except Exception as e:
        log.error(f"Erro ao buscar partidas: {e}")
    return []


def format_team(match, side: str) -> str:
    return match[side]["shortName"] or match[side]["name"]


def format_score(match) -> str:
    s = match["score"]["fullTime"]
    h = s["home"] if s["home"] is not None else "?"
    a = s["away"] if s["away"] is not None else "?"
    # durante o jogo usa current score
    if match["status"] in ("IN_PLAY", "PAUSED"):
        s2 = match["score"]["regularTime"] or match["score"]["fullTime"]
        h = s2["home"] if s2["home"] is not None else "0"
        a = s2["away"] if s2["away"] is not None else "0"
    return f"{h} × {a}"


def get_scorers_text(match) -> str:
    """Extrai artilheiros do jogo (disponível em alguns planos da API)"""
    goals = match.get("goals", [])
    if not goals:
        return ""
    lines = []
    for g in goals:
        scorer = g.get("scorer", {}).get("name", "?")
        minute = g.get("minute", "?")
        team   = g.get("team", {}).get("shortName", "")
        lines.append(f"{scorer} {minute}' ({team})")
    return "\n".join(lines)


# ─── Lógica principal de monitoramento ───────────────────────

def process_match(match):
    mid    = match["id"]
    home   = format_team(match, "homeTeam")
    away   = format_team(match, "awayTeam")
    status = match["status"]
    score  = match["score"]

    # Placar atual
    cur_home = (score.get("regularTime") or score.get("fullTime") or {}).get("home") or 0
    cur_away = (score.get("regularTime") or score.get("fullTime") or {}).get("away") or 0

    prev = state.get(mid, {
        "score_home": 0,
        "score_away": 0,
        "status": None,
        "notified_start": False,
        "notified_end": False,
    })

    # ── Início do jogo ──────────────────────────────────────
    if status == "IN_PLAY" and not prev["notified_start"]:
        notify(
            title=f"🟢 Começa agora! {home} vs {away}",
            message=f"A bola rolou!\n{home} × {away}\nGrupo {match.get('group','?')}",
            priority="high",
            tags=["soccer", "loudspeaker"],
        )
        prev["notified_start"] = True

    # ── Gol! ────────────────────────────────────────────────
    if status in ("IN_PLAY", "PAUSED"):
        if cur_home > prev["score_home"]:
            scorers = get_scorers_text(match)
            notify(
                title=f"⚽ GOL DE {home.upper()}!",
                message=f"{home} {cur_home} × {cur_away} {away}\n{scorers}".strip(),
                priority="urgent",
                tags=["soccer", "tada"],
            )
        if cur_away > prev["score_away"]:
            scorers = get_scorers_text(match)
            notify(
                title=f"⚽ GOL DE {away.upper()}!",
                message=f"{home} {cur_home} × {cur_away} {away}\n{scorers}".strip(),
                priority="urgent",
                tags=["soccer", "tada"],
            )

    # ── Fim do jogo ─────────────────────────────────────────
    if status == "FINISHED" and not prev["notified_end"]:
        ft = score["fullTime"]
        fh = ft["home"] if ft["home"] is not None else cur_home
        fa = ft["away"] if ft["away"] is not None else cur_away

        if fh > fa:
            result = f"Vitória de {home}!"
        elif fa > fh:
            result = f"Vitória de {away}!"
        else:
            result = "Empate!"

        scorers = get_scorers_text(match)
        notify(
            title=f"🏁 Fim de jogo: {home} {fh} × {fa} {away}",
            message=f"{result}\n{scorers}".strip(),
            priority="high",
            tags=["soccer", "checkered_flag"],
        )
        prev["notified_end"] = True

    # Atualiza estado
    prev["score_home"] = cur_home
    prev["score_away"] = cur_away
    prev["status"]     = status
    state[mid] = prev


def run():
    log.info("🏆 Copa do Mundo 2026 Tracker iniciado!")
    log.info(f"   Tópico Ntfy: {NTFY_TOPIC}")
    log.info(f"   Intervalo de verificação: {CHECK_INTERVAL}s")

    if not FOOTBALL_API_KEY:
        log.error("FOOTBALL_API_KEY não definida! Configure a variável de ambiente.")
        return

    # Notificação de teste ao iniciar
    notify(
        title="🏆 Copa 2026 Tracker ativo!",
        message="Você receberá notificações de início, gols e fim de cada partida.",
        tags=["trophy"],
    )

    while True:
        log.info("Verificando partidas...")
        matches = get_live_matches()
        log.info(f"  {len(matches)} partida(s) encontrada(s)")

        for match in matches:
            try:
                process_match(match)
            except Exception as e:
                log.error(f"Erro ao processar partida {match.get('id')}: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
