import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Sidebar }   from "./components/ui/Sidebar";
import { Overview }  from "./pages/Overview";
import { Resources } from "./pages/Resources";
import { Trends }    from "./pages/Trends";
import { Budgets }   from "./pages/Budgets";
import { Score }     from "./pages/Score";
import { Anomalies } from "./pages/Anomalies";
import { Forecast }  from "./pages/Forecast";
import { Alerts }    from "./pages/Alerts";
import { Slack }     from "./pages/Slack";
import { Reports }   from "./pages/Reports";
import "./index.css";

const App: React.FC = () => (
  <BrowserRouter>
    <div className="layout">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/"          element={<Overview />}  />
          <Route path="/resources" element={<Resources />} />
          <Route path="/trends"    element={<Trends />}    />
          <Route path="/budgets"   element={<Budgets />}   />
          <Route path="/score"     element={<Score />}     />
          <Route path="/anomalies" element={<Anomalies />} />
          <Route path="/forecast"  element={<Forecast />}  />
          <Route path="/alerts"    element={<Alerts />}    />
          <Route path="/slack"     element={<Slack />}     />
          <Route path="/reports"   element={<Reports />}   />
        </Routes>
      </main>
    </div>
  </BrowserRouter>
);

export default App;
