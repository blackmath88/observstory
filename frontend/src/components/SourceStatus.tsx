import { AlertIcon, CheckIcon, DashIcon, XIcon } from "@primer/octicons-react";
import type { SourceResult } from "../data/types";

export type Tone = "ok" | "warn" | "bad" | "off";

/** One sentence per state, written for the person reading the page. */
export function statusSentence(result: SourceResult<unknown>, required: boolean): { tone: Tone; text: string } {
  switch (result.status) {
    case "ok":
      return {
        tone: "ok",
        text: result.contract === "full" ? "Loaded and valid" : "Loaded · identity fields checked (no schema file yet)",
      };
    case "missing":
      return required ? { tone: "bad", text: "Not published" } : { tone: "off", text: "Not published (optional)" };
    case "unsupported":
      return { tone: "bad", text: `Unsupported version: found ${result.found ?? "no schema id"}, this view reads ${result.expected}` };
    case "invalid":
      return { tone: "bad", text: "Does not match the schema" };
    case "unreadable":
      return { tone: "bad", text: "Not valid JSON" };
    case "unreachable":
      return { tone: "warn", text: `Could not be fetched (${result.detail})` };
  }
}

export function SourceStatus({ result, required }: { result: SourceResult<unknown>; required: boolean }) {
  const { tone, text } = statusSentence(result, required);
  const Icon = tone === "ok" ? CheckIcon : tone === "off" ? DashIcon : tone === "warn" ? AlertIcon : XIcon;
  return (
    <span className={`source-status ${tone}`}>
      <Icon size={16} />
      {text}
    </span>
  );
}
