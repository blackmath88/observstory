# Observatory creature: north-star prompts for Nano Banana

The goal is one north-star image of the observatory as a **being**: wholesome, alive, a creature
first glance, an observatory second glance. We'll then turn it into high-fidelity pixel art and
rebuild it in code so it can animate.

Workflow in Nano Banana (Gemini image):

1. Run the **base prompt** with each **species seed** (A–E). Generate 2–4 images per seed.
2. Keep the 1–3 images that pass the rubric below.
3. Use the **edit prompts** on those, with the same chat and the same image, to get a pose sheet,
   state sheet and pixel-art version.
4. Bring the favourites back. They become the north star for the code-drawn sprite.

Do not upload frames from existing films as references for anything that will ship. These prompts
describe qualities, not a film. Generated images are reference only.

---

## Base prompt: paste first, then add one species seed

```
A wholesome concept painting of a living observatory creature, an old gentle being whose body
IS a small astronomical observatory. It is clearly an animal first: soft rounded body, a calm
breathing posture, heavy sleepy eyelids, kind expressive eyes, little feet with toes, a tail.
It is clearly an observatory second: a patched verdigris-copper dome with riveted seams on its
back, an open dome slit, and a long cream-enamel brass-ringed telescope it uses like a curious
snout to peer at the sky. Its eyes are two round porthole windows glowing warm amber from
inside, with wooden shutters for eyelids. Moss and tiny ferns grow in its stone seams, small
birds nest on the dome, a brass lantern hangs from the telescope. Little tinkered instruments
are fixed to it like jewellery: a small armillary sphere, a weathervane, a ladder, a balcony
rail. It stands on a grassy hill at dusk, violet and rose clouds, first stars, distant snowy
mountains, wildflowers in the foreground. Mood: tender, curious, safe, a little funny.
Hand-painted 1990s Japanese animation background style, soft brushwork, warm lamp light in a
cool dusk palette (verdigris, slate blue, lavender, cream), no brown rust. Side three-quarter
view, the creature fills the middle of the frame, 16:9.
```

## Species seeds: add one line at the end

```
A · Tortoise: an ancient tortoise; the observatory dome is its shell, stubby wrinkled legs, a slow wise face peeking out under the dome rim.
```
```
B · Hermit crab: a big gentle hermit crab that has made an old observatory its shell; little eyestalks and soft jointed legs peek out from under the stone drum.
```
```
C · Owl: a round owl-shaped observatory; the dome is its head, the two porthole windows are big owl eyes, roof shingles like feathers, small talon feet gripping a rock.
```
```
D · Sleepy dog: a large shaggy moss-covered dog-like creature lying down with the observatory built on its back, chin on its paws, the telescope rising from its shoulders.
```
```
E · Snail: an enormous calm snail whose spiral shell is a winding observatory tower with windows along the spiral, the telescope at the top, leaving a faint glowing trail of starlight.
```

## Edit prompts: send in the same chat, on a chosen image

**Make it more alive** (use this if it still reads as a building):
```
Keep this exact creature and scene. Make it read more as a living being: give it a clearer face
and expression, a gentle smile in the shape of its stone base, a visible tail, softer rounded
silhouette, and a small sleepy breath of steam from its nose. Keep the observatory details.
```

**State sheet** (our three states):
```
Keep this exact creature design. Make a clean character state sheet on a plain pale background,
three poses side by side, same scale, labelled:
1 "Resting": lying down, eyes shuttered half closed, looks like a cozy building on the hill.
2 "Up": standing, eyes open and glowing, a small orange lantern lit on its telescope.
3 "Travelling": mid-step walking, the armillary sphere spinning, a few stars trailing behind it.
```

**Turnaround:**
```
Keep this exact creature design. Character turnaround on a plain background: front, three-quarter,
side and back views at the same scale and lighting, no scenery.
```

**Pixel-art translation:**
```
Redraw this exact creature as high-detail pixel art in the style of modern high-resolution
indie pixel-art games: visible square pixels at about 256×192 native resolution, clean 1-pixel
dark outline, about 48–64 colours, hand-placed shading with light from the upper left, dithering
only at soft edges, side view facing right, plain flat background. It must stay readable when
shown small. Same face, same eyes, same dome, same palette.
```

