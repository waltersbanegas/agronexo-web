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
  
  // Modales
  const [showModalLote, setShowModalLote] = useState(false);
  const [showModalCosecha, setShowModalCosecha] = useState(false);
  const [showModalAnimal, setShowModalAnimal] = useState(false);
  const [showModalPesaje, setShowModalPesaje] = useState(false);
  const [showModalGasto, setShowModalGasto] = useState(false); 
  const [showModalDetalleAnimal, setShowModalDetalleAnimal] = useState(false);
  const [showModalMover, setShowModalMover] = useState(false); 
  const [showModalBaja, setShowModalBaja] = useState(false); 
  const [showModalSanidad, setShowModalSanidad] = useState(false); 
  const [showModalLluvia, setShowModalLluvia] = useState(false);
  const [showModalNuevoSilo, setShowModalNuevoSilo] = useState(false);
  const [showModalVentaGrano, setShowModalVentaGrano] = useState(false);
  const [showModalRepro, setShowModalRepro] = useState(false);
  const [showModalReproMasivo, setShowModalReproMasivo] = useState(false);
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
  const [datosBaja, setDatosBaja] = useState({ animal_id: null, motivo: 'VENTA', comprador: '', detalle: '', kilos: '', precio: '' });
  const [datosSanidad, setDatosSanidad] = useState({ lote_id: 'all', concepto: '', monto: '', fecha: '' });
  const [nuevoRegistroLluvia, setNuevoRegistroLluvia] = useState({ lote_id: '', milimetros: '', fecha: '' });
  const [nuevoEventoRepro, setNuevoEventoRepro] = useState({ animal_id: null, tipo: 'INSEMINACION', detalle: '', fecha: '', protocolo_id: '', genetica_id: '', condicion_corporal: '' });
  const [datosReproMasivo, setDatosReproMasivo] = useState({ tipo: 'INSEMINACION', detalle: '', fecha: '', protocolo_id: '', genetica_id: '' });

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const cargarTodo = () => {
    axios.get(`${API_URL}/liquidaciones`).then(res => { setLotes(res.data); if(res.data.length > 0) cargarClima(res.data[0].lat, res.data[0].lng, res.data[0].lote); }).catch(e => console.error("Error Lotes"));
    axios.get(`${API_URL}/animales`).then(res => setAnimales(res.data)).catch(e => console.error("Error Animales"));
    axios.get(`${API_URL}/silos`).then(res => setSilos(res.data)).catch(e => console.error("Error Silos"));
    axios.get(`${API_URL}/resumen_general`).then(res => setDashboardData(res.data)).catch(e => console.error("Error Resumen"));
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

  const resetFabrica = () => {
      if(window.confirm("⚠️ ¿ESTÁS SEGURO?\n\nEsto borrará ABSOLUTAMENTE TODOS los datos.\n\n¿Deseas continuar?")) {
          axios.post(`${API_URL}/reset_fabrica`).then(res => {
              alert(res.data.mensaje);
              window.location.reload();
          }).catch(err => alert("Error: " + err.message));
      }
  }

  const abrirDetalleAnimal = (vaca) => {
      if (modoSeleccion) { toggleSeleccion(vaca.id); return; }
      setDatosDetalleAnimal({...vaca, historial_pesos: [], historial_gastos: [], historial_repro: []});
      setShowModalDetalleAnimal(true);
      axios.get(`${API_URL}/detalle_animal/${vaca.id}`).then(res => setDatosDetalleAnimal({...res.data, id: vaca.id}));
  };

  const iniciarBaja = () => {
      if (!datosDetalleAnimal || !datosDetalleAnimal.id) return alert("Error: ID no encontrado. Recarga.");
      setDatosBaja({ animal_id: datosDetalleAnimal.id, motivo: 'VENTA', comprador: '', detalle: '', kilos: '', precio: '' });
      setShowModalDetalleAnimal(false);
      setShowModalBaja(true);
  };

  const confirmarBaja = (e) => {
      e.preventDefault();
      const k = parseFloat(datosBaja.kilos.toString().replace(',','.')) || 0;
      const p = parseFloat(datosBaja.precio.toString().replace(',','.')) || 0;
      axios.post(`${API_URL}/registrar_baja`, { ...datosBaja, kilos: k, precio: k * p }).then((res) => {
          alert(`✅ Baja registrada: ${datosBaja.motivo}`);
          setShowModalBaja(false); cargarTodo();
      }).catch(err => alert("Error: " + err.message));
  };

  const iniciarEventoRepro = () => {
      if (!datosDetalleAnimal || !datosDetalleAnimal.id) return alert("Error: ID no encontrado.");
      setNuevoEventoRepro({ animal_id: datosDetalleAnimal.id, tipo: 'INSEMINACION', detalle: '', fecha: '', protocolo_id: '', genetica_id: '', condicion_corporal: '' }); 
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
      .then(() => { alert("Hacienda movida correctamente 🚚"); setShowModalMover(false); setModoSeleccion(false); setAnimalesSeleccionados([]); cargarTodo(); })
      .catch(e => alert("Error al mover: " + e.message));
  };

  const irACrearLote = () => { setShowModalMover(false); abrirNuevoLote(); };
  const abrirNuevoLote = () => { setModoEdicion(null); setNuevoContrato({ nombreLote: '', hectareas: '', propietario: '', tipo: 'APARCERIA', porcentaje: 0, lat: null, lng: null }); setShowModalLote(true); };
  const abrirEditarLote = (item) => { setModoEdicion(item.lote_id); setNuevoContrato({ nombreLote: item.lote, hectareas: item.hectareas, propietario: item.propietario, tipo: item.tipo, porcentaje: item.porcentaje, lat: item.lat, lng: item.lng }); setShowModalLote(true); };
  const guardarContrato = (e) => { e.preventDefault(); const method = axios.post; const data = { ...nuevoContrato }; if (!data.lat) { data.lat = 0; data.lng = 0; } method(`${API_URL}/nuevo_contrato`, data).then(() => { setShowModalLote(false); cargarTodo(); }).catch(err => alert("Error al guardar: " + (err.response?.data?.error || err.message))); };
  const eliminarLote = (id) => { if (window.confirm("¿Eliminar?")) axios.delete(`${API_URL}/eliminar_lote/${id}`).then(() => cargarTodo()); };
  const guardarCosecha = (e) => { e.preventDefault(); axios.post(`${API_URL}/nueva_cosecha`, nuevaCosecha).then(() => { setShowModalCosecha(false); cargarTodo(); }); }; 
  const guardarAnimal = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_animal`, nuevoAnimal).then(() => { setShowModalAnimal(false); cargarTodo(); alert("Registrado"); }); };
  const guardarPesaje = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_pesaje`, { animal_id: nuevoPesaje.animal_id, kilos: nuevoPesaje.kilos, fecha: nuevoPesaje.fecha }).then(() => { setShowModalPesaje(false); cargarTodo(); }); };
  const guardarGasto = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_gasto`, nuevoGasto).then(() => { setShowModalGasto(false); cargarTodo(); alert("Gasto OK"); }); };
  const abrirGasto = (tipo, item) => { setNuevoGasto({ lote_id: tipo === 'LOTE' ? item.lote_id : null, animal_id: tipo === 'ANIMAL' ? item.id : null, nombre_destino: tipo === 'LOTE' ? item.lote : `RP: ${item.caravana}`, concepto: '', monto: '', categoria: 'INSUMO', fecha: '' }); setShowModalGasto(true); };
  const guardarEventoRepro = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_evento_reproductivo`, nuevoEventoRepro).then(() => { alert("Evento registrado 🧬"); setShowModalRepro(false); cargarTodo(); }).catch(e => alert("Error: " + e.message)); }
  const confirmarReproMasivo = (e) => { e.preventDefault(); axios.post(`${API_URL}/evento_reproductivo_masivo`, { animales_ids: animalesSeleccionados, ...datosReproMasivo }).then((res) => { alert(res.data.mensaje); setShowModalReproMasivo(false); setModoSeleccion(false); setAnimalesSeleccionados([]); cargarTodo(); }); };
  const abrirEditarAnimal = () => { if(!datosDetalleAnimal) return; setDatosEdicionAnimal({ id: datosDetalleAnimal.id, caravana: datosDetalleAnimal.caravana, rfid: datosDetalleAnimal.rfid || '', categoria: datosDetalleAnimal.categoria, raza: datosDetalleAnimal.raza }); setShowModalEditarAnimal(true); }
  const guardarEdicionAnimal = (e) => { e.preventDefault(); axios.put(`${API_URL}/editar_animal/${datosEdicionAnimal.id}`, datosEdicionAnimal).then(() => { alert("Editado"); setShowModalEditarAnimal(false); setShowModalDetalleAnimal(false); cargarTodo(); }); }
  const confirmarSanidad = (e) => { e.preventDefault(); axios.post(`${API_URL}/gasto_masivo`, datosSanidad).then(res => { alert(res.data.mensaje); setShowModalSanidad(false); cargarTodo(); }); };
  const guardarLluvia = (e) => { e.preventDefault(); axios.post(`${API_URL}/registrar_lluvia`, nuevoRegistroLluvia).then(() => { alert("Lluvia OK"); setShowModalLluvia(false); cargarTodo(); }); };
  const guardarSilo = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_silo`, nuevoSilo).then(() => { alert("Silo OK"); setShowModalNuevoSilo(false); cargarTodo(); }); };
  const abrirCosecha = (lote) => { setNuevaCosecha({ lote_id: lote.lote_id, lote_nombre: lote.lote, kilos: '', destino: 'VENTA', silo_id: '' }); setShowModalCosecha(true); };
  const abrirVentaGrano = (silo) => { setVentaGrano({ silo_id: silo.id, kilos: '', precio_total: '', comprador: '', tipo_grano: silo.contenido, origen: 'SILO' }); setShowModalVentaGrano(true); };
  const confirmarVentaGrano = (e) => { e.preventDefault(); axios.post(`${API_URL}/venta_grano`, ventaGrano).then(() => { alert("Venta OK"); setShowModalVentaGrano(false); cargarTodo(); }); };

  const totalEstimadoBaja = (datosBaja.kilos && datosBaja.precio) ? (parseFloat(datosBaja.kilos) * parseFloat(datosBaja.precio)).toLocaleString() : '0';

  useEffect(() => { cargarTodo(); }, []);

  function ClickEnMapa() { useMapEvents({ click(e) { setTempPos(e.latlng); }, }); return null; }
  const iniciarCargaDesdeMapa = (tipo) => { if (tempPos) { if (tipo === 'LOTE') { setModoEdicion(null); setNuevoContrato({ ...nuevoContrato, lat: tempPos.lat, lng: tempPos.lng }); setTempPos(null); setShowModalLote(true); } else { setNuevoSilo({ ...nuevoSilo, lat: tempPos.lat, lng: tempPos.lng }); setTempPos(null); setShowModalNuevoSilo(true); } } };
  const obtenerUbicacion = () => { if (navigator.geolocation) { navigator.geolocation.getCurrentPosition((pos) => { setNuevoContrato({ ...nuevoContrato, lat: pos.coords.latitude, lng: pos.coords.longitude }); alert("📍 GPS Detectado"); }); } };
  const cambiarSeccion = (sec) => { setSeccion(sec); setMenuAbierto(false); }; 

  return (
    <div style={{ fontFamily: 'Segoe UI, sans-serif', backgroundColor: '#f1f5f9', height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {isMobile && (<div style={{height: '60px', background:'#0f172a', padding:'0 15px', color:'white', display:'flex', justifyContent:'space-between', alignItems:'center', flexShrink: 0, zIndex: 20}}><h2 style={{margin:0, color:'#4ade80', fontSize:'1.2rem'}}>AgroNexo ☁️</h2><button onClick={() => setMenuAbierto(!menuAbierto)} style={{background:'transparent', border:'none', color:'white'}}><Menu size={28}/></button></div>)}
      <div style={{display: 'flex', flex: 1, overflow: 'hidden', position: 'relative'}}>
          <div style={{width: '250px', height: '100%', background: '#0f172a', color: 'white', display: 'flex', flexDirection: 'column', padding: '20px', gap: '10px', position: isMobile ? 'absolute' : 'relative', left: isMobile ? (menuAbierto ? 0 : '-100%') : 0, zIndex: 30, transition: 'left 0.3s ease', boxShadow: isMobile ? '2px 0 10px rgba(0,0,0,0.5)' : 'none', overflowY: 'auto'}}>
             {!isMobile && <h2 style={{color:'#4ade80', marginBottom:'30px'}}>AgroNexo ☁️</h2>}
             <button onClick={() => cambiarSeccion('DASHBOARD')} style={{...btnMenu, background: seccion === 'DASHBOARD' ? '#1e293b' : 'transparent'}}><LayoutDashboard size={20}/> Resumen / Inicio</button>
             <button onClick={() => cambiarSeccion('MAPA')} style={{...btnMenu, background: seccion === 'MAPA' ? '#1e293b' : 'transparent'}}><MapPin size={20}/> Mapa General</button>
             <button onClick={() => cambiarSeccion('AGRICULTURA')} style={{...btnMenu, background: seccion === 'AGRICULTURA' ? '#1e293b' : 'transparent'}}><Sprout size={20}/> Agricultura</button>
             <button onClick={() => cambiarSeccion('GANADERIA')} style={{...btnMenu, background: seccion === 'GANADERIA' ? '#1e293b' : 'transparent'}}><Tractor size={20}/> Ganadería</button>
             <button onClick={() => setShowModalLluvia(true)} style={{...btnMenu, color:'#93c5fd'}}><CloudLightning size={20}/> Registrar Lluvia</button>
             <button onClick={descargarExcel} style={{...btnMenu, marginTop:'10px', color:'#38bdf8'}}><FileDown size={20}/> Exportar Reporte</button>
             <div style={{marginTop:'auto', borderTop:'1px solid #334155', paddingTop:'20px'}}><button onClick={resetFabrica} style={{...btnMenu, color:'#ef4444', border:'1px solid #ef4444', justifyContent:'center', fontWeight:'bold'}}><AlertTriangle size={18}/> RESET FÁBRICA</button></div>
          </div>
          {isMobile && menuAbierto && (<div onClick={() => setMenuAbierto(false)} style={{position:'absolute', top:0, left:0, width:'100%', height:'100%', background:'rgba(0,0,0,0.5)', zIndex: 25}}></div>)}
          <main style={{flex: 1, position: 'relative', display: 'flex', flexDirection: 'column', background: '#f1f5f9', overflowY: seccion === 'MAPA' ? 'hidden' : 'auto'}}>
              {seccion === 'DASHBOARD' && (<div style={{padding: '20px', paddingBottom: '80px'}}><h1 style={{color:'#1e293b', fontSize: isMobile ? '1.5rem' : '2rem', marginBottom:'20px'}}>Hola, Productor 👋</h1><div style={{display:'grid', gridTemplateColumns:'repeat(auto-fit, minmax(250px, 1fr))', gap:'20px'}}><div style={{background:'white', padding:'20px', borderRadius:'15px', boxShadow:'0 2px 5px rgba(0,0,0,0.05)', borderLeft:'5px solid #22c55e'}}><div style={{display:'flex', alignItems:'center', gap:'10px', color:'#64748b'}}><Tractor size={20}/> <span style={{fontWeight:'bold'}}>Hacienda Activa</span></div><div style={{fontSize:'2.5rem', fontWeight:'bold', color:'#0f172a', margin:'10px 0'}}>{dashboardData.cabezas} <span style={{fontSize:'1rem', color:'#64748b'}}>cabezas</span></div><button onClick={()=>cambiarSeccion('GANADERIA')} style={{...btnOutline, width:'auto', fontSize:'0.8rem'}}>Ver Animales</button></div><div style={{background:'white', padding:'20px', borderRadius:'15px', boxShadow:'0 2px 5px rgba(0,0,0,0.05)', borderLeft:'5px solid #eab308'}}><div style={{display:'flex', alignItems:'center', gap:'10px', color:'#64748b'}}><Sprout size={20}/> <span style={{fontWeight:'bold'}}>Superficie Cargada</span></div><div style={{fontSize:'2.5rem', fontWeight:'bold', color:'#0f172a', margin:'10px 0'}}>{dashboardData.hectareas} <span style={{fontSize:'1rem', color:'#64748b'}}>has</span></div><button onClick={()=>cambiarSeccion('AGRICULTURA')} style={{...btnOutline, width:'auto', fontSize:'0.8rem'}}>Ver Lotes</button></div></div></div>)}
              {seccion === 'AGRICULTURA' && (<div style={{padding: '20px', paddingBottom: '80px'}}><div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'20px'}}><h1 style={{color:'#1e293b'}}>Agricultura</h1><div style={{display:'flex', gap:'10px'}}><button onClick={() => setShowModalNuevoSilo(true)} style={{...btnOutline, width:'auto', borderColor:'#f97316', color:'#f97316'}}><Factory size={20}/> Nuevo Silo</button><button onClick={abrirNuevoLote} style={btnAzul}><PlusCircle size={20}/> Nuevo Lote</button></div></div><div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>{lotes.map((item) => { return ( <div key={item.id} style={cardEstilo}><div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}> <div><h3 style={{margin:0, color:'#0f172a', fontWeight:'bold', fontSize:'1.2rem'}}>{item.lote}</h3><span style={tagEstilo}>{item.tipo}</span></div> <div style={{display:'flex', gap:'5px'}}> <button onClick={(e) => {e.stopPropagation(); eliminarLote(item.lote_id)}} style={{...btnIcon, color:'#ef4444'}}><Trash2 size={18}/></button> </div> </div><div style={{display:'flex', gap:'10px', marginTop:'10px'}}> <button onClick={(e) => {e.stopPropagation(); abrirCosecha(item)}} style={btnOutline}><Truck size={16}/> Cosecha</button> <button onClick={(e) => {e.stopPropagation(); abrirGasto('LOTE', item)}} style={{...btnOutline, borderColor:'#dc2626', color:'#dc2626'}}><DollarSign size={16}/> Gasto</button> </div></div> )})}</div></div>)}
              {seccion === 'GANADERIA' && (<div style={{padding: '20px', paddingBottom: '80px'}}><div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'20px'}}><h1 style={{color:'#1e293b'}}>Ganadería</h1><div style={{display:'flex', gap:'10px'}}><button onClick={() => setShowModalSanidad(true)} style={{...btnOutline, width:'auto', borderColor:'#16a34a', color:'#16a34a'}}><Syringe size={20}/> Sanidad</button><button onClick={() => {setModoSeleccion(!modoSeleccion); setAnimalesSeleccionados([])}} style={{...btnOutline, width:'auto', background: modoSeleccion ? '#e0f2fe' : 'white'}}><ArrowRightLeft size={20}/> {modoSeleccion ? 'Cancelar' : 'Rotar'}</button><button onClick={() => setShowModalAnimal(true)} style={btnAzul}><PlusCircle size={20}/> Nuevo</button></div></div><div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>{animales.map((vaca) => (<div key={vaca.id} style={{...cardEstilo, border: animalesSeleccionados.includes(vaca.id) ? '2px solid #2563eb' : 'none'}} onClick={() => abrirDetalleAnimal(vaca)}><div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}><div style={{display:'flex', alignItems:'center', gap:'10px'}}>{modoSeleccion && (<div style={{color: animalesSeleccionados.includes(vaca.id) ? '#2563eb' : '#cbd5e1'}}>{animalesSeleccionados.includes(vaca.id) ? <CheckSquare size={24}/> : <Square size={24}/>}</div>)}<h2 style={{margin:0, color:'#0f172a', fontSize:'1.1rem'}}>{vaca.caravana}</h2></div><span style={{...tagEstilo, background:'#ecfccb', color:'#3f6212'}}>{vaca.categoria}</span></div><div style={{background:'#f8fafc', padding:'15px', borderRadius:'10px', margin:'15px 0'}}><div style={{display:'flex', justifyContent:'space-between', marginBottom:'5px', fontSize:'0.9rem'}}><span style={{color:'#64748b'}}>Ubicación:</span><strong style={{color:'#2563eb'}}>{vaca.ubicacion}</strong></div></div></div>))}</div></div>)}
              
              {showModalBaja && (<div style={modalBackdrop} onClick={()=>setShowModalBaja(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><h3 style={{margin:0, color:'#ef4444'}}>Dar de Baja / Vender</h3><form onSubmit={confirmarBaja} style={formStyle}><label style={labelStyle}>Motivo:</label><select style={inputStyle} value={datosBaja.motivo} onChange={e=>setDatosBaja({...datosBaja, motivo:e.target.value})}><option value="VENTA">💰 Venta</option><option value="CONSUMO">🍖 Consumo</option><option value="MUERTE">💀 Muerte</option><option value="ROBO">👮 Robo</option></select>{datosBaja.motivo === 'VENTA' && (<><label style={labelStyle}>Kilos:</label><input style={inputStyle} type="number" value={datosBaja.kilos} onChange={e=>setDatosBaja({...datosBaja, kilos:e.target.value})}/><label style={labelStyle}>Precio:</label><input style={inputStyle} type="number" value={datosBaja.precio} onChange={e=>setDatosBaja({...datosBaja, precio:e.target.value})}/><div style={{textAlign:'right'}}>Total: $ {totalEstimadoBaja}</div></>)}<button style={{...btnAzul, background:'#ef4444'}}>Confirmar</button></form></div></div>)}
              {showModalDetalleAnimal && (<div style={modalBackdrop} onClick={()=>setShowModalDetalleAnimal(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><div style={{display:'flex', justifyContent:'space-between'}}><h2 style={{margin:0}}>{datosDetalleAnimal?.caravana}</h2><button onClick={abrirEditarAnimal} style={btnIcon}><Edit size={20}/></button></div><div style={{marginBottom:'20px', display:'flex', gap:'10px'}}><button onClick={iniciarBaja} style={{...btnOutline, borderColor:'#ef4444', color:'#ef4444'}}><ArrowRightLeft size={20}/> Baja/Venta</button><button onClick={iniciarEventoRepro} style={btnOutline}><Dna size={20}/> Repro</button></div></div></div>)}
              {showModalLote && (<div style={modalBackdrop} onClick={()=>setShowModalLote(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><h3 style={{color:'#0f172a'}}>Nuevo Lote</h3><form onSubmit={guardarContrato} style={formStyle}><label style={labelStyle}>Nombre:</label><input value={nuevoContrato.nombreLote} onChange={e=>setNuevoContrato({...nuevoContrato, nombreLote:e.target.value})} style={inputStyle} required/><label style={labelStyle}>Hectáreas:</label><input type="number" value={nuevoContrato.hectareas} onChange={e=>setNuevoContrato({...nuevoContrato, hectareas:e.target.value})} style={inputStyle} required/><button style={btnAzul}>Crear</button></form></div></div>)}
              {showModalAnimal && (<div style={modalBackdrop} onClick={()=>setShowModalAnimal(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><h3 style={{color:'#0f172a'}}>Alta Animal</h3><form onSubmit={guardarAnimal} style={formStyle}><label style={labelStyle}>Caravana:</label><input onChange={e=>setNuevoAnimal({...nuevoAnimal, caravana:e.target.value})} style={inputStyle} required/><label style={labelStyle}>Categoría:</label><select onChange={e=>setNuevoAnimal({...nuevoAnimal, categoria:e.target.value})} style={inputStyle}><option>Ternero</option><option>Novillo</option><option>Vaca</option><option>Toro</option></select><button style={btnAzul}>Guardar</button></form></div></div>)}
              {showModalLluvia && (<div style={modalBackdrop} onClick={()=>setShowModalLluvia(false)}><div style={modalContent} onClick={e=>e.stopPropagation()}><h3 style={{color:'#2563eb'}}>Registrar Lluvia</h3><form onSubmit={guardarLluvia} style={formStyle}><select style={inputStyle} onChange={e=>setNuevoRegistroLluvia({...nuevoRegistroLluvia, lote_id:e.target.value})} required><option value="">Lote</option>{lotes.map(l => <option key={l.id} value={l.lote_id}>{l.lote}</option>)}</select><input type="number" placeholder="mm" onChange={e=>setNuevoRegistroLluvia({...nuevoRegistroLluvia, milimetros:e.target.value})} style={inputStyle} required/><button style={btnAzul}>Guardar</button></form></div></div>)}
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