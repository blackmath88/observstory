import { createFileRoute, getRouteApi } from "@tanstack/react-router";
import { WorkspaceView } from "../../components/workspace/WorkspaceView";
export const Route = createFileRoute("/_app/")({ component: Overview });
const layout = getRouteApi("/_app");
function Overview() {
  return <WorkspaceView bundle={layout.useLoaderData()} />;
}
