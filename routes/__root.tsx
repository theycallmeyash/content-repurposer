import { Outlet, Link, createRootRoute, HeadContent, Scripts } from "@tanstack/react-router";
import { TopNav } from "../components/TopNav";
import { Footer } from "../components/Footer";

import appCss from "../styles.css?url";

function NotFoundComponent() {
  return (
    <div className="min-h-screen flex flex-col">
      <TopNav />
      <div className="flex-1 grid grid-cols-12 border-b border-ink">
        <div className="col-span-12 md:col-span-7 border-r border-ink/15 p-12 md:p-20 flex flex-col justify-center">
          <div className="font-mono-ed text-[10px] uppercase tracking-widest text-foreground/50 mb-6">
            Error · 404 · Page not located
          </div>
          <h1 className="font-display text-[20vw] md:text-[14vw] leading-[0.85] tracking-tighter">
            Off<span className="italic font-light text-indigo-electric">·</span>Press
          </h1>
          <p className="mt-6 font-display text-2xl md:text-3xl max-w-xl leading-tight">
            This page never made it to <span className="italic">print</span>.
            The grid does not contain the requested column.
          </p>
          <div className="mt-10 flex gap-3">
            <Link to="/" className="ed-btn">Return to index →</Link>
            <Link to="/dashboard" className="ed-btn ed-btn-ghost">View Dashboard</Link>
          </div>
        </div>
        <div className="col-span-12 md:col-span-5 p-8 bg-ink text-newsprint flex items-center justify-center">
          <pre className="font-mono-ed text-xs leading-[1.4]">{`> trace.error
  CODE      404
  TARGET    /unknown
  REASON    not_in_routetree
  SUGGEST   /, /dashboard
  TIME      ${new Date().toISOString()}
  ENGINE    press/engine v3.027`}</pre>
        </div>
      </div>
      <Footer />
    </div>
  );
}

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Press/Engine — Automate the aesthetic" },
      { name: "description", content: "An algorithmic editorial engine. Ingest your social profiles, train a private model, and publish on-brand content with mechanical precision." },
      { name: "author", content: "Press/Engine" },
      { property: "og:title", content: "Press/Engine — Automate the aesthetic" },
      { property: "og:description", content: "An algorithmic editorial engine. Ingest, synthesize, publish." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [{ rel: "stylesheet", href: appCss }],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
});

function RootShell({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  return <Outlet />;
}
