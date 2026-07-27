"""FantaBeach — genera l'immagine risultato da una partita fivb_matches."""
import os, json
from PIL import Image, ImageFont
from italic import text_layer
from detect import detect

FONT = os.path.join(os.path.dirname(__file__), "fonts/anton.ttf")
NUM_STROKE, TXT_STROKE = 9, 4
STRETCH_V, PAD, VS_RATIO, GAP = 1.15, 0.94, 0.62, 4
NAME_SIZE = None          # None = adattivo; numero = corpo fisso su tutti i template

PARTICELLE = {"DI","DE","DA","DAL","DEL","DELLA","DELLE","DELLO","DEI","DEGLI",
              "LA","LO","LE","RE","LI","VAN","VON","DER","DEN","SAN","SANTA","MC","MAC","ST"}

def template_for(phase, round_):
    if phase == "qualification": return "QUALIFICATION"
    if phase == "pool":          return "POOL"
    if phase == "main_draw":
        return {"1° Turno Vincenti":"ROUND_OF_12", "2° Turno Vincenti":"QUARTERFINAL",
                "Semifinale":"SEMIFINAL", "Finale 3°-4°":"FINAL_3_4",
                "Finale 1°-2°":"FINAL_1_2"}.get(round_)
    return None

def cognome(full):
    p = full.strip().upper().split()
    if not p: return ""
    if p[0] in PARTICELLE and len(p) > 1: return p[0] + " " + p[1]
    return p[0]

def coppia(team_name):
    return [cognome(x) for x in team_name.split(" - ")]

def fmt_sets(sets):
    if any((a == 0 and b == 21) or (a == 21 and b == 0) for a, b in sets): return "FORFAIT"
    return "   ".join(f"{a}-{b}" for a, b in sets)

def _paste(im, lay, box, dy=0):
    x0, y0, x1, y1 = box
    im.paste(lay, (int(x0 + (x1-x0-lay.width)/2), int(y0 + (y1-y0-lay.height)/2 + dy)), lay)

def render(tpl_path, match, out_path):
    box = detect(tpl_path)
    im = Image.open(tpl_path).convert("RGB")

    bw, bh = box["A"][2]-box["A"][0], box["A"][3]-box["A"][1]
    ns = 80
    for s in range(760, 80, -4):
        f = ImageFont.truetype(FONT, s)
        L = [text_layer(d, f, NUM_STROKE, shear=0) for d in "012"]
        if max(l.width for l in L) <= bw*0.90 and max(l.height for l in L)*STRETCH_V <= bh*0.95:
            ns = s; break
    fn = ImageFont.truetype(FONT, ns)
    for v, k in zip(match["result"].split("-"), ("A", "B")):
        L = text_layer(v, fn, NUM_STROKE, shear=0)
        _paste(im, L.resize((L.width, int(L.height*STRETCH_V)), Image.LANCZOS), box[k])

    st = fmt_sets(match["sets"])
    for s in range(140, 27, -1):
        L = text_layer(st, ImageFont.truetype(FONT, s), TXT_STROKE, shear=0)
        if L.width <= (box["C"][2]-box["C"][0])*PAD and L.height <= (box["C"][3]-box["C"][1])*PAD:
            _paste(im, L, box["C"]); break

    D = box["D"]; W = (D[2]-D[0])*PAD; H = (D[3]-D[1])*PAD
    r1 = " / ".join(coppia(match["team_a_name"]))
    r3 = " / ".join(coppia(match["team_b_name"]))
    sizes = [NAME_SIZE] if NAME_SIZE else range(160, 17, -1)
    chosen = None
    for s in sizes:
        f = ImageFont.truetype(FONT, s); fv = ImageFont.truetype(FONT, max(12, int(s*VS_RATIO)))
        L1 = text_layer(r1, f, TXT_STROKE, shear=0)
        L3 = text_layer(r3, f, TXT_STROKE, shear=0)
        LV = text_layer("VS", fv, TXT_STROKE, shear=0)
        if max(L1.width, L3.width, LV.width) <= W and L1.height+LV.height+L3.height+2*GAP <= H:
            chosen = (s, L1, LV, L3); break
    if chosen is None: raise RuntimeError("nomi non entrano: %s | %s" % (r1, r3))
    s, L1, LV, L3 = chosen
    tot = L1.height + LV.height + L3.height + 2*GAP
    y = D[1] + ((D[3]-D[1]) - tot)/2
    for L in (L1, LV, L3):
        im.paste(L, (int(D[0] + ((D[2]-D[0]) - L.width)/2), int(y)), L); y += L.height + GAP
    im.save(out_path, quality=95)
    return s
