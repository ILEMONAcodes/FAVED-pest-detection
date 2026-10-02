import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";
import App from "./App.tsx";
import { BrowserRouter } from "react-router-dom";
import { DataContextProvider } from "./context/DataContext.tsx";

createRoot(document.getElementById("root")!).render(
	<StrictMode>
		<BrowserRouter>
			<DataContextProvider>
				<App />
			</DataContextProvider>
		</BrowserRouter>
	</StrictMode>,
);
