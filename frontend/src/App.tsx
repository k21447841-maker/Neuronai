import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ProtectedRoute } from "./components/auth/ProtectedRoute";
import { AppShell } from "./components/layout/AppShell";
import { AuthPage } from "./pages/AuthPage";
import { OverviewPage } from "./pages/OverviewPage";
import { ScriptWriterPage } from "./pages/ScriptWriterPage";
import { ContentResearchPage } from "./pages/ContentResearchPage";
import { Animation2DPage } from "./pages/Animation2DPage";
import { Animation3DPage } from "./pages/Animation3DPage";
import { VoiceStudioPage } from "./pages/VoiceStudioPage";
import { AudioEditorPage } from "./pages/AudioEditorPage";
import { VideoEditorPage } from "./pages/VideoEditorPage";
import { ThumbnailSeoPage } from "./pages/ThumbnailSeoPage";
import { YouTubeChannelsPage } from "./pages/YouTubeChannelsPage";
import { AutomationCenterPage } from "./pages/AutomationCenterPage";
import { ContentLibraryPage } from "./pages/ContentLibraryPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { ApiIntegrationsPage } from "./pages/ApiIntegrationsPage";
import { UsageBillingPage } from "./pages/UsageBillingPage";
import { SettingsPage } from "./pages/SettingsPage";

const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/auth" element={<AuthPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/" element={<OverviewPage />} />
              <Route path="/script-writer" element={<ScriptWriterPage />} />
              <Route path="/content-research" element={<ContentResearchPage />} />
              <Route path="/2d-studio" element={<Animation2DPage />} />
              <Route path="/3d-studio" element={<Animation3DPage />} />
              <Route path="/voice-studio" element={<VoiceStudioPage />} />
              <Route path="/audio-editor" element={<AudioEditorPage />} />
              <Route path="/video-editor" element={<VideoEditorPage />} />
              <Route path="/thumbnail-studio" element={<ThumbnailSeoPage />} />
              <Route path="/youtube-channels" element={<YouTubeChannelsPage />} />
              <Route path="/automation" element={<AutomationCenterPage />} />
              <Route path="/library" element={<ContentLibraryPage />} />
              <Route path="/analytics" element={<AnalyticsPage />} />
              <Route path="/integrations" element={<ApiIntegrationsPage />} />
              <Route path="/billing" element={<UsageBillingPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
