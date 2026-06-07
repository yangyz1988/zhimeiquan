"use client";

import { useState, useEffect } from "react";
import { CheckCircle2, AlertCircle, Info, X } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  type: ToastType;
}

let listeners: ((toast: Toast) => void)[] = [];

export function toast(message: string, type: ToastType = "info") {
  const t = { id: Date.now(), message, type };
  listeners.forEach((l) => l(t));
}

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const listener = (t: Toast) => {
      setToasts((prev) => [...prev, t]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((x) => x.id !== t.id));
      }, 4000);
    };
    listeners.push(listener);
    return () => {
      listeners = listeners.filter((l) => l !== listener);
    };
  }, []);

  const remove = (id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <div className="fixed right-4 top-20 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`flex items-center gap-2 rounded-lg border bg-card px-4 py-3 shadow-lg animate-in slide-in-from-right ${
            t.type === "success"
              ? "border-green-500"
              : t.type === "error"
              ? "border-red-500"
              : "border-blue-500"
          }`}
        >
          {t.type === "success" && <CheckCircle2 className="h-4 w-4 text-green-500" />}
          {t.type === "error" && <AlertCircle className="h-4 w-4 text-red-500" />}
          {t.type === "info" && <Info className="h-4 w-4 text-blue-500" />}
          <span className="text-sm">{t.message}</span>
          <button onClick={() => remove(t.id)} className="ml-2">
            <X className="h-3 w-3" />
          </button>
        </div>
      ))}
    </div>
  );
}
