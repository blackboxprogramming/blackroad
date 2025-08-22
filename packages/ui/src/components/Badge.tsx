import React from 'react';
import clsx from 'classnames';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /**
   * Semantic color variant of the badge. Uses design token names.
   */
  variant?:
    | 'primary'
    | 'secondary'
    | 'accent'
    | 'neutral'
    | 'info'
    | 'danger'
    | 'warning'
    | 'success';
  /**
   * Size of the badge controlling padding and font size.
   */
  size?: 'sm' | 'md' | 'lg';
}

/**
 * A badge component for denoting status or highlighting text. Variants map
 * to semantic colors defined in the design tokens. Sizes map to padding
 * and font size combinations.
 */
export const Badge: React.FC<BadgeProps> = ({
  variant = 'primary',
  size = 'md',
  className,
  children,
  ...rest
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full';
  const sizeStyles: Record<string, string> = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };
  const variantStyles: Record<string, string> = {
    primary: 'bg-primary text-white',
    secondary: 'bg-secondary text-white',
    accent: 'bg-accent text-white',
    neutral: 'bg-neutral text-gray-900',
    info: 'bg-info text-white',
    danger: 'bg-danger text-white',
    warning: 'bg-warning text-white',
    success: 'bg-success text-white',
  };
  return (
    <span
      className={clsx(baseStyles, sizeStyles[size], variantStyles[variant], className)}
      {...rest}
    >
      {children}
    </span>
  );
};

export default Badge;
