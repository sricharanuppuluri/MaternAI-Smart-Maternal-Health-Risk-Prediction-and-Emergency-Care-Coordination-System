/**
 * Agent Tool Execution View component.
 *
 * Displays the authorized decision-support tools executed by the MaternAI Agent:
 * - Shows execution status: SUCCESS, SKIPPED, DENIED
 * - Displays tool summary and factual data returned
 * - Enforces transparent presentation without client-side data synthesis
 */

import React from 'react';
import type { AgentToolExecution, ToolExecutionStatus } from '../../types/ai';
import { Badge } from '../common';

export interface AgentToolExecutionViewProps {
  toolsInvoked?: AgentToolExecution[];
  className?: string;
}

export const AgentToolExecutionView: React.FC<AgentToolExecutionViewProps> = ({
  toolsInvoked,
  className = '',
}) => {
  if (!toolsInvoked || toolsInvoked.length === 0) {
    return null;
  }

  const getStatusVariant = (status: ToolExecutionStatus): 'success' | 'danger' | 'neutral' => {
    switch (status) {
      case 'SUCCESS':
        return 'success';
      case 'DENIED':
        return 'danger';
      case 'SKIPPED':
      default:
        return 'neutral';
    }
  };

  const formatToolName = (name: string): string => {
    return name
      .replace(/^get_|^check_|^explain_/, '')
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  return (
    <div className={`agent-tools-execution space-y-2 mt-3 ${className}`}>
      <h5 className="text-xs font-semibold text-muted uppercase tracking-wider">
        Authorized Decision Tools Invoked ({toolsInvoked.length}):
      </h5>
      <ul className="tools-list space-y-2 list-none p-0 m-0">
        {toolsInvoked.map((tool, index) => (
          <li
            key={`${tool.tool_name}-${index}`}
            className="tool-execution-item p-2 border rounded bg-neutral-light text-xs space-y-1"
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold text-primary">
                {formatToolName(tool.tool_name)}
              </span>
              <Badge
                label={tool.status}
                variant={getStatusVariant(tool.status)}
                className="text-xs"
              />
            </div>
            {tool.summary && (
              <p className="text-muted m-0">{tool.summary}</p>
            )}
            {tool.data && Object.keys(tool.data).length > 0 && (
              <details className="mt-1">
                <summary className="cursor-pointer text-muted font-medium hover:underline">
                  View tool context data
                </summary>
                <pre className="mt-1 p-2 bg-white border rounded text-[11px] overflow-x-auto text-left">
                  {JSON.stringify(tool.data, null, 2)}
                </pre>
              </details>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};
