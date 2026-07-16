"use client";

import { useState } from "react";

export function CodePanel({
  title,
  content,
  language = "text",
}: {
  title: string;
  content: string;
  language?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <section className="code-panel">
      <div className="code-header">
        <div>
          <span className="code-title">{title}</span>
          <span className="code-language">{language}</span>
        </div>
        <button className="code-copy" type="button" onClick={copy}>
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre>
        <code>{content || "No content is available yet."}</code>
      </pre>
    </section>
  );
}
