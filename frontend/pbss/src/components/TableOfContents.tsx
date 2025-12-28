import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { TocItem } from '../types/api';
import { BlockDetails } from './BlockDetails';
import { ArrowTurnUpLeftIcon } from '@heroicons/react/24/solid';
import { useTocStore } from '../stores/useTocStore';
import { useBooksStore } from '../stores/useBooksStore';


interface TableOfContentsProps {
  width?: number;
  height?: number;
}

export function TableOfContents({ 
  width = 800,
  height = 150,
}: TableOfContentsProps) {
  const { state, handleTocItemClick, handleBack } = useTocStore();
  const { selectedBook } = useBooksStore();
  const { displayItems, totalPages, selectedItem, opacity } = state;

  const checkViewMode = () => {
    if (selectedItem && selectedItem.type === 'chapter') {
      return 'Chapter';
    }
    if (selectedItem && selectedItem.type === 'section') {
      return 'Section';
    }
    return 'None';
  }

  const showBackButton = selectedItem !== null;

  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(width);

  useEffect(() => {
    // Update container width when window resizes
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.clientWidth);
      }
    };
    
    updateWidth();
    window.addEventListener('resize', updateWidth);
    return () => window.removeEventListener('resize', updateWidth);
  }, []);

  useEffect(() => {
    if (!svgRef.current || displayItems.length === 0) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current);
    const margin = { top: 30, right: 20, bottom: 80, left: 30 };
    const chartWidth = Math.max(containerWidth - margin.left - margin.right, width);
    const chartHeight = height - margin.top - margin.bottom;

    // Calculate the total width needed for all bars
    const barWidth = 120;
    const barSpacing = 1;
    const totalBarsWidth = displayItems.length * (barWidth + barSpacing) - barSpacing;
    const actualWidth = Math.max(chartWidth, totalBarsWidth + margin.left + margin.right);

    // Set SVG dimensions
    svg.attr('width', actualWidth).attr('height', height);

    // Create main group
    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Calculate page range
    const maxPage = totalPages || Math.max(...displayItems.map(item => item.end_page_number || item.start_page_number), 100);

    // Create scales
    const xScale = d3.scaleBand()
      .domain(displayItems.map((_, i) => i.toString()))
      .range([0, totalBarsWidth])
      .padding(0.1);

    // Use logarithmic scale for y-axis (can't use 0, so use 1 as minimum)
    const yScale = d3.scaleLog()
      .domain([1, maxPage])
      .range([chartHeight, 0]);

    // Create color scale
    const colorScale = d3.scaleSequential(d3.interpolateCool)
      .domain([0, displayItems.length - 1]);

    // Draw bars
    const bars = g.selectAll<SVGGElement, TocItem>('.bar')
      .data(displayItems)
      .enter()
      .append('g')
      .attr('class', 'bar')
      .attr('transform', (_, i) => `translate(${xScale(i.toString())}, 0)`);

    // Fixed bar height
    const barHeight = 40;
    
    bars.append('rect')
      .attr('x', 0)
      .attr('width', xScale.bandwidth())
      .attr('y', d => yScale(Math.max(1, d.start_page_number)) - barHeight / 2)
      .attr('height', barHeight)
      .attr('fill', (_, i) => colorScale(i))
      .attr('stroke', '#fff')
      .attr('stroke-width', 1)
      .attr('rx', 4)
      .style('cursor', 'pointer')
      .on('mouseover', function(event, d) {
        d3.select(this)
          .attr('opacity', 0.8)
          .attr('stroke-width', 2);
        
        // Show tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'toc-tooltip')
          .style('position', 'absolute')
          .style('background', 'rgba(0, 0, 0, 0.8)')
          .style('color', 'white')
          .style('padding', '8px 12px')
          .style('border-radius', '4px')
          .style('pointer-events', 'none')
          .style('z-index', '1000')
          .style('font-size', '12px')
          .style('max-width', '300px')
          .html(`
            <div><strong>${d.title}</strong></div>
            <div>Pages: ${d.start_page_number}${d.end_page_number ? ` - ${d.end_page_number}` : '+'}</div>
          `);
        
        const mouseEvent = event as MouseEvent;
        tooltip
          .style('left', `${mouseEvent.pageX + 10}px`)
          .style('top', `${mouseEvent.pageY - 10}px`);
      })
      .on('mouseout', function() {
        d3.select(this)
          .attr('opacity', 1)
          .attr('stroke-width', 1);
        
        d3.selectAll('.toc-tooltip').remove();
      })
      .on('click', function(_, d) {
        handleTocItemClick(d);
        d3.selectAll('.toc-tooltip').remove();
      });

    // Helper function to wrap text into multiple lines
    const wrapText = (text: string, maxWidth: number, fontSize: number = 12): string[] => {
      const avgCharWidth = fontSize * 0.6; // Approximate character width
      const maxCharsPerLine = Math.floor(maxWidth / avgCharWidth);
      
      if (text.length <= maxCharsPerLine) {
        return [text];
      }
      
      const words = text.split(' ');
      const lines: string[] = [];
      let currentLine = '';
      
      for (const word of words) {
        const testLine = currentLine ? `${currentLine} ${word}` : word;
        if (testLine.length <= maxCharsPerLine) {
          currentLine = testLine;
        } else {
          if (currentLine) {
            lines.push(currentLine);
          }
          // If a single word is longer than maxCharsPerLine, break it
          if (word.length > maxCharsPerLine) {
            for (let i = 0; i < word.length; i += maxCharsPerLine) {
              lines.push(word.substring(i, i + maxCharsPerLine));
            }
            currentLine = '';
          } else {
            currentLine = word;
          }
        }
      }
      
      if (currentLine) {
        lines.push(currentLine);
      }
      
      return lines;
    };

    // Add chapter labels with text wrapping
    const labelTexts = bars.append('text')
      .attr('x', xScale.bandwidth() / 2)
      .attr('y', chartHeight+ 30)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('font-weight', 'bold')
      .attr('fill', '#666')
      .style('cursor', 'pointer')
      .on('click', function(_, d) {
        handleTocItemClick(d);
      });

    labelTexts.each(function(d, i) {
      const title = d.title || `Ch ${i + 1}`;
      const maxWidth = xScale.bandwidth() * 0.9; // Use 90% of bar width
      const lines = wrapText(title, maxWidth, 12);
      const lineHeight = 14; // Line spacing
      
      const textElement = d3.select(this);
      lines.forEach((line, lineIndex) => {
        textElement.append('tspan')
          .attr('x', xScale.bandwidth() / 2)
          .attr('dy', lineIndex === 0 ? '0' : lineHeight)
          .text(line);
      });
    });

    // Add page number labels on bars
    bars.append('text')
      .attr('x', xScale.bandwidth() / 2)
      .attr('y', d => yScale(Math.max(1, d.start_page_number)))
      // .attr('y', d => yScale(Math.max(1, d.start_page_number)) - barHeight / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '20px')
      .attr('fill', '#fff')
      .attr('font-weight', 'bold')
      .attr('dominant-baseline', 'middle')
      .text(d => d.start_page_number)
      .style('pointer-events', 'none');

    // Add Y-axis (page numbers) - only show 1 and max page (log scale can't show 0)
    const yAxis = d3.axisLeft(yScale)
      .tickValues([1, maxPage])
      .tickFormat(d => d.toString());

    g.append('g')
      .attr('class', 'y-axis')
      .call(yAxis)
      .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', -15)
      .attr('x', -chartHeight / 2)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('fill', '#666')
      .text('Pg');

  }, [displayItems, totalPages, containerWidth, height, width]);

  // Handle horizontal scrolling with mouse wheel
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      if (e.shiftKey || e.deltaX !== 0) {
        // Allow default horizontal scrolling
        return;
      }
      
      // Convert vertical scroll to horizontal
      e.preventDefault();
      container.scrollLeft += e.deltaY;
    };

    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, []);

  if (displayItems.length === 0 && opacity === 1) {
    return (
      <div className="px-6 py-4 text-text-secondary text-sm">
        {checkViewMode() === 'Section' ? 'No sections available.' : 'No chapters available. Please update the table of contents for this book.'}
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Header with title and back button */}
      <div className="flex items-center mb-3 mt-2 h-2">
        <h3 
          className="text-sm font-semibold text-text-primary transition-opacity duration-200 ease-in-out"
        >
          {checkViewMode() !== 'None' ? selectedItem?.title || 'No title' : 'Table of Contents'}
        </h3>
        {showBackButton && (
            <button
              onClick={() => handleBack()}
              className="ml-4 p-2 text-sm font-medium text-gray-600 hover:bg-gray-200 rounded-lg transition-all duration-200"
            >
            <div className="flex items-center gap-2">
              <ArrowTurnUpLeftIcon className="w-4 h-4" />
              <span className="text-sm font-semibold text-gray-600">Back</span>
            </div>
          </button>
        )}
      </div>
      <div 
        ref={containerRef}
        className="w-full overflow-x-auto overflow-y-hidden transition-all"
        style={{ 
          scrollbarWidth: 'none',
          scrollbarColor: '#cbd5e0 transparent',
          opacity,
          transitionDuration: '400ms'
        }}
      >
        <svg ref={svgRef} className="block" />
      </div>
      
      {/* Division Information Component */}
      <div style={{ opacity }}>
      <BlockDetails 
        item={selectedItem} 
        viewMode={checkViewMode()}
        bookId={selectedBook?.book_id}
      />
      </div>
    </div>
  );
}

