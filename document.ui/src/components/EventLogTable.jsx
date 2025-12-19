import React, { useEffect, useState, forwardRef, useImperativeHandle } from 'react';
import api from '../api/client';

const EventLogTable = forwardRef((props, ref) => {
  const [logs, setLogs] = useState([]);
  const [filterType, setFilterType] = useState('');
  const [filterText, setFilterText] = useState('');
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');

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

  // aplicar filtros en memoria
  const filteredLogs = logs.filter(log => {
    const matchesType = filterType ? log.event_type === filterType : true;
    const matchesText = filterText ? log.description.toLowerCase().includes(filterText.toLowerCase()) : true;
    const logDate = new Date(log.created_at);
    const matchesStart = filterStartDate ? logDate >= new Date(filterStartDate) : true;
    //const matchesEnd = filterEndDate ? logDate <= new Date(filterEndDate) : true;
    const endDate = filterEndDate ? new Date(filterEndDate + 'T23:59:59') : null;
    const matchesEnd = endDate ? logDate <= endDate : true;
    return matchesType && matchesText && matchesStart && matchesEnd;
  });

  return (
    <div className="bg-[#161B22] rounded-2xl border border-gray-800 p-6 mt-8">
      <h2 className="text-xl font-bold mb-4">Histórico de Eventos</h2>

      {/* Filtros */}
      <div className="flex flex-wrap gap-4 mb-4">
        <select
          value={filterType}
          onChange={e => setFilterType(e.target.value)}
          className="bg-gray-800 text-white p-2 rounded"
        >
          <option value="">Todos</option>
          <option value="UPLOAD">UPLOAD</option>
          <option value="ANALYSIS">ANALYSIS</option>
        </select>

        <input
          type="text"
          placeholder="Buscar descripción..."
          value={filterText}
          onChange={e => setFilterText(e.target.value)}
          className="bg-gray-800 text-white p-2 rounded flex-1"
        />

        <input
          type="date"
          value={filterStartDate}
          onChange={e => setFilterStartDate(e.target.value)}
          className="bg-gray-800 text-white p-2 rounded"
        />

        <input
          type="date"
          value={filterEndDate}
          onChange={e => setFilterEndDate(e.target.value)}
          className="bg-gray-800 text-white p-2 rounded"
        />
      </div>

      {/* Tabla */}
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
          {filteredLogs.map(log => (
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