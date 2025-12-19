/* eslint-disable no-unused-vars */
import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ShieldCheck, User } from 'lucide-react';

export default function Login()
{
  const [ username, setUsername ] = useState( '' );
  const [ password, setPassword ] = useState( '' );
  const [ error, setError ] = useState( '' );
  const { login } = useAuth();
  const navigate = useNavigate();
  const [ isLoading, setIsLoading ] = useState( false );

  const handleSubmit = async ( e ) =>
  {
    e.preventDefault();
    setIsLoading( true );
    setError( '' );
    try
    {
      await login( username, password );
      navigate( '/' );
    } catch ( err )
    {
      setError( 'Credenciales inválidas. Intente de nuevo.' );
    } finally
    {
      setIsLoading( false );
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-black overflow-hidden relative">
      {/* Background Blobs */ }
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
      <div className="absolute top-[-10%] right-[-10%] w-96 h-96 bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>
      <div className="absolute -bottom-32 left-20 w-96 h-96 bg-pink-600 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-4000"></div>

      <motion.div
        initial={ { opacity: 0, y: 20 } }
        animate={ { opacity: 1, y: 0 } }
        transition={ { duration: 0.5 } }
        className="w-full max-w-md p-8 rounded-2xl bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl relative z-10"
      >
        <div className="flex flex-col items-center mb-8">
          <div className="p-3 bg-gradient-to-tr from-blue-500 to-purple-500 rounded-full shadow-lg mb-4">
            <ShieldCheck className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
            Bienvenido
          </h2>
          <p className="text-gray-400 mt-2 text-sm">Inicia sesión para gestionar tus documentos</p>
        </div>

        { error && (
          <motion.div
            initial={ { opacity: 0, height: 0 } }
            animate={ { opacity: 1, height: 'auto' } }
            className="mb-4 p-3 rounded-lg bg-red-500/20 border border-red-500/50 text-red-200 text-sm text-center"
          >
            { error }
          </motion.div>
        ) }

        <form onSubmit={ handleSubmit } className="space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300 ml-1">Usuario</label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User className="h-5 w-5 text-gray-500 group-focus-within:text-blue-400 transition-colors" />
              </div>
              <input
                type="text"
                value={ username }
                onChange={ ( e ) => setUsername( e.target.value ) }
                className="w-full pl-10 pr-4 py-3 bg-gray-900/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-white placeholder-gray-500 transition-all duration-200"
                placeholder="Ingrese su usuario"
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-300 ml-1">Contraseña</label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <ShieldCheck className="h-5 w-5 text-gray-500 group-focus-within:text-purple-400 transition-colors" />
              </div>
              <input
                type="password"
                value={ password }
                onChange={ ( e ) => setPassword( e.target.value ) }
                className="w-full pl-10 pr-4 py-3 bg-gray-900/50 border border-gray-700 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none text-white placeholder-gray-500 transition-all duration-200"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <motion.button
            whileHover={ { scale: 1.02 } }
            whileTap={ { scale: 0.98 } }
            type="submit"
            disabled={ isLoading }
            className={ `w-full py-3.5 rounded-xl font-bold text-white shadow-lg bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 focus:ring-4 focus:ring-purple-500/30 transition-all duration-200 ${ isLoading ? 'opacity-70 cursor-not-allowed' : '' }` }
          >
            { isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Procesando...
              </span>
            ) : 'Iniciar Sesión' }
          </motion.button>
        </form>

        <div className="mt-6 text-center text-xs text-gray-500">
          <p>Acceso seguro al sistema de gestión documental</p>
        </div>
      </motion.div>
    </div>
  );
}
