"""
Copa do Mundo 2026 - Tracker com nomes em PT-BR e bandeiras
"""

import os
import time
import logging
import requests

FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "")
NTFY_TOPIC       = os.environ.get("NTFY_TOPIC", "copa2026-seu-nome")
NTFY_SERVER      = os.environ.get("NTFY_SERVER", "https://ntfy.sh")
CHECK_INTERVAL   = int(os.environ.get("CHECK_INTERVAL", "60"))
COMPETITION_ID   = "WC"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

state = {}

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
    "Japan":               ("🇯🇵", "Japão"),
    "Qatar":               ("🇶🇦", "Catar"),
    "South Korea":         ("🇰🇷", "Coreia do Sul"),
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
    "Russia":              ("🇷🇺", "Rússia"),
    "Scotland":            ("🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Escócia"),
    "Wales":               ("🏴󠁧󠁢󠁷󠁬󠁳󠁿", "País de Gales"),
    "Ireland":             ("🇮🇪", "Irlanda"),
    "Albania":             ("🇦🇱", "Albânia"),
    "Georgia":             ("🇬🇪", "Geórgia"),
    "North Macedonia":     ("🇲🇰", "Macedônia do Norte"),
}

def traduzir(nome_en: str) -> str:
    """Retorna 'bandeira Nome-PT' para o país, ou o nome original se não encontrado"""
    if nome_en in PAISES:
        flag, nome_pt = PAISES[nome_en]
        return f"{flag} {nome_pt}"
    # fallback: tenta match parcial
    for key, (flag, nome_pt) in PAISES.items():
        if key.lower() in nome_en.lower() or nome_en.lower() in key.lower():
            return f"{flag} {nome_pt}"
    return nome_en  # retorna original se não achar


# ─── Ntfy ────────────────────────────────────────────────────

def notify(title: str, message: str, priority: str = "default", tags: list = None):
    try:
        r = requests.post(
            f"{NTFY_SERVER}/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title":        title.encode("utf-8").decode("latin-1", errors="ignore"),
                "Priority":     priority,
                "Tags":         ",".join(tags or ["soccer"]),
                "Content-Type": "text/plain; charset=utf-8",
            },
            timeout=10,
        )
        r.raise_for_status()
        log.info(f"Notif: {title}")
    except Exception as e:
        log.error(f"Erro notif: {e}")


# ─── API football-data.org ────────────────────────────────────

def get_matches():
    try:
        r = requests.get(
            f"https://api.football-data.org/v4/competitions/{COMPETITION_ID}/matches",
            headers={"X-Auth-Token": FOOTBALL_API_KEY},
            params={"status": "LIVE,IN_PLAY,PAUSED,FINISHED,SCHEDULED"},
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


def get_scorer(match, side: str, prev_goals: int, cur_goals: int) -> str:
    """Tenta extrair o nome do autor do gol mais recente"""
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

def process_match(match):
    mid    = match["id"]
    home_en = match["homeTeam"].get("name", "?")
    away_en = match["awayTeam"].get("name", "?")
    home   = traduzir(home_en)
    away   = traduzir(away_en)
    status = match["status"]
    score  = match["score"]

    cur = score.get("regularTime") or score.get("fullTime") or {}
    cur_home = cur.get("home") or 0
    cur_away = cur.get("away") or 0

    prev = state.get(mid, {
        "score_home": 0, "score_away": 0,
        "status": None,
        "notified_start": False, "notified_end": False,
    })

    # Inicio
    if status == "IN_PLAY" and not prev["notified_start"]:
        notify(
            title="Comecou!",
            message=f"Bola rolando para\n{home} x {away}",
            priority="high",
            tags=["rotating_light"],
        )
        prev["notified_start"] = True

    # Gol casa
    if status in ("IN_PLAY", "PAUSED") and cur_home > prev["score_home"]:
        scorer = get_scorer(match, "homeTeam", prev["score_home"], cur_home)
        placar = f"[{cur_home}]x{cur_away}"
        msg = f"{home} {placar} {away}"
        if scorer:
            msg += f"\n{scorer}"
        notify(title="Gol!", message=msg, priority="urgent", tags=["soccer"])

    # Gol fora
    if status in ("IN_PLAY", "PAUSED") and cur_away > prev["score_away"]:
        scorer = get_scorer(match, "awayTeam", prev["score_away"], cur_away)
        placar = f"{cur_home}x[{cur_away}]"
        msg = f"{home} {placar} {away}"
        if scorer:
            msg += f"\n{scorer}"
        notify(title="Gol!", message=msg, priority="urgent", tags=["soccer"])

    # Fim
    if status == "FINISHED" and not prev["notified_end"]:
        ft = score["fullTime"]
        fh = ft.get("home") if ft.get("home") is not None else cur_home
        fa = ft.get("away") if ft.get("away") is not None else cur_away

        if fh > fa:   result = f"Vitoria de {home}!"
        elif fa > fh: result = f"Vitoria de {away}!"
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


# ─── Main ────────────────────────────────────────────────────

def run():
    log.info("Copa 2026 Tracker iniciado!")
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
        matches = get_matches()
        log.info(f"  {len(matches)} partida(s)")
        for m in matches:
            try:
                process_match(m)
            except Exception as e:
                log.error(f"Erro partida {m.get('id')}: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    run()
