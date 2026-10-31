# Pixel rig for the painted north star

Reproducible steps, using ImageMagick and Node. Image numbers refer to `references/generated/`.

```bash
# 1. Resize the four Nano Banana frames to 320×179 (box filter).
#    06 = telescope in dome, 07 = up, 08 = resting, 09 = up on a flat background.
magick 07-state-up.jpg -filter Box -resize 320x179! f17.png   # likewise 06→f16, 08→f18, 09→f19
# 2. Build one shared 64-colour palette and remap every frame to it (no dither).
magick f16.png f17.png f18.png f19.png -append -dither None -colors 64 -unique-colors pal.png
magick f17.png -dither None -remap pal.png q17.png            # likewise q16, q18, q19
# 3. Export raw RGB and compute the creature masks.
magick f17.png -depth 8 rgb:f17.raw                           # likewise f18, f19
node mask.mjs                                                 # writes mUp.gray, mRest.gray
# 4. Cut the creature out of each state frame.
magick -size 320x179 -depth 8 gray:mUp.gray mUp.png
magick q17.png mUp.png -alpha off -compose CopyOpacity -composite cut-up.png   # likewise rest
```

`mask.mjs` takes the creature's outline from frame 09, which has a flat background:
- a flood fill from the border, then closing small holes;
- keeping the largest component;
- dropping sky-coloured pixels around the lantern halo and where the telescope sits in the
  resting frame.

The frame coordinates in `study-04.src.html` (`BOX`, `PIVOT`, `FOOT`) are in these 320×179 pixels.
