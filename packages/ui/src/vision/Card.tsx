import React from 'react';
import clsx from 'classnames';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Visual variant of the card. Controls border, background and shadow.
   * - `plain`: white/dark background with border
   * - `outlined`: transparent background with border
   * - `elevated`: white/dark background with border and shadow
   */
  variant?: 'plain' | 'outlined' | 'elevated';
}

/**
 * A card component to group related content. Variants map to semantic colors
 * derived from the design tokens. Pass any additional props via rest.
 */
export const Card: React.FC<CardProps> = ({
  variant = 'plain',
  className,
  children,
  ...rest
}) => {
  const baseStyles = 'p-4 rounded-lg';
  const variantStyles: Record<string, string> = {
    plain: 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700',
    outlined: 'bg-transparent border border-gray-200 dark:border-gray-700',
    elevated: 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 shadow-lg',
  };
  return (
    <div className={clsx(baseStyles, variantStyles[variant], className)} {...rest}>
      {children}
    </div>
  );
};

export default Card;
