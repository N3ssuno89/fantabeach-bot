"""FantaBeach — tabelloni qualifiche su Telegram, in tre stati.

t0 = accoppiamenti noti          (12 partite in calendario)
t1 = primo turno concluso        (12 partite giocate)
t2 = qualifiche concluse         (6 spareggi giocati)

Ogni stato viene pubblicato una volta sola: la chiave in posted_items
contiene lo stato, quindi t1 non viene bloccato da t0.
"""
import os, json, pathlib, requests
from tabellone_quali import render, S

SB_URL = os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY = os.environ["SUPABASE_KEY"]
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT", "")
PROVA = os.environ.get("PROVA", "").lower() == "true"
TORNEI = [t.strip() for t in os.environ.get("TORNEI", "").split(",") if t.strip()]

OUT = pathlib.Path("out"); OUT.mkdir(exist_ok=True)
MAPPA = json.loads(pathlib.Path("templates/index.json").read_text())
H = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"}


def sb(tabella, params):
    r = requests.get(f"{SB_URL}/rest/v1/{tabella}", headers=H, params=params, timeout=30)
    r.raise_for_status(); return r.json()


def sb_ins(tabella, righe):
    r = requests.post(f"{SB_URL}/rest/v1/{tabella}",
                      headers={**H, "Content-Type": "application/json",
                               "Prefer": "return=minimal"}, json=righe, timeout=30)
    r.raise_for_status()


def stato(partite):
    p1 = [m for m in partite if m["match_no"] <= 12]
    p2 = [m for m in partite if 13 <= m["match_no"] <= 18]
    fatte = lambda L: [m for m in L if m.get("status") not in (None, "scheduled", "live")]
    if len(p2) == 6 and len(fatte(p2)) == 6: return "t2"
    if len(p1) == 12 and len(fatte(p1)) == 12: return "t1"
    if len(p1) == 12 and len(fatte(p1)) == 0: return "t0"
    return None


def punteggi(m):
    if not m or not m.get("result"): return None, None
    try:
        a, b = m["result"].split("-"); return int(a), int(b)
    except Exception:
        return None, None


def costruisci(partite, seeds):
    """Percorso i -> gare 2i-1, 2i e 12+i."""
    per_no = {m["match_no"]: m for m in partite}
    perc = []
    for i in range(1, 7):
        blocco = []
        for n in (2*i - 1, 2*i, 12 + i):
            m = per_no.get(n)
            if not m:
                blocco.append((S(), S())); continue
            a, b = punteggi(m)
            ta, tb = m.get("team_a_name"), m.get("team_b_name")
            blocco.append((S(seeds.get(ta, ""), ta, a, b),
                           S(seeds.get(tb, ""), tb, b, a)))
        fin = per_no.get(12 + i)
        oro = bool(fin and fin.get("result"))
        perc.append([blocco[0], blocco[1], blocco[2], oro])
    return perc


def invia(percorso, didascalia):
    with open(percorso, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                          data={"chat_id": TG_CHAT, "caption": didascalia},
                          files={"photo": f}, timeout=60)
    r.raise_for_status(); return r.json()["result"]["message_id"]


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
            "select": "match_no,team_a_name,team_b_name,result,status",
            "tournament_vis_id": f"eq.{v}", "phase": "eq.qualification",
            "order": "match_no"})
        st = stato(partite)
        print(f"  {v}: {len(partite)} partite -> stato {st}")
        if st is None: continue

        chiave = f"quali:{v}:{st}"
        if sb("posted_items", {"select": "id", "id": f"eq.{chiave}"}):
            print(f"     {st} gia' pubblicato"); continue

        tappa = MAPPA.get(v)
        sfondo = None
        for est in (".jpg", ".png"):
            c = pathlib.Path(f"templates/{tappa}/BRACKET_QUALIFICATION{est}")
            if c.exists(): sfondo = str(c); break
        if sfondo is None:
            allarmi.append(f"sfondo mancante: templates/{tappa}/BRACKET_QUALIFICATION"); continue

        seeds = {}
        for e in sb("fivb_entries", {"select": "team_name,pos", "tournament_vis_id": f"eq.{v}"}):
            if e.get("team_name"): seeds[e["team_name"]] = e["pos"]

        dest = OUT / f"{v}_QUALI_{st}.png"
        try:
            render(costruisci(partite, seeds), str(dest), sfondo=sfondo)
        except Exception as ex:
            allarmi.append(f"render {v}/{st}: {ex}"); continue

        t = tor.get(v, {})
        etichetta = {"t0": "Tabellone qualificazioni",
                     "t1": "Qualificazioni — 1° turno concluso",
                     "t2": "Qualificazioni — coppie qualificate"}[st]
        cap = f"{t.get('city','')} {t.get('gender','')} — {etichetta}"
        if PROVA:
            print(f"     [prova] generata {dest.name}"); continue
        try:
            mid = invia(str(dest), cap)
        except Exception as ex:
            allarmi.append(f"invio {v}/{st}: {ex}"); continue
        sb_ins("posted_items", [{"id": chiave, "kind": "tabellone",
                                 "telegram_message_id": mid}])
        print(f"     inviato {st}")

    for a in allarmi: print("  !", a)
    if allarmi and TG_TOKEN:
        pre = "[PROVA] " if PROVA else ""
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      data={"chat_id": TG_CHAT,
                            "text": pre + "Tabelloni — problemi:\n" + "\n".join(allarmi[:10])},
                      timeout=30)


if __name__ == "__main__":
    main()
