import React, { useEffect, useState, forwardRef, useImperativeHandle } from 'react';
import api from '../api/client';

const EventLogTable = forwardRef((props, ref) => {
  const [logs, setLogs] = useState([]);

  // función para consultar logs
  const fetchLogs = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await api.get('/event-logs', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setLogs(res.data);
    } catch (error) {
      console.error("Error al cargar logs:", error);
    }
  };

  // exponer método al padre
  useImperativeHandle(ref, () => ({
    refreshLogs: () => {
      fetchLogs();
    }
  }), []);

  // cargar al montar
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchLogs();
  }, []);

  return (
    <div className="bg-[#161B22] rounded-2xl border border-gray-800 p-6 mt-8">
      <h2 className="text-xl font-bold mb-4">Histórico de Eventos</h2>
      <table className="w-full text-sm text-gray-300">
        <thead>
          <tr className="text-gray-400">
            <th className="text-left">ID</th>
            <th className="text-left">Tipo</th>
            <th className="text-left">Descripción</th>
            <th className="text-left">Fecha</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id} className="border-t border-gray-700">
              <td>{log.id}</td>
              <td>{log.event_type}</td>
              <td>{log.description}</td>
              <td>{new Date(log.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
});

export default EventLogTable;