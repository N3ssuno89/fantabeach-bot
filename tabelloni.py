"""FantaBeach — tabelloni su Telegram.

QUALIFICHE (gare 1-18)
  t0 = 12 partite in calendario, nessuna giocata
  t1 = primo turno concluso
  t2 = qualifiche concluse

POOL (gare 19-34)
  t0 = 16 partite in calendario, nessuna giocata
  t1 = tutte le partite dei gironi concluse

Ogni stato esce una volta sola: la chiave in posted_items lo contiene.
PROVA=true  genera sempre, negli artifact, senza pubblicare.
FORZA=true  pubblica su Telegram i dati del momento, anche fuori dagli stati:
            usa una chiave con l'orario, quindi non blocca gli stati automatici.
"""
import os, json, pathlib, requests
from datetime import datetime, timezone
from tabellone_quali import render as render_quali, S
from tabellone_pool import render as render_pool
from tabellone_md import albero

SB_URL = os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY = os.environ["SUPABASE_KEY"]
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT", "")
PROVA = os.environ.get("PROVA", "").lower() == "true"
FORZA = os.environ.get("FORZA", "").lower() == "true"
TORNEI = [t.strip() for t in os.environ.get("TORNEI", "").split(",") if t.strip()]

OUT = pathlib.Path("out"); OUT.mkdir(exist_ok=True)
MAPPA = json.loads(pathlib.Path("templates/index.json").read_text())
H = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"}
GIOCATA = lambda m: m.get("status") not in (None, "scheduled", "live")


def sb(tab, params):
    r = requests.get(f"{SB_URL}/rest/v1/{tab}", headers=H, params=params, timeout=30)
    r.raise_for_status(); return r.json()


def sb_ins(tab, righe):
    r = requests.post(f"{SB_URL}/rest/v1/{tab}",
                      headers={**H, "Content-Type": "application/json",
                               "Prefer": "return=minimal"}, json=righe, timeout=30)
    r.raise_for_status()


def punti(m):
    if not m or not m.get("result"): return None, None
    try:
        a, b = m["result"].split("-"); return int(a), int(b)
    except Exception:
        return None, None


# ---------- QUALIFICHE ----------
def stato_quali(p):
    p1 = [m for m in p if m["match_no"] <= 12]
    p2 = [m for m in p if 13 <= m["match_no"] <= 18]
    if len(p2) == 6 and all(GIOCATA(m) for m in p2): return "t2"
    if len(p1) == 12 and all(GIOCATA(m) for m in p1): return "t1"
    if len(p1) == 12 and not any(GIOCATA(m) for m in p1): return "t0"
    return None


def dati_quali(partite, seeds):
    pn = {m["match_no"]: m for m in partite}
    out = []
    for i in range(1, 7):
        blocco = []
        for n in (2*i - 1, 2*i, 12 + i):
            m = pn.get(n)
            if not m: blocco.append((S(), S())); continue
            a, b = punti(m)
            ta, tb = m.get("team_a_name"), m.get("team_b_name")
            blocco.append((S(seeds.get(ta, ""), ta, a, b), S(seeds.get(tb, ""), tb, b, a)))
        fin = pn.get(12 + i)
        out.append([blocco[0], blocco[1], blocco[2], bool(fin and fin.get("result"))])
    return out


# ---------- POOL ----------
def stato_pool(p):
    g = [m for m in p if 19 <= m["match_no"] <= 34]
    if len(g) < 16: return None
    l1 = [m for m in g if m["match_no"] <= 26]
    l2 = [m for m in g if m["match_no"] >= 27]
    if all(GIOCATA(m) for m in l2): return "t2"
    if all(GIOCATA(m) for m in l1) and not any(GIOCATA(m) for m in l2): return "t1"
    if not any(GIOCATA(m) for m in g): return "t0"
    return None


