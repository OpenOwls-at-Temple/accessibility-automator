import FileExplorer from "../components/FileExplorer.jsx";
import SignInForm from "../components/SignInForm.jsx";
import TopMenu from "../components/TopMenu.jsx";
import TopPanel from "../components/TopPanel.jsx";
import { useAuth } from "../hooks/useAuth.jsx";

export default function HomePage() {
  const { user, loading } = useAuth();

  if (loading) return <div className="page muted">Loading…</div>;
  if (!user) return <SignInForm />;

  return (
    <>
      <TopMenu />
      <div className="page">
        <TopPanel />
        <FileExplorer />
      </div>
    </>
  );
}
