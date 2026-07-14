import { BrowserRouter, Route, Routes } from "react-router-dom";
import HomePage from "./pages/HomePage";
import SelectLinePage from "./pages/SelectLinePage";
import BoardPage from "./pages/BoardPage";
import SelectMapLinePage from "./pages/SelectMapLinePage";
import LiveMapPage from "./pages/LiveMapPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/select-line" element={<SelectLinePage />} />
        <Route path="/board" element={<BoardPage />} />
        <Route path="/select-map-line" element={<SelectMapLinePage />} />
        <Route path="/live-map" element={<LiveMapPage />} />
      </Routes>
    </BrowserRouter>
  );
}
