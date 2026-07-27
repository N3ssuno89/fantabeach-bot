from PIL import Image, ImageDraw, ImageFont
SHEAR = 0.22


def text_layer(txt, font, stroke=4, fill=(255,255,255), sfill=(20,20,45), shear=None):
    d0 = ImageDraw.Draw(Image.new("RGBA",(1,1)))
    l,t,r,b = d0.textbbox((0,0), txt, font=font, stroke_width=stroke)
    w,h = r-l+40, b-t+40
    lay = Image.new("RGBA",(w,h),(0,0,0,0))
    ImageDraw.Draw(lay).text((20-l,20-t), txt, font=font, fill=fill+(255,),
                             stroke_width=stroke, stroke_fill=sfill+(255,))
    sh = SHEAR if shear is None else shear
    ext = int(h*sh)
    lay2 = Image.new("RGBA",(w+ext,h),(0,0,0,0))
    lay2.paste(lay,(0,0),lay)
    lay2 = lay2.transform((w+ext,h), Image.AFFINE, (1,sh,-sh*h,0,1,0),
                          resample=Image.BICUBIC)
    return lay2.crop(lay2.getbbox())

def fit_layer(txt, fontpath, box, hi, lo, stroke=4):
    x0,y0,x1,y1 = box; bw,bh = x1-x0, y1-y0
    best=None
    for s in range(hi, lo-1, -1):
        lay = text_layer(txt, ImageFont.truetype(fontpath,s), stroke)
        if lay.width<=bw and lay.height<=bh:
            best=(lay,s); break
    if best is None:
        best=(text_layer(txt, ImageFont.truetype(fontpath,lo), stroke), lo)
    return best

def paste_center(im, lay, box):
    x0,y0,x1,y1 = box
    im.paste(lay,(int(x0+(x1-x0-lay.width)/2), int(y0+(y1-y0-lay.height)/2)), lay)
