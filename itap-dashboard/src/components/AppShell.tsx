// src/components/AppShell.tsx
import type React from "react";
import TopNav from "@/components/TopNav";

type Props = {
    children: React.ReactNode;
};

export default function AppShell({ children }: Props) {
    return (
        <div className="min-h-screen bg-slate-50 text-slate-900">
            <TopNav />
            <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        </div>
    );
}
