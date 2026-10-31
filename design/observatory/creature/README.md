# Walking Observatory: creature study 01

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
