// src/components/TopNav.tsx
import { NavLink } from "react-router-dom";

const links = [
    { to: "/overview", label: "Overview" },
    { to: "/alerts", label: "Alerts" },
    { to: "/aggregates", label: "Aggregates" },
    { to: "/metrics", label: "Metrics" },
    { to: "/health", label: "Health" },
];

export default function TopNav() {
    return (
        <header className="border-b bg-white">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
                <div className="text-lg font-semibold text-slate-900">
                    ITAP Dashboard
                </div>
                <nav className="flex gap-4 text-sm">
                    {links.map((link) => (
                        <NavLink
                            key={link.to}
                            to={link.to}
                            className={({ isActive }) =>
                                [
                                    "transition-colors",
                                    isActive ? "text-indigo-500" : "text-slate-400 hover:text-slate-700",
                                ].join(" ")
                            }
                        >
                            {link.label}
                        </NavLink>
                    ))}
                </nav>
            </div>
        </header>
    );
}
