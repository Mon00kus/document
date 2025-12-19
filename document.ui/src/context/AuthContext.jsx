import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../api/client';

const AuthContext = createContext();

export const AuthProvider = ( { children } ) =>
{
  const [ user, setUser ] = useState( null );
  const [ loading, setLoading ] = useState( true );

  useEffect( () =>
  {
    const checkAuth = async () =>
    {
      const token = localStorage.getItem( 'token' );
      if ( token )
      {
        try
        {
          const response = await api.get( '/me' );
          setUser( response.data );
        } catch ( error )
        {
          console.error( "Auth check failed", error );
          localStorage.removeItem( 'token' );
          localStorage.removeItem( 'refresh_token' );
        }
      }
      setLoading( false );
    };
    checkAuth();
  }, [] );

  const login = async ( username, password ) =>
  {
    try
    {
      const response = await api.post( '/login', { username, password } );
      const { access_token, refresh_token } = response.data;

      localStorage.setItem( 'token', access_token );
      localStorage.setItem( 'refresh_token', refresh_token );

      // Get user info
      const meResponse = await api.get( '/me' );
      setUser( meResponse.data );
      return true;
    } catch ( error )
    {
      console.error( "Login failed", error );
      throw error;
    }
  };

  const logout = () =>
  {
    localStorage.removeItem( 'token' );
    localStorage.removeItem( 'refresh_token' );
    setUser( null );
  };

  return (
    <AuthContext.Provider value={ { user, login, logout, loading } }>
      { children }
    </AuthContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useAuth = () => useContext( AuthContext );
