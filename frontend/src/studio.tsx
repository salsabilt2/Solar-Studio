import {
  lazy,
  Suspense,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  ChevronDown,
  CirclePlus,
  Copy,
  Download,
  LayoutDashboard,
  LogOut,
  MapPin,
  Menu,
  Settings2,
  Sparkles,
  Sun,
  Trash2,
  X,
} from "lucide-react";
import {
  api,
  Estimate,
  json,
  navigate,
  Panel,
  Project,
  Report,
  Setup,
  User,
} from "./api";

function useData<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const reload = useCallback(() => {
    if (!path) return;
    api<T>(path)
      .then(setData)
      .catch((error) => setError(error.message));
  }, [path]);
  useEffect(reload, [reload]);
  return { data, error, reload, setData };
}

function Notice({ message, clear }: { message: string; clear?: () => void }) {
  return message ? (
    <div className="notice" role="alert">
      <span>{message}</span>
      {clear && (
        <button onClick={clear} aria-label="Dismiss">
          <X size={16} />
        </button>
      )}
    </div>
  ) : null;
}

function DeleteConfirmDialog({
  title,
  description,
  busy,
  onConfirm,
  onCancel,
}: {
  title: string;
  description: string;
  busy: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (dialog && !dialog.open) dialog.showModal();
    return () => {
      if (dialog?.open) dialog.close();
    };
  }, []);

  return (
    <dialog
      ref={dialogRef}
      className="setup-confirm"
      aria-labelledby="delete-confirm-title"
      aria-describedby="delete-confirm-description"
      aria-busy={busy}
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onCancel();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget && !busy) onCancel();
      }}
    >
      <div className="setup-confirm-content">
        <span className="setup-confirm-icon" aria-hidden="true">
          <Trash2 size={19} />
        </span>
        <p className="studio-overline">Please confirm</p>
        <h2 id="delete-confirm-title">{title}</h2>
        <p id="delete-confirm-description">{description}</p>
        <div className="setup-confirm-actions">
          <button
            className="button-outline"
            type="button"
            autoFocus
            disabled={busy}
            onClick={onCancel}
          >
            Cancel
          </button>
          <button
            className="button-danger"
            type="button"
            disabled={busy}
            onClick={onConfirm}
          >
            {busy ? "Removing…" : "Confirm"}
          </button>
        </div>
      </div>
    </dialog>
  );
}

function Auth({ onUser }: { onUser: (user: User) => void }) {
  const [register, setRegister] = useState(false);
  const [company, setCompany] = useState(false);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    invite_code: "",
    company_name: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = await api<User>(
        register ? "/auth/register" : "/auth/login",
        json(
          "POST",
          register
            ? { ...form, company_name: company ? form.company_name : null }
            : { email: form.email, password: form.password },
        ),
      );
      onUser(user);
      window.scrollTo(0, 0);
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-page">
      <div className="auth-left">
        <button className="back-link" onClick={() => navigate("/")}>
          <ArrowLeft size={17} /> Back to the story
        </button>
        <div>
          <div className="auth-orbit">
            <Sun size={86} strokeWidth={0.6} />
          </div>
          <p className="eyebrow">Solar Studio</p>
          <h1>
            Better decisions
            <br />
            begin with light.
          </h1>
          <p>
            Explore your place. Shape a setup. See what the past weather
            suggests.
          </p>
        </div>
        <span className="auth-bottom">
          A private place for your solar ideas.
        </span>
      </div>
      <div className="auth-right">
        <div className="auth-form-wrap">
          <span className="form-symbol">✳</span>
          <h2>{register ? "Create your space." : "Welcome back."}</h2>
          <p>
            {register
              ? "Start planning with a free account."
              : "Pick up where your ideas left off."}
          </p>
          <form onSubmit={submit}>
            {register && (
              <label>
                Your name
                <input
                  required
                  minLength={2}
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Your name"
                />
              </label>
            )}
            <label>
              Email address
              <input
                required
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                placeholder="you@example.com"
              />
            </label>
            <label>
              Password
              <input
                required
                type="password"
                minLength={register ? 10 : undefined}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder={
                  register ? "At least 10 characters" : "Your password"
                }
              />
            </label>
            {register && (
              <>
                <label>
                  Invitation code
                  <input
                    value={form.invite_code}
                    onChange={(e) =>
                      setForm({ ...form, invite_code: e.target.value })
                    }
                    placeholder="If required"
                  />
                </label>
                <label className="check-row">
                  <input
                    type="checkbox"
                    checked={company}
                    onChange={(e) => setCompany(e.target.checked)}
                  />{" "}
                  I manage panel products for a company
                </label>
                {company && (
                  <label>
                    Company name
                    <input
                      required
                      value={form.company_name}
                      onChange={(e) =>
                        setForm({ ...form, company_name: e.target.value })
                      }
                    />
                  </label>
                )}
              </>
            )}
            <Notice message={error} clear={() => setError("")} />
            <button className="button-dark full" disabled={busy}>
              {busy ? "Please wait…" : register ? "Create account" : "Sign in"}{" "}
              <ArrowRight size={17} />
            </button>
          </form>
          <button
            className="auth-switch"
            onClick={() => {
              setRegister(!register);
              setError("");
            }}
          >
            {register
              ? "Already have an account? Sign in"
              : "New here? Create an account"}
          </button>
        </div>
      </div>
    </div>
  );
}

