import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';

const PrivateRoute = ( { children } ) =>
{
  const { user, loading } = useAuth();

  if ( loading )
  {
    return <div className="flex h-screen items-center justify-center bg-black text-white">Cargando...</div>;
  }

  return user ? children : <Navigate to="/login" />;
};

function App()
{
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={ <Login /> } />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
