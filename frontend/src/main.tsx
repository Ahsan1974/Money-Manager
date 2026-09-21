import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { registerSW } from "virtual:pwa-register";
import App from "./App";
import "./index.css";
import { applyTheme, useUI } from "@/stores/ui";

applyTheme(useUI.getState().theme);

try {
  registerSW({
    immediate: true,
    onRegisteredSW(_url, registration) {
      registration?.update().catch(() => undefined);
    },
  });
} catch {
  /* PWA registration is optional */
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
