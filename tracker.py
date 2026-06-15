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
NTFY_TOPIC       = os.environ.get("NTFY_TOPIC", "copa2026-seu-nome")
NTFY_SERVER      = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
CHECK_INTERVAL   = int(os.environ.get("CHECK_INTERVAL", "60"))

COMPETITION_ID = "WC"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

state = {}


# ─── Funções de notificação ───────────────────────────────────

def notify(title: str, message: str, priority: str = "default", tags: list = None):
    """Envia push notification via Ntfy.sh usando headers HTTP (evita encoding issues)"""
    priority_map = {"default": "default", "high": "high", "urgent": "urgent"}
    try:
        r = requests.post(
            f"{NTFY_SERVER}/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title":    title.encode("utf-8").decode("latin-1", errors="ignore"),
                "Priority": priority_map.get(priority, "default"),
                "Tags":     ",".join(tags or ["soccer"]),
                "Content-Type": "text/plain; charset=utf-8",
            },
            timeout=10,
        )
        r.raise_for_status()
        log.info(f"Notificacao enviada: {title}")
    except Exception as e:
        log.error(f"Falha ao enviar notificacao: {e}")


# ─── Funções da API ───────────────────────────────────────────

def get_live_matches():
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
    return match[side].get("shortName") or match[side]["name"]


def format_score(cur_home, cur_away) -> str:
    return f"{cur_home} x {cur_away}"


def get_scorers_text(match) -> str:
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


# ─── Lógica principal ────────────────────────────────────────

def process_match(match):
    mid    = match["id"]
    home   = format_team(match, "homeTeam")
    away   = format_team(match, "awayTeam")
    status = match["status"]
    score  = match["score"]

    cur = (score.get("regularTime") or score.get("fullTime") or {})
    cur_home = cur.get("home") or 0
    cur_away = cur.get("away") or 0

    prev = state.get(mid, {
        "score_home": 0,
        "score_away": 0,
        "status": None,
        "notified_start": False,
        "notified_end": False,
    })

    # Inicio do jogo
    if status == "IN_PLAY" and not prev["notified_start"]:
        notify(
            title=f"Comeca agora! {home} vs {away}",
            message=f"A bola rolou!\n{home} x {away}",
            priority="high",
            tags=["soccer", "loudspeaker"],
        )
        prev["notified_start"] = True

    # Gol
    if status in ("IN_PLAY", "PAUSED"):
        if cur_home > prev["score_home"]:
            scorers = get_scorers_text(match)
            notify(
                title=f"GOL DE {home.upper()}!",
                message=f"{home} {cur_home} x {cur_away} {away}\n{scorers}".strip(),
                priority="urgent",
                tags=["soccer", "tada"],
            )
        if cur_away > prev["score_away"]:
            scorers = get_scorers_text(match)
            notify(
                title=f"GOL DE {away.upper()}!",
                message=f"{home} {cur_home} x {cur_away} {away}\n{scorers}".strip(),
                priority="urgent",
                tags=["soccer", "tada"],
            )

    # Fim do jogo
    if status == "FINISHED" and not prev["notified_end"]:
        ft = score["fullTime"]
        fh = ft["home"] if ft["home"] is not None else cur_home
        fa = ft["away"] if ft["away"] is not None else cur_away

        if fh > fa:
            result = f"Vitoria de {home}!"
        elif fa > fh:
            result = f"Vitoria de {away}!"
        else:
            result = "Empate!"

        scorers = get_scorers_text(match)
        notify(
            title=f"Fim: {home} {fh} x {fa} {away}",
            message=f"{result}\n{scorers}".strip(),
            priority="high",
            tags=["soccer", "checkered_flag"],
        )
        prev["notified_end"] = True

    prev["score_home"] = cur_home
    prev["score_away"] = cur_away
    prev["status"]     = status
    state[mid] = prev


def run():
    log.info("Copa do Mundo 2026 Tracker iniciado!")
    log.info(f"   Topico Ntfy: {NTFY_TOPIC}")
    log.info(f"   Intervalo: {CHECK_INTERVAL}s")

    if not FOOTBALL_API_KEY:
        log.error("FOOTBALL_API_KEY nao definida!")
        return

    notify(
        title="Copa 2026 Tracker ativo!",
        message="Voce recebera notificacoes de inicio, gols e fim de cada partida.",
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
