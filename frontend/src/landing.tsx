import { useEffect, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  CircleHelp,
  MapPin,
  Sun,
} from "lucide-react";
import {
  motion,
  useMotionTemplate,
  useMotionValue,
  useMotionValueEvent,
  useScroll,
  useSpring,
  useTransform,
  useReducedMotion,
} from "motion/react";
import { api, Estimate, navigate } from "./api";

function Brand({ light = false }: { light?: boolean }) {
  return (
    <a
      href="/"
      className={`brand ${light ? "brand-light" : ""}`}
      onClick={(event) => {
        event.preventDefault();
        navigate("/");
      }}
    >
      <span className="brand-mark" aria-hidden="true">
        <span />
      </span>
      <span>
        solar<span className="brand-thin">studio</span>
      </span>
    </a>
  );
}

function pointsForDay(curve: Estimate["day_curve"]) {
  if (!curve?.length) return "";
  const max = Math.max(...curve.map((item) => item.kwh), 0.001);
  return curve
    .map(
      (item, index) =>
        `${20 + (index * 560) / Math.max(curve.length - 1, 1)},${128 - (item.kwh / max) * 106}`,
    )
    .join(" ");
}

function RoofArt({
  progress,
}: {
  progress: ReturnType<typeof useScroll>["scrollYProgress"];
}) {
  const reduce = useReducedMotion();
  const sunX = useTransform(progress, [0, 0.48, 0.85, 1], [-10, 210, 555, 680]);
  const sunY = useTransform(progress, [0, 0.48, 0.85, 1], [120, -100, 40, 140]);
  const sunTransform = useMotionTemplate`translate3d(${sunX}px, ${sunY}px, 0)`;
  const lightOpacity = useTransform(
    progress,
    [0, 0.3, 0.55, 0.82, 1],
    [0.03, 0.1, 0.24, 0.15, 0.03],
  );
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const x = useSpring(mx, { stiffness: 100, damping: 22 });
  const y = useSpring(my, { stiffness: 100, damping: 22 });
  const roofTransform = useMotionTemplate`translate3d(${x}px, ${y}px, 0)`;

  function move(event: React.PointerEvent<SVGSVGElement>) {
    if (
      reduce ||
      !window.matchMedia("(hover: hover) and (pointer: fine)").matches
    )
      return;
    const box = event.currentTarget.getBoundingClientRect();
    mx.set(((event.clientX - box.left) / box.width - 0.5) * 12);
    my.set(((event.clientY - box.top) / box.height - 0.5) * 9);
  }

  return (
    <svg
      className="roof-svg"
      viewBox="0 0 900 620"
      role="img"
      aria-label="A drawn roof with solar panels, illuminated as the day progresses"
      onPointerMove={move}
      onPointerLeave={() => {
        mx.set(0);
        my.set(0);
      }}
    >
      <path
        d="M93 502 C255 515 617 515 806 492"
        stroke="#426058"
        strokeWidth="1"
        fill="none"
        opacity=".65"
      />
      <path
        d="M120 208 C220 112 372 82 506 109 C666 139 744 250 798 382"
        stroke="#d2ac57"
        strokeWidth="2"
        fill="none"
        strokeDasharray="5 10"
        opacity=".7"
      />
      <motion.g style={reduce ? undefined : { transform: sunTransform }}>
        <circle cx="118" cy="210" r="62" fill="#e4ba62" opacity=".1" />
        <circle cx="118" cy="210" r="40" fill="#ecc777" />
        <circle
          cx="118"
          cy="210"
          r="39"
          fill="none"
          stroke="#fff1ca"
          strokeWidth="2"
        />
      </motion.g>
      <motion.g style={reduce ? undefined : { transform: roofTransform }}>
        <path d="M132 355 L434 200 L784 350 L477 516 Z" fill="#54716b" />
        <path d="M132 355 L434 200 L477 516 L173 466 Z" fill="#33524d" />
        <path d="M434 200 L784 350 L477 516 Z" fill="#183a35" />
        <path
          d="M132 355 L434 200 L784 350"
          fill="none"
          stroke="#b9c8b7"
          strokeWidth="5"
          strokeLinejoin="round"
        />
        <path
          d="M173 466 L477 516 L784 350"
          fill="none"
          stroke="#102f2b"
          strokeWidth="5"
          strokeLinejoin="round"
        />
        <g transform="translate(0 -1)">
          {Array.from({ length: 3 }).map((_, row) =>
            Array.from({ length: 4 }).map((_, col) => {
              const baseX = 454 + col * 53 - row * 59;
              const baseY = 227 + col * 24 + row * 31;
              return (
                <g key={`${row}-${col}`}>
                  <path
                    d={`M${baseX} ${baseY} l46 21 l-50 26 l-46 -21 Z`}
                    fill="#082b32"
                    stroke="#8baba6"
                    strokeWidth="2"
                  />
                  <path
                    d={`M${baseX - 23} ${baseY + 12} l46 21 M${baseX + 22} ${baseY + 11} l-50 26`}
                    stroke="#55767b"
                    strokeWidth="1"
                    opacity=".65"
                  />
                </g>
              );
            }),
          )}
        </g>
        <motion.path
          d="M459 235 L691 342 L485 452 L256 345 Z"
          fill="#f2cc78"
          style={{ opacity: reduce ? 0.55 : lightOpacity }}
        />
        <path
          d="M477 516 L477 545 M277 481 L277 534 M702 398 L702 530"
          stroke="#31504a"
          strokeWidth="6"
        />
        <path
          d="M277 534 L477 545 L702 530"
          fill="none"
          stroke="#31504a"
          strokeWidth="5"
        />
      </motion.g>
      <circle cx="120" cy="505" r="3" fill="#e0b863" />
      <circle cx="802" cy="492" r="3" fill="#e0b863" />
    </svg>
  );
}

