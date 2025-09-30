import './App.css';
import React, { useState, useEffect, useCallback } from "react";

function App() {
  // Estado para la calculadora simple (GET)
  const [numerosInput, setNumerosInput] = useState("10 5 2");
  const [resultado, setResultado] = useState(null);

  // Estado para el constructor de lotes (POST)
  const [loteOperaciones, setLoteOperaciones] = useState([]);
  const [loteOpActual, setLoteOpActual] = useState("sum");
  const [loteNumsInput, setLoteNumsInput] = useState("5 5");
  const [resultadoLote, setResultadoLote] = useState(null);

  // Estado para el historial y sus filtros
  const [historial, setHistorial] = useState([]);
  const [filtroOperacion, setFiltroOperacion] = useState("");
  const [filtroFecha, setFiltroFecha] = useState("");

  const apiUrl = ''; // Asegúrate de que el puerto sea el correcto

  // --- LÓGICA DE HISTORIAL ---
  const obtenerHistorial = useCallback(async () => {
    let url = `${apiUrl}/calculadora/historial`;
    if (filtroOperacion) {
      url = `${apiUrl}/calculadora/historial/operacion/${filtroOperacion}`;
    } else if (filtroFecha) {
      url = `${apiUrl}/calculadora/historial/fecha/${filtroFecha}`;
    }
    
    try {
      const res = await fetch(url);
      const data = await res.json();
      if (res.ok) {
        setHistorial(data.historial ? data.historial.reverse() : []);
      } else {
        alert(`Error al obtener historial: ${data.detail}`);
      }
    } catch (error) {
      console.error("Error de conexión:", error);
      alert("No se pudo conectar con la API. ¿Está encendida?");
    }
  }, [filtroOperacion, filtroFecha]);

  useEffect(() => {
    obtenerHistorial();
  }, [obtenerHistorial]);

  // --- LÓGICA DE CALCULADORA SIMPLE (GET) ---
  const calcular = async (operacion) => {
    const nums = numerosInput.split(/[\s,]+/).filter(Boolean).map(Number);
    if (nums.some(isNaN) || nums.length < 2) {
      alert("Por favor, introduce al menos dos números válidos separados por espacios o comas.");
      return;
    }

    const queryString = new URLSearchParams(nums.map(n => ['nums', n])).toString();
    
    try {
      const res = await fetch(`${apiUrl}/calculadora/${operacion}?${queryString}`);
      const data = await res.json();
      
      if (res.ok) {
        setResultado(data.resultado);
        obtenerHistorial(); // Actualizamos el historial tras una operación exitosa
      } else {
        const errorMsg = data.detail.message || data.detail;
        alert(`Error: ${errorMsg}`);
        setResultado(null);
      }
    } catch (error) {
      console.error("Error de conexión:", error);
      alert("No se pudo conectar con la API.");
    }
  };

  // --- LÓGICA DE LOTES (POST) ---
  const agregarAlLote = () => {
    const nums = loteNumsInput.split(/[\s,]+/).filter(Boolean).map(Number);
    if (nums.some(isNaN) || nums.length === 0) {
      alert("Introduce números válidos para el lote.");
      return;
    }
    setLoteOperaciones([...loteOperaciones, { op: loteOpActual, nums }]);
    setLoteNumsInput(""); // Limpiamos el input
  };
  
  const enviarLote = async () => {
    if (loteOperaciones.length === 0) {
      alert("Añade al menos una operación al lote.");
      return;
    }
    
    try {
      const res = await fetch(`${apiUrl}/calculadora/lote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loteOperaciones)
      });
      const data = await res.json();
      
      if (res.ok) {
        setResultadoLote(data);
        setLoteOperaciones([]); // Limpiamos el lote tras enviarlo
      } else {
        const errorMsg = data.detail.message || data.detail;
        alert(`Error en el lote: ${errorMsg}\nOperación: ${data.detail.operacion_fallida}\nNúmeros: ${data.detail.numeros_enviados.join(', ')}`);
        setResultadoLote(null);
      }
    } catch (error) {
      console.error("Error de conexión:", error);
      alert("No se pudo conectar con la API.");
    }
  };

  const formatOperacion = (op) => {
    if (!op.numeros || op.numeros.length === 0) return "Operación inválida";
    const symbolMap = { suma: '+', resta: '-', multiplicacion: '*', division: '/' };
    return `${op.numeros.join(` ${symbolMap[op.operacion] || '?'} `)} = ${op.resultado}`;
  };

  return (
    <div className="App">
      <div className="calculator-container">
        <h1>Calculadora Neón  Neon</h1>

        {/* --- CALCULADORA SIMPLE --- */}
        <div className="section">
          <h2>Calculadora Simple (GET)</h2>
          <textarea
            value={numerosInput}
            onChange={(e) => setNumerosInput(e.target.value)}
            placeholder="Escribe números separados por espacios o comas..."
          />
          <div className="button-group">
            <button onClick={() => calcular('sum')}>+</button>
            <button onClick={() => calcular('res')}>-</button>
            <button onClick={() => calcular('mul')}>*</button>
            <button onClick={() => calcular('div')}>/</button>
          </div>
          {resultado !== null && (
            <div className="result">
              <h3>Resultado: <span className="result-value">{resultado}</span></h3>
            </div>
          )}
        </div>

        {/* --- OPERACIONES POR LOTES --- */}
        <div className="section">
          <h2>Operaciones por Lotes (POST)</h2>
          <div className="lote-builder">
            <select value={loteOpActual} onChange={(e) => setLoteOpActual(e.target.value)}>
              <option value="sum">Suma</option>
              <option value="res">Resta</option>
              <option value="mul">Multiplicación</option>
              <option value="div">División</option>
            </select>
            <input
              type="text"
              value={loteNumsInput}
              onChange={(e) => setLoteNumsInput(e.target.value)}
              placeholder="Números..."
            />
            <button onClick={agregarAlLote}>Añadir al Lote</button>
          </div>
          <div className="lote-display">
            <h4>Lote Actual:</h4>
            <ul>
              {loteOperaciones.map((op, i) => <li key={i}>{op.op}: [{op.nums.join(', ')}]</li>)}
            </ul>
            <button onClick={enviarLote} disabled={loteOperaciones.length === 0}>Enviar Lote</button>
          </div>
          {resultadoLote && (
            <div className="result">
              <h3>Resultado del Lote:</h3>
              <pre>{JSON.stringify(resultadoLote, null, 2)}</pre>
            </div>
          )}
        </div>

        {/* --- HISTORIAL Y FILTROS --- */}
        <div className="section">
          <h2>Historial</h2>
          <div className="history-filters">
            <select value={filtroOperacion} onChange={e => { setFiltroOperacion(e.target.value); setFiltroFecha(''); }}>
              <option value="">Todas las operaciones</option>
              <option value="suma">Suma</option>
              <option value="resta">Resta</option>
              <option value="multiplicacion">Multiplicación</option>
              <option value="division">División</option>
            </select>
            <input type="date" value={filtroFecha} onChange={e => { setFiltroFecha(e.target.value); setFiltroOperacion(''); }}/>
          </div>
          <div className="history">
            <ul>
              {historial.slice(0, 10).map((op, i) => (
                <li key={i}>{formatOperacion(op)}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;