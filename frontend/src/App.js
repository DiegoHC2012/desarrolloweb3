import React, { useEffect, useMemo, useState, useCallback } from "react";
import "./App.css";

const DEFAULT_API = "http://127.0.0.1:8089";

export default function App() {
  const [apiUrl, setApiUrl] = useState(DEFAULT_API);
  const [savingApi, setSavingApi] = useState(false);

  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [resultado, setResultado] = useState(null);

  const [historial, setHistorial] = useState([]);
  const [limit, setLimit] = useState(20);

  const [cargando, setCargando] = useState(false);
  const [cargandoHist, setCargandoHist] = useState(false);
  const [error, setError] = useState("");

  const baseApi = useMemo(() => apiUrl.replace(/\/$/, ""), [apiUrl]);

  const guardarApi = () => {
    localStorage.setItem("API_URL", baseApi);
    setSavingApi(true);
    setTimeout(() => setSavingApi(false), 500);
  };

  const formatDate = (dateString) => {
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return dateString;
      return date.toLocaleString();
    } catch {
      return dateString;
    }
  };

  const obtenerHistorial = useCallback(async (customLimit) => {
    setError("");
    setCargandoHist(true);
    try {
      const url = new URL(`${baseApi}/calculadora/historial`);
      url.searchParams.set("limit", String(customLimit ?? limit));
      const res = await fetch(url.toString());
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      // tu backend ya ordena DESC por fecha; mostramos directo
      setHistorial(Array.isArray(data.historial) ? data.historial : []);
    } catch (e) {
      console.error(e);
      setError("No se pudo obtener el historial. Verifica la conexión con el backend.");
    } finally {
      setCargandoHist(false);
    }
  }, [baseApi, limit]);

  const calcularSuma = async (e) => {
    e?.preventDefault?.();
    setError("");
    setResultado(null);
    setCargando(true);
    try {
      const aNum = a === "" ? 0 : Number(a);
      const bNum = b === "" ? 0 : Number(b);
      if (Number.isNaN(aNum) || Number.isNaN(bNum)) {
        throw new Error("Ingresa números válidos.");
      }

      const url = new URL(`${baseApi}/calculadora/sum`);
      url.searchParams.set("a", String(aNum));
      url.searchParams.set("b", String(bNum));

      const res = await fetch(url.toString());
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResultado(data.resultado);

      // refrescar historial tras operación
      await obtenerHistorial();
    } catch (e) {
      console.error(e);
      setError("No se pudo calcular la suma. Revisa que el backend esté funcionando y CORS habilitado.");
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    obtenerHistorial();
  }, [obtenerHistorial]);

  const limpiar = () => {
    setA("");
    setB("");
    setResultado(null);
    setError("");
  };

  return (
    <div className="page">
      <div className="card">
        <header className="header">
          <div className="title">
            <h1>Calculadora React</h1>
            <p>Backend FastAPI · MongoDB · Suma e Historial</p>
          </div>

          <div className="api-box">
            <input
              className="input"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              placeholder="http://127.0.0.1:8000"
            />
            <button className={`btn btn-outline ${savingApi ? "btn-pulse" : ""}`} onClick={guardarApi}>
              Guardar API
            </button>
          </div>
        </header>

        <section className="calc">
          <form onSubmit={calcularSuma} className="calc-grid">
            <input
              type="number"
              className="input"
              value={a}
              onChange={(e) => setA(e.target.value)}
              placeholder="Valor A"
              inputMode="decimal"
            />
            <span className="op">+</span>
            <input
              type="number"
              className="input"
              value={b}
              onChange={(e) => setB(e.target.value)}
              placeholder="Valor B"
              inputMode="decimal"
            />
            <button type="submit" className="btn" disabled={cargando}>
              {cargando ? "Calculando…" : "Calcular"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={limpiar} disabled={cargando}>
              Limpiar
            </button>
          </form>

          <div className="result-wrap">
            {error && <div className="alert alert-error">{error}</div>}

            {resultado !== null && !error && (
              <div className="result">
                <div className="result-label">Resultado</div>
                <div className="result-value">{resultado}</div>
              </div>
            )}
          </div>
        </section>

        <section className="hist">
          <div className="hist-head">
            <h2>Historial</h2>
            <div className="hist-controls">
              <label className="label">Límite</label>
              <input
                type="number"
                min={1}
                max={200}
                className="input small"
                value={limit}
                onChange={(e) => setLimit(Number(e.target.value) || 1)}
              />
              <button className="btn btn-outline" onClick={() => obtenerHistorial()} disabled={cargandoHist}>
                {cargandoHist ? "Cargando…" : "Actualizar"}
              </button>
            </div>
          </div>

          <div className="hist-list">
            {historial.length === 0 ? (
              <p className="muted">No hay operaciones en el historial.</p>
            ) : (
              historial.map((op, i) => (
                <div className="hist-item" key={`${op._id || i}-${op.date || i}`}>
                  <div className="hist-left">
                    <span className="mono">
                      {op.a} + {op.b} = <strong className="accent">{op.resultado}</strong>
                    </span>
                  </div>
                  <div className="hist-right">
                    <small className="muted">{formatDate(op.date)}</small>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="api-foot">
            API: <span className="mono">{baseApi}</span>
          </div>
        </section>
      </div>
    </div>
  );
}

//Comentario para crear workflow