def dati_pool(partite, seeds):
    pn = {m["match_no"]: m for m in partite}
    pools = []
    for p in range(4):
        def coppia(n, invertito=False):
            m = pn.get(n)
            if not m: return (S(), S())
            a, b = punti(m)
            ta, tb = m.get("team_a_name"), m.get("team_b_name")
            return (S(seeds.get(ta, ""), ta, a, b), S(seeds.get(tb, ""), tb, b, a))
        f12, f34 = pn.get(28 + 2*p), pn.get(27 + 2*p)
        d = {"nome": "ABCD"[p], "sf1": coppia(19 + 2*p), "sf2": coppia(20 + 2*p),
             "f12": coppia(28 + 2*p), "f34": coppia(27 + 2*p)}
        for chiave, m, alto, basso in (("e12", f12, "1", "2"), ("e34", f34, "3", "4")):
            if m and m.get("result"):
                a, b = punti(m)
                d[chiave] = (alto, basso) if a > b else (basso, alto)
        pools.append(d)
    return pools


# ---------- MAIN DRAW ----------
TURNI = {"t0": (35, 42), "t1": (35, 42), "t2": (43, 46), "t3": (47, 48)}

def stato_md(p):
    g = lambda a, b: [m for m in p if a <= m["match_no"] <= b]
    r12, qf, sf = g(35, 42), g(43, 46), g(47, 48)
    if len(sf) == 2 and all(GIOCATA(m) for m in sf): return "t3"
    if len(qf) == 4 and all(GIOCATA(m) for m in qf): return "t2"
    if len(r12) == 8 and all(GIOCATA(m) for m in r12): return "t1"
    if len(r12) == 8 and not any(GIOCATA(m) for m in r12): return "t0"
    return None


def dati_md(partite, seeds, st):
    pn = {m["match_no"]: m for m in partite}
    def coppia(n):
        m = pn.get(n)
        if not m: return (S(), S())
        a, b = punti(m)
        ta, tb = m.get("team_a_name"), m.get("team_b_name")
        return (S(seeds.get(ta, ""), ta, a, b), S(seeds.get(tb, ""), tb, b, a))
    blocchi = {"t0": (range(35, 43), range(43, 47), "ROUND OF 12", "QUARTI DI FINALE"),
               "t1": (range(35, 43), range(43, 47), "ROUND OF 12", "QUARTI DI FINALE"),
               "t2": (range(43, 47), range(47, 49), "QUARTI DI FINALE", "SEMIFINALI"),
               "t3": (range(47, 49), (50, 49), "SEMIFINALI", "FINALI")}[st]
    sx, dx, tsx, tdx = blocchi
    return ([coppia(n) for n in sx], [coppia(n) for n in dx], tsx, tdx)


# ---------- comune ----------
def sfondo_per(tappa, nome):
    for est in (".jpg", ".png"):
        c = pathlib.Path(f"templates/{tappa}/{nome}{est}")
        if c.exists(): return str(c)
    return None


def invia(percorso, didascalia):
    with open(percorso, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                          data={"chat_id": TG_CHAT, "caption": didascalia},
                          files={"photo": f}, timeout=60)
    r.raise_for_status(); return r.json()["result"]["message_id"]


ETICHETTE = {
    ("quali", "t0"): "Tabellone qualificazioni",
    ("quali", "t1"): "Qualificazioni — 1° turno concluso",
    ("quali", "t2"): "Qualificazioni — coppie qualificate",
    ("pool", "t0"): "Gironi — accoppiamenti",
    ("pool", "t1"): "Gironi — semifinali concluse",
    ("pool", "t2"): "Gironi — classifiche finali",
    ("md", "t0"): "Tabellone principale — sorteggio",
    ("md", "t1"): "Round of 12 — risultati e quarti",
    ("md", "t2"): "Quarti — risultati e semifinali",
    ("md", "t3"): "Semifinali — risultati e finali",
}


