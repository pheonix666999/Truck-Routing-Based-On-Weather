import { useEffect, useState } from "react";
import { checkServer } from "../api/routingApi";

const wakeWindow = 150000;
const retryDelay = 5000;

export function useServerStatus() {
  const [status, setStatus] = useState("checking");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let timer;
    const started = Date.now();
    const waking = setTimeout(() => setStatus("waking"), 4000);
    const check = async () => {
      try {
        await checkServer(controller.signal);
        if (!controller.signal.aborted) {
          clearTimeout(waking);
          setStatus("ready");
        }
      } catch {
        if (controller.signal.aborted) return;
        if (Date.now() - started >= wakeWindow) {
          setStatus("unavailable");
        } else {
          setStatus("waking");
          timer = setTimeout(check, retryDelay);
        }
      }
    };
    // Defer until after Strict Mode's development mount/cleanup cycle.
    timer = setTimeout(check, 0);
    return () => {
      controller.abort();
      clearTimeout(timer);
      clearTimeout(waking);
    };
  }, [attempt]);

  return { status, retry: () => { setStatus("checking"); setAttempt((n) => n + 1); } };
}
