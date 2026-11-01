import { createHashHistory, createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";

/** Hash routing (`…/#/work`): one prebuilt bundle is served from any GitHub Pages project
 *  subpath or opened from a downloaded artifact folder. The path part of the URL never changes,
 *  so the prerendered shell (rendered for `/`) and the browser always agree, and direct entry
 *  and reload need no server fallback. See docs/adr/0001-frontend-foundation.md. */
export function getRouter() {
  return createRouter({
    routeTree,
    history: typeof window === "undefined" ? undefined : createHashHistory(),
    scrollRestoration: false,
    defaultPreload: false,
  });
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof getRouter>;
  }
}
