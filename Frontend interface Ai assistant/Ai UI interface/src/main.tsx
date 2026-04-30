import React from 'react'
import ReactDOM from 'react-dom/client'
import { Index } from './routes/index'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div className="dark">
        <Index />
    </div>
  </React.StrictMode>,
)
