const githubUrl = "https://github.com/Amal-David/bookshelf";

const installs = [
  {
    host: "Codex",
    label: "Desktop + CLI",
    command:
      "codex plugin marketplace add Amal-David/bookshelf\ncodex plugin add bookshelf@bookshelf",
    behavior: "On-demand skill · optional Stop event banner",
  },
  {
    host: "Claude",
    label: "Claude Code",
    command:
      "/plugin marketplace add Amal-David/bookshelf\n/plugin install bookshelf@bookshelf",
    behavior: "On-demand skill · optional lifecycle event",
  },
  {
    host: "Hermes",
    label: "Hermes Agent",
    command: "hermes plugins install Amal-David/bookshelf --enable",
    behavior: "On-demand skill · optional response footer",
  },
  {
    host: "Pi",
    label: "Pi coding agent",
    command: "pi install git:github.com/Amal-David/bookshelf",
    behavior: "On-demand skill · optional native notification",
  },
];

const genres = [
  ["Fiction", "176"],
  ["Science", "151"],
  ["Motivation", "132"],
  ["Philosophy", "132"],
  ["History", "116"],
  ["Psychology", "97"],
  ["Startup", "96"],
  ["Romance", "83"],
];

export default function Home() {
  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Bookshelf home">
          <span className="brand-mark" aria-hidden="true">
            B
          </span>
          <span>Bookshelf</span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#demo">Demo</a>
          <a href="#install">Install</a>
          <a className="github-link" href={githubUrl}>
            GitHub ↗
          </a>
        </nav>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">A literary companion for coding agents</p>
          <h1>
            A great book can meet you in the middle of{" "}
            <em>the work.</em>
          </h1>
          <p className="hero-lede">
            Bookshelf brings 2,539 carefully tagged quotes from 983 books into
            Codex, Claude, Hermes, and Pi—on demand, or quietly after a task.
          </p>
          <div className="hero-actions">
            <a className="button button-primary" href="#install">
              Install the skill
            </a>
            <a className="button button-secondary" href={githubUrl}>
              View source ↗
            </a>
          </div>
          <div className="hero-proof" aria-label="Catalog summary">
            <span>
              <strong>983</strong> books
            </span>
            <span>
              <strong>2,539</strong> quotes
            </span>
            <span>
              <strong>4</strong> agent hosts
            </span>
          </div>
        </div>

        <aside className="quote-card" aria-label="Featured quote">
          <p className="card-index">B · 042</p>
          <blockquote>
            “What stands in the way becomes the way.”
          </blockquote>
          <div className="quote-meta">
            <span>Marcus Aurelius</span>
            <span>Meditations</span>
          </div>
          <div className="book-spine" aria-hidden="true">
            <span />
            <span />
            <span />
            <span />
          </div>
        </aside>
      </section>

      <section className="demo-section" id="demo">
        <div className="section-heading">
          <p className="eyebrow">See it in the work</p>
          <h2>A post-task note, not another interruption.</h2>
          <p>
            Finish the task. Keep your flow. When ambient mode is enabled and
            its cadence is due, Bookshelf finds a quote that fits the moment.
          </p>
        </div>
        <div className="video-frame">
          <div className="video-bar">
            <span>Bookshelf · agent session</span>
            <span>20 sec · sound on</span>
          </div>
          <video
            controls
            playsInline
            preload="metadata"
            poster="/bookshelf-poster.png"
          >
            <source src="/bookshelf-demo.mp4" type="video/mp4" />
            Your browser does not support the demo video.
          </video>
        </div>
      </section>

      <section className="library-section">
        <div className="library-intro">
          <p className="eyebrow">The library</p>
          <h2>Eight shelves. One useful thought at a time.</h2>
          <p>
            Every book includes editorial context and mood tags. Every quote
            carries work-aware tags for moments like debugging, reviewing,
            building, and shipping.
          </p>
        </div>
        <div className="genre-ledger" aria-label="Books by genre">
          {genres.map(([genre, count]) => (
            <div className="genre-row" key={genre}>
              <span>{genre}</span>
              <span className="genre-dots" aria-hidden="true" />
              <strong>{count}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="install-section" id="install">
        <div className="section-heading">
          <p className="eyebrow">One skill, four native surfaces</p>
          <h2>Install it where you already build.</h2>
          <p>
            The skill is available immediately. Ambient mode remains off until
            you enable it, and each host presents it through its own native
            extension surface.
          </p>
        </div>
        <div className="install-grid">
          {installs.map((install) => (
            <article className="install-card" key={install.host}>
              <div className="install-card-header">
                <h3>{install.host}</h3>
                <span>{install.label}</span>
              </div>
              <pre>
                <code>{install.command}</code>
              </pre>
              <p>{install.behavior}</p>
            </article>
          ))}
        </div>
        <div className="ambient-note">
          <div>
            <p className="eyebrow">Opt-in by design</p>
            <h3>Quotes can never break the agent turn.</h3>
          </div>
          <code>bookshelf ambient enable --cadence 5</code>
          <p>
            Every adapter isolates its own failures. Codex and Claude surface
            lifecycle events; Pi uses a native notification; Hermes can append
            a footer after the response.
          </p>
        </div>
      </section>

      <section className="final-cta">
        <p className="eyebrow">Keep the books close</p>
        <h2>Open the shelf when the work needs perspective.</h2>
        <div className="hero-actions">
          <a className="button button-light" href={githubUrl}>
            Get Bookshelf on GitHub ↗
          </a>
          <a className="text-link" href="#top">
            Back to the beginning ↑
          </a>
        </div>
      </section>

      <footer>
        <span>Bookshelf · MIT-licensed software</span>
        <span>Built for Codex · Claude · Hermes · Pi</span>
      </footer>
    </main>
  );
}
