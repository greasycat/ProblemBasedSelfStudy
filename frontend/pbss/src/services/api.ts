// API Service - Centralized API client for backend communication
// This module can be easily extended with new endpoints

import type {
  PDFPathRequest,
  PageNumberRequest,
  PageImageRequest,
  UpdateBookInfoRequest,
  UpdateTocRequest,
  UpdateAlignmentOffsetRequest,
  TotalPagesResponse,
  PageTextResponse,
  PageImageResponse,
  AlignmentCheckResponse,
  BookInfoResponse,
  TocResponse,
  AlignmentOffsetResponse,
  TocExistsResponse,
  HealthResponse,
  BooksListResponse,
} from '../types/api';

// Use VITE_API_BASE_URL if set, otherwise use relative URLs (for Vite proxy)
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

class ApiError extends Error {
  status: number;
  statusText: string;

  constructor(
    message: string,
    status: number,
    statusText: string
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.statusText = statusText;
  }
}

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  console.log('Fetching API:', url);
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new ApiError(
      errorText || `HTTP ${response.status}`,
      response.status,
      response.statusText
    );
  }

  // Check if response is actually JSON before parsing
  const contentType = response.headers.get('content-type');
  if (!contentType || !contentType.includes('application/json')) {
    const text = await response.text();
    console.error('Non-JSON response received:', {
      url,
      status: response.status,
      contentType,
      body: text.substring(0, 200), // First 200 chars
    });
    throw new ApiError(
      `Expected JSON but got ${contentType || 'unknown type'}. Response: ${text.substring(0, 100)}`,
      response.status,
      response.statusText
    );
  }

  try {
    return await response.json();
  } catch (parseError) {
    const text = await response.text().catch(() => 'Could not read response');
    console.error('JSON parse error:', {
      url,
      status: response.status,
      contentType,
      responseText: text.substring(0, 200),
      error: parseError,
    });
    throw new ApiError(
      `Failed to parse JSON response: ${parseError instanceof Error ? parseError.message : 'Unknown error'}. Response: ${text.substring(0, 100)}`,
      response.status,
      response.statusText
    );
  }
}

// Health & Status
export const healthApi = {
  check: async (): Promise<HealthResponse> => {
    return fetchAPI<HealthResponse>('/health');
  },
};

// Book Operations
export const bookApi = {
  // Get total pages for a PDF
  getTotalPages: async (request: PDFPathRequest): Promise<TotalPagesResponse> => {
    return fetchAPI<TotalPagesResponse>('/total-pages', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Get text content from a page
  getPageText: async (request: PageNumberRequest): Promise<PageTextResponse> => {
    return fetchAPI<PageTextResponse>('/page-text', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Get image of a page (as base64)
  getPageImage: async (request: PageImageRequest): Promise<PageImageResponse> => {
    return fetchAPI<PageImageResponse>('/page-image', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Get image of a page (as binary URL)
  getPageImageUrl: (pdf_path: string, page_number: number, dpi: number = 150): string => {
    const params = new URLSearchParams({
      pdf_path,
      page_number: page_number.toString(),
      dpi: dpi.toString(),
    });
    const baseUrl = API_BASE_URL || '';
    return `${baseUrl}/page-image-binary?${params.toString()}`;
  },

  // Update book information
  updateBookInfo: async (request: UpdateBookInfoRequest): Promise<BookInfoResponse> => {
    return fetchAPI<BookInfoResponse>('/update-book-info', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Check if TOC exists
  checkTocExists: async (pdf_path: string): Promise<TocExistsResponse> => {
    const params = new URLSearchParams({ pdf_path });
    return fetchAPI<TocExistsResponse>(`/check-toc-exists?${params.toString()}`);
  },

  // Update table of contents
  updateToc: async (request: UpdateTocRequest): Promise<TocResponse> => {
    return fetchAPI<TocResponse>('/update-toc', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Update alignment offset
  updateAlignmentOffset: async (
    request: UpdateAlignmentOffsetRequest
  ): Promise<AlignmentOffsetResponse> => {
    return fetchAPI<AlignmentOffsetResponse>('/update-alignment-offset', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Check alignment offset
  checkAlignmentOffset: async (pdf_path: string): Promise<AlignmentCheckResponse> => {
    return fetchAPI<AlignmentCheckResponse>('/check-alignment-offset', {
      method: 'POST',
      body: JSON.stringify({ pdf_path }),
    });
  },

  // Get all books from database
  getAllBooks: async (): Promise<BooksListResponse> => {
    return fetchAPI<BooksListResponse>('/books');
  },
};

export { ApiError };

