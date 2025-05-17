import { useAuth } from "react-oidc-context";

function Home() {
  const auth = useAuth();

  return (
    <div>
      <h2>Welcome! Please log in.</h2>
      <button onClick={() => auth.signinRedirect()}>Sign in</button>
    </div>
  );
}

export default Home;
