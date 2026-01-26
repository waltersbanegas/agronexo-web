import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Tractor, PlusCircle, Truck, RefreshCw, Sprout, Scale, DollarSign, MapPin, Locate, Trash2, Edit, CloudRain, Wind, Thermometer, Map as MapIcon, Menu, X, FileDown, Activity, ArrowRightLeft, CheckSquare, Square, Banknote, Syringe, CloudLightning, LayoutDashboard, Warehouse, Factory, Dna, Settings, AlertTriangle } from 'lucide-react';

import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({ iconUrl: icon, shadowUrl: iconShadow, iconSize: [25, 41], iconAnchor: [12, 41] });
let SiloIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

function App() {
  const API_URL = 'https://agronexo-backend.onrender.com/api'; 

  const [seccion, setSeccion] = useState('DASHBOARD'); 
  const [rol, setRol] = useState('PRODUCTOR'); 
  const [lotes, setLotes] = useState([]);
  const [animales, setAnimales] = useState([]);
  const [silos, setSilos] = useState([]); 
  const [clima, setClima] = useState(null);
  const [loteClimaNombre, setLoteClimaNombre] = useState('General');
  const [tempPos, setTempPos] = useState(null); 
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [menuAbierto, setMenuAbierto] = useState(false); 
  const [dashboardData, setDashboardData] = useState({ cabezas: 0, hectareas: 0, gastos_mes: 0, margen_mes: 0, lluvia_mes: 0, stock_granos: 0 });
  const [configRepro, setConfigRepro] = useState({ toros: [], protocolos: [] });

  // Modales
  const [showModalLote, setShowModalLote] = useState(false);
  const [showModalCosecha, setShowModalCosecha] = useState(false);
  const [showModalAnimal, setShowModalAnimal] = useState(false);
  const [showModalPesaje, setShowModalPesaje] = useState(false);
  const [showModalGasto, setShowModalGasto] = useState(false); 
  const [showModalDetalleAnimal, setShowModalDetalleAnimal] = useState(false);
  const [showModalMover, setShowModalMover] = useState(false); 
  const [showModalBaja, setShowModalBaja] = useState(false); // 🆕 NUEVO MODAL DE BAJA
  const [showModalSanidad, setShowModalSanidad] = useState(false); 
  const [showModalLluvia, setShowModalLluvia] = useState(false);
  const [showModalNuevoSilo, setShowModalNuevoSilo] = useState(false);
  const [showModalVentaGrano, setShowModalVentaGrano] = useState(false);
  const [showModalRepro, setShowModalRepro] = useState(false);
  const [showModalReproMasivo, setShowModalReproMasivo] = useState(false);
  const [showModalConfigRepro, setShowModalConfigRepro] = useState(false);
  const [showModalEditarAnimal, setShowModalEditarAnimal] = useState(false);
  
  const [modoEdicion, setModoEdicion] = useState(null); 
  const [modoSeleccion, setModoSeleccion] = useState(false);
  const [animalesSeleccionados, setAnimalesSeleccionados] = useState([]);
  const [loteDestino, setLoteDestino] = useState("");

  const [nuevoContrato, setNuevoContrato] = useState({ nombreLote: '', hectareas: '', propietario: '', tipo: 'APARCERIA', porcentaje: 0, lat: null, lng: null });
  const [nuevaCosecha, setNuevaCosecha] = useState({ lote_id: null, lote_nombre: '', kilos: '', destino: 'VENTA', silo_id: '' });
  const [nuevoAnimal, setNuevoAnimal] = useState({ caravana: '', rfid: '', raza: 'Braford', categoria: 'Ternero', peso_inicial: '', fecha: '' });
  const [nuevoPesaje, setNuevoPesaje] = useState({ animal_id: null, caravana: '', kilos: '', fecha: '' });
  const [nuevoGasto, setNuevoGasto] = useState({ lote_id: null, animal_id: null, nombre_destino: '', concepto: '', monto: '', categoria: 'INSUMO', fecha: '' });
  const [nuevoSilo, setNuevoSilo] = useState({ nombre: '', tipo: 'SILOBOLSA', contenido: 'SOJA', capacidad: '', lat: null, lng: null });
  const [ventaGrano, setVentaGrano] = useState({ silo_id: null, kilos: '', precio_total: '', comprador: '', tipo_grano: '', origen: 'SILO' });

  const [datosDetalleAnimal, setDatosDetalleAnimal] = useState(null);
  const [datosEdicionAnimal, setDatosEdicionAnimal] = useState({ id:null, caravana:'', rfid:'', categoria:'', raza:'' });
  
  // 🆕 DATOS BAJA (Venta/Robo/Etc)
  const [datosBaja, setDatosBaja] = useState({ animal_id: null, motivo: 'VENTA', comprador: '', detalle: '', kilos: '', precio: '' });
  
  const [datosSanidad, setDatosSanidad] = useState({ lote_id: 'all', concepto: '', monto: '', fecha: '' });
  const [nuevoRegistroLluvia, setNuevoRegistroLluvia] = useState({ lote_id: '', milimetros: '', fecha: '' });
  const [nuevoEventoRepro, setNuevoEventoRepro] = useState({ animal_id: null, tipo: 'INSEMINACION', detalle: '', fecha: '', protocolo_id: '', genetica_id: '', condicion_corporal: '' });
  const [datosReproMasivo, setDatosReproMasivo] = useState({ tipo: 'INSEMINACION', detalle: '', fecha: '', protocolo_id: '', genetica_id: '' });
  const [nuevoItemConfig, setNuevoItemConfig] = useState({ tipo_objeto: 'TORO', nombre: '', tipo: 'SEMEN_CONVENCIONAL', raza:'Braford', costo:'', descripcion:'' });

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const cargarTodo = () => {
    axios.get(`${API_URL}/liquidaciones`).then(res => {
        setLotes(res.data);
        if (res.data.length > 0 && res.data[0].lat) cargarClima(res.data[0].lat, res.data[0].lng, res.data[0].lote);
    }).catch(err => console.error(err));
    axios.get(`${API_URL}/animales`).then(res => setAnimales(res.data));
    axios.get(`${API_URL}/silos`).then(res => setSilos(res.data));
    axios.get(`${API_URL}/resumen_general`).then(res => setDashboardData(res.data)).catch(console.error);
  };

  const cargarClima = (lat, lng, nombreLote) => {
    if (!lat || !lng) return;
    setClima(null); setLoteClimaNombre(nombreLote);
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current_weather=true&daily=precipitation_sum&timezone=auto`;
    axios.get(url).then(res => setClima({ temp: res.data.current_weather.temperature, wind: res.data.current_weather.windspeed, rain: res.data.daily.precipitation_sum[0] })).catch(e => console.log(e));
  };

  const descargarExcel = async () => {
    try {
        const response = await axios.get(`${API_URL}/exportar_excel`, { responseType: 'blob' });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'Reporte_AgroNexo.xlsx');
        document.body.appendChild(link);
        link.click();
        link.remove();
    } catch (error) { alert("Error al descargar reporte."); }
  };

  // ⚠️ NUEVO: RESET DE FÁBRICA
  const resetFabrica = () => {
      if(window.confirm("⚠️ ¿ESTÁS SEGURO?\n\nEsto borrará ABSOLUTAMENTE TODOS los datos.\nEs necesario para arreglar los errores actuales.\n\n¿Proceder?")) {
          axios.post(`${API_URL}/reset_fabrica`).then(res => {
              alert(res.data.mensaje);
              window.location.reload();
          }).catch(err => alert("Error al resetear: " + err.message));
      }
  }

  const abrirDetalleAnimal = (vaca) => {
      if (modoSeleccion) { toggleSeleccion(vaca.id); return; }
      setDatosDetalleAnimal(null);
      setDatosDetalleAnimal({...vaca, historial_pesos: [], historial_gastos: [], historial_repro: []});
      setShowModalDetalleAnimal(true);
      axios.get(`${API_URL}/detalle_animal/${vaca.id}`).then(res => setDatosDetalleAnimal({...res.data, id: vaca.id}));
  };

  // 🆕 NUEVO: INICIAR BAJA (VENTA/ROBO/ETC)
  const iniciarBaja = () => {
      if (!datosDetalleAnimal || !datosDetalleAnimal.id) return alert("Error: ID del animal no encontrado. Recarga.");
      setDatosBaja({ 
          animal_id: datosDetalleAnimal.id, 
          motivo: 'VENTA', 
          comprador: '', detalle: '', kilos: '', precio: '' 
      });
      setShowModalDetalleAnimal(false);
      setShowModalBaja(true);
  };

  const confirmarBaja = (e) => {
      e.preventDefault();
      // Validaciones para venta
      if (datosBaja.motivo === 'VENTA') {
          const k = parseFloat(datosBaja.kilos.toString().replace(',','.'));
          const p = parseFloat(datosBaja.precio.toString().replace(',','.'));
          if (isNaN(k) || k <= 0) return alert("Kilos inválidos");
          if (isNaN(p) || p <= 0) return alert("Precio inválido");
          
          // Calcular total si es venta
          const total = k * p;
          axios.post(`${API_URL}/registrar_baja`, { ...datosBaja, kilos: k, precio: total }).then((res) => {
              alert(`✅ Baja registrada: ${datosBaja.motivo}\nTotal: $ ${total.toLocaleString()}`);
              setShowModalBaja(false); cargarTodo();
          }).catch(err => alert("Error: " + err.message));
      } else {
          // Otras bajas
          axios.post(`${API_URL}/registrar_baja`, datosBaja).then((res) => {
              alert(`✅ Baja registrada: ${datosBaja.motivo}`);
              setShowModalBaja(false); cargarTodo();
          }).catch(err => alert("Error: " + err.message));
      }
  };

  const iniciarEventoRepro = () => {
      if (!datosDetalleAnimal || !datosDetalleAnimal.id) return alert("Error: ID del animal no encontrado. Recarga.");
      setNuevoEventoRepro({ 
          animal_id: datosDetalleAnimal.id,
          tipo: 'INSEMINACION', detalle: '', fecha: '', protocolo_id: '', genetica_id: '', condicion_corporal: '' 
      }); 
      setShowModalRepro(true);
  }

  const toggleSeleccion = (id) => {
      if (animalesSeleccionados.includes(id)) setAnimalesSeleccionados(animalesSeleccionados.filter(a => a !== id));
      else setAnimalesSeleccionados([...animalesSeleccionados, id]);
  };

  const iniciarMovimiento = () => {
      if (animalesSeleccionados.length === 0) return alert("Selecciona al menos un animal");
      setLoteDestino(""); setShowModalMover(true);
  };

  const confirmarMovimiento = () => {
      const destinoFinal = loteDestino === "" ? null : loteDestino;
      axios.post(`${API_URL}/mover_hacienda`, { lote_destino_id: destinoFinal, animales_ids: animalesSeleccionados })
      .then(() => {
          alert("Hacienda movida correctamente 🚚");
          setShowModalMover(false); setModoSeleccion(false); setAnimalesSeleccionados([]); cargarTodo();
      })
      .catch(e => alert("Error al mover: " + e.message));
  };

  const irACrearLote = () => { setShowModalMover(false); abrirNuevoLote(); };
  const abrirNuevoLote = () => { setModoEdicion(null); setNuevoContrato({ nombreLote: '', hectareas: '', propietario: '', tipo: 'APARCERIA', porcentaje: 0, lat: null, lng: null }); setShowModalLote(true); };
  const abrirEditarLote = (item) => { setModoEdicion(item.lote_id); setNuevoContrato({ nombreLote: item.lote, hectareas: item.hectareas, propietario: item.propietario, tipo: item.tipo, porcentaje: item.porcentaje, lat: item.lat, lng: item.lng }); setShowModalLote(true); };
  
  const guardarContrato = (e) => { 
      e.preventDefault(); 
      const endpoint = modoEdicion ? `${API_URL}/editar_lote/${modoEdicion}` : `${API_URL}/nuevo_contrato`; 
      const method = modoEdicion ? axios.put : axios.post; 
      const data = { ...nuevoContrato };
      if (!data.lat) { data.lat = 0; data.lng = 0; }
      method(endpoint, data).then(() => { setShowModalLote(false); cargarTodo(); })
      .catch(err => alert("Error al guardar: " + (err.response?.data?.error || err.message))); 
  };
  
  const eliminarLote = (id) => { if (window.confirm("¿Eliminar?")) axios.delete(`${API_URL}/eliminar_lote/${id}`).then(() => cargarTodo()); };
  const guardarCosecha = (e) => { e.preventDefault(); axios.post(`${API_URL}/nueva_cosecha`, nuevaCosecha).then(() => { setShowModalCosecha(false); cargarTodo(); }); }; 
  const guardarAnimal = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_animal`, nuevoAnimal).then(() => { setShowModalAnimal(false); cargarTodo(); alert("Registrado"); }); };
  const guardarPesaje = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_pesaje`, { animal_id: nuevoPesaje.animal_id, kilos: nuevoPesaje.kilos, fecha: nuevoPesaje.fecha }).then(() => { setShowModalPesaje(false); cargarTodo(); }); };
  const guardarGasto = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_gasto`, nuevoGasto).then(() => { setShowModalGasto(false); cargarTodo(); alert("Gasto OK"); }); };
  const abrirGasto = (tipo, item) => { setNuevoGasto({ lote_id: tipo === 'LOTE' ? item.lote_id : null, animal_id: tipo === 'ANIMAL' ? item.id : null, nombre_destino: tipo === 'LOTE' ? item.lote : `RP: ${item.caravana}`, concepto: '', monto: '', categoria: 'INSUMO', fecha: '' }); setShowModalGasto(true); };
  const guardarEventoRepro = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_evento_reproductivo`, nuevoEventoRepro).then(() => { alert("Evento registrado 🧬"); setShowModalRepro(false); cargarTodo(); }).catch(e => alert("Error: " + e.message)); }
  const confirmarReproMasivo = (e) => { e.preventDefault(); axios.post(`${API_URL}/evento_reproductivo_masivo`, { animales_ids: animalesSeleccionados, ...datosReproMasivo }).then((res) => { alert(res.data.mensaje); setShowModalReproMasivo(false); setModoSeleccion(false); setAnimalesSeleccionados([]); cargarTodo(); }); };
  const guardarConfigRepro = (e) => { e.preventDefault(); axios.post(`${API_URL}/crear_config_repro`, nuevoItemConfig).then(() => { alert("Guardado"); setShowModalConfigRepro(false); }); };
  const abrirEditarAnimal = () => { if(!datosDetalleAnimal) return; setDatosEdicionAnimal({ id: datosDetalleAnimal.id, caravana: datosDetalleAnimal.caravana, rfid: datosDetalleAnimal.rfid || '', categoria: datosDetalleAnimal.categoria, raza: datosDetalleAnimal.raza }); setShowModalEditarAnimal(true); }
  const guardarEdicionAnimal = (e) => { e.preventDefault(); axios.put(`${API_URL}/editar_animal/${datosEdicionAnimal.id}`, datosEdicionAnimal).then(() => { alert("Editado"); setShowModalEditarAnimal(false); setShowModalDetalleAnimal(false); cargarTodo(); }); }
  const confirmarSanidad = (e) => { e.preventDefault(); axios.post(`${API_URL}/gasto_masivo`, datosSanidad).then(res => { alert(res.data.mensaje); setShowModalSanidad(false); cargarTodo(); }); };
  const guardarLluvia = (e) => { e.preventDefault(); axios.post(`${API_URL}/registrar_lluvia`, nuevoRegistroLluvia).then(() => { alert("Lluvia OK"); setShowModalLluvia(false); cargarTodo(); }); };
  const guardarSilo = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_silo`, nuevoSilo).then(() => { alert("Silo OK"); setShowModalNuevoSilo(false); cargarTodo(); }); };
  const abrirCosecha = (lote) => { setNuevaCosecha({ lote_id: lote.lote_id, lote_nombre: lote.lote, kilos: '', destino: 'VENTA', silo_id: '' }); setShowModalCosecha(true); };
  const abrirVentaGrano = (silo) => { setVentaGrano({ silo_id: silo.id, kilos: '', precio_total: '', comprador: '', tipo_grano: silo.contenido, origen: 'SILO' }); setShowModalVentaGrano(true); };
  const confirmarVentaGrano = (e) => { e.preventDefault(); axios.post(`${API_URL}/venta_grano`, ventaGrano).then(() => { alert("Venta OK"); setShowModalVentaGrano(false); cargarTodo(); }); };

  const totalEstimadoBaja = (datosBaja.kilos && datosBaja.precio) ? (parseFloat(datosBaja.kilos) * parseFloat(datosBaja.precio)).toLocaleString() : '0';

  return (
    <div style={{ fontFamily: 'Segoe UI, sans-serif', backgroundColor: '#f1f5f9', height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      
      {isMobile && (
          <div style={{height: '60px', background:'#0f172a', padding:'0 15px', color:'white', display:'flex', justifyContent:'space-between', alignItems:'center', flexShrink: 0, zIndex: 20}}>
              <h2 style={{margin:0, color:'#4ade80', fontSize:'1.2rem'}}>AgroNexo ☁️</h2>
              <button onClick={() => setMenuAbierto(!menuAbierto)} style={{background:'transparent', border:'none', color:'white'}}>
                  {menuAbierto ? <X size={28}/> : <Menu size={28}/>}
              </button>
          </div>
      )}

      {/* SIDEBAR */}
      <div style={{display: 'flex', flex: 1, overflow: 'hidden', position: 'relative'}}>
          <div style={{
              width: '250px', height: '100%', background: '#0f172a', color: 'white', display: 'flex', flexDirection: 'column', padding: '20px', gap: '10px',
              position: isMobile ? 'absolute' : 'relative', left: isMobile ? (menuAbierto ? 0 : '-100%') : 0, zIndex: 30, transition: 'left 0.3s ease',
              boxShadow: isMobile ? '2px 0 10px rgba(0,0,0,0.5)' : 'none',
              overflowY: 'auto'
          }}>
             {!isMobile && <h2 style={{color:'#4ade80', marginBottom:'30px'}}>AgroNexo ☁️</h2>}
             <button onClick={() => cambiarSeccion('DASHBOARD')} style={{...btnMenu, background: seccion === 'DASHBOARD' ? '#1e293b' : 'transparent'}}><LayoutDashboard size={20}/> Resumen / Inicio</button>
             <button onClick={() => cambiarSeccion('MAPA')} style={{...btnMenu, background: seccion === 'MAPA' ? '#1e293b' : 'transparent'}}><MapPin size={20}/> Mapa General</button>
             <button onClick={() => cambiarSeccion('AGRICULTURA')} style={{...btnMenu, background: seccion === 'AGRICULTURA' ? '#1e293b' : 'transparent'}}><Sprout size={20}/> Agricultura</button>
             <button onClick={() => cambiarSeccion('GANADERIA')} style={{...btnMenu, background: seccion === 'GANADERIA' ? '#1e293b' : 'transparent'}}><Tractor size={20}/> Ganadería</button>
             <button onClick={() => setShowModalLluvia(true)} style={{...btnMenu, color:'#93c5fd'}}><CloudLightning size={20}/> Registrar Lluvia</button>
             <button onClick={() => setShowModalConfigRepro(true)} style={{...btnMenu, color:'#f472b6'}}><Settings size={20}/> Config. Repro</button>
             <button onClick={descargarExcel} style={{...btnMenu, marginTop:'10px', color:'#38bdf8'}}><FileDown size={20}/> Exportar Reporte</button>
             
             {/* ⚠️ BOTÓN DE RESET TOTAL */}
             <div style={{marginTop:'auto', borderTop:'1px solid #334155', paddingTop:'20px'}}>
                 <button onClick={resetFabrica} style={{...btnMenu, color:'#ef4444', border:'1px solid #ef4444', justifyContent:'center', fontWeight:'bold'}}><AlertTriangle size={18}/> RESET FÁBRICA</button>
             </div>
             
             <div style={{marginTop: '10px', borderTop:'1px solid #334155', paddingTop:'20px', marginBottom: '80px'}}>
                 <button onClick={() => setRol(rol === 'PRODUCTOR' ? 'PROPIETARIO' : 'PRODUCTOR')} style={{...btnMenu, fontSize:'0.8rem', background:'#334155'}}><RefreshCw size={14}/> Modo: {rol}</button>
            </div>
          </div>

          {isMobile && menuAbierto && (<div onClick={() => setMenuAbierto(false)} style={{position:'absolute', top:0, left:0, width:'100%', height:'100%', background:'rgba(0,0,0,0.5)', zIndex: 25}}></div>)}

          <main style={{flex: 1, position: 'relative', display: 'flex', flexDirection: 'column', background: '#f1f5f9', overflowY: seccion === 'MAPA' ? 'hidden' : 'auto'}}>
              
              {/* SECCIÓN DASHBOARD */}
              {seccion === 'DASHBOARD' && (<div style={{padding: '20px', paddingBottom: '80px'}}><h1 style={{color:'#1e293b', fontSize: isMobile ? '1.5rem' : '2rem', marginBottom:'20px'}}>Hola, Productor 👋</h1><div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(250px, 1fr))', gap:'20px'}}><div style={{background:'white', padding:'20px', borderRadius:'15px', boxShadow:'0 2px 5px rgba(0,0,0,0.05)', borderLeft:'5px solid #22c55e'}}><div style={{display:'flex', alignItems:'center', gap:'10px', color:'#64748b'}}><Tractor size={20}/> <span style={{fontWeight:'bold'}}>Hacienda Activa</span></div><div style={{fontSize:'2.5rem', fontWeight:'bold', color:'#0f172a', margin:'10px 0'}}>{dashboardData.cabezas} <span style={{fontSize:'1rem', color:'#64748b'}}>cabezas</span></div><button onClick={()=>cambiarSeccion('GANADERIA')} style={{...btnOutline, width:'auto', fontSize:'0.8rem'}}>Ver Animales</button></div><div style={{background:'white', padding:'20px', borderRadius:'15px', boxShadow:'0 2px 5px rgba(0,0,0,0.05)', borderLeft:'5px solid #f97316'}}><div style={{display:'flex', alignItems:'center', gap:'10px', color:'#64748b'}}><Warehouse size={20}/> <span style={{fontWeight:'bold'}}>Stock Acopio</span></div><div style={{fontSize:'2.5rem', fontWeight:'bold', color:'#0f172a', margin:'10px 0'}}>{(dashboardData.stock_granos / 1000).toFixed(1)} <span style={{fontSize:'1rem', color:'#64748b'}}>Ton</span></div><small style={{color:'#94a3b8'}}>En {silos.length} silos/bolsas</small></div><div style={{background:'white', padding:'20px', borderRadius:'15px', boxShadow:'0 2px 5px rgba(0,0,0,0.05)', borderLeft:'5px solid #eab308'}}><div style={{display:'flex', alignItems:'center', gap:'10px', color:'#64748b'}}><Sprout size={20}/> <span style={{fontWeight:'bold'}}>Superficie Cargada</span></div><div style={{fontSize:'2.5rem', fontWeight:'bold', color:'#0f172a', margin:'10px 0'}}>{dashboardData.hectareas} <span style={{fontSize:'1rem', color:'#64748b'}}>has</span></div><button onClick={()=>cambiarSeccion('AGRICULTURA')} style={{...btnOutline, width:'auto', fontSize:'0.8rem'}}>Ver Lotes</button></div><div style={{background:'white', padding:'20px', borderRadius:'15px', boxShadow:'0 2px 5px rgba(0,0,0,0.05)', borderLeft:'5px solid #3b82f6'}}><div style={{display:'flex', alignItems:'center', gap:'10px', color:'#64748b'}}><DollarSign size={20}/> <span style={{fontWeight:'bold'}}>Finanzas (Este Mes)</span></div><div style={{marginTop:'10px'}}><div style={{display:'flex', justifyContent:'space-between', fontSize:'0.9rem', color:'#ef4444'}}><span>Gastos:</span> <strong>$ {dashboardData.gastos_mes.toLocaleString()}</strong></div><div style={{display:'flex', justifyContent:'space-between', fontSize:'0.9rem', color:'#16a34a', marginTop:'5px'}}><span>Margen Ventas:</span> <strong>$ {dashboardData.margen_mes.toLocaleString()}</strong></div></div></div></div></div>)}
              {/* SECCIÓN MAPA Y AGRICULTURA IGUAL QUE ANTES (Omitido para brevedad, mantener código anterior) */}
              {seccion === 'MAPA' && (<div style={{flex: 1, width: '100%', height: '100%', zIndex: 1}}><MapContainer center={[-26.78, -60.85]} zoom={11} style={{ height: '100%', width: '100%' }}><TileLayer url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}" /><ClickEnMapa />{tempPos && (<Marker position={tempPos}><Popup><div style={{textAlign:'center', display:'flex', flexDirection:'column', gap:'5px'}}><strong>¿Qué quieres crear aquí?</strong><button onClick={()=>iniciarCargaDesdeMapa('LOTE')} style={{...btnAzul, padding:'5px', fontSize:'0.8rem'}}>🌱 Nuevo Lote</button><button onClick={()=>iniciarCargaDesdeMapa('SILO')} style={{...btnAzul, background:'#f97316', padding:'5px', fontSize:'0.8rem'}}>🏭 Nuevo Silo</button></div></Popup></Marker>)}{lotes.map(lote => (lote.lat && (<Marker key={lote.id} position={[lote.lat, lote.lng]}><Popup><div style={{textAlign:'center'}}><strong style={{fontSize:'1rem'}}>{lote.lote}</strong><br/>{lote.hectareas} Has</div></Popup></Marker>)))}{silos.map(s => (s.lat && (<Marker key={`silo-${s.id}`} position={[s.lat, s.lng]} icon={SiloIcon}><Popup><div style={{textAlign:'center'}}><strong style={{fontSize:'1.1rem', color:'#f97316'}}>{s.nombre}</strong><br/>{(s.kilos_actuales / 1000).toFixed(1)} Ton</div></Popup></Marker>)))}</MapContainer></div>)}
              {seccion === 'AGRICULTURA' && (<div style={{padding: '20px', paddingBottom: '80px'}}><div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'20px'}}><h1 style={{color:'#1e293b', fontSize: isMobile ? '1.5rem' : '2rem'}}>Agricultura</h1><div style={{display:'flex', gap:'10px'}}><button onClick={() => setShowModalNuevoSilo(true)} style={{...btnOutline, width:'auto', borderColor:'#f97316', color:'#f97316'}}><Factory size={20}/> <span style={{display: isMobile ? 'none' : 'inline'}}>Nuevo Silo</span></button><button onClick={abrirNuevoLote} style={btnAzul}><PlusCircle size={20}/> Nuevo Lote</button></div></div><div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>{lotes.map((item) => { return ( <div key={item.id} style={cardEstilo}><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}> <div><h3 style={{margin:0, color:'#0f172a', fontWeight:'bold', fontSize:'1.2rem'}}>{item.lote}</h3><span style={tagEstilo}>{item.tipo}</span></div> <div style={{display:'flex', gap:'5px'}}> <button onClick={(e) => {e.stopPropagation(); abrirEditarLote(item)}} style={{...btnIcon, color:'#3b82f6'}}><Edit size={18}/></button> <button onClick={(e) => {e.stopPropagation(); eliminarLote(item.lote_id)}} style={{...btnIcon, color:'#ef4444'}}><Trash2 size={18}/></button> </div> </div><div style={{background:'#f0fdf4', padding:'10px', borderRadius:'8px', margin:'10px 0'}}> <div style={{display:'flex', justifyContent:'space-between', fontSize:'0.9rem'}}><span>🌱 Cosecha:</span><strong>{item.total_cosechado.toLocaleString()} kg</strong></div> </div><div style={{display:'flex', gap:'10px'}}> <button onClick={(e) => {e.stopPropagation(); abrirCosecha(item)}} style={btnOutline}><Truck size={16}/> Cosecha</button> <button onClick={(e) => {e.stopPropagation(); abrirGasto('LOTE', item)}} style={{...btnOutline, borderColor:'#dc2626', color:'#dc2626'}}><DollarSign size={16}/> Gasto</button> </div></div> )})}</div></div>)}
              {seccion === 'GANADERIA' && (
                  <div style={{padding: '20px', paddingBottom: '80px'}}>
                        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'20px'}}>
                            <h1 style={{color:'#1e293b', fontSize: isMobile ? '1.5rem' : '2rem'}}>Ganadería</h1>
                            <div style={{display:'flex', gap:'10px'}}>
                                <button onClick={() => setShowModalSanidad(true)} style={{...btnOutline, width:'auto', borderColor:'#16a34a', color:'#16a34a'}}><Syringe size={20}/> <span style={{display: isMobile ? 'none' : 'inline'}}>Sanidad</span></button>
                                <button onClick={() => {setModoSeleccion(!modoSeleccion); setAnimalesSeleccionados([])}} style={{...btnOutline, width:'auto', background: modoSeleccion ? '#e0f2fe' : 'white'}}><ArrowRightLeft size={20}/> <span style={{display: isMobile ? 'none' : 'inline'}}>{modoSeleccion ? 'Cancelar' : 'Rotar'}</span></button>
                                <button onClick={() => setShowModalAnimal(true)} style={btnAzul}><PlusCircle size={20}/> Nuevo</button>
                            </div>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                            {animales.map((vaca) => (
                                <div key={vaca.id} style={{...cardEstilo, border: animalesSeleccionados.includes(vaca.id) ? '2px solid #2563eb' : 'none'}} onClick={() => abrirDetalleAnimal(vaca)}>
                                    <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
                                        <div style={{display:'flex', alignItems:'center', gap:'10px'}}>
                                            {modoSeleccion && (<div style={{color: animalesSeleccionados.includes(vaca.id) ? '#2563eb' : '#cbd5e1'}}>{animalesSeleccionados.includes(vaca.id) ? <CheckSquare size={24}/> : <Square size={24}/>}</div>)}
                                            <h2 style={{margin:0, color:'#0f172a', fontSize:'1.1rem'}}>{vaca.caravana}</h2>
                                        </div>
                                        <span style={{...tagEstilo, background:'#ecfccb', color:'#3f6212'}}>{vaca.categoria}</span>
                                    </div>
                                    <div style={{background:'#f8fafc', padding:'15px', borderRadius:'10px', margin:'15px 0'}}> 
                                        <div style={{display:'flex', justifyContent:'space-between', marginBottom:'5px', fontSize:'0.9rem'}}><span style={{color:'#64748b'}}>Ubicación:</span><strong style={{color:'#2563eb'}}>{vaca.ubicacion || 'Sin Lote'}</strong></div>
                                        <div style={{display:'flex', justifyContent:'space-between'}}><span style={{color:'#64748b'}}>Peso:</span><strong style={{fontSize:'1.1rem'}}>{vaca.peso_actual} kg</strong></div> 
                                    </div>
                                    <div style={{display:'flex', gap:'10px'}}>
                                        <button onClick={(e) => {e.stopPropagation(); setNuevoPesaje({animal_id: vaca.id, caravana: vaca.caravana, kilos: '', fecha: ''}); setShowModalPesaje(true)}} style={btnOutline}><Scale size={16}/> Pesar</button>
                                        <button onClick={(e) => {e.stopPropagation(); abrirGasto('ANIMAL', vaca)}} style={{...btnOutline, borderColor:'#dc2626', color:'#dc2626'}}><DollarSign size={16}/> Gasto</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                  </div>
              )}

              {/* 🆕 MODAL DE BAJA / VENTA MEJORADO */}
              {showModalBaja && (
                  <div style={modalBackdrop} onClick={()=>setShowModalBaja(false)}>
                      <div style={modalContent} onClick={e=>e.stopPropagation()}>
                          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'15px'}}>
                              <h3 style={{margin:0, color:'#ef4444'}}>Dar de Baja / Vender</h3>
                              <button onClick={()=>setShowModalBaja(false)} style={btnIcon}><X size={24}/></button>
                          </div>
                          <form onSubmit={confirmarBaja} style={formStyle}>
                              <label style={labelStyle}>Motivo de Baja:</label>
                              <select style={inputStyle} value={datosBaja.motivo} onChange={e=>setDatosBaja({...datosBaja, motivo:e.target.value})}>
                                  <option value="VENTA">💰 Venta</option>
                                  <option value="CONSUMO">🍖 Consumo Propio</option>
                                  <option value="MUERTE">💀 Muerte</option>
                                  <option value="ROBO">👮 Robo / Abigeato</option>
                                  <option value="DONACION">🎁 Donación</option>
                              </select>

                              {datosBaja.motivo === 'VENTA' ? (
                                  <>
                                      <label style={labelStyle}>Comprador:</label>
                                      <input style={inputStyle} placeholder="Nombre del comprador" value={datosBaja.comprador} onChange={e=>setDatosBaja({...datosBaja, comprador:e.target.value})} required/>
                                      <label style={labelStyle}>Kilos Totales:</label>
                                      <input style={inputStyle} type="number" placeholder="Kg" value={datosBaja.kilos} onChange={e=>setDatosBaja({...datosBaja, kilos:e.target.value})} required/>
                                      <label style={labelStyle}>Precio por Kg ($):</label>
                                      <input style={inputStyle} type="number" placeholder="$" value={datosBaja.precio} onChange={e=>setDatosBaja({...datosBaja, precio:e.target.value})} required/>
                                      <div style={{textAlign:'right', marginTop:'5px', color:'#16a34a', fontWeight:'bold'}}>Total: $ {totalEstimadoBaja}</div>
                                  </>
                              ) : (
                                  <>
                                      <label style={labelStyle}>Detalles / Observaciones:</label>
                                      <textarea style={inputStyle} placeholder="Causa de muerte, denuncia policial, etc." value={datosBaja.detalle} onChange={e=>setDatosBaja({...datosBaja, detalle:e.target.value})}></textarea>
                                  </>
                              )}
                              <button style={{...btnAzul, background:'#ef4444'}}>Confirmar Baja</button>
                          </form>
                      </div>
                  </div>
              )}

              {/* MODALES RESTANTES (Se mantienen igual) */}
              {showModalEditarAnimal && (<div style={modalBackdrop} onClick={()=>setShowModalEditarAnimal(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><div style={{display:'flex', justifyContent:'space-between', marginBottom:'15px'}}><h3 style={{color:'#0f172a'}}>Editar Animal</h3><button onClick={()=>setShowModalEditarAnimal(false)} style={btnIcon}><X color="#000"/></button></div><form onSubmit={guardarEdicionAnimal} style={formStyle}><label style={labelStyle}>Caravana (RP):</label><input value={datosEdicionAnimal.caravana} onChange={e=>setDatosEdicionAnimal({...datosEdicionAnimal, caravana:e.target.value})} style={inputStyle} required/><label style={labelStyle}>RFID:</label><input value={datosEdicionAnimal.rfid} onChange={e=>setDatosEdicionAnimal({...datosEdicionAnimal, rfid:e.target.value})} style={inputStyle}/><label style={labelStyle}>Categoría:</label><select value={datosEdicionAnimal.categoria} onChange={e=>setDatosEdicionAnimal({...datosEdicionAnimal, categoria:e.target.value})} style={inputStyle}><option>Ternero</option><option>Novillo</option><option>Vaca</option><option>Vaquillona</option><option>Toro</option></select><label style={labelStyle}>Raza:</label><select value={datosEdicionAnimal.raza} onChange={e=>setDatosEdicionAnimal({...datosEdicionAnimal, raza:e.target.value})} style={inputStyle}><option>Braford</option><option>Brangus</option><option>Angus</option><option>Hereford</option></select><button style={btnAzul}>Guardar Cambios</button></form></div></div>)}
              {showModalDetalleAnimal && (
                  <div style={modalBackdrop} onClick={()=>setShowModalDetalleAnimal(false)}>
                      <div style={{...modalContent, maxWidth:'600px'}} onClick={e=>e.stopPropagation()}>
                          {datosDetalleAnimal ? (
                              <>
                                <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'5px'}}>
                                    <div style={{display:'flex', alignItems:'center', gap:'10px'}}>
                                        <h2 style={{margin:0, color:'#0f172a'}}>RP: {datosDetalleAnimal?.caravana}</h2>
                                        <button onClick={abrirEditarAnimal} style={btnIcon} title="Editar Animal"><Edit size={20} color="#2563eb"/></button>
                                    </div>
                                    <button onClick={()=>setShowModalDetalleAnimal(false)} style={{background:'transparent', border:'none', cursor:'pointer'}}><X size={28} color="#0f172a"/></button>
                                </div>
                                <div style={{color:'#64748b', marginBottom:'20px', fontWeight:'bold', fontSize:'1.1rem'}}>{datosDetalleAnimal?.categoria || 'Sin Categoría'}</div>
                                <div style={{marginBottom:'20px', display:'flex', gap:'10px'}}>
                                    {/* 🆕 BOTÓN NUEVO DE BAJA */}
                                    <button onClick={iniciarBaja} style={{...btnOutline, borderColor:'#ef4444', color:'#ef4444', background:'#fef2f2'}}><ArrowRightLeft size={20}/> Dar de Baja / Vender</button>
                                    <button onClick={iniciarEventoRepro} style={{...btnOutline, borderColor:'#be185d', color:'#be185d', background:'#fdf2f8'}}><Dna size={20}/> Reproducción</button>
                                </div>
                                {/* Resto del modal igual */}
                                <div style={{height:'200px', width:'100%', background:'#f8fafc', borderRadius:'10px', padding:'10px', marginBottom:'20px'}}><h4 style={{margin:'0 0 10px 0', color:'#64748b'}}>Engorde</h4>{datosDetalleAnimal?.historial_pesos && datosDetalleAnimal.historial_pesos.length > 0 ? (<ResponsiveContainer><LineChart data={datosDetalleAnimal.historial_pesos}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="fecha" /><YAxis /><Tooltip /><Line type="monotone" dataKey="kilos" stroke="#16a34a" strokeWidth={3} activeDot={{ r: 8 }} /></LineChart></ResponsiveContainer>) : <div style={sinDatos}>Sin historial de pesos</div>}</div>
                              </>
                          ) : <p style={{color:'#334155'}}>Cargando historia...</p>}
                      </div>
                  </div>
              )}
              {/* RESTO DE MODALES VIEJOS (Lote, Cosecha, etc) - MANTENER IGUAL */}
              {showModalLote && (<div style={modalBackdrop} onClick={()=>setShowModalLote(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><div style={{display:'flex', justifyContent:'space-between'}}><h3 style={{color:'#0f172a'}}>{modoEdicion ? 'Editar Lote' : 'Nuevo Lote'}</h3><button onClick={()=>setShowModalLote(false)} style={btnIcon}><X color="#000"/></button></div><form onSubmit={guardarContrato} style={formStyle}><label style={labelStyle}>Nombre del Lote:</label><input value={nuevoContrato.nombreLote} onChange={e=>setNuevoContrato({...nuevoContrato, nombreLote:e.target.value})} style={inputStyle} required/><label style={labelStyle}>Hectáreas:</label><input type="number" value={nuevoContrato.hectareas} onChange={e=>setNuevoContrato({...nuevoContrato, hectareas:e.target.value})} style={inputStyle} required/><button type="button" onClick={obtenerUbicacion} style={{...btnGris, background:'#0f172a', color:'white', justifyContent:'center'}}><Locate size={18}/> {nuevoContrato.lat ? 'GPS OK' : 'Usar GPS'}</button><label style={labelStyle}>Dueño:</label><input value={nuevoContrato.propietario} onChange={e=>setNuevoContrato({...nuevoContrato, propietario:e.target.value})} style={inputStyle} required/><div style={{display:'flex', gap:'10px'}}><select value={nuevoContrato.tipo} onChange={e=>setNuevoContrato({...nuevoContrato, tipo:e.target.value})} style={{...inputStyle, flex:1}}><option value="APARCERIA">Aparcería</option><option value="PROPIO">Propio</option></select><input placeholder="%" type="number" value={nuevoContrato.porcentaje} onChange={e=>setNuevoContrato({...nuevoContrato, porcentaje:e.target.value})} style={{...inputStyle, width:'80px'}}/></div><button style={btnAzul}>{modoEdicion ? 'Guardar' : 'Crear'}</button><button type="button" onClick={()=>setShowModalLote(false)} style={btnGris}>Cancelar</button></form></div></div>)}
              {showModalCosecha && (<div style={modalBackdrop} onClick={()=>setShowModalCosecha(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><div style={{display:'flex', justifyContent:'space-between'}}><h3 style={{color:'#0f172a'}}>Cargar Camión 🚛</h3><button onClick={()=>setShowModalCosecha(false)} style={btnIcon}><X color="#000"/></button></div><form onSubmit={guardarCosecha} style={formStyle}><label style={labelStyle}>Kilos Netos:</label><input type="number" placeholder="Kg" onChange={e=>setNuevaCosecha({...nuevaCosecha, kilos:e.target.value})} style={inputStyle} autoFocus required/><label style={labelStyle}>Destino de la Carga:</label><div style={{display:'flex', gap:'10px'}}><button type="button" onClick={()=>setNuevaCosecha({...nuevaCosecha, destino:'VENTA'})} style={{...btnOutline, background: nuevaCosecha.destino === 'VENTA' ? '#dbeafe' : 'white', borderColor: nuevaCosecha.destino === 'VENTA' ? '#2563eb' : '#cbd5e1'}}>💰 Venta Directa</button><button type="button" onClick={()=>setNuevaCosecha({...nuevaCosecha, destino:'SILO'})} style={{...btnOutline, background: nuevaCosecha.destino === 'SILO' ? '#ffedd5' : 'white', borderColor: nuevaCosecha.destino === 'SILO' ? '#f97316' : '#cbd5e1'}}>🏭 Acopio / Silo</button></div>{nuevaCosecha.destino === 'SILO' && (<div style={{marginTop:'10px'}}><label style={labelStyle}>Seleccionar Silo:</label><select style={inputStyle} onChange={e=>setNuevaCosecha({...nuevaCosecha, silo_id:e.target.value})} required><option value="">-- Elegir Silo --</option>{silos.map(s => (<option key={s.id} value={s.id}>{s.nombre} ({s.contenido})</option>))}</select></div>)}<button style={btnAzul}>Registrar Carga</button></form></div></div>)}
              {showModalVentaGrano && (<div style={modalBackdrop} onClick={()=>setShowModalVentaGrano(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><div style={{display:'flex', justifyContent:'space-between'}}><h3 style={{color:'#16a34a'}}>Vender Stock 💰</h3><button onClick={()=>setShowModalVentaGrano(false)} style={btnIcon}><X color="#000"/></button></div><form onSubmit={confirmarVentaGrano} style={formStyle}><div style={{background:'#f0fdf4', padding:'10px', borderRadius:'8px', fontSize:'0.9rem', color:'#166534', border:'1px solid #bbf7d0', marginBottom:'10px'}}>Vendiendo {ventaGrano.tipo_grano} desde Silo.</div><label style={labelStyle}>Comprador:</label><input placeholder="Ej: AFA" value={ventaGrano.comprador} onChange={e=>setVentaGrano({...ventaGrano, comprador:e.target.value})} style={inputStyle} required/><label style={labelStyle}>Kilos a Vender:</label><input type="number" placeholder="Kg" value={ventaGrano.kilos} onChange={e=>setVentaGrano({...ventaGrano, kilos:e.target.value})} style={inputStyle} required/><label style={labelStyle}>Precio Total ($):</label><input type="number" placeholder="$" value={ventaGrano.precio_total} onChange={e=>setVentaGrano({...ventaGrano, precio_total:e.target.value})} style={inputStyle} required/><button style={{...btnAzul, background:'#16a34a'}}>Confirmar Venta</button></form></div></div>)}
              {showModalNuevoSilo && (<div style={modalBackdrop} onClick={()=>setShowModalNuevoSilo(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><h3 style={{color:'#f97316'}}>Nuevo Silo / Acopio</h3><form onSubmit={guardarSilo} style={formStyle}><label style={labelStyle}>Nombre:</label><input placeholder="Ej: Silobolsa Soja 2024" value={nuevoSilo.nombre} onChange={e=>setNuevoSilo({...nuevoSilo, nombre:e.target.value})} style={inputStyle} required/><label style={labelStyle}>Tipo:</label><select style={inputStyle} value={nuevoSilo.tipo} onChange={e=>setNuevoSilo({...nuevoSilo, tipo:e.target.value})}><option>SILOBOLSA</option><option>CELDA</option><option>SILO FIJO</option></select><label style={labelStyle}>Contenido (Grano):</label><select style={inputStyle} value={nuevoSilo.contenido} onChange={e=>setNuevoSilo({...nuevoSilo, contenido:e.target.value})}><option>SOJA</option><option>MAIZ</option><option>GIRASOL</option><option>TRIGO</option><option>SORGO</option></select><label style={labelStyle}>Capacidad Max (Tn):</label><input type="number" placeholder="Ej: 200" value={nuevoSilo.capacidad} onChange={e=>setNuevoSilo({...nuevoSilo, capacidad:e.target.value})} style={inputStyle} required/><button type="button" onClick={obtenerUbicacion} style={{...btnGris, background:'#0f172a', color:'white', justifyContent:'center'}}><Locate size={18}/> {nuevoSilo.lat ? 'GPS Detectado' : 'Usar GPS'}</button><button style={{...btnAzul, background:'#f97316'}}>Crear Silo</button></form></div></div>)}
              {showModalPesaje && (<div style={modalBackdrop} onClick={()=>setShowModalPesaje(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><div style={{display:'flex', justifyContent:'space-between'}}><h3 style={{color:'#0f172a'}}>Nuevo Pesaje</h3><button onClick={()=>setShowModalPesaje(false)} style={btnIcon}><X color="#000"/></button></div><form onSubmit={guardarPesaje} style={formStyle}><label style={labelStyle}>Fecha:</label><input type="date" onChange={e=>setNuevoPesaje({...nuevoPesaje, fecha:e.target.value})} style={inputStyle}/><label style={labelStyle}>Kilos:</label><input type="number" placeholder="Kilos" onChange={e=>setNuevoPesaje({...nuevoPesaje, kilos:e.target.value})} style={inputStyle} autoFocus required/><button style={btnAzul}>Registrar</button><button type="button" onClick={()=>setShowModalPesaje(false)} style={btnGris}>Cancelar</button></form></div></div>)}
              {showModalGasto && (<div style={modalBackdrop} onClick={()=>setShowModalGasto(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><div style={{display:'flex', justifyContent:'space-between'}}><h3 style={{color:'#dc2626'}}>💸 Nuevo Gasto</h3><button onClick={()=>setShowModalGasto(false)} style={btnIcon}><X color="#000"/></button></div><form onSubmit={guardarGasto} style={formStyle}><label style={labelStyle}>Fecha:</label><input type="date" onChange={e=>setNuevoGasto({...nuevoGasto, fecha:e.target.value})} style={inputStyle}/><label style={labelStyle}>Concepto:</label><input placeholder="Ej: Semillas" onChange={e=>setNuevoGasto({...nuevoGasto, concepto:e.target.value})} style={inputStyle} autoFocus required/><label style={labelStyle}>Monto:</label><input type="number" placeholder="$" onChange={e=>setNuevoGasto({...nuevoGasto, monto:e.target.value})} style={inputStyle} required/><select onChange={e=>setNuevoGasto({...nuevoGasto, categoria:e.target.value})} style={inputStyle}><option value="INSUMO">Insumo</option><option value="LABOR">Labor</option><option value="SANITARIO">Sanitario</option></select><button style={{...btnAzul, background:'#dc2626'}}>Registrar Gasto</button><button type="button" onClick={()=>setShowModalGasto(false)} style={btnGris}>Cancelar</button></form></div></div>)}
              {showModalLluvia && (<div style={modalBackdrop} onClick={()=>setShowModalLluvia(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'15px'}}><h3 style={{margin:0, color:'#2563eb'}}>Registrar Lluvia 🌧️</h3><button onClick={()=>setShowModalLluvia(false)} style={btnIcon}><X size={24} color="#0f172a"/></button></div><form onSubmit={guardarLluvia} style={formStyle}><label style={labelStyle}>Fecha:</label><input type="date" value={nuevoRegistroLluvia.fecha} onChange={e=>setNuevoRegistroLluvia({...nuevoRegistroLluvia, fecha:e.target.value})} style={inputStyle}/><label style={labelStyle}>Lote / Campo:</label><select style={inputStyle} value={nuevoRegistroLluvia.lote_id} onChange={e=>setNuevoRegistroLluvia({...nuevoRegistroLluvia, lote_id:e.target.value})} required><option value="">-- Seleccionar --</option>{lotes.map(l => <option key={l.id} value={l.lote_id}>{l.lote}</option>)}</select><label style={labelStyle}>Milímetros (mm):</label><input type="number" placeholder="Ej: 45" value={nuevoRegistroLluvia.milimetros} onChange={e=>setNuevoRegistroLluvia({...nuevoRegistroLluvia, milimetros:e.target.value})} style={inputStyle} required/><button style={{...btnAzul, background:'#2563eb'}}>Guardar Lluvia</button></form></div></div>)}
              {showModalRepro && (<div style={modalBackdrop} onClick={()=>setShowModalRepro(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'15px'}}><h3 style={{margin:0, color:'#be185d'}}>Nuevo Evento Reproductivo 🧬</h3><button onClick={()=>setShowModalRepro(false)} style={btnIcon}><X size={24} color="#0f172a"/></button></div><form onSubmit={guardarEventoRepro} style={formStyle}><label style={labelStyle}>Fecha:</label><input type="date" onChange={e=>setNuevoEventoRepro({...nuevoEventoRepro, fecha:e.target.value})} style={inputStyle}/><label style={labelStyle}>Tipo de Evento:</label><select style={inputStyle} value={nuevoEventoRepro.tipo} onChange={e=>{const t = e.target.value; setNuevoEventoRepro({...nuevoEventoRepro, tipo:t, detalle: t==='TACTO'?'POSITIVO':''});}}><option value="INSEMINACION">Inseminación (IA)</option><option value="TACTO">Tacto / Diagnóstico</option><option value="PARTO">Parto</option></select>{nuevoEventoRepro.tipo === 'INSEMINACION' && (<><label style={labelStyle}>Detalle (Toro/Pajuela):</label><input placeholder="Ej: Toro Campeón 001" onChange={e=>setNuevoEventoRepro({...nuevoEventoRepro, detalle:e.target.value})} style={inputStyle} required/></>)}{nuevoEventoRepro.tipo === 'TACTO' && (<><label style={labelStyle}>Resultado:</label><select style={inputStyle} onChange={e=>setNuevoEventoRepro({...nuevoEventoRepro, detalle:e.target.value})}><option value="POSITIVO">Positivo (Preñada)</option><option value="NEGATIVO">Negativo (Vacía)</option></select></>)}{nuevoEventoRepro.tipo === 'PARTO' && (<><label style={labelStyle}>Detalle Cría:</label><input placeholder="Ej: Macho 35kg" onChange={e=>setNuevoEventoRepro({...nuevoEventoRepro, detalle:e.target.value})} style={inputStyle} required/></>)}<button style={{...btnAzul, background:'#be185d'}}>Registrar Evento</button></form></div></div>)}
              {modoSeleccion && animalesSeleccionados.length > 0 && (<div style={{position:'fixed', bottom:0, left:0, width:'100%', background:'white', padding:'15px', borderTop:'1px solid #cbd5e1', display:'flex', justifyContent:'space-between', alignItems:'center', zIndex:3000, boxShadow:'0 -2px 10px rgba(0,0,0,0.1)'}}><strong style={{color:'#0f172a'}}>{animalesSeleccionados.length} seleccionados</strong><div style={{display:'flex', gap:'10px'}}><button onClick={()=>setShowModalReproMasivo(true)} style={{...btnOutline, borderColor:'#be185d', color:'#be185d', background:'#fdf2f8'}}><Dna size={18}/> Inseminar / Repro</button><button onClick={iniciarMovimiento} style={btnAzul}>Mover <ArrowRightLeft size={18}/></button></div></div>)}
              {showModalReproMasivo && (<div style={modalBackdrop} onClick={()=>setShowModalReproMasivo(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'15px'}}><h3 style={{margin:0, color:'#be185d'}}>Inseminación Masiva 🧬</h3><button onClick={()=>setShowModalReproMasivo(false)} style={btnIcon}><X size={24} color="#0f172a"/></button></div><p style={{color:'#334155'}}>Aplicar a <strong>{animalesSeleccionados.length} animales</strong>.</p><form onSubmit={confirmarReproMasivo} style={formStyle}><label style={labelStyle}>Fecha:</label><input type="date" onChange={e=>setDatosReproMasivo({...datosReproMasivo, fecha:e.target.value})} style={inputStyle}/><label style={labelStyle}>Tipo de Evento:</label><select style={inputStyle} value={datosReproMasivo.tipo} onChange={e=>{const t = e.target.value; setDatosReproMasivo({...datosReproMasivo, tipo:t, detalle: t==='TACTO'?'POSITIVO':''});}}><option value="INSEMINACION">Inseminación (IA)</option><option value="TACTO">Tacto / Diagnóstico</option><option value="PARTO">Parto</option></select>{datosReproMasivo.tipo === 'INSEMINACION' && (<><label style={labelStyle}>Detalle (Toro/Pajuela):</label><input placeholder="Ej: Toro Campeón 001" onChange={e=>setDatosReproMasivo({...datosReproMasivo, detalle:e.target.value})} style={inputStyle} required/></>)}{datosReproMasivo.tipo === 'TACTO' && (<><label style={labelStyle}>Resultado:</label><select style={inputStyle} onChange={e=>setDatosReproMasivo({...datosReproMasivo, detalle:e.target.value})}><option value="POSITIVO">Positivo (Preñada)</option><option value="NEGATIVO">Negativo (Vacía)</option></select></>)}<button style={{...btnAzul, background:'#be185d'}}>Confirmar Evento Masivo</button></form></div></div>)}
              {showModalConfigRepro && (<div style={modalBackdrop} onClick={()=>setShowModalConfigRepro(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'15px'}}><h3 style={{margin:0, color:'#be185d'}}>Configuración Repro ⚙️</h3><button onClick={()=>setShowModalConfigRepro(false)} style={btnIcon}><X size={24} color="#0f172a"/></button></div><form onSubmit={guardarConfigRepro} style={formStyle}><label style={labelStyle}>¿Qué deseas crear?</label><select style={inputStyle} value={nuevoItemConfig.tipo_objeto} onChange={e=>setNuevoItemConfig({...nuevoItemConfig, tipo_objeto:e.target.value})}><option value="TORO">Toro / Semen</option><option value="PROTOCOLO">Protocolo IATF</option></select><label style={labelStyle}>Nombre:</label><input placeholder={nuevoItemConfig.tipo_objeto==='TORO'?"Ej: Toro Campeón":"Ej: IATF Convencional"} value={nuevoItemConfig.nombre} onChange={e=>setNuevoItemConfig({...nuevoItemConfig, nombre:e.target.value})} style={inputStyle} required/>{nuevoItemConfig.tipo_objeto === 'TORO' ? (<><label style={labelStyle}>Tipo:</label><select style={inputStyle} onChange={e=>setNuevoItemConfig({...nuevoItemConfig, tipo:e.target.value})}><option value="SEMEN_CONVENCIONAL">Semen Convencional</option><option value="SEMEN_SEXADO">Semen Sexado</option><option value="TORO_NATURAL">Toro Natural</option></select><label style={labelStyle}>Raza:</label><input placeholder="Ej: Braford" onChange={e=>setNuevoItemConfig({...nuevoItemConfig, raza:e.target.value})} style={inputStyle}/></>) : (<><label style={labelStyle}>Descripción:</label><input placeholder="Detalles de hormonas..." onChange={e=>setNuevoItemConfig({...nuevoItemConfig, descripcion:e.target.value})} style={inputStyle}/></>)}<label style={labelStyle}>Costo Estimado ($):</label><input type="number" placeholder="$ por Dosis/Cabeza" onChange={e=>setNuevoItemConfig({...nuevoItemConfig, costo:e.target.value})} style={inputStyle} required/><button style={{...btnAzul, background:'#be185d'}}>Guardar Configuración</button></form><div style={{marginTop:'20px', borderTop:'1px solid #ccc', paddingTop:'10px'}}><small style={{fontWeight:'bold', color:'#555'}}>Existentes:</small><ul style={{fontSize:'0.8rem', color:'#666', paddingLeft:'20px'}}>{configRepro.toros.map(t=><li key={`t-${t.id}`}>🐂 {t.nombre}</li>)}{configRepro.protocolos.map(p=><li key={`p-${p.id}`}>📋 {p.nombre} (${p.costo})</li>)}</ul></div></div></div>)}
          </main>
      </div>
    </div>
  );
}

// Estilos
const btnMenu = { width:'100%', padding:'10px', border:'none', color:'white', textAlign:'left', cursor:'pointer', display:'flex', gap:'10px', alignItems:'center', borderRadius:'8px' };
const btnAzul = { background: '#2563eb', color:'white', border:'none', padding:'10px 20px', borderRadius:'8px', cursor:'pointer', display:'flex', gap:'5px', fontWeight:'bold' };
const btnGris = { background: '#94a3b8', color:'white', border:'none', padding:'10px', borderRadius:'8px', cursor:'pointer', display:'flex', alignItems:'center', gap:'5px' };
const btnOutline = { background: 'white', color:'#2563eb', border:'1px solid #2563eb', padding:'8px', borderRadius:'8px', cursor:'pointer', width:'100%', display:'flex', justifyContent:'center', gap:'5px', fontWeight:'bold' };
const btnIcon = { background: 'transparent', border:'none', cursor:'pointer', padding:'5px' };
const cardEstilo = { background: 'white', padding: '20px', borderRadius: '15px', boxShadow: '0 2px 5px rgba(0,0,0,0.05)', cursor:'pointer', transition: 'transform 0.1s' };
const tagEstilo = { background: '#dbeafe', color: '#1e40af', padding: '2px 8px', borderRadius: '15px', fontSize:'0.75rem', fontWeight:'bold', marginTop:'2px', display:'inline-block' };
const sinDatos = { height:'100%', display:'flex', alignItems:'center', justifyContent:'center', border:'2px dashed #e2e8f0', color:'#94a3b8', borderRadius:'10px' };
const modalBackdrop = { position:'fixed', top:0, left:0, width:'100%', height:'100%', background:'rgba(0,0,0,0.5)', display:'flex', justifyContent:'center', alignItems:'center', zIndex:2000 };
const modalContent = { background:'white', padding:'30px', borderRadius:'15px', width:'90%', maxWidth:'400px', maxHeight: '90vh', overflowY: 'auto' };
const formStyle = { display:'flex', flexDirection:'column', gap:'10px', marginTop:'20px' };
const inputStyle = { padding:'12px', borderRadius:'8px', border:'1px solid #cbd5e1', backgroundColor: '#ffffff', color: '#1e293b', width: '100%', boxSizing: 'border-box' };
const labelStyle = { display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#334155', fontSize: '0.9rem' };

export default App;