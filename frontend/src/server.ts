import { createStartHandler, defaultStreamHandler } from "@tanstack/react-start/server";

/** Asset URLs must stay relative: one prebuilt bundle is served from any GitHub Pages project
 *  subpath (or opened as a downloaded artifact). Start joins the router basepath and Vite's
 *  relative base into `/./assets/…`; turn that back into `./assets/…`. Runs once, at prerender. */
export function relativeAssetUrl(url: string): string {
  return url.replace(/^\/\.\//, "./");
}

const fetch = createStartHandler({
  handler: defaultStreamHandler,
  transformAssets: { transform: ({ url }) => relativeAssetUrl(url) },
});

export default { fetch };
