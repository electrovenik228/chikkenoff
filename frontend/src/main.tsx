import React from "react";
import ReactDOM from "react-dom/client";
import { CssBaseline, ThemeProvider, createTheme } from "@mui/material";

import App from "./App";
import "./styles/app.css";

const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#215c5c" },
    secondary: { main: "#b2472d" },
    success: { main: "#2e7d32" },
    warning: { main: "#c77700" },
    error: { main: "#b3261e" },
    background: { default: "#f5f6f7", paper: "#ffffff" }
  },
  typography: {
    fontFamily: ["Inter", "Segoe UI", "Arial", "sans-serif"].join(","),
    button: { textTransform: "none", fontWeight: 700 },
    h1: { letterSpacing: 0 },
    h2: { letterSpacing: 0 },
    h3: { letterSpacing: 0 },
    h4: { letterSpacing: 0 },
    h5: { letterSpacing: 0 },
    h6: { letterSpacing: 0 }
  },
  shape: { borderRadius: 8 },
  components: {
    MuiButton: {
      styleOverrides: { root: { minHeight: 42 } }
    },
    MuiCard: {
      styleOverrides: { root: { border: "1px solid #d8dde1", boxShadow: "none" } }
    }
  }
});

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
