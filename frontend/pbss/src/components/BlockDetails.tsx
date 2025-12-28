import { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import type { TocItem } from '../types/api';

interface BlockDetailsProps {
  item: TocItem | null;
  viewMode: 'Chapter' | 'Section' | 'None';
  bookId?: number;
}

export function BlockDetails({ item, viewMode }: BlockDetailsProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (!item || viewMode === 'None') {
    return null;
  }

  const pageRange = item.end_page_number 
    ? `${item.start_page_number} - ${item.end_page_number}`
    : `${item.start_page_number}+`;


  return (
    <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-center gap-2 mb-2">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="flex items-center justify-center w-6 h-6 rounded hover:bg-gray-200 transition-colors"
          aria-label={isCollapsed ? 'Expand' : 'Collapse'}
        >
          {isCollapsed ? (
            <ChevronDownIcon className="w-4 h-4 text-gray-600" />
          ) : (
            <ChevronUpIcon className="w-4 h-4 text-gray-600" />
          )}
        </button>
        {isCollapsed && (
          <span className="text-sm font-semibold text-gray-700">
            {viewMode} Details
          </span>
        )}
      </div>
      {!isCollapsed && (
        <div className="space-y-3">
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-1">
              {viewMode} Details
            </h4>
            <h3 className="text-lg font-bold text-text-primary">
              {item.book_index_string ?? ''} {item.title}
            </h3>
          </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-600 font-medium">Page Range:</span>
            <span className="ml-2 text-text-primary">{pageRange}</span>
          </div>
          
          {/* {pageCount !== null && (
            <div>
              <span className="text-gray-600 font-medium">Page Count:</span>
              <span className="ml-2 text-text-primary">{pageCount} pages</span>
            </div>
          )} */}

          {/* {item.book_index_string && (
            <div className="col-span-2">
              <span className="text-gray-600 font-medium">Index:</span>
              <span className="ml-2 text-text-primary font-mono text-xs">
                {item.book_index_string}
              </span>
            </div>
          )} */}

          {/* {item.type === 'section' && (item as SectionItem).section_id && (
            <div>
              <span className="text-gray-600 font-medium">Section ID:</span>
              <span className="ml-2 text-text-primary">{(item as SectionItem).section_id}</span>
            </div>
          )} */}

          {/* {item.type === 'chapter' && item.chapter_id && (
            <div>
              <span className="text-gray-600 font-medium">Chapter ID:</span>
              <span className="ml-2 text-text-primary">{item.chapter_id}</span>
            </div>
          )} */}

            <div className="col-span-2 mt-2">
              <span className="text-gray-600 font-medium block mb-1">Summary:</span>
              <p className="text-text-primary text-sm leading-relaxed">
                {item.summary || 'No summary available'}
              </p>
            </div>
        </div>
        </div>
      )}
    </div>
  );
}

