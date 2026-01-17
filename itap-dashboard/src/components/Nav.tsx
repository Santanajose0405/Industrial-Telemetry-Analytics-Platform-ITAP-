// src/components/Nav.tsx
import { NavLink } from "react-router-dom";

type NavItem = {
    to: string;
    label: string;
};

const defaultItems: NavItem[] = [
    { to: "/overview", label: "Overview" },
    { to: "/alerts", label: "Alerts" },
    { to: "/aggregates", label: "Aggregates" },
    { to: "/metrics", label: "Metrics" },
    { to: "/health", label: "Health" },
];

type Props = {
    items?: NavItem[];
};

export default function Nav({ items = defaultItems }: Props) {
    return (
        <nav className="flex gap-4 text-sm">
            {items.map((item) => (
                <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                        [
                            "transition-colors",
                            isActive ? "text-indigo-500" : "text-slate-400 hover:text-slate-700",
                        ].join(" ")
                    }
                >
                    {item.label}
                </NavLink>
            ))}
        </nav>
    );
}
