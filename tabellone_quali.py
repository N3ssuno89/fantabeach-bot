from PIL import Image, ImageDraw, ImageFont
from italic import text_layer
from render import cognome, FONT


SCURO=(18,30,68); CHIP=(52,84,160); GRIGIO=(198,205,214)
VINC=(204,227,255); ORO=(250,214,116); LINEA=(150,168,200)

def sc(im,s,size,box,align="left",col=SCURO):
    L=text_layer(str(s),ImageFont.truetype(FONT,size),0,shear=0,fill=col,sfill=(255,255,255))
    x0,y0,x1,y1=box
    if L.width>(x1-x0): L=L.resize((int(x1-x0),L.height),Image.LANCZOS)
    x=x0 if align=="left" else (x1-L.width if align=="right" else x0+(x1-x0-L.width)//2)
    im.paste(L,(int(x),int(y0+(y1-y0-L.height)/2)),L)

def coppia(t):
    if not t: return ""
    u=t.upper()
    if u.startswith("WILD"): return "WILD CARD"
    if u.startswith("BYE"):  return "BYE"
    return " / ".join(cognome(x) for x in t.split(" - "))

def match(im,d,x,y,w,h,t1,t2,oro=False):
    ph=58
    ov=Image.new("RGBA",im.size,(0,0,0,0))
    ImageDraw.Draw(ov).rounded_rectangle([x+2,y+5,x+w+2,y+h+5],13,fill=(12,22,52,90))
    im.paste(Image.alpha_composite(im.convert("RGBA"),ov).convert("RGB"))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle([x,y,x+w,y+h],13,fill=(253,253,255),
                        outline=ORO if oro else (168,184,212),width=4 if oro else 1)
    rh=h//2
    for i,t in enumerate((t1,t2)):
        yy=y+i*rh
        vuoto = not t[1]
        bye = bool(t[1]) and t[1].upper().startswith("BYE")
        vin = t[2] is not None and t[3] is not None and t[2]>t[3]
        if vin:
            d.rounded_rectangle([x+3,yy+3,x+w-3,yy+rh-3],10,fill=ORO if oro else VINC)
        largo = x+w-12
        if t[2] is not None:
            d.rounded_rectangle([x+w-ph,yy+5,x+w-6,yy+rh-5],9,fill=GRIGIO)
            sc(im,t[2],30,(x+w-ph,yy,x+w-6,yy+rh),"center")
            largo = x+w-ph-10
        if t[0]!="":
            d.rounded_rectangle([x+10,yy+9,x+50,yy+rh-9],8,fill=CHIP)
            sc(im,t[0],19,(x+10,yy+9,x+50,yy+rh-9),"center",(255,255,255))
        sc(im,coppia(t[1]),27,(x+60,yy,largo,yy+rh),"left",
           (146,158,180) if (bye or vuoto) else SCURO)
    d.line([x+10,y+rh,x+w-10,y+rh],fill=(198,208,226),width=1)

def render(perc,out,sfondo=None):
    im=Image.open(sfondo).convert("RGB"); d=ImageDraw.Draw(im)
    Y0,PH,G=406,205,8
    LX,LW,RX,RW=44,500,600,436
    for tit,x0,x1 in (("1\u00b0 TURNO",LX,LX+LW),("2\u00b0 TURNO",RX,RX+RW)):
        d.rounded_rectangle([x0,368,x1,398],9,fill=(20,38,92))
        sc(im,tit,20,(x0,368,x1,398),"center",(214,232,255))
    for i,p in enumerate(perc):
        y=Y0+i*(PH+G)
        match(im,d,LX,y+4,LW,92,*p[0])
        match(im,d,LX,y+102,LW,92,*p[1])
        mx=LX+LW
        for yy in (y+50,y+148):
            d.line([mx+4,yy,mx+24,yy],fill=(255,255,255),width=5)
            d.line([mx+4,yy,mx+24,yy],fill=LINEA,width=3)
        d.line([mx+24,y+50,mx+24,y+148],fill=(255,255,255),width=5)
        d.line([mx+24,y+50,mx+24,y+148],fill=LINEA,width=3)
        d.line([mx+24,y+99,RX-4,y+99],fill=(255,255,255),width=5)
        d.line([mx+24,y+99,RX-4,y+99],fill=LINEA,width=3)
        match(im,d,RX,y+53,RW,92,*p[2],oro=p[3])
    im.save(out,quality=95)

def S(seed=None,team=None,a=None,b=None): return (seed if seed is not None else "",team,a,b)

