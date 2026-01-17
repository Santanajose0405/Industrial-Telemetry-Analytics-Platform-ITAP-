// Remove the following line because '@tailwindcss/vite' does not exist
// import tailwindcss from "@tailwindcss/vite"
import path from "path"
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// Tailwind CSS is typically configured via postcss.config.js or tailwind.config.js, not as a Vite plugin
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        proxy: {
            "/api": {
                target: "http://127.0.0.1:8000",
                changeOrigin: true,
            },
        },
    },
})