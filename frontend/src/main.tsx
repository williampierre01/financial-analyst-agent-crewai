import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import Access from "./components/Access";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Access />
  </StrictMode>,
);
