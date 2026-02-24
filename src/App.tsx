import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import Execute from "./pages/Execute";
import Blueprints from "./pages/Blueprints";
import BlueprintEditor from "./pages/BlueprintEditor";
import Reports from "./pages/Reports";
import ReportDetail from "./pages/ReportDetail";
import Network from "./pages/Network";
import Settings from "./pages/Settings";
import Profile from "./pages/Profile";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/execute" element={<Execute />} />
            <Route path="/execute/:id" element={<Execute />} />
            <Route path="/blueprints" element={<Blueprints />} />
            <Route path="/blueprints/create" element={<BlueprintEditor />} />
            <Route path="/blueprints/:id/edit" element={<BlueprintEditor />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/reports/:id" element={<ReportDetail />} />
            <Route path="/network" element={<Network />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/profile" element={<Profile />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
