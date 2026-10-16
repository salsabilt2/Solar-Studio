import React, { Suspense } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const Landing = React.lazy(() =>
  import("./landing").then((module) => ({ default: module.Landing })),
);
const Studio = React.lazy(() =>
  import("./studio").then((module) => ({ default: module.Studio })),
);

function App() {
  const [path, setPath] = React.useState(window.location.pathname);
  React.useEffect(() => {
    const update = () => setPath(window.location.pathname);
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  return (
    <Suspense
      fallback={<div className="app-loading">Opening Solar Studio…</div>}
    >
      {path.startsWith("/app") ? <Studio path={path} /> : <Landing />}
    </Suspense>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
