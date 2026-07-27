"""Controlla che i template ci siano tutti, con i nomi giusti.
Gira a ogni run: se manca qualcosa lo dice prima che serva davvero."""
import json, pathlib, sys

FASI = ["QUALIFICATION", "POOL", "ROUND_OF_12", "QUARTERFINAL",
        "SEMIFINAL", "FINAL_3_4", "FINAL_1_2"]
BASE = pathlib.Path("templates")
mappa = json.loads((BASE / "index.json").read_text())

tappe = {}
for vis, tappa in mappa.items():
    tappe.setdefault(tappa, []).append(vis)

problemi = []
print("=== INVENTARIO TEMPLATE ===")
for tappa in sorted(tappe):
    cart = BASE / tappa
    if not cart.is_dir():
        print(f"  {tappa:<14} cartella assente  (vis_id {','.join(sorted(tappe[tappa]))})")
        continue
    ok, mancanti = [], []
    for fase in FASI:
        trovato = next((e for e in (".jpg", ".png") if (cart / f"{fase}{e}").exists()), None)
        (ok if trovato else mancanti).append(fase)
    stato = "COMPLETA" if not mancanti else f"MANCANO {len(mancanti)}"
    print(f"  {tappa:<14} {len(ok)}/7  {stato}")
    for f in mancanti:
        print(f"       - manca {f}")
        problemi.append(f"{tappa}/{f}")
    # file con estensione o nome sbagliato
    attesi = {f"{f}{e}" for f in FASI for e in (".jpg", ".png")}
    for altro in sorted(p.name for p in cart.iterdir() if p.is_file()):
        if altro not in attesi:
            print(f"       ? file non riconosciuto: {altro}")

if problemi:
    print(f"\n!! {len(problemi)} template mancanti — le partite di quelle fasi non verranno pubblicate")
else:
    print("\nTutte le cartelle presenti sono complete.")
