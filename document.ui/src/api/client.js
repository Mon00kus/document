import axios from 'axios';

const api = axios.create( {
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
} );

// Interceptor para agregar el token
api.interceptors.request.use( ( config ) =>
{
  const token = localStorage.getItem( 'token' );
  if ( token )
  {
    config.headers.Authorization = `Bearer ${ token }`;
  }
  return config;
} );

// Interceptor para manejar errores (ej. refresh token)
api.interceptors.response.use(
  ( response ) => response,
  async ( error ) =>
  {
    const originalRequest = error.config;
    if ( error.response.status === 401 && !originalRequest._retry )
    {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem( 'refresh_token' );
      if ( refreshToken )
      {
        try
        {
          // Form format needed for refresh token endpoint
          const formData = new FormData();
          formData.append( 'refresh_token', refreshToken );

          const response = await axios.post( 'http://localhost:8000/api/v1/refresh-token', formData );

          localStorage.setItem( 'token', response.data.access_token );
          localStorage.setItem( 'refresh_token', response.data.refresh_token );

          api.defaults.headers.common[ 'Authorization' ] = `Bearer ${ response.data.access_token }`;
          return api( originalRequest );
        // eslint-disable-next-line no-unused-vars
        } catch ( refreshError )
        {
          // Si falla el refresh, logout
          localStorage.removeItem( 'token' );
          localStorage.removeItem( 'refresh_token' );
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject( error );
  }
);

export default api;
