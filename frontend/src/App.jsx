import { useState, useEffect } from 'react'

function App() {
  const [view, setView] = useState('ciudadano');

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      {/* Header Institucional */}
      <header className="bg-blue-800 text-white p-4 shadow-md">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-xl font-bold">Municipalidad Provincial de Yau</h1>
          <nav>
            <button 
              onClick={() => setView('ciudadano')}
              className={`mr-4 px-3 py-1 rounded ${view === 'ciudadano' ? 'bg-blue-600' : 'hover:bg-blue-700'}`}
            >
              Portal Ciudadano
            </button>
            <button 
              onClick={() => setView('funcionario')}
              className={`px-3 py-1 rounded ${view === 'funcionario' ? 'bg-blue-600' : 'hover:bg-blue-700'}`}
            >
              Panel Funcionario
            </button>
          </nav>
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-4 mt-6">
        {view === 'ciudadano' ? <VistaCiudadano /> : <VistaFuncionario />}
      </main>
    </div>
  )
}

function VistaCiudadano() {
  const [formData, setFormData] = useState({
    dni: '',
    nombres: '',
    email: '',
    descripcion: ''
  });
  const [mensaje, setMensaje] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMensaje(null);
    try {
      const response = await fetch('http://localhost:8000/tramites/nuevo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (response.ok) {
        setMensaje({ tipo: 'exito', texto: 'Trámite registrado correctamente. Recibirá una notificación en su correo.' });
        setFormData({ dni: '', nombres: '', email: '', descripcion: '' });
      } else {
        setMensaje({ tipo: 'error', texto: 'Error al registrar el trámite.' });
      }
    } catch (error) {
      setMensaje({ tipo: 'error', texto: 'No se pudo conectar con el servidor.' });
    }
    setLoading(false);
  };

  return (
    <div className="max-w-md mx-auto bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <h2 className="text-2xl font-semibold mb-6 text-gray-800">Reportar Incidente / Trámite</h2>
      
      {mensaje && (
        <div className={`p-4 mb-4 rounded ${mensaje.tipo === 'exito' ? 'bg-green-100 text-green-800 border-green-300 border' : 'bg-red-100 text-red-800 border-red-300 border'}`}>
          {mensaje.texto}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">DNI</label>
          <input 
            type="text" required 
            className="w-full border border-gray-300 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={formData.dni} onChange={e => setFormData({...formData, dni: e.target.value})}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Nombre Completo</label>
          <input 
            type="text" required 
            className="w-full border border-gray-300 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={formData.nombres} onChange={e => setFormData({...formData, nombres: e.target.value})}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Correo Electrónico</label>
          <input 
            type="email" required 
            className="w-full border border-gray-300 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={formData.email} onChange={e => setFormData({...formData, email: e.target.value})}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Descripción del Problema</label>
          <textarea required rows="4"
            className="w-full border border-gray-300 rounded p-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Ej: Hay un poste de luz a punto de caer en la Avenida Principal..."
            value={formData.descripcion} onChange={e => setFormData({...formData, descripcion: e.target.value})}
          ></textarea>
        </div>
        <button 
          type="submit" disabled={loading}
          className="w-full bg-blue-700 hover:bg-blue-800 text-white font-bold py-2 px-4 rounded transition-colors disabled:bg-gray-400"
        >
          {loading ? 'Enviando...' : 'Enviar Reporte'}
        </button>
      </form>
    </div>
  )
}

function VistaFuncionario() {
  const [tramites, setTramites] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTramites = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/tramites');
      if (response.ok) {
        const data = await response.json();
        const orden = { "Alta": 1, "Media": 2, "Baja": 3 };
        data.sort((a, b) => {
          if (orden[a.prioridad] !== orden[b.prioridad]) {
            return orden[a.prioridad] - orden[b.prioridad];
          }
          return b.id - a.id;
        });
        setTramites(data);
      }
    } catch (error) {
      console.error("Error cargando trámites", error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchTramites();
  }, []);

  const getBadgeColor = (prioridad) => {
    if (prioridad === 'Alta') return 'bg-red-100 text-red-800 border-red-200';
    if (prioridad === 'Media') return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-gray-800">Panel de Control: Bandeja de Entrada</h2>
        <button onClick={fetchTramites} className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded text-sm font-medium border border-gray-300">
          Actualizar Lista
        </button>
      </div>
      
      {loading ? (
        <div className="text-center py-8 text-gray-500">Cargando datos...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200 text-gray-600 text-sm">
                <th className="p-3 font-medium">ID</th>
                <th className="p-3 font-medium">Ciudadano</th>
                <th className="p-3 font-medium">Descripción (Analizada por IA)</th>
                <th className="p-3 font-medium text-center">Prioridad</th>
                <th className="p-3 font-medium">Estado</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {tramites.length === 0 ? (
                <tr><td colSpan="5" className="p-4 text-center text-gray-500">No hay trámites registrados.</td></tr>
              ) : (
                tramites.map(t => (
                  <tr key={t.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="p-3">#{t.id}</td>
                    <td className="p-3 font-medium text-gray-900">{t.nombres}<br/><span className="text-xs text-gray-500">{t.dni}</span></td>
                    <td className="p-3 max-w-md truncate" title={t.descripcion}>{t.descripcion}</td>
                    <td className="p-3 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold border ${getBadgeColor(t.prioridad)}`}>
                        {t.prioridad}
                      </span>
                    </td>
                    <td className="p-3 text-gray-600">{t.estado}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default App
