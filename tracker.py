"""
Copa do Mundo 2026 - Tracker com nomes em PT-BR, bandeiras e alerta pré-jogo
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")
NTFY_TOPIC       = os.environ.get("NTFY_TOPIC", "copa2026-seu-nome")
NTFY_SERVER      = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
CHECK_INTERVAL   = int(os.environ.get("CHECK_INTERVAL", "60"))
PRE_MATCH_MINS   = int(os.environ.get("PRE_MATCH_MINS", "5"))
COMPETITION_ID   = "WC"
STATE_FILE       = os.environ.get("STATE_FILE", "/data/state.json")
LOCAL_TZ_OFFSET  = int(os.environ.get("LOCAL_TZ_OFFSET", "-3"))  # BRT = UTC-3

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ─── Países: nome EN (API) → (bandeira, nome PT-BR) ──────────
PAISES = {
    "Brazil":              ("🇧🇷", "Brasil"),
    "Argentina":           ("🇦🇷", "Argentina"),
    "France":              ("🇫🇷", "França"),
    "Germany":             ("🇩🇪", "Alemanha"),
    "Spain":               ("🇪🇸", "Espanha"),
    "Portugal":            ("🇵🇹", "Portugal"),
    "England":             ("🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Inglaterra"),
    "Netherlands":         ("🇳🇱", "Holanda"),
    "Belgium":             ("🇧🇪", "Bélgica"),
    "Croatia":             ("🇭🇷", "Croácia"),
    "Morocco":             ("🇲🇦", "Marrocos"),
    "Senegal":             ("🇸🇳", "Senegal"),
    "Japan":               ("🇯🇵", "Japão"),
    "South Korea":         ("🇰🇷", "Coreia do Sul"),
    "Australia":           ("🇦🇺", "Austrália"),
    "Mexico":              ("🇲🇽", "México"),
    "United States":       ("🇺🇸", "Estados Unidos"),
    "Canada":              ("🇨🇦", "Canadá"),
    "Uruguay":             ("🇺🇾", "Uruguai"),
    "Colombia":            ("🇨🇴", "Colômbia"),
    "Ecuador":             ("🇪🇨", "Equador"),
    "Chile":               ("🇨🇱", "Chile"),
    "Venezuela":           ("🇻🇪", "Venezuela"),
    "Bolivia":             ("🇧🇴", "Bolívia"),
    "Paraguay":            ("🇵🇾", "Paraguai"),
    "Peru":                ("🇵🇪", "Peru"),
    "Saudi Arabia":        ("🇸🇦", "Arábia Saudita"),
    "Iran":                ("🇮🇷", "Irã"),
    "Qatar":               ("🇶🇦", "Catar"),
    "Uzbekistan":          ("🇺🇿", "Uzbequistão"),
    "Indonesia":           ("🇮🇩", "Indonésia"),
    "Egypt":               ("🇪🇬", "Egito"),
    "Nigeria":             ("🇳🇬", "Nigéria"),
    "Cameroon":            ("🇨🇲", "Camarões"),
    "Ivory Coast":         ("🇨🇮", "Costa do Marfim"),
    "Ghana":               ("🇬🇭", "Gana"),
    "Mali":                ("🇲🇱", "Mali"),
    "Algeria":             ("🇩🇿", "Argélia"),
    "South Africa":        ("🇿🇦", "África do Sul"),
    "Tunisia":             ("🇹🇳", "Tunísia"),
    "Switzerland":         ("🇨🇭", "Suíça"),
    "Austria":             ("🇦🇹", "Áustria"),
    "Denmark":             ("🇩🇰", "Dinamarca"),
    "Sweden":              ("🇸🇪", "Suécia"),
    "Norway":              ("🇳🇴", "Noruega"),
    "Poland":              ("🇵🇱", "Polônia"),
    "Ukraine":             ("🇺🇦", "Ucrânia"),
    "Hungary":             ("🇭🇺", "Hungria"),
    "Romania":             ("🇷🇴", "Romênia"),
    "Serbia":              ("🇷🇸", "Sérvia"),
    "Slovakia":            ("🇸🇰", "Eslováquia"),
    "Slovenia":            ("🇸🇮", "Eslovênia"),
    "Czech Republic":      ("🇨🇿", "República Tcheca"),
    "Czechia":             ("🇨🇿", "República Tcheca"),
    "Greece":              ("🇬🇷", "Grécia"),
    "Turkey":              ("🇹🇷", "Turquia"),
    "New Zealand":         ("🇳🇿", "Nova Zelândia"),
    "Guatemala":           ("🇬🇹", "Guatemala"),
    "Costa Rica":          ("🇨🇷", "Costa Rica"),
    "Panama":              ("🇵🇦", "Panamá"),
    "Jamaica":             ("🇯🇲", "Jamaica"),
    "Haiti":               ("🇭🇹", "Haiti"),
    "Cuba":                ("🇨🇺", "Cuba"),
    "Honduras":            ("🇭🇳", "Honduras"),
    "El Salvador":         ("🇸🇻", "El Salvador"),
    "Trinidad and Tobago": ("🇹🇹", "Trinidad e Tobago"),
    "Iraq":                ("🇮🇶", "Iraque"),
    "Israel":              ("🇮🇱", "Israel"),
    "Jordan":              ("🇯🇴", "Jordânia"),
    "Thailand":            ("🇹🇭", "Tailândia"),
    "China PR":            ("🇨🇳", "China"),
    "China":               ("🇨🇳", "China"),
    "India":               ("🇮🇳", "Índia"),
    "Scotland":            ("🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Escócia"),
    "Wales":               ("🏴󠁧󠁢󠁷󠁬󠁳󠁿", "País de Gales"),
    "Ireland":             ("🇮🇪", "Irlanda"),
    "Albania":             ("🇦🇱", "Albânia"),
    "Georgia":             ("🇬🇪", "Geórgia"),
    "North Macedonia":     ("🇲🇰", "Macedônia do Norte"),
}

def traduzir(nome_en: str) -> str:
    if nome_en in PAISES:
        flag, nome_pt = PAISES[nome_en]
        return f"{flag} {nome_pt}"
    for key, (flag, nome_pt) in PAISES.items():
        if key.lower() in nome_en.lower() or nome_en.lower() in key.lower():
            return f"{flag} {nome_pt}"
    return nome_en


# ─── Estado persistido ────────────────────────────────────────

def load_state() -> dict:
    try:
        p = Path(STATE_FILE)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        log.warning(f"Nao foi possivel carregar state: {e}")
    return {}

def save_state(state: dict):
    try:
        p = Path(STATE_FILE)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(state), encoding="utf-8")
    except Exception as e:
        log.warning(f"Nao foi possivel salvar state: {e}")


# ─── Ntfy ────────────────────────────────────────────────────

def notify(title: str, message: str, priority: str = "default", tags: list = None, retries: int = 3):
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(
                f"{NTFY_SERVER}/{NTFY_TOPIC}",
                data=message.encode("utf-8"),
                headers={
                    "Title":        title,
                    "Priority":     priority,
                    "Tags":         ",".join(tags or ["soccer"]),
                    "Content-Type": "text/plain; charset=utf-8",
                },
                timeout=10,
            )
            r.raise_for_status()
            log.info(f"Notif: {title}")
            return
        except Exception as e:
            log.warning(f"Erro notif (tentativa {attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(2 ** attempt)
    log.error(f"Falha ao enviar notificacao apos {retries} tentativas: {title}")


# ─── API ─────────────────────────────────────────────────────

def get_matches():
    now = datetime.now(timezone.utc)
    date_from = now.strftime("%Y-%m-%d")
    date_to   = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{COMPETITION_ID}/matches",
            headers={"X-Auth-Token": FOOTBALL_API_KEY},
            params={
                "status":   "LIVE,IN_PLAY,PAUSED,FINISHED,SCHEDULED",
                "dateFrom": date_from,
                "dateTo":   date_to,
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("matches", [])
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            log.warning("Rate limit. Aguardando 60s...")
            time.sleep(60)
        else:
            log.error(f"Erro API: {e}")
    except Exception as e:
        log.error(f"Erro ao buscar partidas: {e}")
    return []


def get_scorer(match, side: str, cur_goals: int) -> str:
    goals = match.get("goals", [])
    team_id = match[side]["id"]
    team_goals = [g for g in goals if g.get("team", {}).get("id") == team_id]
    if len(team_goals) >= cur_goals:
        g = team_goals[cur_goals - 1]
        scorer = g.get("scorer", {}).get("name", "")
        minute = g.get("minute", "")
        if scorer:
            return f"{minute}' {scorer}" if minute else scorer
    return ""


# ─── Processamento ───────────────────────────────────────────

def process_match(match, state: dict):
    mid  = str(match["id"])
    home = traduzir(match["homeTeam"].get("name", "?"))
    away = traduzir(match["awayTeam"].get("name", "?"))
    status = match["status"]
    score  = match["score"]

    cur = score.get("regularTime") or score.get("fullTime") or {}
    cur_home = cur.get("home") or 0
    cur_away = cur.get("away") or 0

    prev = state.get(mid, {
        "score_home": 0, "score_away": 0,
        "status": None,
        "notified_pre": False,
        "notified_start": False,
        "notified_end": False,
    })

    # ── Alerta pré-jogo ────────────────────────────────────
    if status == "SCHEDULED" and not prev["notified_pre"]:
        kickoff_str = match.get("utcDate")
        if kickoff_str:
            kickoff = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
            diff = (kickoff - datetime.now(timezone.utc)).total_seconds() / 60
            if 0 < diff <= PRE_MATCH_MINS:
                mins = int(diff)
                label = "1 minuto" if mins <= 1 else f"{mins} minutos"
                notify(
                    title=f"Jogo em {label}!",
                    message=f"{home} x {away}\nPrepara o lanche!",
                    priority="high",
                    tags=["alarm_clock"],
                )
                prev["notified_pre"] = True

    # ── Início ─────────────────────────────────────────────
    if status == "IN_PLAY" and not prev["notified_start"]:
        notify(
            title="Começou!",
            message=f"Bola rolando para\n{home} x {away}",
            priority="high",
            tags=["rotating_light"],
        )
        prev["notified_start"] = True
        prev["notified_pre"]   = True

    # ── Gols ───────────────────────────────────────────────
    if status in ("IN_PLAY", "PAUSED"):
        # Gol casa — checamos contra prev ANTES de atualizar
        if cur_home > prev["score_home"]:
            scorer = get_scorer(match, "homeTeam", cur_home)
            msg = f"{home} [{cur_home}]x{cur_away} {away}"
            if scorer:
                msg += f"\n{scorer}"
            notify(title="Gol!", message=msg, priority="urgent", tags=["soccer"])

        # Gol fora
        if cur_away > prev["score_away"]:
            scorer = get_scorer(match, "awayTeam", cur_away)
            msg = f"{home} {cur_home}x[{cur_away}] {away}"
            if scorer:
                msg += f"\n{scorer}"
            notify(title="Gol!", message=msg, priority="urgent", tags=["soccer"])

    # ── Fim ────────────────────────────────────────────────
    if status == "FINISHED" and not prev["notified_end"]:
        ft = score.get("fullTime") or {}
        fh = ft.get("home") if ft.get("home") is not None else cur_home
        fa = ft.get("away") if ft.get("away") is not None else cur_away

        if fh > fa:   result = f"Vitória de {home}!"
        elif fa > fh: result = f"Vitória de {away}!"
        else:         result = "Empate!"

        notify(
            title="Fim de papo!",
            message=f"{home} {fh}x{fa} {away}\n{result}",
            priority="high",
            tags=["checkered_flag"],
        )
        prev["notified_end"] = True

    prev["score_home"] = cur_home
    prev["score_away"] = cur_away
    prev["status"]     = status
    state[mid] = prev


def local_now() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=LOCAL_TZ_OFFSET)


def notify_daily_schedule(matches: list):
    today = local_now().date()
    today_matches = [
        m for m in matches
        if m["status"] != "FINISHED"
        and datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).astimezone(
            timezone(timedelta(hours=LOCAL_TZ_OFFSET))
        ).date() == today
    ]
    if not today_matches:
        return
    lines = []
    for m in today_matches:
        home = traduzir(m["homeTeam"].get("name", "?"))
        away = traduzir(m["awayTeam"].get("name", "?"))
        kickoff_str = m.get("utcDate", "")
        if kickoff_str:
            kickoff_utc = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
            kickoff_local = kickoff_utc + timedelta(hours=LOCAL_TZ_OFFSET)
            hora = kickoff_local.strftime("%H:%M")
        else:
            hora = "?"
        lines.append(f"{hora} — {home} x {away}")
    notify(
        title=f"Jogos de hoje ({len(today_matches)})",
        message="\n".join(lines),
        priority="default",
        tags=["calendar"],
    )


def notify_daily_results(matches: list):
    today = local_now().date()
    finished = [
        m for m in matches
        if m["status"] == "FINISHED"
        and datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")).astimezone(
            timezone(timedelta(hours=LOCAL_TZ_OFFSET))
        ).date() == today
    ]
    if not finished:
        return
    lines = []
    for m in finished:
        home = traduzir(m["homeTeam"].get("name", "?"))
        away = traduzir(m["awayTeam"].get("name", "?"))
        ft = (m["score"].get("fullTime") or {})
        fh = ft.get("home", "?")
        fa = ft.get("away", "?")
        lines.append(f"{home} {fh}x{fa} {away}")
    notify(
        title="Resultados do dia",
        message="\n".join(lines),
        priority="default",
        tags=["trophy"],
    )


def sleep_interval(matches: list) -> int:
    """Aumenta o intervalo quando não há jogos ao vivo para economizar requests."""
    live = any(m["status"] in ("IN_PLAY", "PAUSED") for m in matches)
    if live:
        return CHECK_INTERVAL
    # Verifica se tem jogo chegando em menos de 30 min
    now = datetime.now(timezone.utc)
    for m in matches:
        if m["status"] == "SCHEDULED":
            kickoff_str = m.get("utcDate", "")
            if kickoff_str:
                kickoff = datetime.fromisoformat(kickoff_str.replace("Z", "+00:00"))
                if (kickoff - now).total_seconds() < 30 * 60:
                    return CHECK_INTERVAL
    return max(CHECK_INTERVAL, 300)  # 5 min se não tiver nada urgente


# ─── Main ────────────────────────────────────────────────────

def run():
    log.info("Copa 2026 Tracker iniciado!")
    log.info(f"  Alerta pre-jogo: {PRE_MATCH_MINS} minutos antes")
    if not FOOTBALL_API_KEY:
        log.error("FOOTBALL_API_KEY nao definida!")
        return

    state = load_state()

    notify(
        title="Copa 2026 Tracker ativo!",
        message=f"Voce recebera alertas {PRE_MATCH_MINS} min antes, ao inicio, em cada gol e no fim das partidas.",
        tags=["trophy"],
    )

    last_schedule_date  = None  # data em que o resumo matinal foi enviado
    last_results_date   = None  # data em que os resultados foram enviados

    while True:
        log.info("Verificando partidas...")
        matches = get_matches()
        log.info(f"  {len(matches)} partida(s) hoje")

        now_local = local_now()
        today     = now_local.date()

        # ── Resumo matinal às 8h ───────────────────────────
        if now_local.hour >= 8 and last_schedule_date != today:
            if matches:
                notify_daily_schedule(matches)
                last_schedule_date = today
                log.info("Resumo matinal enviado")

        # ── Processar partidas ─────────────────────────────
        for m in matches:
            try:
                process_match(m, state)
            except Exception as e:
                log.error(f"Erro partida {m.get('id')}: {e}")

        # ── Resultados do dia após último jogo ─────────────
        if matches and last_results_date != today:
            all_done = all(m["status"] == "FINISHED" for m in matches)
            if all_done:
                notify_daily_results(matches)
                last_results_date = today
                log.info("Resultados do dia enviados")

        save_state(state)
        interval = sleep_interval(matches)
        log.info(f"  Proximo check em {interval}s")
        time.sleep(interval)


if __name__ == "__main__":
    run()