def main():
    vis = TORNEI or [str(t["vis_id"]) for t in
                     sb("fivb_tournaments", {"select": "vis_id", "status": "eq.ongoing",
                                             "season": "eq.2026"})]
    if not vis:
        print("nessun torneo in corso"); return
    print("tornei:", vis)
    tor = {str(t["vis_id"]): t for t in sb("fivb_tournaments",
           {"select": "vis_id,city,gender", "vis_id": f"in.({','.join(vis)})"})}
    allarmi = []

    for v in vis:
        partite = sb("fivb_matches", {
            "select": "match_no,phase,team_a_name,team_b_name,result,status",
            "tournament_vis_id": f"eq.{v}",
            "phase": "in.(qualification,pool,main_draw)", "order": "match_no"})
        seeds = {e["team_name"]: e["pos"] for e in
                 sb("fivb_entries", {"select": "team_name,pos", "tournament_vis_id": f"eq.{v}"})
                 if e.get("team_name")}
        tappa = MAPPA.get(v)

        for tipo, filtro, calcola, costruisci, disegna, sfondo_nome in (
            ("quali", lambda m: m["phase"] == "qualification", stato_quali,
             dati_quali, render_quali, "BRACKET_QUALIFICATION"),
            ("pool", lambda m: m["phase"] == "pool", stato_pool,
             dati_pool, render_pool, "BRACKET_POOL"),
            ("md", lambda m: m["phase"] == "main_draw", stato_md,
             None, None, "BRACKET_MAIN_DRAW"),
        ):
            sub = [m for m in partite if filtro(m)]
            st = calcola(sub)
            print(f"  {v} {tipo}: {len(sub)} partite -> stato {st or '-'}")
            if not sub: continue
            if st is None and not (PROVA or FORZA): continue

            if FORZA:
                chiave = f"{tipo}:{v}:manuale:{datetime.now(timezone.utc):%Y-%m-%dT%H:%M}"
            else:
                chiave = f"{tipo}:{v}:{st}"
                if not PROVA and sb("posted_items", {"select": "id", "id": f"eq.{chiave}"}):
                    print(f"     {st} gia' pubblicato"); continue

            sf = sfondo_per(tappa, sfondo_nome)
            if sf is None:
                allarmi.append(f"sfondo mancante: templates/{tappa}/{sfondo_nome}"); continue

            dest = OUT / f"{v}_{tipo.upper()}_{st or 'manuale'}.png"
            try:
                if tipo == "md":
                    sx, dx, tsx, tdx = dati_md(sub, seeds, st or "t1")
                    et = ["FINALE 1° POSTO", "FINALE 3° POSTO"] if (st or "") == "t3" else None
                    albero(sf, sx, dx, tsx, tdx, str(dest),
                           oro_dx=((st or "") == "t3"), etichette=et)
                elif tipo == "pool":
                    disegna(sf, costruisci(sub, seeds), str(dest))
                else:
                    disegna(costruisci(sub, seeds), str(dest), sfondo=sf)
            except Exception as ex:
                allarmi.append(f"render {v}/{tipo}/{st}: {ex}"); continue

            if PROVA:
                print(f"     [prova] generata {dest.name}"); continue
            t = tor.get(v, {})
            testo = ETICHETTE.get((tipo, st)) or (
                "Tabellone qualificazioni" if tipo == "quali" else "Gironi")
            cap = f"{t.get('city','')} {t.get('gender','')} — {testo}"
            if FORZA: cap += " (aggiornamento)"
            try:
                mid = invia(str(dest), cap)
            except Exception as ex:
                allarmi.append(f"invio {v}/{tipo}/{st}: {ex}"); continue
            sb_ins("posted_items", [{"id": chiave, "kind": "tabellone",
                                     "telegram_message_id": mid}])
            print(f"     inviato {tipo} {st}")

    for a in allarmi: print("  !", a)
    if allarmi and TG_TOKEN:
        pre = "[PROVA] " if PROVA else ""
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      data={"chat_id": TG_CHAT,
                            "text": pre + "Tabelloni — problemi:\n" + "\n".join(allarmi[:10])},
                      timeout=30)


if __name__ == "__main__":
    main()
