import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App"
import "./index.css"

const initialTheme = globalThis.localStorage.getItem("onboarding-theme")
if (initialTheme === "dark") {
  document.documentElement.classList.add("dark")
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
