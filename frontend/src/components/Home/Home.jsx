import { useAuth } from "react-oidc-context";
import "./Home.css";
import { useState, useEffect } from 'react'

function Home() {
  const auth = useAuth();
  const [signingIn, setSigningIn] = useState(false);
  const [currentYear] = useState(new Date().getFullYear());

  const handleSignIn = () => {
    setSigningIn(true);
    // Call auth.signinRedirect() after a short delay to show the animation
    setTimeout(() => {
      auth.signinRedirect();
    }, 500);
  };

   useEffect(() => {
    if (signingIn) {
      const timer = setTimeout(() => {
        setSigningIn(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [signingIn]);

  return (
    <div className="wrapper">
      <div className="nav">
        <div>InfyCode</div>
        <div className="profile"></div>
      </div>
      
      <div className="container">
        <div className="welcomeSelection">
          <h1 className="greet">Welcome <span>back!</span></h1>
        </div>
        
        <div className="card">
          <p>Sign in to access your workspace</p>
          <button 
            className="signinBtn"
            onClick={handleSignIn}
            disabled={signingIn}
          >
            <span>{signingIn ? "Signing in..." : "Sign in"}</span>
            <div className="iconContainer">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14"></path>
                <path d="m12 5 7 7-7 7"></path>
              </svg>
            </div>
          </button>
          <div 
            className={`$"progressBar" ${signingIn ? "animateProgress" : ''}`} 
            style={{ width: signingIn ? '100%' : '0' }}
          ></div>
        </div>
        
        <div className="buttonGroup">
          <button className="altBtn">Register</button>
          <button className="altBtn">Help</button>
        </div>
      </div>
      
      <div className="bottomInfo">
        © {currentYear} InfyCode. All rights reserved.
      </div>
    </div>
  );
}

export default Home;
