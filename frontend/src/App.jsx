import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Tractor, PlusCircle, Truck, RefreshCw, Sprout, Scale, DollarSign, MapPin, Locate, Trash2, Edit, CloudRain, Wind, Thermometer, Map as MapIcon, Menu, X } from 'lucide-react';

import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
let DefaultIcon = L.icon({ iconUrl: icon, shadowUrl: iconShadow, iconSize: [25, 41], iconAnchor: [12, 41] });
L.Marker.prototype.options.icon = DefaultIcon;

function App() {
  const API_URL = 'https://agronexo-backend.onrender.com/api'; 

  const [seccion, setSeccion] = useState('MAPA'); 
  const [rol, setRol] = useState('PRODUCTOR'); 
  const [lotes, setLotes] = useState([]);
  const [animales, setAnimales] = useState([]);
  const [clima, setClima] = useState(null);
  const [loteClimaNombre, setLoteClimaNombre] = useState('General');
  const [tempPos, setTempPos] = useState(null); 
  
  // Responsive
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [menuAbierto, setMenuAbierto] = useState(false); 

  // Modales
  const [showModalLote, setShowModalLote] = useState(false);
  const [showModalCosecha, setShowModalCosecha] = useState(false);
  const [showModalAnimal, setShowModalAnimal] = useState(false);
  const [showModalPesaje, setShowModalPesaje] = useState(false);
  const [showModalGasto, setShowModalGasto] = useState(false); 
  const [modoEdicion, setModoEdicion] = useState(null); 

  // Formularios
  const [nuevoContrato, setNuevoContrato] = useState({ nombreLote: '', hectareas: '', propietario: '', tipo: 'APARCERIA', porcentaje: 0, lat: null, lng: null });
  const [nuevaCosecha, setNuevaCosecha] = useState({ lote_id: null, lote_nombre: '', kilos: '' });
  const [nuevoAnimal, setNuevoAnimal] = useState({ caravana: '', raza: 'Braford', categoria: 'Ternero', peso_inicial: '', fecha: '' });
  const [nuevoPesaje, setNuevoPesaje] = useState({ animal_id: null, caravana: '', kilos: '', fecha: '' });
  const [nuevoGasto, setNuevoGasto] = useState({ lote_id: null, animal_id: null, nombre_destino: '', concepto: '', monto: '', categoria: 'INSUMO', fecha: '' });

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const cargarTodo = () => {
    axios.get(`${API_URL}/liquidaciones`).then(res => {
        setLotes(res.data);
        if (res.data.length > 0 && res.data[0].lat) cargarClima(res.data[0].lat, res.data[0].lng, res.data[0].lote);
        else cargarClima(-26.78, -60.85, 'Chaco (General)');
    }).catch(err => console.error(err));
    axios.get(`${API_URL}/animales`).then(res => setAnimales(res.data));
  };

  const cargarClima = (lat, lng, nombreLote) => {
    if (!lat || !lng) return;
    setClima(null); setLoteClimaNombre(nombreLote);
    const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current_weather=true&daily=precipitation_sum&timezone=auto`;
    axios.get(url).then(res => setClima({ temp: res.data.current_weather.temperature, wind: res.data.current_weather.windspeed, rain: res.data.daily.precipitation_sum[0] })).catch(e => console.log(e));
  };

  useEffect(() => { cargarTodo(); }, []);

  function ClickEnMapa() { useMapEvents({ click(e) { setTempPos(e.latlng); }, }); return null; }
  const iniciarCargaDesdeMapa = () => { if (tempPos) { setModoEdicion(null); setNuevoContrato({ ...nuevoContrato, lat: tempPos.lat, lng: tempPos.lng }); setTempPos(null); setShowModalLote(true); } };
  const obtenerUbicacion = () => { if (navigator.geolocation) { navigator.geolocation.getCurrentPosition((pos) => { setNuevoContrato({ ...nuevoContrato, lat: pos.coords.latitude, lng: pos.coords.longitude }); alert("📍 GPS Detectado"); }); } };
  
  const cambiarSeccion = (sec) => { setSeccion(sec); setMenuAbierto(false); }; 

  // CRUD
  const abrirNuevoLote = () => { setModoEdicion(null); setNuevoContrato({ nombreLote: '', hectareas: '', propietario: '', tipo: 'APARCERIA', porcentaje: 0, lat: null, lng: null }); setShowModalLote(true); };
  const abrirEditarLote = (item) => { setModoEdicion(item.lote_id); setNuevoContrato({ nombreLote: item.lote, hectareas: item.hectareas, propietario: item.propietario, tipo: item.tipo, porcentaje: item.porcentaje, lat: item.lat, lng: item.lng }); setShowModalLote(true); };
  const guardarContrato = (e) => { e.preventDefault(); const endpoint = modoEdicion ? `${API_URL}/editar_lote/${modoEdicion}` : `${API_URL}/nuevo_contrato`; const method = modoEdicion ? axios.put : axios.post; method(endpoint, nuevoContrato).then(() => { setShowModalLote(false); cargarTodo(); }); };
  const eliminarLote = (id) => { if (window.confirm("¿Eliminar?")) axios.delete(`${API_URL}/eliminar_lote/${id}`).then(() => cargarTodo()); };
  const guardarCosecha = (e) => { e.preventDefault(); axios.post(`${API_URL}/nueva_cosecha`, { lote_id: nuevaCosecha.lote_id, kilos: nuevaCosecha.kilos }).then(() => { setShowModalCosecha(false); cargarTodo(); }); };
  const guardarAnimal = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_animal`, nuevoAnimal).then(() => { setShowModalAnimal(false); cargarTodo(); alert("Registrado"); }); };
  const guardarPesaje = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_pesaje`, { animal_id: nuevoPesaje.animal_id, kilos: nuevoPesaje.kilos, fecha: nuevoPesaje.fecha }).then(() => { setShowModalPesaje(false); cargarTodo(); }); };
  const guardarGasto = (e) => { e.preventDefault(); axios.post(`${API_URL}/nuevo_gasto`, nuevoGasto).then(() => { setShowModalGasto(false); cargarTodo(); alert("Gasto OK"); }); };
  const abrirGasto = (tipo, item) => { setNuevoGasto({ lote_id: tipo === 'LOTE' ? item.lote_id : null, animal_id: tipo === 'ANIMAL' ? item.id : null, nombre_destino: tipo === 'LOTE' ? item.lote : `RP: ${item.caravana}`, concepto: '', monto: '', categoria: 'INSUMO', fecha: '' }); setShowModalGasto(true); };
  
  const COLORES_AGRO = ['#22c55e', '#9ca3af'];

  // --- INTERFAZ ---
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

      <div style={{display: 'flex', flex: 1, overflow: 'hidden', position: 'relative'}}>
          
          <div style={{
              width: '250px', height: '100%', background: '#0f172a', color: 'white', display: 'flex', flexDirection: 'column', padding: '20px', gap: '10px',
              position: isMobile ? 'absolute' : 'relative', left: isMobile ? (menuAbierto ? 0 : '-100%') : 0, zIndex: 30, transition: 'left 0.3s ease',
              boxShadow: isMobile ? '2px 0 10px rgba(0,0,0,0.5)' : 'none'
          }}>
             {!isMobile && <h2 style={{color:'#4ade80', marginBottom:'30px'}}>AgroNexo ☁️</h2>}
             <button onClick={() => cambiarSeccion('MAPA')} style={{...btnMenu, background: seccion === 'MAPA' ? '#1e293b' : 'transparent'}}><MapPin size={20}/> Mapa General</button>
             <button onClick={() => cambiarSeccion('AGRICULTURA')} style={{...btnMenu, background: seccion === 'AGRICULTURA' ? '#1e293b' : 'transparent'}}><Sprout size={20}/> Agricultura</button>
             <button onClick={() => cambiarSeccion('GANADERIA')} style={{...btnMenu, background: seccion === 'GANADERIA' ? '#1e293b' : 'transparent'}}><Tractor size={20}/> Ganadería</button>
             
             <div style={{marginTop:'auto', background:'#1e293b', padding:'15px', borderRadius:'10px', border:'1px solid #334155'}}>
                <small style={{color:'#94a3b8', display:'block', marginBottom:'5px', fontSize:'0.7rem'}}>CLIMA EN:</small>
                <strong style={{color:'white', display:'block', marginBottom:'10px', fontSize:'0.9rem'}}>{loteClimaNombre}</strong>
                {clima ? ( <> <div style={{display:'flex', alignItems:'center', gap:'10px', marginBottom:'5px'}}><Thermometer size={18} color="#fcd34d"/> <span style={{fontSize:'1.1rem', fontWeight:'bold'}}>{clima.temp}°C</span></div><div style={{display:'flex', alignItems:'center', gap:'10px', fontSize:'0.9rem', color:'#94a3b8'}}><Wind size={16}/> {clima.wind} km/h</div><div style={{display:'flex', alignItems:'center', gap:'10px', fontSize:'0.9rem', color:'#60a5fa', marginTop:'5px'}}><CloudRain size={16}/> {clima.rain} mm</div> </> ) : <span style={{color:'#64748b', fontSize:'0.8rem'}}>Cargando...</span>}
            </div>
          </div>

          {isMobile && menuAbierto && (<div onClick={() => setMenuAbierto(false)} style={{position:'absolute', top:0, left:0, width:'100%', height:'100%', background:'rgba(0,0,0,0.5)', zIndex: 25}}></div>)}

          <main style={{flex: 1, position: 'relative', display: 'flex', flexDirection: 'column', background: '#f1f5f9', overflowY: seccion === 'MAPA' ? 'hidden' : 'auto'}}>
              {seccion === 'MAPA' ? (
                  <div style={{flex: 1, width: '100%', height: '100%', zIndex: 1}}>
                       <style>{` .leaflet-container { height: 100% !important; width: 100% !important; } `}</style>
                       <MapContainer center={[-26.78, -60.85]} zoom={11} style={{ height: '100%', width: '100%' }}>
                          <TileLayer url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}" attribution="Google Maps Satellite" />
                          <ClickEnMapa />
                          {tempPos && <Marker position={tempPos}><Popup><div style={{textAlign:'center'}}><strong>¿Nuevo Lote?</strong><br/><button onClick={iniciarCargaDesdeMapa} style={{...btnAzul, padding:'5px', fontSize:'0.8rem'}}>✅ Crear</button></div></Popup></Marker>}
                          {lotes.map(lote => ( lote.lat && ( <Marker key={lote.id} position={[lote.lat, lote.lng]} eventHandlers={{ click: () => cargarClima(lote.lat, lote.lng, lote.lote) }}> <Popup><div style={{textAlign:'center'}}><strong>{lote.lote}</strong><br/>{lote.hectareas} Has</div></Popup> </Marker> ) ))}
                       </MapContainer>
                  </div>
              ) : (
                  <div style={{padding: '20px', paddingBottom: '80px'}}>
                        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'20px'}}>
                            <h1 style={{color:'#1e293b', fontSize: isMobile ? '1.5rem' : '2rem'}}>{seccion === 'AGRICULTURA' ? 'Agricultura' : 'Ganadería'}</h1>
                            <button onClick={() => seccion === 'AGRICULTURA' ? abrirNuevoLote() : setShowModalAnimal(true)} style={btnAzul}><PlusCircle size={20}/> Nuevo</button>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                            {seccion === 'AGRICULTURA' && lotes.map((item) => {
                                let miParte = rol === 'PRODUCTOR' ? item.kilos_propios : item.kilos_dueno; let parteOtro = rol === 'PRODUCTOR' ? item.kilos_dueno : item.kilos_propios;
                                return (
                                    <div key={item.id} style={cardEstilo} onClick={() => cargarClima(item.lat, item.lng, item.lote)}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}> <div><h3 style={{margin:0, color:'#0f172a', fontWeight:'bold', fontSize:'1.2rem'}}>{item.lote}</h3><span style={tagEstilo}>{item.tipo} {item.porcentaje}%</span></div> <div style={{display:'flex', gap:'5px'}}> <button onClick={(e) => {e.stopPropagation(); abrirEditarLote(item)}} style={{...btnIcon, color:'#3b82f6'}}><Edit size={18}/></button> <button onClick={(e) => {e.stopPropagation(); eliminarLote(item.lote_id)}} style={{...btnIcon, color:'#ef4444'}}><Trash2 size={18}/></button> </div> </div>
                                        <div style={{background:'#f0fdf4', padding:'10px', borderRadius:'8px', margin:'10px 0', border:'1px solid #bbf7d0'}}> <div style={{display:'flex', justifyContent:'space-between', fontSize:'0.9rem'}}><span style={{color:'#166534'}}>🌱 Cosecha:</span><strong>{item.total_cosechado.toLocaleString()} kg</strong></div> <div style={{display:'flex', justifyContent:'space-between', fontSize:'0.9rem', marginTop:'5px', color:'#dc2626'}}><span>💸 Gastos:</span><strong>$ {item.total_gastos?.toLocaleString()}</strong></div> </div>
                                        <div style={{ height: '150px', width:'100%' }}> {item.total_cosechado > 0 ? ( <ResponsiveContainer><PieChart><Pie data={[{ name: 'Tú', value: miParte }, { name: 'Otro', value: parteOtro }]} cx="50%" cy="50%" innerRadius={35} outerRadius={55} dataKey="value"><Cell fill={COLORES_AGRO[0]} /><Cell fill={COLORES_AGRO[1]} /></Pie><Tooltip formatter={(val) => `${val.toLocaleString()} kg`} /></PieChart></ResponsiveContainer> ) : <div style={sinDatos}>Sin Cosecha</div>} </div>
                                        <div style={{display:'flex', gap:'10px'}}> <button onClick={(e) => {e.stopPropagation(); setNuevaCosecha({lote_id:item.lote_id, kilos:''}); setShowModalCosecha(true)}} style={btnOutline}><Truck size={16}/> Cosecha</button> <button onClick={(e) => {e.stopPropagation(); abrirGasto('LOTE', item)}} style={{...btnOutline, borderColor:'#dc2626', color:'#dc2626'}}><DollarSign size={16}/> Gasto</button> </div>
                                    </div>
                                )
                            })}
                            {seccion === 'GANADERIA' && animales.map((vaca) => (
                                <div key={vaca.id} style={cardEstilo}>
                                    <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}><h2 style={{margin:0, color:'#0f172a'}}>RP: {vaca.caravana}</h2><span style={{...tagEstilo, background:'#ecfccb', color:'#3f6212'}}>{vaca.raza}</span></div>
                                    <div style={{background:'#f8fafc', padding:'15px', borderRadius:'10px', margin:'15px 0'}}> <div style={{display:'flex', justifyContent:'space-between'}}><span style={{color:'#64748b'}}>Peso:</span><strong style={{fontSize:'1.1rem'}}>{vaca.peso_actual} kg</strong></div> <div style={{display:'flex', justifyContent:'space-between', marginTop:'5px'}}><span style={{color:'#64748b'}}>GDP:</span><strong style={{color: vaca.gdp > 0.8 ? '#16a34a' : '#ea580c'}}>{vaca.gdp} kg/d</strong></div> <div style={{display:'flex', justifyContent:'space-between', marginTop:'5px', borderTop:'1px solid #e2e8f0', paddingTop:'5px'}}><span style={{color:'#dc2626', fontSize:'0.9rem'}}>Costo Acum:</span><strong style={{color:'#dc2626'}}>$ {vaca.costo_acumulado?.toLocaleString()}</strong></div> </div>
                                    <div style={{display:'flex', gap:'10px'}}><button onClick={() => {setNuevoPesaje({animal_id: vaca.id, caravana: vaca.caravana, kilos: '', fecha: ''}); setShowModalPesaje(true)}} style={btnOutline}><Scale size={16}/> Pesar</button><button onClick={() => abrirGasto('ANIMAL', vaca)} style={{...btnOutline, borderColor:'#dc2626', color:'#dc2626'}}><DollarSign size={16}/> Gasto</button></div>
                                </div>
                            ))}
                        </div>
                  </div>
              )}

              {/* MODALES ARREGLADOS CON ETIQUETAS VISIBLES */}
              {showModalLote && (<div style={modalBackdrop}><div style={modalContent}>
                  <h3>{modoEdicion ? 'Editar Lote' : 'Nuevo Lote'}</h3>
                  <form onSubmit={guardarContrato} style={formStyle}>
                      <label style={labelStyle}>Nombre del Lote:</label>
                      <input value={nuevoContrato.nombreLote} onChange={e=>setNuevoContrato({...nuevoContrato, nombreLote:e.target.value})} style={inputStyle} required/>
                      
                      <label style={labelStyle}>Hectáreas:</label>
                      <input type="number" value={nuevoContrato.hectareas} onChange={e=>setNuevoContrato({...nuevoContrato, hectareas:e.target.value})} style={inputStyle} required/>
                      
                      <button type="button" onClick={obtenerUbicacion} style={{...btnGris, background:'#0f172a', color:'white', justifyContent:'center'}}><Locate size={18}/> {nuevoContrato.lat ? 'GPS Detectado' : 'Usar mi GPS'}</button>
                      
                      <label style={labelStyle}>Dueño / Contraparte:</label>
                      <input value={nuevoContrato.propietario} onChange={e=>setNuevoContrato({...nuevoContrato, propietario:e.target.value})} style={inputStyle} required/>
                      
                      <label style={labelStyle}>Tipo de Contrato:</label>
                      <div style={{display:'flex', gap:'10px'}}>
                          <select value={nuevoContrato.tipo} onChange={e=>setNuevoContrato({...nuevoContrato, tipo:e.target.value})} style={{...inputStyle, flex:1}}><option value="APARCERIA">Aparcería</option><option value="PROPIO">Propio</option></select>
                          <input placeholder="%" type="number" value={nuevoContrato.porcentaje} onChange={e=>setNuevoContrato({...nuevoContrato, porcentaje:e.target.value})} style={{...inputStyle, width:'80px'}}/>
                      </div>
                      <button style={btnAzul}>{modoEdicion ? 'Guardar Cambios' : 'Crear Lote'}</button>
                      <button type="button" onClick={()=>setShowModalLote(false)} style={btnGris}>Cancelar</button>
                  </form>
              </div></div>)}

              {showModalAnimal && (<div style={modalBackdrop}><div style={modalContent}>
                  <h3>Alta Animal</h3>
                  <form onSubmit={guardarAnimal} style={formStyle}>
                      <label style={labelStyle}>Fecha Ingreso:</label>
                      <input type="date" onChange={e=>setNuevoAnimal({...nuevoAnimal, fecha:e.target.value})} style={inputStyle}/>
                      
                      <label style={labelStyle}>Caravana (ID):</label>
                      <input placeholder="Ej: A-001" onChange={e=>setNuevoAnimal({...nuevoAnimal, caravana:e.target.value})} style={inputStyle} required/>
                      
                      <label style={labelStyle}>Raza:</label>
                      <select onChange={e=>setNuevoAnimal({...nuevoAnimal, raza:e.target.value})} style={inputStyle}><option>Braford</option><option>Brangus</option><option>Angus</option></select>
                      
                      <label style={labelStyle}>Categoría:</label>
                      <select onChange={e=>setNuevoAnimal({...nuevoAnimal, categoria:e.target.value})} style={inputStyle}><option>Ternero</option><option>Novillo</option><option>Vaca</option></select>
                      
                      <label style={labelStyle}>Peso Inicial (Kg):</label>
                      <input placeholder="Kilos" type="number" onChange={e=>setNuevoAnimal({...nuevoAnimal, peso_inicial:e.target.value})} style={inputStyle}/>
                      
                      <button style={btnAzul}>Guardar</button>
                      <button type="button" onClick={()=>setShowModalAnimal(false)} style={btnGris}>Cancelar</button>
                  </form>
              </div></div>)}

              {showModalCosecha && (<div style={modalBackdrop}><div style={modalContent}>
                  <h3>Cargar Camión</h3>
                  <form onSubmit={guardarCosecha} style={formStyle}>
                      <label style={labelStyle}>Kilos Totales:</label>
                      <input type="number" placeholder="Kilos" onChange={e=>setNuevaCosecha({...nuevaCosecha, kilos:e.target.value})} style={inputStyle} autoFocus required/>
                      <button style={btnAzul}>Registrar Carga</button>
                      <button type="button" onClick={()=>setShowModalCosecha(false)} style={btnGris}>Cancelar</button>
                  </form>
              </div></div>)}

              {showModalPesaje && (<div style={modalBackdrop}><div style={modalContent}>
                  <h3>Nuevo Pesaje</h3>
                  <form onSubmit={guardarPesaje} style={formStyle}>
                      <label style={labelStyle}>Fecha:</label>
                      <input type="date" onChange={e=>setNuevoPesaje({...nuevoPesaje, fecha:e.target.value})} style={inputStyle}/>
                      <label style={labelStyle}>Kilos:</label>
                      <input type="number" placeholder="Kilos" onChange={e=>setNuevoPesaje({...nuevoPesaje, kilos:e.target.value})} style={inputStyle} autoFocus required/>
                      <button style={btnAzul}>Registrar Peso</button>
                      <button type="button" onClick={()=>setShowModalPesaje(false)} style={btnGris}>Cancelar</button>
                  </form>
              </div></div>)}

              {showModalGasto && (<div style={modalBackdrop}><div style={modalContent}>
                  <h3 style={{color:'#dc2626'}}>💸 Nuevo Gasto</h3>
                  <form onSubmit={guardarGasto} style={formStyle}>
                      <label style={labelStyle}>Fecha:</label>
                      <input type="date" onChange={e=>setNuevoGasto({...nuevoGasto, fecha:e.target.value})} style={inputStyle}/>
                      <label style={labelStyle}>Concepto:</label>
                      <input placeholder="Ej: Semillas, Vacuna" onChange={e=>setNuevoGasto({...nuevoGasto, concepto:e.target.value})} style={inputStyle} autoFocus required/>
                      <label style={labelStyle}>Monto ($):</label>
                      <input type="number" placeholder="Monto ($)" onChange={e=>setNuevoGasto({...nuevoGasto, monto:e.target.value})} style={inputStyle} required/>
                      <label style={labelStyle}>Categoría:</label>
                      <select onChange={e=>setNuevoGasto({...nuevoGasto, categoria:e.target.value})} style={inputStyle}><option value="INSUMO">Insumo</option><option value="LABOR">Labor</option><option value="SANITARIO">Sanitario</option></select>
                      <button style={{...btnAzul, background:'#dc2626'}}>Registrar Gasto</button>
                      <button type="button" onClick={()=>setShowModalGasto(false)} style={btnGris}>Cancelar</button>
                  </form>
              </div></div>)}
              
          </main>
      </div>
    </div>
  );
}

// Estilos Corregidos
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

// ⚠️ CORRECCIÓN DE COLORES EN INPUTS Y LABELS
const inputStyle = { padding:'12px', borderRadius:'8px', border:'1px solid #cbd5e1', backgroundColor: '#ffffff', color: '#1e293b', width: '100%', boxSizing: 'border-box' };
const labelStyle = { display: 'block', marginBottom: '5px', fontWeight: 'bold', color: '#334155', fontSize: '0.9rem' };

export default App;