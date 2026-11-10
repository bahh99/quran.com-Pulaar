import sys, os
from PIL import Image, ImageDraw
src, res_root, out_flavors = sys.argv[1], sys.argv[2], sys.argv[3:]
im = Image.open(src).convert("RGB")
W = im.size[0]
CREAM = (244, 230, 207)
S = 4  # supersample for smooth masks

def rrect_mask(size, box, radius):
    m = Image.new("L", (size[0]*S, size[1]*S), 0)
    ImageDraw.Draw(m).rounded_rectangle([v*S for v in box], radius=radius*S, fill=255)
    return m.resize(size, Image.LANCZOS)

# legacy square icon: full image with transparent rounded corners
sq = im.convert("RGBA")
sq.putalpha(rrect_mask(im.size, (24, 24, W-24, W-24), 285))

# emblem crop (ring + book) for adaptive/round icons
box = (95, 60, 1160, 1190)
emb = im.crop(box).convert("RGBA")
emb.putalpha(rrect_mask(emb.size, (0, 0, emb.size[0], emb.size[1]), 300))

def fit_on_canvas(img, canvas, frac, bg=None):
    c = Image.new("RGBA", (canvas, canvas), bg or (0, 0, 0, 0))
    k = frac * canvas / max(img.size)
    r = img.resize((round(img.size[0]*k), round(img.size[1]*k)), Image.LANCZOS)
    c.alpha_composite(r, ((canvas-r.size[0])//2, (canvas-r.size[1])//2))
    return c

legacy = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
fg = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}
for flavor in out_flavors:
    for d in legacy:
        out = os.path.join(res_root, flavor, "res", f"mipmap-{d}")
        if not os.path.isdir(out):
            continue
        n = legacy[d]
        sq.resize((n, n), Image.LANCZOS).save(os.path.join(out, "ic_launcher.png"))
        rnd = fit_on_canvas(emb, n*S, 0.98, CREAM+(255,))
        mask = Image.new("L", rnd.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, rnd.size[0]-1, rnd.size[1]-1), fill=255)
        rnd.putalpha(mask)
        rnd.resize((n, n), Image.LANCZOS).save(os.path.join(out, "ic_launcher_round.png"))
        f = fit_on_canvas(emb, fg[d]*S, 0.64).resize((fg[d], fg[d]), Image.LANCZOS)
        f.save(os.path.join(out, "ic_launcher_foreground.png"))
print("done")