function Nav({
  user,
  path,
  signOut,
}: {
  user: User;
  path: string;
  signOut: () => void;
}) {
  const [open, setOpen] = useState(false);
  const items = [
    { name: "Overview", path: "/app", icon: LayoutDashboard },
    { name: "Assistant", path: "/app/assistant", icon: Sparkles },
    ...(user.role === "company" || user.role === "admin"
      ? [{ name: "Products", path: "/app/products", icon: Sun }]
      : []),
    { name: "Profile", path: "/app/profile", icon: Settings2 },
    ...(user.role === "admin"
      ? [{ name: "Admin", path: "/app/admin", icon: BookOpen }]
      : []),
  ];
  return (
    <>
      <button
        className="mobile-menu"
        onClick={() => setOpen(!open)}
        aria-label="Toggle menu"
      >
        <Menu size={21} />
      </button>
      <aside className={`studio-sidebar ${open ? "open" : ""}`}>
        <button className="sidebar-logo" onClick={() => navigate("/")}>
          <span className="brand-mark">
            <span />
          </span>
          <span>
            solar<span className="brand-thin">studio</span>
          </span>
        </button>
        <div className="sidebar-divider" />
        <p className="sidebar-label">Workspace</p>
        <nav aria-label="Workspace">
          {items.map((item) => (
            <button
              key={item.path}
              className={path === item.path ? "active" : ""}
              onClick={() => {
                navigate(item.path);
                setOpen(false);
              }}
            >
              <item.icon size={19} strokeWidth={1.8} /> {item.name}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-help">
            <Sun size={22} />
            <strong>Make room for better ideas.</strong>
            <span>Everything begins with a place on the map.</span>
          </div>
          <button
            className="sidebar-user"
            onClick={() => navigate("/app/profile")}
          >
            <span className="avatar">{user.name.charAt(0).toUpperCase()}</span>
            <span>
              <strong>{user.name}</strong>
              <small>{user.tier} account</small>
            </span>
            <ChevronDown size={15} />
          </button>
          <button className="signout" onClick={signOut}>
            <LogOut size={17} /> Sign out
          </button>
        </div>
      </aside>
    </>
  );
}

function StudioHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="studio-header">
      <div>
        <p className="studio-overline">Your workspace</p>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {action}
    </header>
  );
}

function Dashboard({ user }: { user: User }) {
  const { data: projects, error, reload } = useData<Project[]>("/projects");
  const [filter, setFilter] = useState<"all" | "active" | "completed">("all");
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [message, setMessage] = useState("");
  const [projectToRemove, setProjectToRemove] = useState<Project | null>(null);
  const [deletingProject, setDeletingProject] = useState(false);
  async function create() {
    try {
      const project = await api<Project>("/projects", json("POST", { name }));
      setCreating(false);
      setName("");
      reload();
      navigate(`/app/projects/${project.id}`);
    } catch (error) {
      setMessage((error as Error).message);
    }
  }
  async function removeProject() {
    if (!projectToRemove) return;
    try {
      setDeletingProject(true);
      await api(`/projects/${projectToRemove.id}`, { method: "DELETE" });
      setProjectToRemove(null);
      setMessage("Project deleted.");
      reload();
    } catch (error) {
      setProjectToRemove(null);
      setMessage((error as Error).message);
    } finally {
      setDeletingProject(false);
    }
  }
  const shown = (projects || []).filter(
    (project) => filter === "all" || project.status === filter,
  );
  return (
    <>
      <StudioHeader
        title={`Hello, ${user.name.split(" ")[0]}.`}
        subtitle="A clearer picture of your solar ideas starts here."
        action={
          <button className="button-dark" onClick={() => setCreating(true)}>
            <CirclePlus size={18} /> New project
          </button>
        }
      />
      <div className="dashboard-band">
        <div>
          <span className="band-small">Your solar space</span>
          <h2>
            One good idea can
            <br />
            change everything.
          </h2>
          <p>Map a place, try a panel, and see what the weather tells you.</p>
          <button onClick={() => setCreating(true)}>
            Create a project <ArrowUpRight size={18} />
          </button>
        </div>
        <div className="band-art" aria-hidden="true">
          <Sun size={160} strokeWidth={0.5} />
        </div>
      </div>
      <div className="content-heading">
        <div>
          <p className="studio-overline">Your work</p>
          <h2>
            Projects <span>{projects?.length || 0}</span>
          </h2>
        </div>
        <div className="segmented" role="group" aria-label="Filter projects">
          {(["all", "active", "completed"] as const).map((item) => (
            <button
              key={item}
              className={filter === item ? "selected" : ""}
              onClick={() => setFilter(item)}
            >
              {item[0].toUpperCase() + item.slice(1)}
            </button>
          ))}
        </div>
      </div>
      <Notice message={message || error} clear={() => setMessage("")} />
      {projects && !shown.length ? (
        <div className="empty-state">
          <div className="empty-icon">
            <MapPin size={35} strokeWidth={1.2} />
          </div>
          <h3>
            {filter === "all"
              ? "Your first place is waiting."
              : `No ${filter} projects yet.`}
          </h3>
          <p>
            {filter === "all"
              ? "Create a project to put an idea on the map."
              : "Try another filter to see your work."}
          </p>
          {filter === "all" && (
            <button className="text-action" onClick={() => setCreating(true)}>
              Create project <ArrowRight size={18} />
            </button>
          )}
        </div>
      ) : (
        <div className="project-grid">
          {shown.map((project) => (
            <article className="project-card" key={project.id}>
              <button
                type="button"
                className="project-card-open"
                onClick={() => navigate(`/app/projects/${project.id}`)}
              >
                <span className="project-card-top">
                  <span className={`status-dot ${project.status}`} />
                  {project.status === "active" ? "In progress" : "Completed"}
                  <ArrowUpRight size={19} />
                </span>
                <span className="project-card-title">{project.name}</span>
                <span className="project-card-bottom">
                  {project.setups.length} panel{" "}
                  {project.setups.length === 1 ? "setup" : "setups"}{" "}
                  <span>
                    Explore <ArrowRight size={17} />
                  </span>
                </span>
              </button>
              <button
                type="button"
                className="project-card-delete"
                aria-label={`Delete ${project.name}`}
                title={`Delete ${project.name}`}
                onClick={() => setProjectToRemove(project)}
              >
                <Trash2 size={16} />
              </button>
            </article>
          ))}
        </div>
      )}
      {creating && (
        <div className="modal-backdrop" onMouseDown={() => setCreating(false)}>
          <form
            className="modal"
            onMouseDown={(e) => e.stopPropagation()}
            onSubmit={(e) => {
              e.preventDefault();
              create();
            }}
          >
            <button
              type="button"
              className="close"
              onClick={() => setCreating(false)}
              aria-label="Close"
            >
              <X size={20} />
            </button>
            <p className="studio-overline">New project</p>
            <h2>Give your idea a name.</h2>
            <p>You can add places and panel setups next.</p>
            <label>
              Project name
              <input
                autoFocus
                required
                minLength={2}
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="My rooftop"
              />
            </label>
            <button className="button-dark full">
              Create project <ArrowRight size={18} />
            </button>
          </form>
        </div>
      )}
      {projectToRemove && (
        <DeleteConfirmDialog
          title={`Delete “${projectToRemove.name}”?`}
          description="This project and its reports will be permanently removed. You can’t undo this."
          busy={deletingProject}
          onConfirm={removeProject}
          onCancel={() => setProjectToRemove(null)}
        />
      )}
    </>
  );
}

const SetupMap = lazy(() => import("./setup-map"));

function SetupForm({
  initial,
  panels,
  picked,
  onSave,
  onCancel,
}: {
  initial?: Setup;
  panels: Panel[];
  picked: [number, number] | null;
  onSave: (value: Record<string, unknown>) => void;
  onCancel: () => void;
}) {
  const [form, setForm] = useState({
    label: initial?.label || "South roof",
    panel_id: initial?.panel_id || panels[0]?.id || 0,
    latitude: initial?.latitude ?? 50.8278,
    longitude: initial?.longitude ?? 12.9214,
    location_name: initial?.location_name || "Chemnitz, Germany",
    orientation: initial?.orientation ?? 180,
    tilt: initial?.tilt ?? 30,
    panel_count: initial?.panel_count ?? 10,
    roof_area_m2: initial?.roof_area_m2 ?? 30,
    loss_pct: initial?.loss_pct ?? 14,
  });
  const [query, setQuery] = useState("");
  const [places, setPlaces] = useState<
    { name: string; latitude: number; longitude: number }[]
  >([]);
  const [searchError, setSearchError] = useState("");
  useEffect(() => {
    if (picked)
      setForm((previous) => ({
        ...previous,
        latitude: +picked[0].toFixed(5),
        longitude: +picked[1].toFixed(5),
        location_name: "Selected on map",
      }));
  }, [picked]);
  useEffect(() => {
    if (query.trim().length < 3) {
      setPlaces([]);
      return;
    }
    const timer = setTimeout(
      () =>
        api<typeof places>(`/locations?q=${encodeURIComponent(query)}`)
          .then(setPlaces)
          .catch((error) => setSearchError(error.message)),
      350,
    );
    return () => clearTimeout(timer);
  }, [query]);
  const panel = panels.find((item) => item.id === Number(form.panel_id));
  return (
    <form
      className="setup-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSave({ ...form, panel_id: Number(form.panel_id) });
      }}
    >
      <div className="form-title">
        <div>
          <p className="studio-overline">Panel setup</p>
          <h3>{initial ? "Edit your setup" : "Add a setup"}</h3>
        </div>
        <button type="button" onClick={onCancel} aria-label="Close">
          <X size={18} />
        </button>
      </div>
      <label>
        Give this setup a name
        <input
          required
          value={form.label}
          onChange={(e) => setForm({ ...form, label: e.target.value })}
        />
      </label>
      <label>
        Find a place
        <input
          value={query}
          placeholder="Search city or town"
          onChange={(e) => setQuery(e.target.value)}
        />
      </label>
      <Notice message={searchError} clear={() => setSearchError("")} />
      {places.length > 0 && (
        <div className="places-list">
          {places.map((place) => (
            <button
              type="button"
              key={`${place.latitude}-${place.longitude}`}
              onClick={() => {
                setForm({
                  ...form,
                  latitude: place.latitude,
                  longitude: place.longitude,
                  location_name: place.name,
                });
                setQuery(place.name);
                setPlaces([]);
              }}
            >
              {place.name}
            </button>
          ))}
        </div>
      )}
      <div className="coordinate-readout">
        <MapPin size={15} />
        {form.location_name} · {Number(form.latitude).toFixed(3)},{" "}
        {Number(form.longitude).toFixed(3)}
      </div>
      <label>
        Panel product
        <select
          value={form.panel_id}
          onChange={(e) =>
            setForm({ ...form, panel_id: Number(e.target.value) })
          }
        >
          {panels.map((item) => (
            <option value={item.id} key={item.id}>
              {item.maker} · {item.model}
            </option>
          ))}
        </select>
      </label>
      <div className="two-fields">
        <label>
          Panels
          <input
            type="number"
            min="1"
            max="10000"
            value={form.panel_count}
            onChange={(e) =>
              setForm({ ...form, panel_count: Number(e.target.value) })
            }
          />
        </label>
        <label>
          Slope °
          <input
            type="number"
            min="0"
            max="90"
            value={form.tilt}
            onChange={(e) => setForm({ ...form, tilt: Number(e.target.value) })}
          />
        </label>
      </div>
      <label>
        Usable roof space (m²)
        <input
          type="number"
          min="0.1"
          step="0.1"
          required
          value={form.roof_area_m2}
          onChange={(e) =>
            setForm({ ...form, roof_area_m2: Number(e.target.value) })
          }
        />
      </label>
      <p className="field-help">Leave room for roof edges and access paths.</p>
      {panel && panel.area_m2 * form.panel_count > form.roof_area_m2 && (
        <p className="field-help">
          These panels need more space than you entered.
        </p>
      )}
      <label>
        Direction
        <select
          value={form.orientation}
          onChange={(e) =>
            setForm({ ...form, orientation: Number(e.target.value) })
          }
        >
          <option value="0">North</option>
          <option value="90">East</option>
          <option value="180">South</option>
          <option value="270">West</option>
        </select>
      </label>
      <label>
        System loss %
        <input
          type="number"
          min="0"
          max="50"
          value={form.loss_pct}
          onChange={(e) =>
            setForm({ ...form, loss_pct: Number(e.target.value) })
          }
        />
      </label>
      <div className="computed-readout">
        <span>
          Rated power{" "}
          <strong>
            {(((panel?.rated_w || 0) * form.panel_count) / 1000).toFixed(2)} kW
          </strong>
        </span>
        <span>
          Panel area{" "}
          <strong>
            {((panel?.area_m2 || 0) * form.panel_count).toFixed(1)} m²
          </strong>
        </span>
      </div>
      <button
        className="button-dark full"
        disabled={
          !!panel && panel.area_m2 * form.panel_count > form.roof_area_m2
        }
      >
        {initial ? "Save changes" : "Add setup"} <ArrowRight size={18} />
      </button>
    </form>
  );
}

