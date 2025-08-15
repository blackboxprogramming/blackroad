import React from 'react';
import clsx from 'classnames';

export interface Tab {
  id: string;
  title: string;
  content: React.ReactNode;
}

export interface TabsProps {
  /**
   * Collection of tabs to render.  Each tab requires a unique ID,
   * display title and content.
   */
  tabs: Tab[];
  /**
   * Initially selected tab ID.  Defaults to the first tab if none
   * provided.
   */
  defaultTabId?: string;
}

/**
 * Simple tabs component that manages internal state.  The active
 * indicator uses the primary color from the design tokens.  Consumers
 * can override styling via Tailwind’s utility classes on the
 * surrounding container.
 */
export const Tabs: React.FC<TabsProps> = ({ tabs, defaultTabId }) => {
  const [activeId, setActiveId] = React.useState<string>(
    defaultTabId || tabs[0]?.id,
  );

  const activeTab = tabs.find((t) => t.id === activeId) || tabs[0];

  return (
    <div>
      <div className="border-b border-gray-200 flex space-x-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveId(tab.id)}
            className={clsx(
              'px-3 py-2 text-sm font-medium transition-colors -mb-px',
              tab.id === activeId
                ? 'border-b-2 border-primary text-primary'
                : 'border-b-2 border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300',
            )}
          >
            {tab.title}
          </button>
        ))}
      </div>
      <div className="py-4">{activeTab?.content}</div>
    </div>
  );
};

export default Tabs;
