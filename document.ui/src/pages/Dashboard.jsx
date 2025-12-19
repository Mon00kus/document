import React, { useState, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import FileUpload from '../components/FileUpload';
// eslint-disable-next-line no-unused-vars
import { motion } from 'framer-motion';
import { FileText, LogOut, LayoutDashboard, Database, DollarSign, Activity } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';
import EventLogTable from '../components/EventLogTable';

export default function Dashboard()
{
  const { user, logout } = useAuth();
  const [ analysisResult, setAnalysisResult ] = useState( null );

  const eventLogRef = useRef();

  const handleUploadComplete = ( data ) =>
  {
    setAnalysisResult( data );
    eventLogRef.current?.refreshLogs();
  };

  return (
    <div className="min-h-screen bg-[#0F1115] text-white">
      {/* Navbar */ }
      <nav className="border-b border-gray-800 bg-[#0F1115]/80 backdrop-blur-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="bg-gradient-to-br from-blue-500 to-purple-600 p-2 rounded-lg">
                <LayoutDashboard className="h-5 w-5 text-white" />
              </div>
              <span className="font-bold text-xl tracking-tight">DocuAI</span>
            </div>

            <div className="flex items-center gap-6">
              <div className="hidden md:flex flex-col items-end">
                <span className="text-sm font-medium text-gray-200">{ user?.username }</span>
                <span className="text-xs text-gray-500 capitalize">{ user?.role }</span>
              </div>
              <button
                onClick={ logout }
                className="p-2 rounded-lg hover:bg-white/5 text-gray-400 hover:text-white transition-colors"
                title="Cerrar Sesión"
              >
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

          {/* Left Column: Upload */ }
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-[#161B22] rounded-2xl border border-gray-800 p-6 shadow-xl">
              <h2 className="text-xl font-bold mb-1 flex items-center gap-2">
                <FileText className="text-blue-500" />
                Cargar Documento
              </h2>
              <p className="text-gray-400 text-sm mb-6">Sube tus facturas o documentos de texto para análisis automático.</p>
              <FileUpload onUploadComplete={ handleUploadComplete } />
            </div>

            {/* Quick Stats or Info could go here */ }
            <div className="bg-[#161B22] rounded-2xl border border-gray-800 p-6 opacity-60">
              <h3 className="text-sm font-medium text-gray-400 mb-4">CAPACIDADES DEL SISTEMA</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400">
                    <DollarSign size={ 16 } />
                  </div>
                  <span className="text-sm text-gray-300">Extracción de Facturas</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-400">
                    <Activity size={ 16 } />
                  </div>
                  <span className="text-sm text-gray-300">Análisis de Sentimiento</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Results */ }
          <div className="lg:col-span-7">
            <AnimatePresence mode="wait">
              { analysisResult ? (
                <motion.div
                  initial={ { opacity: 0, x: 20 } }
                  animate={ { opacity: 1, x: 0 } }
                  exit={ { opacity: 0, x: -20 } }
                  className="bg-[#161B22] rounded-2xl border border-gray-800 p-8 shadow-2xl overflow-hidden relative"
                >
                  <div className="absolute top-0 right-0 p-4 opacity-50">
                    <Database className="w-32 h-32 text-gray-800 -mr-10 -mt-10 transform rotate-12" />
                  </div>

                  <div className="relative z-10">
                    <div className="flex items-center justify-between mb-8">
                      <div>
                        <span className="text-xs font-bold tracking-wider text-blue-400 uppercase bg-blue-500/10 px-3 py-1 rounded-full border border-blue-500/20">
                          { analysisResult.classification || 'Resultado' }
                        </span>
                        <h2 className="text-2xl font-bold mt-3 text-white">Análisis Completado</h2>
                      </div>
                      <div className="text-right">
                        <span className="text-xs text-gray-500 block">ID ANÁLISIS</span>
                        <span className="font-mono text-gray-300">#{ analysisResult.analysis_id }</span>
                      </div>
                    </div>

                    <div className="space-y-6">
                      { analysisResult.data && (
                        <div className="grid grid-cols-2 gap-6">
                          { analysisResult.data.vendor_name && (
                            <div className="col-span-2 sm:col-span-1 p-4 rounded-xl bg-gray-800/50 border border-gray-700">
                              <label className="text-xs text-gray-400 uppercase block mb-1">Proveedor</label>
                              <p className="text-lg font-medium text-white">{ analysisResult.data.vendor_name }</p>
                            </div>
                          ) }
                          { analysisResult.data.client_name && (
                            <div className="col-span-2 sm:col-span-1 p-4 rounded-xl bg-gray-800/50 border border-gray-700">
                              <label className="text-xs text-gray-400 uppercase block mb-1">Cliente</label>
                              <p className="text-lg font-medium text-white">{ analysisResult.data.client_name }</p>
                            </div>
                          ) }
                          { analysisResult.data.invoice_total && (
                            <div className="col-span-2 sm:col-span-1 p-4 rounded-xl bg-gray-800/50 border border-gray-700">
                              <label className="text-xs text-gray-400 uppercase block mb-1">Total Factura</label>
                              <p className="text-2xl font-bold text-green-400">{ analysisResult.data.invoice_total }</p>
                            </div>
                          ) }
                          { analysisResult.data.sentiment && (
                            <div className="col-span-2 sm:col-span-1 p-4 rounded-xl bg-gray-800/50 border border-gray-700">
                              <label className="text-xs text-gray-400 uppercase block mb-1">Sentimiento</label>
                              <p className={ `text-lg font-bold ${ analysisResult.data.sentiment === 'POSITIVO' ? 'text-green-400' :
                                  analysisResult.data.sentiment === 'NEGATIVO' ? 'text-red-400' :
                                    'text-yellow-400'
                                }` }>{ analysisResult.data.sentiment }</p>
                            </div>
                          ) }
                        </div>
                      ) }

                      { analysisResult.data?.summary && (
                        <div className="p-4 rounded-xl bg-gray-800/50 border border-gray-700">
                          <label className="text-xs text-gray-400 uppercase block mb-2">Resumen / Contenido</label>
                          <p className="text-gray-300 leading-relaxed text-sm">
                            { analysisResult.data.summary }
                          </p>
                        </div>
                      ) }
                    </div>
                  </div>
                </motion.div>
              ) : (
                <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-gray-600 border-2 border-dashed border-gray-800 rounded-2xl bg-[#161B22]/50">
                  <LayoutDashboard className="w-16 h-16 mb-4 opacity-20" />
                  <p className="text-lg font-medium opacity-50">Los resultados del análisis aparecerán aquí</p>
                </div>
              ) }
            </AnimatePresence>
          </div>

        </div>
        
          {/* Historico de eventos*/}
          <div className="lg:col-span-12">
            <EventLogTable ref={eventLogRef} />
          </div>

      </main>
    </div>
  );
}