const EnergyChart = lazy(() => import("./energy-chart"));

function ProjectPage({ id }: { id: number }) {
  const {
    data: project,
    error: projectError,
    reload,
  } = useData<Project>(`/projects/${id}`);
  const { data: panels } = useData<Panel[]>("/panels");
  const [selected, setSelected] = useState<number | undefined>();
  const [editing, setEditing] = useState<"new" | number | null>(null);
  const [picked, setPicked] = useState<[number, number] | null>(null);
  const [estimate, setEstimate] = useState<Estimate | null>(null);
  const [dates, setDates] = useState({ start: "", end: "" });
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [setupToRemove, setSetupToRemove] = useState<Setup | null>(null);
  const [compare, setCompare] = useState("");
  const [comparison, setComparison] = useState<{
    current: Estimate;
    proposed: Estimate;
    difference_kwh: number;
    settings: Record<string, number>;
  } | null>(null);
  const setup =
    project?.setups.find((item) => item.id === selected) || project?.setups[0];
  useEffect(() => {
    if (setup) {
      setEstimate(null);
      const params = new URLSearchParams();
      if (dates.start) params.set("start_date", dates.start);
      if (dates.end) params.set("end_date", dates.end);
      api<Estimate>(
        `/setups/${setup.id}/estimate${params.size ? `?${params}` : ""}`,
      )
        .then(setEstimate)
        .catch((error) => setMessage(error.message));
    }
  }, [
    setup?.id,
    setup?.panel_count,
    setup?.tilt,
    setup?.orientation,
    setup?.loss_pct,
    dates.start,
    dates.end,
  ]);
  if (!project)
    return (
      <div className="loading-area">
        {projectError || "Loading your project…"}
      </div>
    );
  async function saveSetup(value: Record<string, unknown>) {
    try {
      setBusy(true);
      const path =
        editing === "new" ? `/projects/${id}/setups` : `/setups/${editing}`;
      const saved = await api<Setup>(
        path,
        json(editing === "new" ? "POST" : "PATCH", value),
      );
      setEditing(null);
      setSelected(saved.id);
      setPicked(null);
      reload();
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function act(path: string, method = "POST", body?: unknown) {
    try {
      setBusy(true);
      await api(path, body === undefined ? { method } : json(method, body));
      reload();
      setMessage("Done.");
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function removeSetup() {
    if (!setupToRemove) return;
    try {
      setBusy(true);
      await api(`/setups/${setupToRemove.id}`, { method: "DELETE" });
      setSelected((current) =>
        current === setupToRemove.id ? undefined : current,
      );
      setSetupToRemove(null);
      setMessage("Setup removed.");
      reload();
    } catch (error) {
      setMessage((error as Error).message);
      setSetupToRemove(null);
    } finally {
      setBusy(false);
    }
  }
  async function makeReport() {
    if (!setup) return;
    try {
      setBusy(true);
      const report = await api<Report>(
        `/setups/${setup.id}/reports`,
        json("POST", {
          start_date: dates.start || null,
          end_date: dates.end || null,
        }),
      );
      navigate(`/app/reports/${report.id}`);
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function copy() {
    try {
      const copy = await api<Project>(`/projects/${id}/copy`, {
        method: "POST",
      });
      navigate(`/app/projects/${copy.id}`);
    } catch (error) {
      setMessage((error as Error).message);
    }
  }
  async function compareSetup() {
    if (!setup) return;
    try {
      setBusy(true);
      setComparison(
        await api(
          `/ai/setups/${setup.id}/compare`,
          json("POST", { request: compare }),
        ),
      );
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <button className="back-link dark" onClick={() => navigate("/app")}>
        <ArrowLeft size={17} /> All projects
      </button>
      <StudioHeader
        title={project.name}
        subtitle={`${project.setups.length} panel ${project.setups.length === 1 ? "setup" : "setups"} · ${project.status === "active" ? "Ready to explore" : "Read-only report saved"}`}
        action={
          project.status === "completed" ? (
            <button className="button-outline" onClick={copy}>
              <Copy size={16} /> Copy project
            </button>
          ) : null
        }
      />
      <Notice message={message} clear={() => setMessage("")} />
      <div className="planner-layout">
        <div className="planner-main">
          <Suspense
            fallback={<div className="map-frame" aria-label="Loading map" />}
          >
            <SetupMap
              setups={project.setups}
              selected={setup?.id}
              onSelect={setSelected}
              onPick={
                project.status === "active"
                  ? (lat, lon) => {
                      setPicked([lat, lon]);
                      setEditing("new");
                    }
                  : undefined
              }
            />
          </Suspense>
          <div className="setup-list-heading">
            <h2>Panel setups</h2>
            <span>{project.setups.length}</span>
          </div>
          <div className="setup-list">
            {project.setups.map((item) => (
              <button
                className={`setup-row ${setup?.id === item.id ? "selected" : ""}`}
                key={item.id}
                onClick={() => setSelected(item.id)}
              >
                <span className="setup-row-icon">
                  <Sun size={20} />
                </span>
                <span>
                  <strong>{item.label}</strong>
                  <small>
                    {item.location_name} · {item.panel.maker}
                  </small>
                </span>
                <span className="setup-row-power">
                  {item.rated_kw.toFixed(2)} kW <ArrowRight size={16} />
                </span>
              </button>
            ))}
            {!project.setups.length && (
              <div className="empty-state compact">
                <h3>Place your first panels.</h3>
                <p>Use the map or add a setup to begin.</p>
              </div>
            )}
          </div>
        </div>
        <aside className="planner-side">
          {editing && panels ? (
            <SetupForm
              key={editing}
              initial={
                typeof editing === "number"
                  ? project.setups.find((item) => item.id === editing)
                  : undefined
              }
              panels={panels}
              picked={picked}
              onSave={saveSetup}
              onCancel={() => {
                setEditing(null);
                setPicked(null);
              }}
            />
          ) : setup ? (
            <>
              <div className="side-top">
                <div className="side-heading">
                  <p className="studio-overline">Selected setup</p>
                  {project.status === "active" && (
                    <div className="side-controls">
                      <button
                        type="button"
                        aria-label={`Edit ${setup.label}`}
                        title="Edit setup"
                        onClick={() => setEditing(setup.id)}
                      >
                        <Settings2 size={17} />
                      </button>
                      <button
                        type="button"
                        className="side-control-delete"
                        aria-label={`Remove ${setup.label}`}
                        title="Remove setup"
                        onClick={() => setSetupToRemove(setup)}
                      >
                        <Trash2 size={17} />
                      </button>
                    </div>
                  )}
                </div>
                <h2>{setup.label}</h2>
                <p>{setup.location_name}</p>
                <div className="side-stats">
                  <div>
                    <strong>{setup.rated_kw.toFixed(2)}</strong>
                    <span>kW rated</span>
                  </div>
                  <div>
                    <strong>{setup.area_m2.toFixed(1)}</strong>
                    <span>m² of panels</span>
                  </div>
                </div>
                <p className="side-panel-name">
                  {setup.panel.maker} · {setup.panel.model}
                </p>
              </div>
              <div className="date-fields">
                <label>
                  From
                  <input
                    type="date"
                    value={dates.start}
                    onChange={(e) =>
                      setDates({ ...dates, start: e.target.value })
                    }
                  />
                </label>
                <label>
                  To
                  <input
                    type="date"
                    value={dates.end}
                    onChange={(e) =>
                      setDates({ ...dates, end: e.target.value })
                    }
                  />
                </label>
              </div>
              <p className="field-help">
                Leave blank for the previous 30 complete days.
              </p>
              {estimate && (
                <div className="side-estimate">
                  <span>Estimated electricity</span>
                  <strong>
                    {estimate.total_kwh.toFixed(1)} <small>kWh</small>
                  </strong>
                  <p>
                    {estimate.daily.length} days · {estimate.source}
                  </p>
                </div>
              )}
              <button
                className="button-dark full"
                onClick={makeReport}
                disabled={busy}
              >
                Create & email report <ArrowRight size={17} />
              </button>
              <button
                className="side-link"
                onClick={() => act(`/setups/${setup.id}/weather/refresh`)}
              >
                Refresh weather now
              </button>
            </>
          ) : (
            <div className="empty-side">
              <Sun size={41} strokeWidth={1} />
              <h2>Your first setup starts here.</h2>
              <p>Add panels to see what this place could make.</p>
              <button className="button-dark" onClick={() => setEditing("new")}>
                Add setup <ArrowRight size={17} />
              </button>
            </div>
          )}
        </aside>
      </div>
      {estimate && (
        <section className="results-section">
          <div className="section-headline">
            <div>
              <p className="studio-overline">The numbers</p>
              <h2>Estimated daily electricity</h2>
            </div>
            <span>kWh · past weather</span>
          </div>
          <Suspense
            fallback={<div className="loading-area">Loading chart…</div>}
          >
            <EnergyChart data={estimate.daily} />
          </Suspense>
          <p className="chart-disclaimer">
            These are estimates, not measured output. Actual production depends
            on shade, installation, and equipment.
          </p>
        </section>
      )}
      {setup && (
        <section className="compare-section">
          <div>
            <p className="studio-overline">Try another angle</p>
            <h2>Ask a what-if question.</h2>
            <p>
              Try “What if these faced west?” or “What if I used 12 panels?”
            </p>
          </div>
          <div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                compareSetup();
              }}
            >
              <input
                value={compare}
                onChange={(e) => setCompare(e.target.value)}
                minLength={5}
                placeholder="What if these faced west?"
              />
              <button className="button-dark" disabled={busy}>
                Compare <ArrowRight size={17} />
              </button>
            </form>
            {comparison && (
              <div className="comparison-result">
                <span>
                  Current{" "}
                  <strong>{comparison.current.total_kwh.toFixed(1)} kWh</strong>
                </span>
                <span>
                  Proposed{" "}
                  <strong>
                    {comparison.proposed.total_kwh.toFixed(1)} kWh
                  </strong>
                </span>
                <p>
                  Difference: {comparison.difference_kwh > 0 ? "+" : ""}
                  {comparison.difference_kwh.toFixed(1)} kWh over the same
                  period.
                </p>
              </div>
            )}
          </div>
        </section>
      )}
      {setupToRemove && (
        <DeleteConfirmDialog
          title={`Remove “${setupToRemove.label}”?`}
          description="This setup will be removed from your project. You can’t undo this."
          busy={busy}
          onConfirm={removeSetup}
          onCancel={() => setSetupToRemove(null)}
        />
      )}
    </>
  );
}

function ReportPage({ id: numberId }: { id: number }) {
  const {
    data: report,
    error,
    reload,
  } = useData<Report>(`/reports/${numberId}`);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [message, setMessage] = useState("");
  useEffect(() => {
    if (report && ["pending", "running"].includes(report.status)) {
      const timer = setTimeout(reload, 2500);
      return () => clearTimeout(timer);
    }
  }, [report, reload]);
  if (!report)
    return <div className="loading-area">{error || "Loading report…"}</div>;
  async function explain() {
    try {
      const result = await api<{ answer: string }>(
        `/ai/reports/${numberId}/explain`,
        json("POST", { question }),
      );
      setAnswer(result.answer);
    } catch (error) {
      setMessage((error as Error).message);
    }
  }
  return (
    <>
      <button className="back-link dark" onClick={() => navigate("/app")}>
        <ArrowLeft size={17} /> Projects
      </button>
      <StudioHeader
        title="Your solar report."
        subtitle={`${report.start_date} to ${report.end_date} · ${report.status}`}
        action={
          report.daily && (
            <a
              className="button-outline"
              href={`/api/v1/reports/${report.id}/pdf`}
            >
              <Download size={17} /> Download PDF
            </a>
          )
        }
      />
      <Notice
        message={message || report.error || ""}
        clear={() => setMessage("")}
      />
      {report.status === "failed" && (
        <button
          className="button-dark"
          onClick={() =>
            api(`/reports/${numberId}/retry`, { method: "POST" })
              .then(reload)
              .catch((error) => setMessage(error.message))
          }
        >
          Retry email
        </button>
      )}
      {!report.daily ? (
        <div className="empty-state">
          <h3>Preparing your report.</h3>
          <p>We are checking the weather and calculating the estimate.</p>
        </div>
      ) : (
        <>
          <div className="report-summary">
            <p>Estimated electricity</p>
            <strong>
              {report.total_kwh?.toFixed(1)} <small>kWh</small>
            </strong>
            <span>
              {report.snapshot?.setup.label} ·{" "}
              {report.snapshot?.setup.location_name}
            </span>
          </div>
          <section className="results-section">
            <div className="section-headline">
              <h2>Day by day</h2>
              <span>kWh</span>
            </div>
            <Suspense
              fallback={<div className="loading-area">Loading chart…</div>}
            >
              <EnergyChart data={report.daily} />
            </Suspense>
            <p className="chart-disclaimer">
              {report.snapshot?.source} · {report.snapshot?.model}. Estimates,
              not measured output.
            </p>
          </section>
          <section className="compare-section">
            <div>
              <p className="studio-overline">Understand your result</p>
              <h2>Ask about this report.</h2>
              <p>AI can explain the saved numbers. It will not change them.</p>
            </div>
            <div>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  explain();
                }}
              >
                <input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  minLength={5}
                  placeholder="Why were some days lower?"
                />
                <button className="button-dark">
                  Explain <ArrowRight size={17} />
                </button>
              </form>
              {answer && <p className="assistant-answer">{answer}</p>}
            </div>
          </section>
        </>
      )}
    </>
  );
}

function Assistant() {
  const { data: documents, reload } = useData<
    {
      id: number;
      filename: string;
      public: boolean;
      can_delete: boolean;
      status: string;
      error: string | null;
    }[]
  >("/ai/documents");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<
    { number: number; document_id: number; filename: string; page: number }[]
  >([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [documentToDelete, setDocumentToDelete] = useState<{
    id: number;
    filename: string;
    public: boolean;
  } | null>(null);
  useEffect(() => {
    if (
      documents?.some(
        (item) => item.status === "pending" || item.status === "processing",
      )
    ) {
      const timer = setTimeout(reload, 2500);
      return () => clearTimeout(timer);
    }
  }, [documents, reload]);
  async function ask() {
    try {
      setBusy(true);
      const result = await api<{ answer: string; sources: typeof sources }>(
        "/ai/ask",
        json("POST", { question }),
      );
      setAnswer(result.answer);
      setSources(result.sources);
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function upload(file: File) {
    try {
      setBusy(true);
      const body = new FormData();
      body.append("file", file);
      await api("/ai/documents", { method: "POST", body });
      reload();
      setMessage("Document saved. Indexing is in progress.");
    } catch (error) {
      setMessage((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function removeDocument() {
    if (!documentToDelete) return;
    try {
      setBusy(true);
      await api(`/ai/documents/${documentToDelete.id}`, { method: "DELETE" });
      setDocumentToDelete(null);
      setAnswer("");
      setSources([]);
      setMessage("Document deleted.");
      reload();
    } catch (error) {
      setMessage((error as Error).message);
      setDocumentToDelete(null);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <StudioHeader
        title="Ask with evidence."
        subtitle="Explore panel documents and see where each answer comes from."
      />
      <div className="assistant-layout">
        <div className="assistant-main">
          <div className="assistant-welcome">
            <span className="assistant-star">
              <Sparkles size={34} />
            </span>
            <p className="studio-overline">The document assistant</p>
            <h2>Good questions deserve grounded answers.</h2>
            <p>
              Ask about materials, performance, and technical details. We show
              the pages behind each answer.
            </p>
          </div>
          <Notice message={message} clear={() => setMessage("")} />
          {answer && (
            <div className="assistant-response">
              <p>{answer}</p>
              {sources.length > 0 && (
                <div className="source-list">
                  {sources.map((source) => (
                    <a
                      key={source.number}
                      href={`/api/v1/ai/documents/${source.document_id}/pdf#page=${source.page}`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      [{source.number}] {source.filename}, page {source.page}
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}
          <form
            className="ask-box"
            onSubmit={(e) => {
              e.preventDefault();
              ask();
            }}
          >
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              minLength={5}
              maxLength={500}
              placeholder="Which panel handles heat better?"
              aria-label="Ask a document question"
            />
            <button
              disabled={busy || !question.trim()}
              aria-label="Ask question"
            >
              <ArrowUpRight size={21} />
            </button>
          </form>
        </div>
        <aside className="assistant-docs">
          <p className="studio-overline">Your library</p>
          <h3>Documents</h3>
          {documents?.length ? (
            documents.map((document) => (
              <div className="doc-row" key={document.id}>
                <BookOpen size={19} />
                <a
                  href={`/api/v1/ai/documents/${document.id}/pdf`}
                  target="_blank"
                  rel="noreferrer"
                >
                  {document.filename}
                  <small>
                    {document.status === "ready"
                      ? document.public
                        ? "Public product document"
                        : "Private document"
                      : document.status === "failed"
                        ? document.error || "Indexing failed"
                        : "Indexing…"}
                  </small>
                </a>
                {document.status === "failed" && (
                  <button
                    type="button"
                    onClick={() =>
                      api(`/ai/documents/${document.id}/retry`, {
                        method: "POST",
                      })
                        .then(reload)
                        .catch((error) => setMessage(error.message))
                    }
                  >
                    Retry
                  </button>
                )}
                {document.can_delete && (
                  <button
                    type="button"
                    className="doc-delete"
                    aria-label={`Delete ${document.filename}`}
                    title={`Delete ${document.filename}`}
                    disabled={busy}
                    onClick={() => setDocumentToDelete(document)}
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            ))
          ) : (
            <p className="muted">
              No documents yet. Add a panel PDF to start asking questions.
            </p>
          )}
          <label className="upload-button">
            Upload a PDF
            <input
              type="file"
              accept="application/pdf"
              hidden
              disabled={busy}
              onChange={(e) => {
                if (e.target.files?.[0]) upload(e.target.files[0]);
              }}
            />
          </label>
          <small>PDFs up to 10 MB. Private by default.</small>
        </aside>
      </div>
      {documentToDelete && (
        <DeleteConfirmDialog
          title={`Delete “${documentToDelete.filename}”?`}
          description={
            documentToDelete.public
              ? "This published PDF and its search content will be removed for everyone. You can’t undo this."
              : "This PDF and its search content will be permanently removed. You can’t undo this."
          }
          busy={busy}
          onConfirm={removeDocument}
          onCancel={() => setDocumentToDelete(null)}
        />
      )}
    </>
  );
}

function Products() {
  const { data: panels, reload } = useData<Panel[]>("/company/panels");
  const [form, setForm] = useState({
    maker: "",
    model: "",
    rated_w: 440,
    area_m2: 1.99,
    temp_coefficient: -0.0035,
    datasheet_url: "",
    published: false,
  });
  const [edit, setEdit] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  async function save() {
    try {
      await api(
        edit ? `/company/panels/${edit}` : "/company/panels",
        json(edit ? "PATCH" : "POST", form),
      );
      reload();
      setEdit(null);
      setForm({
        maker: "",
        model: "",
        rated_w: 440,
        area_m2: 1.99,
        temp_coefficient: -0.0035,
        datasheet_url: "",
        published: false,
      });
      setMessage("Product saved.");
    } catch (error) {
      setMessage((error as Error).message);
    }
  }
  async function upload(panel: Panel, file: File) {
    try {
      const body = new FormData();
      body.append("file", file);
      await api(`/ai/documents?panel_id=${panel.id}&public=true`, {
        method: "POST",
        body,
      });
      setMessage("Public product document saved. Indexing is in progress.");
    } catch (error) {
      setMessage((error as Error).message);
    }
  }
  return (
    <>
      <StudioHeader
        title="Product catalogue."
        subtitle="Publish accurate panel specifications for planners to use."
      />
      <Notice message={message} clear={() => setMessage("")} />
      <div className="product-layout">
        <div>
          <h2>Your panels</h2>
          {panels?.map((panel) => (
            <div className="product-row" key={panel.id}>
              <div>
                <strong>
                  {panel.maker} · {panel.model}
                </strong>
                <span>
                  {panel.rated_w} W · {panel.area_m2.toFixed(2)} m² ·{" "}
                  {panel.published ? "Published" : "Draft"}
                </span>
              </div>
              <div>
                <button
                  onClick={() => {
                    setEdit(panel.id);
                    setForm({
                      maker: panel.maker,
                      model: panel.model,
                      rated_w: panel.rated_w,
                      area_m2: panel.area_m2,
                      temp_coefficient: panel.temp_coefficient,
                      datasheet_url: panel.datasheet_url || "",
                      published: panel.published,
                    });
                  }}
                >
                  Edit
                </button>
                <label>
                  PDF
                  <input
                    hidden
                    type="file"
                    accept="application/pdf"
                    onChange={(e) => {
                      if (e.target.files?.[0]) upload(panel, e.target.files[0]);
                    }}
                  />
                </label>
                <button
                  onClick={() =>
                    api(`/company/panels/${panel.id}`, { method: "DELETE" })
                      .then(reload)
                      .catch((error) => setMessage(error.message))
                  }
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
        <form
          className="setup-form"
          onSubmit={(e) => {
            e.preventDefault();
            save();
          }}
        >
          <p className="studio-overline">
            {edit ? "Edit product" : "New product"}
          </p>
          <h3>Panel details</h3>
          <label>
            Manufacturer
            <input
              required
              value={form.maker}
              onChange={(e) => setForm({ ...form, maker: e.target.value })}
            />
          </label>
          <label>
            Model
            <input
              required
              value={form.model}
              onChange={(e) => setForm({ ...form, model: e.target.value })}
            />
          </label>
          <div className="two-fields">
            <label>
              Rated W
              <input
                required
                type="number"
                min="1"
                value={form.rated_w}
                onChange={(e) =>
                  setForm({ ...form, rated_w: Number(e.target.value) })
                }
              />
            </label>
            <label>
              Area m²
              <input
                required
                type="number"
                step="0.001"
                min="0.1"
                value={form.area_m2}
                onChange={(e) =>
                  setForm({ ...form, area_m2: Number(e.target.value) })
                }
              />
            </label>
          </div>
          <label>
            Temperature coefficient per °C
            <input
              type="number"
              step="0.0001"
              value={form.temp_coefficient}
              onChange={(e) =>
                setForm({ ...form, temp_coefficient: Number(e.target.value) })
              }
            />
          </label>
          <label>
            Datasheet link
            <input
              type="url"
              value={form.datasheet_url}
              onChange={(e) =>
                setForm({ ...form, datasheet_url: e.target.value })
              }
            />
          </label>
          <label className="check-row">
            <input
              type="checkbox"
              checked={form.published}
              onChange={(e) =>
                setForm({ ...form, published: e.target.checked })
              }
            />{" "}
            Publish to users
          </label>
          <button className="button-dark full">
            Save product <ArrowRight size={17} />
          </button>
        </form>
      </div>
    </>
  );
}

function Profile({
  user,
  onUser,
}: {
  user: User;
  onUser: (user: User) => void;
}) {
  const [name, setName] = useState(user.name);
  const [company, setCompany] = useState(user.company_name || "");
  const [message, setMessage] = useState("");
  async function save() {
    try {
      onUser(
        await api<User>("/me", json("PATCH", { name, company_name: company })),
      );
      setMessage("Profile updated.");
    } catch (error) {
      setMessage((error as Error).message);
    }
  }
  async function remove() {
    if (!confirm("Deactivate your account? You will be signed out.")) return;
    try {
      await api("/me", { method: "DELETE" });
      window.location.href = "/";
    } catch (error) {
      setMessage((error as Error).message);
    }
  }
  return (
    <>
      <StudioHeader
        title="Your profile."
        subtitle="Manage the person behind the plans."
      />
      <Notice message={message} clear={() => setMessage("")} />
      <div className="profile-card">
        <p className="studio-overline">Account</p>
        <h2>Personal details</h2>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <label>
          Email
          <input value={user.email} disabled />
        </label>
        {user.role === "company" && (
          <label>
            Company name
            <input
              value={company}
              onChange={(e) => setCompany(e.target.value)}
            />
          </label>
        )}
        <p className="field-help">
          {user.tier} account · {user.role} access
        </p>
        <button className="button-dark" onClick={save}>
          Save changes <ArrowRight size={17} />
        </button>
        <div className="profile-danger">
          <button onClick={remove}>
            <Trash2 size={16} /> Deactivate account
          </button>
        </div>
      </div>
    </>
  );
}

function Admin() {
  const { data: users, reload } = useData<User[]>("/admin/users");
  const { data: deleted } = useData<(User & { deleted_at: string })[]>(
    "/admin/deleted-users",
  );
  const [id, setId] = useState("");
  const [tier, setTier] = useState<"free" | "unlimited">("unlimited");
  const [role, setRole] = useState<"user" | "company" | "admin">("user");
  const [message, setMessage] = useState("");
  async function update() {
    try {
      await api(`/admin/users/${id}`, json("PATCH", { tier, role }));
      reload();
      setMessage("Account access updated.");
    } catch (error) {
      setMessage((error as Error).message);
    }
  }
  return (
    <>
      <StudioHeader
        title="Administration."
        subtitle="Manage account access and review deactivated users."
      />
      <Notice message={message} clear={() => setMessage("")} />
      <div className="profile-card">
        <h2>Active accounts</h2>
        {users?.map((item) => (
          <div className="admin-row" key={item.id}>
            <span>
              <strong>{item.name}</strong>
              <small>
                {item.email} · {item.tier} · {item.role}
              </small>
            </span>
            <button
              onClick={() => {
                setId(String(item.id));
                setTier(item.tier);
                setRole(item.role);
              }}
            >
              Select
            </button>
          </div>
        ))}
        <h2>Change account access</h2>
        <label>
          User ID
          <input
            type="number"
            min="1"
            value={id}
            onChange={(e) => setId(e.target.value)}
          />
        </label>
        <label>
          Tier
          <select
            value={tier}
            onChange={(e) => setTier(e.target.value as typeof tier)}
          >
            <option value="free">Free</option>
            <option value="unlimited">Unlimited</option>
          </select>
        </label>
        <label>
          Role
          <select
            value={role}
            onChange={(e) => setRole(e.target.value as typeof role)}
          >
            <option value="user">User</option>
            <option value="company">Company</option>
            <option value="admin">Admin</option>
          </select>
        </label>
        <button className="button-dark" onClick={update} disabled={!id}>
          Update access
        </button>
        <h2>Deactivated accounts</h2>
        {deleted?.length ? (
          deleted.map((item) => (
            <p key={item.id}>
              {item.email} · {item.deleted_at}
            </p>
          ))
        ) : (
          <p className="muted">No deactivated accounts.</p>
        )}
      </div>
    </>
  );
}

export function Studio({ path }: { path: string }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    api<User>("/me")
      .then(setUser)
      .catch(() => {})
      .finally(() => setReady(true));
  }, []);
  async function signOut() {
    await api("/auth/logout", { method: "POST" });
    setUser(null);
    navigate("/app");
  }
  if (!ready)
    return (
      <div className="app-loading">
        <Sun size={38} />
        <span>Opening Solar Studio…</span>
      </div>
    );
  if (!user) return <Auth onUser={setUser} />;
  let content: React.ReactNode;
  const projectMatch = path.match(/^\/app\/projects\/(\d+)$/);
  const reportMatch = path.match(/^\/app\/reports\/(\d+)$/);
  if (projectMatch)
    content = (
      <ProjectPage key={projectMatch[1]} id={Number(projectMatch[1])} />
    );
  else if (reportMatch)
    content = <ReportPage key={reportMatch[1]} id={Number(reportMatch[1])} />;
  else if (path === "/app/assistant") content = <Assistant />;
  else if (
    path === "/app/products" &&
    (user.role === "company" || user.role === "admin")
  )
    content = <Products />;
  else if (path === "/app/profile")
    content = <Profile user={user} onUser={setUser} />;
  else if (path === "/app/admin" && user.role === "admin") content = <Admin />;
  else content = <Dashboard user={user} />;
  return (
    <div className="studio-shell">
      <Nav user={user} path={path} signOut={signOut} />
      <main className="studio-content">{content}</main>
    </div>
  );
}
