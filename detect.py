"""Rileva i box dal template leggendo i bordi bianchi. Nessuna coordinata fissa."""
from PIL import Image
import numpy as np

def _bands(vals, lo, hi, gap=4, minlen=2):
    ys=[y for y in range(lo,hi) if vals[y]]
    if not ys: return []
    g=[];cur=[ys[0]]
    for y in ys[1:]:
        if y-cur[-1]<=gap: cur.append(y)
        else: g.append((cur[0],cur[-1]));cur=[y]
    g.append((cur[0],cur[-1]))
    return [t for t in g if t[1]-t[0]>=minlen]

def detect(path):
    a=np.array(Image.open(path).convert("RGB")).astype(int)
    H,W,_=a.shape
    white=lambda arr:(arr.min(axis=-1)>195)&(arr.max(axis=-1)-arr.min(axis=-1)<50)
    hb=_bands(white(a[:,int(W*0.28),:]), int(H*0.22), int(H*0.92))
    if len(hb)<6: raise RuntimeError("bordi orizzontali non riconosciuti: %r"%hb)
    A=(hb[0][1]+1, hb[1][0]-1)      # box numeri
    C=(hb[2][1]+1, hb[3][0]-1)      # box set
    D=(hb[4][1]+1, hb[5][0]-1)      # barra VS
    def xr(y0,y1,frac):
        row=white(a[y0:y1,:,:]); c=row.sum(axis=0)
        xs=[x for x in range(int(W*0.05),int(W*0.96)) if c[x]>(y1-y0)*frac]
        return _bands(np.isin(np.arange(W),xs), 0, W, gap=6, minlen=1)
    cb=xr(C[0]+8, C[1]-8, .55)          # il box set da' i margini esterni
    if len(cb)<2: raise RuntimeError("margini esterni non riconosciuti")
    left,right=cb[0][1],cb[-1][0]
    mid=xr(A[0]+60, A[1]-60, .42)       # separatore centrale fra A e B
    inner=[b for b in mid if left+W*0.15<b[0] and b[1]<right-W*0.15]
    if len(inner)>=2: ma,mb=inner[0][0], inner[-1][1]
    elif len(inner)==1: ma,mb=inner[0][0], inner[0][1]
    else: ma,mb=int(W*0.47),int(W*0.53)
    boxA=(left+4, A[0]+4, ma-4, A[1]-4)
    boxB=(mb+4,   A[0]+4, right-4, A[1]-4)
    boxC=(left+8, C[0]+6, right-8, C[1]-6)
    # zona VS: trovo il glifo centrale
    band=white(a[D[0]+10:D[1]-10,:,:]); cc=band.sum(axis=0)
    mid=[x for x in range(int(W*0.35),int(W*0.65)) if cc[x]>8]
    gl=(min(mid),max(mid)) if mid else (int(W*0.46),int(W*0.54))
    boxDL=(left+12, D[0]+8, gl[0]-16, D[1]-8)
    boxDR=(gl[1]+16, D[0]+8, right-12, D[1]-8)
    boxD=(left+12, D[0]+8, right-12, D[1]-8)   # barra intera, senza glifo VS
    return dict(A=boxA,B=boxB,C=boxC,D=boxD,DL=boxDL,DR=boxDR)

if __name__=="__main__":
    import sys,json
    print(json.dumps(detect(sys.argv[1]),indent=1))
