import { NavLink, Route, Routes } from "react-router-dom";
import HealthPage from "./pages/HealthPage";
import OverviewPage from "./pages/OverviewPage";
import AlertsPage from "./pages/AlertsPage";
import AggregatesPage from "./pages/AggregatesPage";
import MetricsPage from "./pages/MetricsPage";

export default function App() {
    return (
        <div className="min-h-screen bg-background text-foreground">
            <header className="border-b">
                <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-4">
                    <div className="text-lg font-semibold">ITAP Dashboard</div>
                    <nav className="flex gap-4 text-sm">
                        <NavLink to="/" className={({ isActive }) => isActive ? "font-semibold" : ""}>Overview</NavLink>
                        <NavLink to="/alerts" className={({ isActive }) => isActive ? "font-semibold" : ""}>Alerts</NavLink>
                        <NavLink to="/aggregates" className={({ isActive }) => isActive ? "font-semibold" : ""}>Aggregates</NavLink>
                        <NavLink to="/metrics" className={({ isActive }) => isActive ? "font-semibold" : ""}>Metrics</NavLink>
                        <NavLink to="/health" className={({ isActive }) => isActive ? "font-semibold" : ""}>Health</NavLink>
                    </nav>
                </div>
            </header>

            <main className="mx-auto max-w-6xl px-6 py-6">
                <Routes>
                    <Route path="/" element={<OverviewPage />} />
                    <Route path="/alerts" element={<AlertsPage />} />
                    <Route path="/aggregates" element={<AggregatesPage />} />
                    <Route path="/metrics" element={<MetricsPage />} />
                    <Route path="/health" element={<HealthPage />} />
                </Routes>
            </main>
        </div>
    );
}