export function Landing() {
  const sceneRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: sceneRef,
    offset: ["start start", "end end"],
  });
  const chartProgress = useTransform(scrollYProgress, [0.19, 0.74], [0, 1]);
  const [stage, setStage] = useState(0);
  useMotionValueEvent(scrollYProgress, "change", (value) =>
    setStage(value < 0.34 ? 0 : value < 0.66 ? 1 : 2),
  );
  const reduce = useReducedMotion();
  const [storyDemo, setStoryDemo] = useState<Estimate | null>(null);
  const [storyError, setStoryError] = useState(false);
  const [demo, setDemo] = useState<Estimate | null>(null);
  const [demoError, setDemoError] = useState(false);
  const [demoLoading, setDemoLoading] = useState(true);
  const [place, setPlace] = useState("Chemnitz");
  const [orientation, setOrientation] = useState(180);
  const [tilt, setTilt] = useState(30);
  const [panelCount, setPanelCount] = useState(10);

  useEffect(() => {
    api<Estimate>("/demo")
      .then(setStoryDemo)
      .catch(() => setStoryError(true));
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setDemoLoading(true);
    setDemoError(false);
    const query = new URLSearchParams({
      place,
      orientation: String(orientation),
      tilt: String(tilt),
      panel_count: String(panelCount),
    });
    const timer = window.setTimeout(() => {
      api<Estimate>(`/demo?${query}`, { signal: controller.signal })
        .then(setDemo)
        .catch(() => {
          if (!controller.signal.aborted) setDemoError(true);
        })
        .finally(() => {
          if (!controller.signal.aborted) setDemoLoading(false);
        });
    }, 250);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [place, orientation, tilt, panelCount]);

  const points = demo ? pointsForDay(demo.day_curve) : "";
  const storyPoints = storyDemo ? pointsForDay(storyDemo.day_curve) : "";
  const storyTotal = storyDemo?.total_kwh;
  const captions = [
    <div>
      <p className="story-small">Morning</p>
      <h2>The day begins with light.</h2>
      <p>As the sun rises, your panels begin to work.</p>
    </div>,
    <div>
      <p className="story-small">Midday</p>
      <h2>Every hour tells a story.</h2>
      <p>Weather and panel direction change the result.</p>
    </div>,
    <div>
      <p className="story-small">Your turn</p>
      <h2>What could your place make?</h2>
      <p>Choose a location and explore a setup of your own.</p>
      <a className="text-action" href="#try-it">
        Try the planner <ArrowRight size={18} />
      </a>
    </div>,
  ];

  return (
    <div className="landing">
      <header className="landing-nav">
        <Brand light />
        <nav aria-label="Main navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#the-method">The method</a>
          <button className="nav-action" onClick={() => navigate("/app")}>
            Open studio <ArrowUpRight size={16} />
          </button>
        </nav>
      </header>

      <main>
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <p className="hero-kicker">
              <span className="kicker-dot" /> A clearer view of solar
            </p>
            <h1 id="hero-title">
              See what your roof <em>could do.</em>
            </h1>
            <p className="hero-description">
              Your place. Your panels. Real weather. An honest picture of the
              energy you could make.
            </p>
            <button className="button-primary" onClick={() => navigate("/app")}>
              Start planning <ArrowUpRight size={20} />
            </button>
            <p className="hero-note">
              No installation needed. Estimates based on historical weather.
            </p>
          </div>
          <div className="hero-roof">
            <RoofArt progress={scrollYProgress} />
            <span className="hero-caption">
              A roof is more than a surface.
              <br />
              It is a possibility.
            </span>
          </div>
          <a className="scroll-prompt" href="#story">
            Scroll to follow the sun <ArrowDown size={16} />
          </a>
        </section>

        <section
          id="story"
          className="story"
          ref={sceneRef}
          aria-label="One roof through one day"
        >
          <div className="story-sticky">
            <div className="story-topline">
              <span>One roof. One day.</span>
              <span>Chemnitz, Germany · Example</span>
            </div>
            <div className="story-visual">
              <RoofArt progress={scrollYProgress} />
            </div>
            <div className="story-words" aria-live="off">
              {reduce ? (
                captions
              ) : (
                <motion.div
                  key={stage}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.28 }}
                >
                  {captions[stage].props.children}
                </motion.div>
              )}
            </div>
            <div className="story-chart">
              <div className="chart-head">
                <span>Estimated electricity through the day</span>
                <strong>
                  {storyTotal !== undefined
                    ? `${storyTotal.toFixed(1)} kWh`
                    : storyError
                      ? "Data unavailable"
                      : "Loading weather…"}
                </strong>
              </div>
              <svg
                viewBox="0 0 600 150"
                role="img"
                aria-label="Estimated hourly electricity for the latest complete day"
              >
                <path d="M20 129 H580" stroke="#627b70" strokeWidth="1" />
                {storyPoints && (
                  <motion.polyline
                    points={storyPoints}
                    fill="none"
                    stroke="#e5b968"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{ pathLength: reduce ? 1 : chartProgress }}
                  />
                )}
              </svg>
              <div className="chart-foot">
                <span>06:00</span>
                <span>12:00</span>
                <span>18:00</span>
              </div>
            </div>
            <div className="story-progress">
              <span>01</span>
              <motion.div style={{ scaleY: scrollYProgress }} />
              <span>03</span>
            </div>
          </div>
        </section>

        <section
          id="try-it"
          className="try-section"
          aria-labelledby="try-title"
        >
          <div className="try-intro">
            <span className="small-index">Now, make it yours</span>
            <h2 id="try-title">Turn the roof. See the day change.</h2>
            <p>
              This is a real calculation for the latest complete day of weather,
              using ten JinkoSolar panels to start. Adjust the setup below.
            </p>
          </div>
          <div className="try-layout">
            <form
              className="try-controls"
              onSubmit={(event) => event.preventDefault()}
            >
              <label>
                Place
                <select
                  value={place}
                  onChange={(event) => setPlace(event.target.value)}
                >
                  <option value="Chemnitz">Chemnitz, Germany</option>
                  <option value="Berlin">Berlin, Germany</option>
                  <option value="Madrid">Madrid, Spain</option>
                </select>
              </label>
              <label>
                Direction
                <select
                  value={orientation}
                  onChange={(event) =>
                    setOrientation(Number(event.target.value))
                  }
                >
                  <option value={90}>East</option>
                  <option value={180}>South</option>
                  <option value={270}>West</option>
                </select>
              </label>
              <label>
                <span>
                  Slope <strong>{tilt}°</strong>
                </span>
                <input
                  type="range"
                  min="0"
                  max="60"
                  step="5"
                  value={tilt}
                  onChange={(event) => setTilt(Number(event.target.value))}
                />
              </label>
              <label>
                <span>
                  Panels <strong>{panelCount}</strong>
                </span>
                <input
                  type="range"
                  min="1"
                  max="20"
                  step="1"
                  value={panelCount}
                  onChange={(event) =>
                    setPanelCount(Number(event.target.value))
                  }
                />
              </label>
            </form>
            <div className="try-result" aria-live="polite">
              <span className="small-index">
                Estimated electricity · one day
              </span>
              <div className="try-number">
                {demoLoading
                  ? "—"
                  : demoError
                    ? "Unavailable"
                    : demo
                      ? demo.total_kwh.toFixed(1)
                      : "—"}
                {!demoLoading && !demoError && demo && <span>kWh</span>}
              </div>
              <p>
                {demoLoading
                  ? "Checking historical weather…"
                  : demoError
                    ? "Weather data is unavailable. Try another place."
                    : `${place} · ${panelCount} panels · ${orientation === 90 ? "east" : orientation === 270 ? "west" : "south"} facing`}
              </p>
              {points && !demoLoading && !demoError && (
                <svg
                  viewBox="0 0 600 150"
                  role="img"
                  aria-label="Estimated hourly electricity for this setup"
                >
                  <path d="M20 129 H580" stroke="#9bb1a2" strokeWidth="1" />
                  <polyline
                    points={points}
                    fill="none"
                    stroke="#e1b45f"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              )}
              <span className="try-source">
                {demo?.source} · {demo?.model} · 14% system loss
              </span>
              <button className="button-dark" onClick={() => navigate("/app")}>
                Save your own setup <ArrowUpRight size={18} />
              </button>
            </div>
          </div>
        </section>

        <section id="how-it-works" className="explain-section">
          <div className="section-label">
            <Sun size={19} /> A plan rooted in your place
          </div>
          <div className="explain-layout">
            <h2>From a place on the map to a picture you can use.</h2>
            <div>
              <p>
                Choose where the panels could sit. Add the products you want to
                compare. We use past sunlight and weather to estimate how much
                electricity each setup could make.
              </p>
              <button className="button-dark" onClick={() => navigate("/app")}>
                Explore your roof <ArrowUpRight size={19} />
              </button>
            </div>
          </div>
        </section>

        <section id="the-method" className="method-section">
          <div className="method-aside">
            <span className="small-index">The method</span>
            <span className="method-glyph" aria-hidden="true">
              <CircleHelp size={130} strokeWidth={0.55} />
            </span>
          </div>
          <div className="method-copy">
            <h2>
              Honest estimates.
              <br />
              Visible assumptions.
            </h2>
            <p>
              Every report shows the panel, location, dates, and weather behind
              its result. Change the direction or slope and see the difference.
              The result is an estimate, not a promise of real-world output.
            </p>
            <div className="method-details">
              <div>
                <strong>01</strong>
                <span>Place</span>
                <p>Pick a location anywhere on the map.</p>
              </div>
              <div>
                <strong>02</strong>
                <span>Arrange</span>
                <p>Choose panels, direction, and slope.</p>
              </div>
              <div>
                <strong>03</strong>
                <span>Understand</span>
                <p>Read a clear report with sources.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="closing-section">
          <div className="closing-inner">
            <MapPin size={31} strokeWidth={1.4} />
            <h2>Your next idea starts with a place.</h2>
            <button className="button-primary" onClick={() => navigate("/app")}>
              Open Solar Studio <ArrowUpRight size={20} />
            </button>
          </div>
        </section>
      </main>
      <footer className="landing-footer">
        <Brand />
        <span>Built to make solar easier to explore.</span>
        <span>Estimates, not measured output.</span>
      </footer>
    </div>
  );
}
