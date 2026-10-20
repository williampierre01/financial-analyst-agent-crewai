import { useEffect, useRef, useState } from "react";
import { ApiError, createAnalysis, readAnalysis, type Analysis } from "./api";

function remember(key: string, id: string | null) {
  try {
    if (id) sessionStorage.setItem(key, id);
    else sessionStorage.removeItem(key);
  } catch {
    /* Storage is optional. */
  }
}
function restore(key: string) {
  try {
    const id = sessionStorage.getItem(key);
    return id && /^[a-f0-9-]{36}$/i.test(id) ? id : null;
  } catch {
    return null;
  }
}

export function useAnalysis(uid: string) {
  const key = `analista.active-analysis.${uid}`;
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [id, setId] = useState<string | null>(() => restore(key));
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");
  const [paused, setPaused] = useState(false);
  const [revision, setRevision] = useState(0);
  const submitting = useRef(false);

  useEffect(() => {
    if (!id) return;
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const controller = new AbortController();
    let failures = 0;
    async function poll() {
      try {
        const result = await readAnalysis(
          id!,
          AbortSignal.any([controller.signal, AbortSignal.timeout(15000)]),
        );
        if (disposed) return;
        setAnalysis(result);
        setError("");
        failures = 0;
        if (result.status !== "running") {
          remember(key, null);
          setId(null);
          return;
        }
      } catch (err) {
        if (disposed) return;
        failures++;
        if (err instanceof ApiError && err.status === 404) {
          setError(err.message);
          remember(key, null);
          setId(null);
          return;
        }
        if (failures >= 3) {
          setError(
            "O acompanhamento foi interrompido. Os dados já recebidos foram preservados. A análise pode continuar no servidor.",
          );
          setPaused(true);
          return;
        }
        setError("Conexão interrompida. Tentando retomar o acompanhamento…");
      }
      timer = setTimeout(poll, 2000);
    }
    void poll();
    return () => {
      disposed = true;
      controller.abort();
      clearTimeout(timer);
    };
  }, [id, revision, key]);

  async function start(ticker: string) {
    if (submitting.current || id) return;
    submitting.current = true;
    setStarting(true);
    setError("");
    setPaused(false);
    setAnalysis(null);
    try {
      const result = await createAnalysis(ticker);
      if (!mounted.current) return;
      setAnalysis(result);
      if (result.status === "running") {
        remember(key, result.id);
        setId(result.id);
      }
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Não foi possível confirmar o início da análise. Ela pode ter sido iniciada no servidor. Aguarde antes de tentar outra consulta.",
      );
    } finally {
      setStarting(false);
      submitting.current = false;
    }
  }
  function resume() {
    setError("");
    setPaused(false);
    setRevision((value) => value + 1);
  }
  function reset() {
    remember(key, null);
    setId(null);
    setAnalysis(null);
    setError("");
    setPaused(false);
  }
  return {
    analysis,
    error,
    paused,
    start,
    resume,
    reset,
    busy: starting || !!id,
    starting,
  };
}
