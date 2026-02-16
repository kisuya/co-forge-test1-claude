"use client";

export type ToastType = "error" | "success" | "info";

export interface ToastMessage {
  id: string;
  type: ToastType;
  text: string;
}

type Listener = (toasts: ToastMessage[]) => void;

let toasts: ToastMessage[] = [];
const listeners = new Set<Listener>();
let nextId = 1;

function emit() {
  const snapshot = [...toasts];
  listeners.forEach((fn) => fn(snapshot));
}

export function addToast(text: string, type: ToastType = "error", durationMs = 3000): string {
  const id = `toast-${nextId++}`;
  toasts = [...toasts, { id, type, text }];
  emit();
  if (durationMs > 0) {
    setTimeout(() => removeToast(id), durationMs);
  }
  return id;
}

export function removeToast(id: string): void {
  toasts = toasts.filter((t) => t.id !== id);
  emit();
}

export function subscribe(fn: Listener): () => void {
  listeners.add(fn);
  fn([...toasts]);
  return () => listeners.delete(fn);
}
