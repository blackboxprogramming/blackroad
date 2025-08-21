import React from 'react';
import clsx from 'classnames';

export interface ToastProps {
  /**
   * Message to display in the toast.
   */
  message: string;
  /**
   * Whether the toast is currently visible.
   */
  open: boolean;
  /**
   * How long in milliseconds the toast should remain visible.  A
   * value of `0` means it will stay visible until manually closed.
   */
  duration?: number;
  /**
   * Visual variant controlling background color and icon.
   */
  variant?: 'info' | 'success' | 'warning' | 'danger';
  /**
   * Callback fired when the toast disappears.
   */
  onClose?: () => void;
}

/**
 * A transient notification component.  When `open` becomes true the
 * toast slides into view; optionally it will auto‑dismiss after
 * `duration` milliseconds.  Variants map to token colors.
 */
export const Toast: React.FC<ToastProps> = ({
  message,
  open,
  duration = 3000,
  variant = 'info',
  onClose,
}) => {
  React.useEffect(() => {
    if (!open || duration === 0) return;
    const timer = setTimeout(() => {
      onClose?.();
    }, duration);
    return () => clearTimeout(timer);
  }, [open, duration, onClose]);

  const variantStyles: Record<NonNullable<ToastProps['variant']>, string> = {
    info: 'bg-info text-white',
    success: 'bg-success text-white',
    warning: 'bg-warning text-white',
    danger: 'bg-danger text-white',
  };

  return (
    <div
      className={clsx(
        'fixed bottom-4 right-4 max-w-sm w-full transition-transform transform-gpu',
        open ? 'translate-y-0 opacity-100' : 'translate-y-full opacity-0 pointer-events-none',
      )}
      role="status"
    >
      <div className={clsx('p-3 rounded-md shadow-lg flex items-center space-x-2', variantStyles[variant])}>
        <span className="flex-1 text-sm font-medium">{message}</span>
        <button
          type="button"
          className="text-white hover:text-gray-200 focus:outline-none"
          onClick={() => onClose?.()}
          aria-label="Close toast"
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default Toast;
