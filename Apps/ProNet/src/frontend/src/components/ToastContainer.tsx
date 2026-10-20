import React from 'react';
import { useToastStore, ToastItem } from '../stores/toastStore';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  if (toasts.length === 0) return null;

  const iconMap = {
    success: <CheckCircle2 className="w-5 h-5 text-success-600 shrink-0" />,
    error: <AlertCircle className="w-5 h-5 text-danger-600 shrink-0" />,
    warning: <AlertTriangle className="w-5 h-5 text-warning-600 shrink-0" />,
    info: <Info className="w-5 h-5 text-brand-600 shrink-0" />,
  };

  const borderMap = {
    success: 'border-success-200 bg-white',
    error: 'border-danger-200 bg-white',
    warning: 'border-warning-200 bg-white',
    info: 'border-brand-200 bg-white',
  };

  return (
    <div
      className="fixed top-16 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((toast: ToastItem) => (
        <div
          key={toast.id}
          className={`pointer-events-auto flex items-start gap-3 p-4 rounded-lg border shadow-elevation-float transition-all animate-in slide-in-from-right-5 ${borderMap[toast.type]}`}
          role={toast.type === 'error' ? 'alert' : 'status'}
        >
          {iconMap[toast.type]}
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-surface-900">{toast.title}</h4>
            <p className="text-xs text-surface-600 mt-0.5 break-words">{toast.message}</p>
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="p-1 text-surface-400 hover:text-surface-700 rounded-md transition-colors"
            aria-label="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
};
