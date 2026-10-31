/* Direction D (round 3) — the walking observatory in the sidebar corner.
 *
 * Posture is the one piece of state the creature carries, and the page always
 * says it in words as well:
 *   lying    — nothing needs a conversation; it is just an observatory on a hill
 *   standing — an overlap / waiting signal exists; it gets up, lantern lit
 *   walking  — replay is playing; it travels through the repository's history
 * The telescope turns to the lane of the selection (or replay event).
 * Breathing, blinking, a peek and the greeting are decoration: they stop with
 * reduced motion and carry no information.
 */
(function (root) {
  "use strict";
  const P = root.ObsPixels, C = root.ObsCreature;

  const AW = 50, AH = 40, GROUND = 35;

  function scene(buf, scroll, drift) {
    C.duskSky(buf, 41, { horizon: GROUND, density: 0.02, drift, stops: [0, 0.45, 0.75, 0.9, 0.97] });
    // far hills, then the near ground that scrolls while walking
    const rnd = P.mulberry32(12);
    const far = []; for (let i = 0; i < 12; i++) far.push(rnd());
    for (let x = 0; x < buf.w; x++) {
      const k = ((x + drift * 0.5) / 9), i = Math.floor(k), f = k - i;
      const h = Math.round(GROUND - 3 - 3 * (far[((i % 11) + 11) % 11] * (1 - f) + far[(((i + 1) % 11) + 11) % 11] * f));
      for (let y = h; y < GROUND; y++) buf.set(x, y, "moss-0");
    }
    for (let x = 0; x < buf.w; x++) {
      buf.set(x, GROUND, "moss-2");
      for (let y = GROUND + 1; y < buf.h; y++) buf.set(x, y, y === GROUND + 1 ? "moss-1" : "moss-0");
      const wx = x + scroll;
      if (((wx * 13) % 17) === 0) buf.set(x, GROUND - 1, "moss-3");
      if (((wx * 7) % 23) === 0) { buf.set(x, GROUND + 2, "rock-1"); buf.set(x + 1, GROUND + 2, "rock-1"); }
    }
  }

  function poseFor(st, motion) {
    const standing = st.posture !== "lying";
    const p = {
      raise: st.raise, head: st.head, step: st.step, angle: st.angle,
      eyes: standing ? "open" : "closed", lantern: st.lantern, note: st.note, door: 1, settle: 0,
    };
    if (!motion) return p;
    const t = st.t;
    if (!standing && t % 46 < 6) p.settle = 1;
    if (!standing && t % 120 > 104) { p.eyes = "half"; }
    if (standing && t % 58 > 55) p.eyes = "closed";
    if (st.greet > 0) { p.eyes = "wide"; p.head = 4; p.door = 2; }
    return p;
  }

  function create() {
    const node = document.createElement("div");
    node.className = "critter";
    const cv = document.createElement("canvas");
    cv.className = "px";
    cv.setAttribute("aria-hidden", "true");
    const greet = document.createElement("button");
    greet.type = "button";
    greet.className = "critter-greet";
    greet.setAttribute("aria-label", "Greet the observatory (decorative)");
    node.append(cv, greet);

    const st = { t: 0, posture: "lying", raise: 0, head: 0, step: 0, angle: 60, target: 60, lantern: false, note: false, greet: 0, cool: 0, scroll: 0, motion: true };
    let timer = null;

    function scale() { return window.innerWidth < 768 ? 4 : 6; }

    function draw() {
      const b = new P.PixelBuffer(AW, AH);
      scene(b, st.scroll, Math.round(st.scroll / 6));
      C.turtle(b, 3, GROUND, poseFor(st, st.motion));
      P.toCanvas(cv, b, scale(), P.paletteFromCSS());
    }

    function settleTargets() {
      const up = st.posture !== "lying";
      return { raise: up ? 5 : 0, head: up ? 3 : 0 };
    }

    function tick() {
      if (!node.isConnected) return;
      st.t++;
      const tg = settleTargets();
      if (st.t % 2 === 0) {
        if (st.raise !== tg.raise) st.raise += Math.sign(tg.raise - st.raise);
        else if (st.head !== tg.head) st.head += Math.sign(tg.head - st.head);
      }
      if (st.angle !== st.target) st.angle += 5 * Math.sign(st.target - st.angle);
      if (st.posture === "walking" && st.raise === 5 && st.t % 3 === 0) { st.step = 1 - st.step; st.scroll++; }
      if (st.posture !== "walking") st.step = 0;
      if (st.greet > 0) st.greet--;
      if (st.cool > 0) st.cool--;
      draw();
    }

    greet.addEventListener("click", () => {
      if (st.cool > 0) return;
      st.greet = 10; st.cool = 40;
      if (!st.motion) { draw(); setTimeout(() => { st.greet = 0; draw(); }, 900); }
    });

    function update(s) {
      st.posture = s.posture; st.lantern = s.lantern; st.note = s.note;
      st.target = P.quantize(s.angle);
      const changedMotion = st.motion !== s.motion;
      st.motion = s.motion;
      if (!s.motion) {
        const tg = settleTargets();
        st.raise = tg.raise; st.head = tg.head; st.angle = st.target; st.step = 0;
      }
      if (changedMotion || !timer) {
        clearInterval(timer); timer = null;
        if (s.motion) timer = setInterval(tick, 100);
      }
      draw();
    }

    window.addEventListener("resize", draw);
    return { node, update };
  }

  /* Small static portrait for status cards: same sprite, posture only. */
  function portrait(canvas, posture, opts = {}) {
    const b = new P.PixelBuffer(46, 30);
    const up = posture !== "lying";
    C.turtle(b, 1, 28, { raise: up ? 5 : 0, head: up ? 3 : 0, eyes: up ? "open" : "closed", angle: opts.angle ?? 40, lantern: !!opts.lantern, step: posture === "walking" ? 1 : 0 });
    P.toCanvas(canvas, b, 2, P.paletteFromCSS());
  }

  root.ObsCritter = { create, portrait, AW, AH };
})(typeof window !== "undefined" ? window : globalThis);
