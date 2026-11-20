"""Раз в сутки (GitHub Actions) тянет из PandaScore матчи наших команд и пишет data/live.json.
Токен берётся из секрета PANDASCORE_TOKEN. Только стандартная библиотека Python."""
import json, os, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

TOKEN = os.environ.get("PANDASCORE_TOKEN", "").strip()
API = "https://api.pandascore.co"
TEAMS = {"furia": "FURIA", "mouz": "MOUZ", "spirit": "Team Spirit", "vitality": "Team Vitality", "aurora": "Aurora",
         "falcons": "Falcons", "betboom": "BetBoom", "navi": "Natus Vincere", "fut": "FUT Esports", "mongolz": "The MongolZ",
         "g2": "G2 Esports", "parivision": "PARIVISION", "legacy": "Legacy", "liquid": "Team Liquid", "faze": "FaZe Clan",
         "astralis": "Astralis", "b8": "B8", "heroic": "HEROIC", "m80": "M80", "gamerlegion": "GamerLegion",
         "pain": "paiN Gaming", "bcgame": "BC.Game"}
ALIASES = {"falcons": ["Team Falcons", "Falcons"], "spirit": ["Team Spirit", "Spirit"], "vitality": ["Vitality", "Team Vitality"],
           "navi": ["Natus Vincere", "NAVI"], "fut": ["FUT Esports", "FUT"], "mongolz": ["The MongolZ", "MongolZ"],
           "g2": ["G2", "G2 Esports"], "liquid": ["Team Liquid", "Liquid"], "faze": ["FaZe", "FaZe Clan"], "pain": ["paiN", "paiN Gaming"],
           "bcgame": ["BC.Game", "BC.Game Esports"], "aurora": ["Aurora", "Aurora Gaming"], "betboom": ["BetBoom Team", "BetBoom"]}
OVERRIDE = json.load(open("scripts/pandascore_ids.json")) if os.path.exists("scripts/pandascore_ids.json") else {}
LOG = []


def get(path, **q):
    url = API + path + ("?" + urllib.parse.urlencode(q) if q else "")
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + TOKEN, "Accept": "application/json", "User-Agent": "cfgpeek.com"})
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            LOG.append(f"{e.code} {path} {q}")
            if e.code in (401, 403, 404):
                return None
            time.sleep(3 * (i + 1))
        except Exception as e:
            LOG.append(f"ERR {path} {e}")
            time.sleep(3 * (i + 1))
    return None


def norm(s):
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


def find_team(slug, name):
    if slug in OVERRIDE:
        return get(f"/csgo/teams/{OVERRIDE[slug]}") or {"id": OVERRIDE[slug], "name": name}
    want = {norm(n) for n in [name] + ALIASES.get(slug, [])}
    cands = []
    for n in [name] + ALIASES.get(slug, []):
        r = get("/csgo/teams", **{"search[name]": n, "per_page": 50}) or []
        cands += r
        exact = [t for t in r if norm(t.get("name")) in want or norm(t.get("acronym")) in want]
        if exact:
            # самая «живая» команда: с текущим составом, дальше — с большим id (новее)
            exact.sort(key=lambda t: (len(t.get("players") or []) > 0, t.get("modified_at") or "", t["id"]), reverse=True)
            return exact[0]
    LOG.append(f"not found: {slug} candidates={[ (t['id'], t.get('name')) for t in cands[:8]]}")
    return None


def slim_match(m, tid):
    opp = [o["opponent"] for o in m.get("opponents") or [] if o.get("opponent") and o["opponent"].get("id") != tid]
    res = {r.get("team_id"): r.get("score") for r in m.get("results") or []}
    games = []
    for g in m.get("games") or []:
        mp = g.get("map") or {}
        w = (g.get("winner") or {}).get("id")
        games.append({"map": mp.get("name"), "win": None if w is None else w == tid, "st": g.get("status")})
    o = opp[0] if opp else {}
    return {"id": m.get("id"), "at": m.get("begin_at") or m.get("scheduled_at"), "bo": m.get("number_of_games"),
            "st": m.get("status"), "opp": o.get("name"), "oppAc": o.get("acronym"), "oppImg": o.get("image_url"),
            "us": res.get(tid), "them": res.get(o.get("id")), "win": None if not m.get("winner_id") else m.get("winner_id") == tid,
            "tour": (m.get("tournament") or {}).get("name"), "league": (m.get("league") or {}).get("name"),
            "serie": (m.get("serie") or {}).get("full_name"), "tier": (m.get("tournament") or {}).get("tier"), "games": games}


def main():
    if not TOKEN:
        sys.exit("нет PANDASCORE_TOKEN")
    out = {"updated": datetime.now(timezone.utc).isoformat(timespec="minutes"), "teams": {}}
    sample = None
    for slug, name in TEAMS.items():
        t = find_team(slug, name)
        if not t:
            continue
        tid = t["id"]
        past = get("/csgo/matches/past", **{"filter[opponent_id]": tid, "sort": "-begin_at", "per_page": 60}) or []
        up = get("/csgo/matches/upcoming", **{"filter[opponent_id]": tid, "sort": "begin_at", "per_page": 10}) or []
        if sample is None and past:
            sample = past[0]
        out["teams"][slug] = {"psId": tid, "psName": t.get("name"), "img": t.get("image_url"),
                              "past": [slim_match(m, tid) for m in past], "next": [slim_match(m, tid) for m in up]}
        time.sleep(0.5)
    os.makedirs("data", exist_ok=True)
    json.dump(out, open("data/live.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    # для отладки: один сырой матч и журнал запросов
    json.dump({"log": LOG, "sample": sample}, open("data/live_debug.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"команд: {len(out['teams'])}/{len(TEAMS)}; ошибок: {len(LOG)}")


if __name__ == "__main__":
    main()
