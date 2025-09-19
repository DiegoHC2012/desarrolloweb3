import './App.css';
import React, { useState, useEffect } from "react";

function App() {
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [resultado, setResultado] = useState(null);
  const [historial, setHistorial] = useState([]);

  // La URL de la API ahora se lee desde una variable de entorno para mayor flexibilidad
  const apiUrl = 'http://127.0.0.1:8089';

  const sumar = async () => {
    // Validamos que los inputs no estén vacíos
    if (!a || !b) {
      alert("Por favor, introduce ambos números.");
      return;
    }
    const res = await fetch(`${apiUrl}/calculadora/sum?a=${a}&b=${b}`);
    const data = await res.json();
    setResultado(data.resultado);
    obtenerHistorial();
  };

  const obtenerHistorial = async () => {
    const res = await fetch(`${apiUrl}/calculadora/historial`);
    const data = await res.json();
    // Mostramos el historial más reciente primero
    setHistorial(data.historial.reverse());
  };

  useEffect(() => {
    obtenerHistorial();
  }, []);

  return (
    <div className="App">
      <div className="calculator-container">
        <h1>Calculadora Neón</h1>

        <div className="input-group">
          <input
            type="number"
            value={a}
            onChange={(e) => setA(e.target.value)}
            placeholder="Primer número"
          />
          <span className="plus-sign">+</span>
          <input
            type="number"
            value={b}
            onChange={(e) => setB(e.target.value)}
            placeholder="Segundo número"
          />
        </div>

        <button onClick={sumar}>Calcular</button>

        {resultado !== null && (
          <div className="result">
            <h2>Resultado: <span className="result-value">{resultado}</span></h2>
          </div>
        )}

        <div className="history">
          <h3>Historial</h3>
          <ul>
            {historial.slice(0, 5).map((op, i) => ( // Mostramos solo los últimos 5
              <li key={i}>
                {op.a} + {op.b} = {op.resultado}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default App;