**Small-size test:**
```
Show this pixel-art creature three times on a dark UI background: at full size, at 96 pixels
wide and at 48 pixels wide. Simplify only what is needed so the face, eyes, dome and lantern stay
readable at the smallest size.
```

---

## Rubric: keep an image only if it passes all five

1. **Being in one second.** You see a creature before you see a building.
2. **Wholesome.** It feels kind, safe and slightly funny, not monstrous, industrial or sad.
3. **Observatory unmistakable.** The dome, slit and telescope read at a glance.
4. **Small-size silhouette.** At 48px wide, the face, dome and lantern still read.
5. **Animatable.** It has clear separate parts: eyelids, telescope, legs or tail, crown
   instrument, lantern.

Our state meanings stay the same: resting means nothing needs a conversation, up (lantern lit)
means an overlap or wait exists, and travelling means replay is playing.

---

## Round 2: after the first Nano Banana results (31 Oct)

Owner picks: the **owl** and the **tortoise**.

What works:
- The porthole window-eyes with wooden shutters as eyelids.
- The tortoise's gentle smile, weight and lying-down posture.
- Moss, birds, ladder, balcony and armillary.

What doesn't work:
- The telescope. On the tortoise it grows out of the forehead like a horn, and on the owl it
  is a loose prop.
- The owner wants a **modern enclosure mechanism**, like a large modern observatory dome: two
  curved shutter halves that part to reveal an open lattice (truss) telescope inside, with a
  louvred ring below.

Direction: tortoise body and face, with a modern dome on its back. The dome's two shells open like
a beetle's wing cases. That opening becomes the state mapping:
- **Resting:** shells closed, eyes shuttered.
- **Up:** shells part, the truss telescope rises, lantern lit.
- **Travelling:** walking, dome rotating.

The telescope is never on the head. The second reference image (a public observatory rendering)
is used for the mechanism only.

**Edit prompt.** Attach the tortoise image first and the dome reference second:
```
Keep the creature from the first image exactly: its kind smiling face, the two round porthole
window-eyes with wooden shutters as eyelids, the stone and verdigris shell, moss, ferns, ladder,
balcony, little birds, the dusk meadow and mountains. Change only the observatory. Remove the
telescope from its forehead completely. The observatory on its back becomes a modern telescope
enclosure like the one in the second image: a large rounded dome made of two curved shell halves
that part down the middle like a beetle's wing cases, revealing an open white lattice truss
telescope with a large round mirror at its base, tilted up toward the first stars. Below the dome
runs a ring of louvred vents, like gills. The telescope lives inside the dome on the creature's
back, never on its head. Dome panels in pale weathered silver-grey with verdigris patina along the
seams and rivets, a little moss on top. The brass lantern hangs from the edge of one open shutter.
Same hand-painted wholesome style and palette.
```

**State sheet.** Send this next in the same chat:
```
Keep this exact creature. Clean state sheet on a plain pale background, three poses side by side,
same scale, labelled:
1 "Resting": lying down, dome shells fully closed, window-eye shutters half closed, a calm sleepy smile.
2 "Up": standing, dome shells parted, the truss telescope raised, eyes open and glowing, orange lantern lit.
3 "Travelling": walking mid-step, dome rotated to one side with shells half open, a few stars trailing behind.
```

**Mechanism close-up**, for animation parts:
```
Keep this exact creature. Close-up cutaway of the dome mechanism only: the two curved shell halves,
their hinge rails and rollers, the louvred vent ring, the white truss telescope on its rotating
mount, the round mirror cell. Plain background, clear separate parts, same style.
```

**Owl variant**, the same fix on the owl image:
```
Keep this owl creature exactly, including its porthole eyes with shutters and its face. Replace
the loose telescope with a modern enclosure built into the top of its head-dome: two curved shell
halves that part like wing cases to reveal an open white lattice truss telescope inside, tilted
upward. A louvred vent ring below it. Same style and palette.
```
