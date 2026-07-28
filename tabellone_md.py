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
    return "BYE" if u.startswith("BYE") else " / ".join(cognome(x) for x in t.split(" - "))

def box(im,d,x,y,w,h,t1,t2,oro=False):
    ov=Image.new("RGBA",im.size,(0,0,0,0))
    ImageDraw.Draw(ov).rounded_rectangle([x+2,y+5,x+w+2,y+h+5],12,fill=(12,22,52,90))
    im.paste(Image.alpha_composite(im.convert("RGBA"),ov).convert("RGB"))
    d=ImageDraw.Draw(im)
    d.rounded_rectangle([x,y,x+w,y+h],12,fill=(253,253,255),
                        outline=ORO if oro else (168,184,212),width=4 if oro else 1)
    rh=h//2
    for i,t in enumerate((t1,t2)):
        yy=y+i*rh; bye=bool(t[1]) and t[1].upper().startswith("BYE")
        vin = t[2] is not None and t[3] is not None and t[2]>t[3]
        if vin: d.rounded_rectangle([x+3,yy+3,x+w-3,yy+rh-3],9,fill=ORO if oro else VINC)
        largo=x+w-12
        if t[2] is not None:
            d.rounded_rectangle([x+w-52,yy+5,x+w-6,yy+rh-5],8,fill=GRIGIO)
            sc(im,t[2],26,(x+w-52,yy,x+w-6,yy+rh),"center"); largo=x+w-62
        if t[0]!="":
            d.rounded_rectangle([x+9,yy+8,x+45,yy+rh-8],7,fill=CHIP)
            sc(im,t[0],17,(x+9,yy+8,x+45,yy+rh-8),"center",(255,255,255))
        sc(im,coppia(t[1]),25,(x+53,yy,largo,yy+rh),"left",
           (150,160,182) if (bye or not t[1]) else SCURO)
    d.line([x+10,y+rh,x+w-10,y+rh],fill=(198,208,226),width=1)

def albero(sfondo,sx,dx,tsx,tdx,out,oro_dx=False,etichette=None):
    im=Image.open(sfondo).convert("RGB"); d=ImageDraw.Draw(im)
    Y0,YE=372,1686; LX,LW,RX,RW=44,506,606,430
    for tit,a,b in ((tsx,LX,LX+LW),(tdx,RX,RX+RW)):
        d.rounded_rectangle([a,Y0,b,Y0+32],9,fill=(20,38,92))
        sc(im,tit,21,(a,Y0,b,Y0+32),"center",(214,232,255))
    top=Y0+42; H=YE-top
    n=len(sx); slot=H/n; bh=min(112,int(slot*0.72))
    ys=[]
    for i,m in enumerate(sx):
        y=int(top+i*slot+(slot-bh)/2); ys.append(y+bh//2)
        box(im,d,LX,y,LW,bh,*m)
    if etichette:
        HH=30; blocco=HH+bh; tot=2*blocco+46
        y0=(ys[0]+ys[-1])//2-tot//2
        for j,m in enumerate(dx):
            yb=y0+j*(blocco+46)
            d.rounded_rectangle([RX,yb,RX+RW,yb+HH],9,fill=(20,38,92))
            sc(im,etichette[j],20,(RX,yb,RX+RW,yb+HH),"center",(214,232,255))
            box(im,d,RX,yb+HH+6,RW,bh,*m,oro=oro_dx and j==0)
        im.save(out,quality=95); return
    for j,m in enumerate(dx):
        if len(sx)==len(dx):
            cy=ys[j]
        else:
            cy=(ys[2*j]+ys[2*j+1])//2
            for k in (2*j,2*j+1):
                d.line([LX+LW+4,ys[k],LX+LW+26,ys[k]],fill=(255,255,255),width=5)
                d.line([LX+LW+4,ys[k],LX+LW+26,ys[k]],fill=LINEA,width=3)
            d.line([LX+LW+26,ys[2*j],LX+LW+26,ys[2*j+1]],fill=(255,255,255),width=5)
            d.line([LX+LW+26,ys[2*j],LX+LW+26,ys[2*j+1]],fill=LINEA,width=3)
            d.line([LX+LW+26,cy,RX-4,cy],fill=(255,255,255),width=5)
            d.line([LX+LW+26,cy,RX-4,cy],fill=LINEA,width=3)
        box(im,d,RX,cy-bh//2,RW,bh,*m,oro=oro_dx)
    im.save(out,quality=95)

def S(seed="",team=None,a=None,b=None): return (seed,team,a,b)
