import React from 'react';
import clsx from 'classnames';

export interface DialogProps {
  /**
   * Controls visibility of the dialog.
   */
  open: boolean;
  /**
   * Callback fired when the overlay or close button is clicked.
   */
  onClose: () => void;
  /**
   * Title displayed in the header of the dialog.
   */
  title?: string;
  /**
   * Optional footer content such as action buttons.
   */
  footer?: React.ReactNode;
  /**
   * Main content of the dialog.
   */
  children: React.ReactNode;
}

/**
 * Accessible modal dialog component.  It renders a centered panel
 * overlaying the page with a darkened backdrop.  The escape key and
 * backdrop click both trigger the `onClose` callback.
 */
export const Dialog: React.FC<DialogProps> = ({
  open,
  onClose,
  title,
  footer,
  children,
}) => {
  React.useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div
      className={clsx(
        'fixed inset-0 z-50 flex items-center justify-center',
        open ? 'pointer-events-auto' : 'pointer-events-none',
      )}
      aria-modal="true"
      role="dialog"
    >
      <div
        className={clsx(
          'absolute inset-0 bg-black/40 transition-opacity',
          open ? 'opacity-100' : 'opacity-0',
        )}
        onClick={onClose}
      />
      <div
        className={clsx(
          'bg-white dark:bg-gray-900 rounded-lg shadow-xl transform transition-transform max-w-lg w-full mx-4',
          open ? 'scale-100' : 'scale-95 opacity-0',
        )}
      >
        {title && (
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 text-lg font-medium">
            {title}
          </div>
        )}
        <div className="p-4">{children}</div>
        {footer && (
          <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-2">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dialog;
