/* eslint-disable no-unused-vars */
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../api/client';
import clsx from 'clsx';

export default function FileUpload( { onUploadComplete } )
{
  const [ uploading, setUploading ] = useState( false );
  const [ uploadStatus, setUploadStatus ] = useState( 'idle' ); // idle, uploading, success, error
  const [ message, setMessage ] = useState( '' );

  const onDrop = useCallback( async ( acceptedFiles ) =>
  {
    setUploadStatus('idle');
    const file = acceptedFiles[ 0 ];
    if ( !file ) return;

    setUploading( true );
    setUploadStatus( 'uploading' );
    setMessage( 'Subiendo y analizando documento...' );

    const formData = new FormData();
    formData.append( 'file', file );

    // Determine endpoint based on file type
    const isCsv = file.name.toLowerCase().endsWith( '.csv' );
    const endpoint = isCsv ? '/upload-csv' : '/upload-document';

    if ( isCsv )
    {
      formData.append( 'param1', 'Frontend Upload' );
      formData.append( 'param2', 'CSV Type' );
    }

    try
    {
      const response = await api.post( endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      } );

      setUploadStatus( 'success' );
      setMessage( 'Documento procesado correctamente.' );
      if ( onUploadComplete )
      {
        onUploadComplete( response.data );
      }
      //setTimeout( () => setUploadStatus( 'idle' ), 3000 );
    } catch ( error )
    {
      console.error( error );
      setUploadStatus( 'error' );
      setMessage( error.response?.data?.detail || 'Error al subir el archivo.' );
    } finally
    {
      setUploading( false );
    }
  }, [ onUploadComplete ] );

  const { getRootProps, getInputProps, isDragActive } = useDropzone( {
    onDrop,
    accept: {
      'application/pdf': [ '.pdf' ],
      'image/png': [ '.png' ],
      'image/jpeg': [ '.jpg', '.jpeg' ],
      'text/csv': [ '.csv' ]
    },
    maxFiles: 1
  } );

  return (
    <div className="w-full">
      <div
        { ...getRootProps() }
        className={ clsx(
          "relative border-2 border-dashed rounded-2xl p-10 transition-all duration-300 ease-in-out cursor-pointer overflow-hidden group",
          isDragActive ? "border-blue-500 bg-blue-500/10" : "border-gray-600 hover:border-blue-400 bg-gray-800/30 hover:bg-gray-800/50"
        ) }
      >
        <input { ...getInputProps() } />

        <div className="relative z-10 flex flex-col items-center justify-center text-center">
          <div className={ clsx(
            "p-4 rounded-full mb-4 transition-all duration-300",
            isDragActive ? "bg-blue-500 text-white shadow-lg shadow-blue-500/30" : "bg-gray-700 text-gray-300 group-hover:bg-blue-500 group-hover:text-white group-hover:scale-110"
          ) }>
            { uploading ? (
              <Loader2 className="w-8 h-8 animate-spin" />
            ) : uploadStatus === 'success' ? (
              <CheckCircle className="w-8 h-8" />
            ) : uploadStatus === 'error' ? (
              <AlertCircle className="w-8 h-8" />
            ) : (
              <UploadCloud className="w-8 h-8" />
            ) }
          </div>

          <h3 className="text-lg font-semibold text-white mb-2">
            { uploading ? 'Procesando...' : 'Arrastra tu documento aquí' }
          </h3>
          <p className="text-gray-400 text-sm max-w-xs">
            Soporta PDF, JPG, PNG (para análisis) o CSV (carga simple).
          </p>
        </div>

        {/* Decorative background glow */ }
        <div className="absolute inset-0  from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      </div>

      <AnimatePresence>
        { message && (
          <motion.div
            initial={ { opacity: 0, y: 10 } }
            animate={ { opacity: 1, y: 0 } }
            exit={ { opacity: 0 } }
            className={ clsx(
              "mt-4 p-3 rounded-lg text-sm font-medium flex items-center gap-2",
              uploadStatus === 'error' ? "bg-red-500/20 text-red-200 border border-red-500/30" :
                uploadStatus === 'success' ? "bg-green-500/20 text-green-200 border border-green-500/30" :
                  "bg-blue-500/20 text-blue-200 border border-blue-500/30"
            ) }
          >
            { uploadStatus === 'error' ? <AlertCircle size={ 16 } /> :
              uploadStatus === 'success' ? <CheckCircle size={ 16 } /> : <Loader2 size={ 16 } className="animate-spin" /> }
            { message }
          </motion.div>
        ) }
      </AnimatePresence>
    </div>
  );
}
