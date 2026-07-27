"""FantaBeach bot — pubblica i risultati delle partite su Telegram.

Ciclo: chiede al DB le partite concluse, scarta quelle gia' in posted_items,
genera l'immagine, la invia, la registra. Nessun trigger: solo polling.
"""
import os, sys, json, time, pathlib, requests
from render import render, template_for

SB_URL = os.environ["SUPABASE_URL"].rstrip("/")
SB_KEY = os.environ["SUPABASE_KEY"]
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TG_CHAT = os.environ.get("TELEGRAM_CHAT", "")
PROVA = os.environ.get("PROVA", "").lower() == "true"
TORNEI = [t.strip() for t in os.environ.get("TORNEI", "").split(",") if t.strip()]

MAX_PER_GIRO = 15        # limite anti rate-limit Telegram
PAUSA = 4                # secondi fra un invio e l'altro
OUT = pathlib.Path("out"); OUT.mkdir(exist_ok=True)
MAPPA = json.loads(pathlib.Path("templates/index.json").read_text())
H = {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}"}


def sb_get(tabella, params):
    r = requests.get(f"{SB_URL}/rest/v1/{tabella}", headers=H, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def sb_insert(tabella, righe):
    r = requests.post(f"{SB_URL}/rest/v1/{tabella}", headers={**H, "Content-Type": "application/json",
                      "Prefer": "return=minimal"}, json=righe, timeout=30)
    r.raise_for_status()


def tornei_attivi():
    if TORNEI:
        return TORNEI
    t = sb_get("fivb_tournaments", {"select": "vis_id", "status": "eq.ongoing", "season": "eq.2026"})
    return [str(x["vis_id"]) for x in t]


def partite(vis_ids):
    return sb_get("fivb_matches", {
        "select": "tournament_vis_id,match_no,phase,round,team_a_name,team_b_name,result,sets,status",
        "tournament_vis_id": f"in.({','.join(vis_ids)})",
        "status": "eq.finished",
        "order": "tournament_vis_id,match_no",
    })


def gia_pubblicate(vis_ids):
    out = set()
    for v in vis_ids:
        for r in sb_get("posted_items", {"select": "id", "id": f"like.risultato:{v}:*"}):
            out.add(r["id"])
    return out


def invia(percorso, didascalia):
    with open(percorso, "rb") as f:
        r = requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto",
                          data={"chat_id": TG_CHAT, "caption": didascalia},
                          files={"photo": f}, timeout=60)
    if r.status_code == 429:
        raise RuntimeError("rate limit Telegram")
    r.raise_for_status()
    return r.json()["result"]["message_id"]


def main():
    vis = tornei_attivi()
    if not vis:
        print("nessun torneo in corso"); return
    print(f"tornei: {vis}")

    tor = {str(t["vis_id"]): t for t in sb_get("fivb_tournaments",
           {"select": "vis_id,title,gender,city", "vis_id": f"in.({','.join(vis)})"})}
    fatte = gia_pubblicate(vis)
    tutte = partite(vis)
    print(f"partite concluse: {len(tutte)} | gia' pubblicate: {len(fatte)}")

    inviate, saltate, allarmi = 0, 0, []
    for m in tutte:
        v = str(m["tournament_vis_id"])
        chiave = f"risultato:{v}:{m['match_no']}"
        if chiave in fatte:
            continue
        if not m.get("team_a_name") or not m.get("team_b_name"):
            saltate += 1; continue
        if m["team_a_name"].startswith("BYE") or m["team_b_name"].startswith("BYE"):
            saltate += 1; continue
        if not m.get("result") or not m.get("sets"):
            saltate += 1; continue

        fase = template_for(m["phase"], m.get("round"))
        if fase is None:
            allarmi.append(f"fase sconosciuta: {m['phase']} / {m.get('round')}"); continue
        tappa = MAPPA.get(v)
        if tappa is None:
            allarmi.append(f"vis_id {v} non in index.json"); continue
        tpl = pathlib.Path(f"templates/{tappa}/{fase}.png")
        if not tpl.exists():
            allarmi.append(f"template mancante: {tpl}"); continue

        dest = OUT / f"{v}_{m['match_no']:02d}_{fase}.png"
        try:
            render(str(tpl), m, str(dest))
        except Exception as e:
            allarmi.append(f"render {v}/{m['match_no']}: {e}"); continue

        t = tor.get(v, {})
        didascalia = f"{t.get('city','')} {t.get('gender','')} — {fase.replace('_',' ').title()}"
        if PROVA:
            inviate += 1
        else:
            try:
                mid = invia(str(dest), didascalia)
            except Exception as e:
                allarmi.append(f"invio {v}/{m['match_no']}: {e}"); break
            sb_insert("posted_items", [{"id": chiave, "kind": "risultato", "telegram_message_id": mid}])
            inviate += 1
            time.sleep(PAUSA)

        if inviate >= MAX_PER_GIRO:
            print(f"raggiunto il limite di {MAX_PER_GIRO}, il resto al prossimo giro"); break

    print(f"inviate: {inviate} | saltate: {saltate} | allarmi: {len(allarmi)}")
    for a in allarmi[:20]:
        print("  !", a)
    if allarmi and not PROVA and TG_TOKEN:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                      data={"chat_id": TG_CHAT,
                            "text": "Problemi:\n" + "\n".join(allarmi[:10])}, timeout=30)


if __name__ == "__main__":
    main()
