#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Exact 3:4 temple-poster compositor for deity-statue posters.

Takes a generated 896x1200 (or similar) poster image, then:
1. Detects the photo/cream split row (scan for first mostly-cream row).
2. Covers the forced service watermark (bottom-right) with sampled cream +
   noise, feathered only on interior edges.
3. Composites top region (cover-fit, no distortion) and bottom region
   (fit-width + reflect pad, or fit-height + blended side pad) onto an exact
   3:4 canvas with the split locked at the exact vertical midpoint.

Usage:
  python compose_poster.py --src IN.png --out OUT.jpg \
      [--canvas 1200x1600] [--patch x0,y0,x1,y1] [--bottom-crop N]

Requires Pillow. In WorkBuddy shells, python lives at
~/.workbuddy/binaries/python/versions/*/ (add to PATH first).
"""
import argparse
import random
import statistics
from pathlib import Path

from PIL import Image, ImageFilter


def is_cream(px):
    r, g, b = px[:3]
    return r > 200 and g > 195 and b > 175 and abs(r - g) < 30 and (r - b) < 45


def detect_split(img):
    """First row (from 1/3 height down) that is >=85% cream pixels."""
    w, h = img.size
    px = img.load()
    for y in range(h // 3, h - 100):
        cnt = sum(1 for x in range(0, w, 8) if is_cream(px[x, y]))
        if cnt / (w / 8) > 0.85:
            return y
    return h // 2


def default_patch(w, h):
    """Watermark sits at the bottom-right corner of generated images."""
    return (int(w * 0.855), int(h * 0.93), w, h)


def patch_watermark(img, rect):
    """Fill rect with median cream sampled above/left, plus mild noise.
    Feather ONLY edges that are interior to the image: an edge lying on the
    canvas boundary must stay fully opaque, otherwise watermark remnants
    under the transparent fringe show through."""
    x0, y0, x1, y1 = rect
    w, h = img.size
    y1 = min(y1, h)
    x1 = min(x1, w)
    px = img.load()
    samples = []
    for yy in range(max(0, y0 - 60), y0, 3):
        for xx in range(x0, max(x0 + 4, x1 - 4), 8):
            samples.append(px[xx, yy])
    for yy in range(y0, y1, 4):
        for xx in range(max(0, x0 - 220), max(0, x0 - 20), 8):
            samples.append(px[xx, yy])
    if not samples:
        return img
    cream = tuple(round(statistics.median(c[i] for c in samples)) for i in range(3))
    rnd = random.Random(42)
    patch = Image.new("RGB", (x1 - x0, y1 - y0), cream)
    pp = patch.load()
    for yy in range(patch.height):
        for xx in range(patch.width):
            n = rnd.randint(-3, 3)
            r, g, b = pp[xx, yy]
            pp[xx, yy] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    mask = Image.new("L", patch.size, 255)
    mp = mask.load()
    f = 10
    for yy in range(patch.height):
        for xx in range(patch.width):
            dl = xx if x0 > 0 else 999
            dt = yy if y0 > 0 else 999
            d = min(dl, dt)
            if d < f:
                mp[xx, yy] = int(255 * d / f)
    mask = mask.filter(ImageFilter.GaussianBlur(1.5))
    img.paste(patch, (x0, y0), mask)
    return img


def cover_fit(img, tw, th, v_anchor="top"):
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = round(sw * scale), round(sh * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    if nh > th:
        top = 0 if v_anchor == "top" else (nh - th) // 2
        img = img.crop((0, top, nw, top + th))
    if nw > tw:
        img = img.crop(((nw - tw) // 2, 0, (nw - tw) // 2 + tw, nh))
    return img


def reflect_pad(img, pad_top, pad_bottom):
    """Extend paper texture by mirroring edge rows (avoids flat-color seams)."""
    w, h = img.size
    canvas = Image.new("RGB", (w, h + pad_top + pad_bottom))
    canvas.paste(img, (0, pad_top))
    if pad_top > 0:
        canvas.paste(img.crop((0, 0, w, pad_top)).transpose(Image.FLIP_TOP_BOTTOM), (0, 0))
    if pad_bottom > 0:
        canvas.paste(img.crop((0, h - pad_bottom, w, h)).transpose(Image.FLIP_TOP_BOTTOM), (0, pad_top + h))
    return canvas


def side_pad_blend(img, target_w, overlap=30):
    """Extend to target_w by mirroring side strips, gradient-blended at seams."""
    w, h = img.size
    side_l = (target_w - w) // 2
    side_r = target_w - w - side_l
    ov = min(overlap, w // 4)
    canvas = Image.new("RGB", (target_w, h))
    strip_l = img.crop((0, 0, side_l + ov, h)).transpose(Image.FLIP_LEFT_RIGHT)
    strip_r = img.crop((w - side_r - ov, 0, w, h)).transpose(Image.FLIP_LEFT_RIGHT)
    canvas.paste(strip_l, (0, 0))
    canvas.paste(strip_r, (target_w - side_r - ov, 0))
    mask = Image.new("L", (w, h), 255)
    mp = mask.load()
    for xx in range(ov):
        a = int(255 * xx / ov)
        for yy in range(h):
            mp[xx, yy] = a
            mp[w - 1 - xx, yy] = a
    canvas.paste(img, (side_l, 0), mask)
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--canvas", default="1200x1600")
    ap.add_argument("--patch", default=None, help="x0,y0,x1,y1 watermark rect (source coords)")
    ap.add_argument("--bottom-crop", type=int, default=0,
                    help="trim N px from source bottom before processing (dark edge rows)")
    ap.add_argument("--quality", type=int, default=95)
    args = ap.parse_args()

    cw, ch = (int(v) for v in args.canvas.lower().split("x"))
    top_h = ch // 2  # split locked at exact vertical midpoint

    img = Image.open(args.src).convert("RGB")
    w, h = img.size
    split = detect_split(img)
    print(f"source={w}x{h} split={split} top_frac={split / h:.3f}")

    patch = (tuple(int(v) for v in args.patch.split(",")) if args.patch
             else default_patch(w, h))

    top_region = img.crop((0, 0, w, split))
    bottom_region = img.crop((0, split, w, h - args.bottom_crop))
    x0, y0, x1, y1 = patch
    bottom_region = patch_watermark(bottom_region, (x0, y0 - split, x1, y1 - split))

    top_fit = cover_fit(top_region, cw, top_h)
    bw, bh = bottom_region.size
    if bh <= 600:  # short cream zone: fit width, reflect-pad vertically
        bottom_fit = bottom_region.resize((cw, round(bh * cw / bw)), Image.LANCZOS)
        pad_total = top_h - bottom_fit.height
        if pad_total > 0:
            half = pad_total // 2
            bottom_fit = reflect_pad(bottom_fit, half, pad_total - half)
        elif pad_total < 0:
            bottom_fit = cover_fit(bottom_region, cw, top_h, v_anchor="bottom")
        print(f"bottom {bw}x{bh} -> fit-width, pad={pad_total}")
    else:  # tall cream zone: fit height, blended side pads
        nw = round(bw * top_h / bh)
        bottom_fit = side_pad_blend(bottom_region.resize((nw, top_h), Image.LANCZOS), cw)
        print(f"bottom {bw}x{bh} -> fit-height {nw}x{top_h}, blended side pads")

    final = Image.new("RGB", (cw, ch))
    final.paste(top_fit, (0, 0))
    final.paste(bottom_fit, (0, top_h))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    final.save(out, quality=args.quality)
    print(f"saved {out} {cw}x{ch} (split locked at y={top_h})")


if __name__ == "__main__":
    main()
