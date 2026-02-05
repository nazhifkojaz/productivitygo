import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from './lib/queryClient'
import './index.css'
import App from './App.tsx'
import { OpenAPI } from './api'
import axios from 'axios'

// Initialize API Configuration
const API_URL = import.meta.env.VITE_API_URL || "";
OpenAPI.BASE = API_URL;
axios.defaults.baseURL = API_URL;

// Set Auth Token if available (initial check)
const sessionStr = localStorage.getItem('sb-' + import.meta.env.VITE_SUPABASE_URL?.split('//')[1].split('.')[0] + '-auth-token');
if (sessionStr) {
  try {
    const session = JSON.parse(sessionStr);
    if (session?.access_token) {
      OpenAPI.TOKEN = session.access_token;
      axios.defaults.headers.common['Authorization'] = `Bearer ${session.access_token}`;
    }
  } catch (e) {
    console.error('Failed to parse session for initial token', e);
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
