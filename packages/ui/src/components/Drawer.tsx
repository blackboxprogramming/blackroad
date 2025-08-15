import React from 'react';
import clsx from 'classnames';

export interface DrawerProps {
  /**
   * When true the drawer is visible.  When false it is hidden.
   */
  open: boolean;
  /**
   * Callback invoked when the user requests to close the drawer,
   * typically by clicking on the backdrop.
   */
  onClose: () => void;
  /**
   * Content displayed inside the drawer panel.
   */
  children: React.ReactNode;
  /**
   * Optional title displayed at the top of the drawer.
   */
  title?: string;
  /**
   * Position of the drawer relative to the viewport.  Defaults to
   * `right`.
   */
  side?: 'left' | 'right' | 'bottom' | 'top';
}

/**
 * A simple sliding panel for off‑canvas content.  The drawer uses
 * Tailwind utilities for positioning and transitions.  It renders a
 * backdrop when open to visually separate the page behind the panel.
 */
export const Drawer: React.FC<DrawerProps> = ({
  open,
  onClose,
  children,
  title,
  side = 'right',
}) => {
  const sideClasses: Record<NonNullable<DrawerProps['side']>, string> = {
    left: 'left-0 top-0 bottom-0 translate-x-0',
    right: 'right-0 top-0 bottom-0 translate-x-0',
    top: 'top-0 left-0 right-0 translate-y-0',
    bottom: 'bottom-0 left-0 right-0 translate-y-0',
  };

  return (
    <div
      className={clsx(
        'fixed inset-0 z-50 flex',
        open ? 'pointer-events-auto' : 'pointer-events-none',
      )}
    >
      {/* Backdrop */}
      <div
        className={clsx(
          'absolute inset-0 bg-black/40 transition-opacity',
          open ? 'opacity-100' : 'opacity-0',
        )}
        onClick={onClose}
      />
      {/* Panel */}
      <div
        className={clsx(
          'relative bg-white dark:bg-gray-900 shadow-xl transform transition-transform w-80 max-w-full',
          side === 'left' && 'origin-left',
          side === 'right' && 'origin-right',
          side === 'top' && 'origin-top',
          side === 'bottom' && 'origin-bottom',
          open
            ? 'translate-x-0 translate-y-0'
            : side === 'left'
            ? '-translate-x-full'
            : side === 'right'
            ? 'translate-x-full'
            : side === 'top'
            ? '-translate-y-full'
            : 'translate-y-full',
        )}
      >
        {title && (
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 text-lg font-medium">
            {title}
          </div>
        )}
        <div className="p-4 overflow-y-auto h-full">{children}</div>
      </div>
    </div>
  );
};

export default Drawer;
