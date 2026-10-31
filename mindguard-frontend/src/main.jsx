import React, { useEffect } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, useNavigate } from 'react-router-dom'
import App from './App.jsx'
import './index.css'

function RedirectHandler({ children }) {
  const navigate = useNavigate()
  useEffect(() => {
    const redirect = sessionStorage.getItem('redirect')
    if (redirect) {
      sessionStorage.removeItem('redirect')
      // Older GitHub Pages links may still contain the former /mindguard prefix.
      const target = redirect.replace(/^\/mindguard(?=\/|$)/, '') || '/'
      navigate(target, { replace: true })
    }
  }, [navigate])
  return children
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    {/* Render serves this app at the domain root, not /mindguard. */}
    <BrowserRouter>
      <RedirectHandler>
        <App />
      </RedirectHandler>
    </BrowserRouter>
  </React.StrictMode>,
)
