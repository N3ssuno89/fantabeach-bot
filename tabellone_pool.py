from PIL import Image, ImageDraw, ImageFont
from italic import text_layer
from render import cognome, FONT

SCURO=(18,30,68); CHIP=(52,84,160); GRIGIO=(198,205,214)
VINC=(204,227,255); ORO=(250,214,116); FUORI=(228,230,236)

def sc(im,s,size,box,align="left",col=SCURO):
    L=text_layer(str(s),ImageFont.truetype(FONT,size),0,shear=0,fill=col,sfill=(255,255,255))
    x0,y0,x1,y1=box
    if L.width>(x1-x0): L=L.resize((int(x1-x0),L.height),Image.LANCZOS)
    x=x0 if align=="left" else (x1-L.width if align=="right" else x0+(x1-x0-L.width)//2)
    im.paste(L,(int(x),int(y0+(y1-y0-L.height)/2)),L)

def coppia(t):
    if not t: return ""
    return " / ".join(cognome(x) for x in t.split(" - "))

def match(im,d,x,y,w,titolo,t1,t2,esiti=(None,None)):
    HH,RH=(26 if titolo else 0),46; h=HH+2*RH
    ov=Image.new("RGBA",im.size,(0,0,0,0))
    ImageDraw.Draw(ov).rounded_rectangle([x+2,y+5,x+w+2,y+h+5],13,fill=(12,22,52,90))
    im.paste(Image.alpha_composite(im.convert("RGBA"),ov).convert("RGB"))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle([x,y,x+w,y+h],13,fill=(253,253,255),outline=(168,184,212),width=1)
    if titolo:
        d.rounded_rectangle([x,y,x+w,y+HH+12],13,fill=(20,38,92))
        d.rectangle([x,y+HH-2,x+w,y+HH],fill=(20,38,92))
        sc(im,titolo,18,(x+12,y,x+w-12,y+HH),"center",(214,232,255))
    for i,(t,es) in enumerate(zip((t1,t2),esiti)):
        yy=y+HH+i*RH
        vin = t[2] is not None and t[3] is not None and t[2]>t[3]
        col = ORO if es=="1" else (VINC if es in ("2","3") else (FUORI if es=="4" else (VINC if vin else None)))
        if col: d.rounded_rectangle([x+3,yy+3,x+w-3,yy+RH-3],9,fill=col)
        largo=x+w-12
        if t[2] is not None:
            d.rounded_rectangle([x+w-54,yy+4,x+w-6,yy+RH-4],8,fill=GRIGIO)
            sc(im,t[2],26,(x+w-54,yy,x+w-6,yy+RH),"center"); largo=x+w-64
        if t[0]!="":
            d.rounded_rectangle([x+10,yy+8,x+48,yy+RH-8],7,fill=CHIP)
            sc(im,t[0],17,(x+10,yy+8,x+48,yy+RH-8),"center",(255,255,255))
        if es: sc(im,es+"\u00b0",20,(largo-34,yy,largo,yy+RH),"right",(120,96,20) if es=="1" else (90,105,140)); largo-=40
        sc(im,coppia(t[1]),25,(x+56,yy,largo,yy+RH),"left",
           (140,150,172) if es=="4" else SCURO)
    return h

def render(sfondo,pools,out):
    im=Image.open(sfondo).convert("RGB"); d=ImageDraw.Draw(im)
    Y0,PH,G=372,316,8
    LX,LW,RX,RW=44,500,600,436
    R2=146
    for i,p in enumerate(pools):
        y=Y0+i*(PH+G)
        d.rounded_rectangle([LX,y,RX+RW,y+32],9,fill=(14,70,68))
        sc(im,"POOL "+p["nome"],23,(LX+16,y,LX+150,y+32),"left",(190,244,238))
        sc(im,"le prime tre passano al tabellone principale",17,
           (LX+160,y,RX+RW-16,y+32),"right",(160,226,220))
        match(im,d,LX,y+42,LW,None,*p["sf1"])
        match(im,d,LX,y+42+R2,LW,None,*p["sf2"])
        match(im,d,RX,y+42,RW,"VINCENTI",*p["f12"],esiti=p.get("e12",(None,None)))
        match(im,d,RX,y+42+R2,RW,"PERDENTI",*p["f34"],esiti=p.get("e34",(None,None)))
    im.save(out,quality=95)

def S(seed="",team=None,a=None,b=None): return (seed,team,a,b)
