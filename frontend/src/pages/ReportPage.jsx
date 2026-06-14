import { Link, useParams } from "react-router-dom";
import ReportViewer from "../components/ReportViewer.jsx";

export default function ReportPage() {
  const { group, name } = useParams();
  return (
    <>
      <nav className="app-nav">
        <span className="brand">🦉 Accessibility Automator</span>
        <Link to="/">← Back to workspace</Link>
      </nav>
      <div className="page">
        <ReportViewer group={group} name={name} />
      </div>
    </>
  );
}
