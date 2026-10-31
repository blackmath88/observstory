# Walking Observatory: creature studies

## Study 04 (current): the painted north star, as pixel art

- Live page: https://claude.ai/artifact/QybWhMBVmFUW8E6Vxqyt83 (private to the owner until shared)
- Source: `study-04.src.html`. `build-04.py` inlines `frames/*.png` into `study-04.html`.
- Frames: the owner's Nano Banana images `references/generated/06–09`.
  - They are resized to 320×179 and quantised to one shared 64-colour palette.
  - The creature is cut out with `rig/mask.mjs`; `rig/README.md` has the steps.
- Animation:
  - the dome opens as a pixel reveal that spreads out from the slit;
  - the eyes blink, peek while resting, and glow;
  - it breathes while resting and bobs 1px while travelling;
  - the lantern flickers, the stars twinkle and the birds hop;
  - shooting stars appear during replay.
- Not possible yet without more frames: a real walk cycle and telescope aim. The page lists the
  Nano Banana prompts for those frames.

## Study 03 (current): brutalism as anatomy

- Live page: https://claude.ai/artifact/TWaKX6op5eq4oYz48pcHQJ (private to the owner until shared)
- Source: `study-03.html`. Concept: `CONCEPT-BRUTALIST-OBSERVATORY.md`.
- A salamander-tortoise drawn at 256×160 art pixels:
  - board-formed concrete shell plates, with verdigris and copper only on seams and rivets;
  - a cantilevered collar with ribbon windows;
  - two curved concrete shells that part like wing cases to reveal a pale lattice telescope;
  - two low rear fins;
  - a wide, smiling head with porthole eyes and wooden shutter eyelids.
- The states animate:
  - the shells open and close;
  - the creature rises and walks;
  - the ribbon windows light up (in a running wave during replay);
  - the eyes blink, and it breathes while resting.
- The page includes a state sheet, a silhouette test, and a preview of the brutalist product
  shell with the ribbon-window lane strip.

## Study 02 (current)

- Live page: https://claude.ai/artifact/9LrQckWMfSpLbtGGrdS4qS (private to the owner until shared)
- Source: `study-02.html`.
- Owner feedback on study 01: put the observatory in focus, so it is the whole creature rather
  than one part among others, and make it less brown.
- The body is a stone drum with ivy plus a large patched verdigris dome (riveted seams, slate and
  a few copper panels). The telescope is a cream-enamel snout with brass rings, and the two
  porthole windows are eyes.
- The tinkering is astronomical instruments, varied by seed:
  - an armillary sphere, anemometer or weathervane on the crown;
  - a turret dome, a sextant arm and a heliostat mirror;
  - a ladder, a stovepipe, a pennant, a balcony walkway and a dormer;
  - a star chart poking out of a hatch.
- The palette is cool: verdigris, slate and stone, with brass and copper only as accents.

## Study 01

This is a creature-only study for direction D, made after round 3. The owner asked for more
fidelity, in the spirit of a tinkered walking house: patchwork, stacked cottages, chimneys and
smoke, riveted iron, walking or hovering. It should be wholesome, with lots of handmade detail,
and still animatable pixel art.

- Live page: https://claude.ai/artifact/3S2JyQgRx25gdJcBWw1fmM (private to the owner until shared)
- Source: `study.html`. This is the artifact body; the publish step wraps it in the
  doctype/head/body skeleton. To open it locally, wrap it the same way or view the published page.
- Everything is drawn by code from a seed at 160×120 art pixels:
  - shaded ellipsoids, cylinders and segments;
  - a 1px exterior outline;
  - ordered dithering, only near tone boundaries;
  - live smoke, a walk cycle, propellers and a sail.

## Choices on the page

The page lets you switch:
- **Locomotion:** tortoise, stilt-walker or drifter.
- **State:** resting, up or travelling.
- **Sky:** dusk or day.
- **Telescope aim.**
- **Detail seed:** which houses, chimneys, water tower, crane and laundry get bolted on.

It also shows the creature at actual size: the 300px sidebar corner at 2× and the status-card
portrait at 1×.

## State meaning (unchanged from round 3)

| State | Means |
|---|---|
| Resting | Nothing needs a conversation. It lies down or lands, and one stove smoulders. |
| Up | An overlap or a waiting dependency exists. It stands, eye open, lantern lit. |
| Travelling | Replay is playing. It walks or drifts through history. |

## References and licensing

The owner's reference frames are from a well-known animated film. They inform *qualities* only.
The creature, palette and parts here are original, and the image-generation prompts on the page
deliberately avoid naming any film or studio. Generated images are reference material, not
shipping assets.
