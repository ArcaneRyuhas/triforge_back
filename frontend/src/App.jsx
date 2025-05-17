import { useAuth } from "react-oidc-context";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import Home from "./components/Home/Home";
import Dashboard from "./components/Dashboard/Dashboard";

function App() {
  const auth = useAuth();

  if (auth.isLoading) return <div>Loading...</div>;
  if (auth.error) return <div>Error: {auth.error.message}</div>;

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={
            auth.isAuthenticated ? (
              <Navigate to="/dashboard" />
            ) : (
              <Home />
            )
          }
        />
        <Route
          path="/dashboard"
          element={
            auth.isAuthenticated ? (
              <Dashboard user={auth.user} />
            ) : (
              <Navigate to="/" />
            )
          }
        />
      </Routes>
    </Router>
  );
}

export default App;