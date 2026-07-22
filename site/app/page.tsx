const githubUrl = "https://github.com/Amal-David/bookshelf";

const catalogFacts = [
  ["3,124", "quote records"],
  ["3,111", "normalized unique texts"],
  ["1,117", "catalogued books"],
  ["949", "quoted works"],
  ["585", "v2 primary-source-linked records pending human review"],
  ["2,539", "legacy records explicitly unverified"],
];

const hostTiers = [
  ["Codex Desktop + CLI", "Install the Bookshelf plugin, trust its Stop hook, and start a new chat."],
  ["Claude Code", "Install from the Bookshelf marketplace; the same bounded Stop hook runs after completed turns."],
  ["Pi + Hermes", "Native adapters are included for people who move between terminal agents."],
  ["Private by default", "No prompt, transcript, command, path, source code, or model output becomes quote context."],
];

export default function Home() {
  return (
    <main>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Bookshelf home">
          <span className="brand-mark" aria-hidden="true">B</span>
          <span>Bookshelf</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#proof">Proof</a>
          <a href="#catalog">Catalog</a>
          <a className="github-link" href={githubUrl}>GitHub ↗</a>
        </nav>
      </header>

      <div id="main-content" tabIndex={-1}>
        <section className="hero" id="top">
          <div className="hero-copy">
            <p className="eyebrow">Bookshelf for Codex + Claude Code</p>
            <h1>Let the terminal <em>widen your world</em> while it works.</h1>
            <p className="hero-lede">
              Instead of staring at another tool call, meet one compact book
              quote every few completed turns—enough to shift your perspective,
              never enough to break your flow.
            </p>
            <div className="hero-actions">
              <a className="button button-primary" href={githubUrl}>Add Bookshelf to your agent ↗</a>
              <a className="button button-secondary" href="#proof">Watch the terminal demo</a>
            </div>
            <div className="hero-proof" aria-label="Catalog summary">
              <span><strong>5</strong> completed turns</span>
              <span><strong>1</strong> widening thought</span>
              <span><strong>0</strong> model calls</span>
            </div>
          </div>
          <aside className="quote-card" aria-label="Example Bookshelf result">
            <p className="card-index">Turn 5 · quiet perspective</p>
            <blockquote>“Do nothing which is of no use.”</blockquote>
            <div className="quote-meta"><span>Miyamoto Musashi</span><span>The Book of Five Rings</span></div>
            <div className="book-spine" aria-hidden="true"><span /><span /><span /><span /></div>
          </aside>
        </section>

        <section className="demo-section" id="proof">
          <div className="section-heading">
            <p className="eyebrow">Actual Claude Code 2.1.217 session · Opus 4.8</p>
            <h2>A real edit, real tests, and a real Bookshelf Stop hook.</h2>
            <p>Captured from a disposable Rust project. Only idle waits are accelerated; the signed-in account is redacted.</p>
          </div>
          <pre className="proof-terminal"><code>$ bookshelf quote --intent refactor{"\n\n"}“Do nothing which is of no use.” — Miyamoto Musashi, The Book of Five Rings{"\n\n"}$ bookshelf feedback up|down</code></pre>
          <div className="video-frame">
            <div className="video-bar"><span>Bookshelf · Claude Code</span><span>actual quote at the Stop boundary</span></div>
            <video controls autoPlay muted loop playsInline preload="metadata" poster="/bookshelf-poster.png">
              <source src="/bookshelf-demo.mp4" type="video/mp4" />
              Your browser does not support the demo video.
            </video>
          </div>
          <details className="transcript"><summary>Accessible transcript</summary><p>In the disposable <code>rewrite-prod-in-rust-by-lunch</code> Rust project, an authenticated Claude Code 2.1.217 session with Opus 4.8 reads the real README and source, changes <code>rollback_window_minutes</code> from zero to 30 minutes for risky deploys, and runs the real Cargo test suite with both tests passing. Claude adds its own dry rollback joke. The actual Bookshelf Stop hook then displays “The darker the night, the brighter the stars.” — Fyodor Dostoevsky, <em>Crime and Punishment</em>. The capture is played at 1.25× with long waits capped; agent actions and output are otherwise untouched.</p></details>
        </section>

        <section className="library-section" id="catalog">
          <div className="library-intro">
            <p className="eyebrow">A library behind the moment</p>
            <h2>Browse when you want. Be surprised when you don&apos;t.</h2>
            <p>The terminal library is the deeper layer: search books, keep reading lists, and request a quote for a named intent. Ambient delivery is the front door.</p>
          </div>
          <div className="catalog-ledger" aria-label="Catalog counts">
            {catalogFacts.map(([count, label]) => <div className="genre-row" key={label}><strong>{count}</strong><span className="genre-dots" aria-hidden="true" /><span>{label}</span></div>)}
          </div>
        </section>

        <section className="install-section" id="hosts">
          <div className="section-heading">
            <p className="eyebrow">Where it meets you</p>
            <h2>Inside the coding session—not in another tab.</h2>
            <p>Bookshelf is packaged for Codex Desktop, Codex CLI, and Claude Code, with Pi and Hermes adapters for terminal-agent users.</p>
          </div>
          <div className="install-grid">
            {hostTiers.map(([title, detail]) => <article className="install-card" key={title}><h3>{title}</h3><p>{detail}</p></article>)}
          </div>
          <div className="ambient-note">
            <div><p className="eyebrow">Bounded by design</p><h3>Enough context to be useful. Nothing else.</h3></div>
            <code>bookshelf quote --intent refactor</code>
            <p>Bookshelf accepts an explicit local intent only—never commands, paths, prompts, transcripts, code, tool arguments, model output, or network calls. Ambient is optional, off by default, and fails closed.</p>
          </div>
        </section>

        <section className="final-cta">
          <p className="eyebrow">Make the waiting useful</p>
          <h2>Let every few turns leave you a little less narrow.</h2>
          <div className="hero-actions"><a className="button button-light" href={githubUrl}>Get Bookshelf on GitHub ↗</a><a className="text-link" href="#top">Back to the beginning ↑</a></div>
        </section>
      </div>
      <footer><span>Bookshelf · MIT-licensed software</span><span>Catalog provenance varies by record</span></footer>
    </main>
  );
}
