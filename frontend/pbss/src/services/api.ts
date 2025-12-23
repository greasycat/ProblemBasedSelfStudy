// API Service - Centralized API client for backend communication
// This module can be easily extended with new endpoints

import type {
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
  ChaptersResponse,
  UploadBookResponse,
  DeleteBookResponse,
  CreateSectionRequest,
  UpdateSectionRequest,
  SectionsResponse,
  SectionResponse,
  SectionMessageResponse,
  CreatePageRequest,
  UpdatePageRequest,
  PagesResponse,
  PageResponse,
  PageMessageResponse,
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
  getTotalPages: async (book_id: number): Promise<TotalPagesResponse> => {
    return fetchAPI<TotalPagesResponse>('/total-pages', {
      method: 'POST',
      body: JSON.stringify({ book_id }),
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
  getPageImageUrl: (book_id: number, page_number: number, dpi: number = 150): string => {
    const params = new URLSearchParams({
      book_id: book_id.toString(),
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
  checkTocExists: async (book_id: number): Promise<TocExistsResponse> => {
    const params = new URLSearchParams({ book_id: book_id.toString() });
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
  checkAlignmentOffset: async (book_id: number): Promise<AlignmentCheckResponse> => {
    return fetchAPI<AlignmentCheckResponse>('/check-alignment-offset', {
      method: 'POST',
      body: JSON.stringify({ book_id }),
    });
  },

  // Get all books from database
  getAllBooks: async (): Promise<BooksListResponse> => {
    return fetchAPI<BooksListResponse>('/books');
  },

  // Get chapters for a book
  getChapters: async (book_id: number): Promise<ChaptersResponse> => {
    const params = new URLSearchParams({ book_id: book_id.toString() });
    const response = await fetchAPI<ChaptersResponse>(`/chapters?${params.toString()}`);
    // remove bibiliography and index from the response
    response.chapters = response.chapters
      .filter(
        chapter => chapter.title.toLowerCase() !== 'bibliography'
        && chapter.title.toLowerCase() !== 'index'
      );
    return response;
  },

  // Upload a PDF file
  uploadBook: async (file: File): Promise<UploadBookResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${API_BASE_URL}/upload-book`;
    console.log('Uploading file to:', url);

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - browser will set it with boundary for multipart/form-data
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      throw new ApiError(
        errorText || `HTTP ${response.status}`,
        response.status,
        response.statusText
      );
    }

    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text();
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
      throw new ApiError(
        `Failed to parse JSON response: ${parseError instanceof Error ? parseError.message : 'Unknown error'}. Response: ${text.substring(0, 100)}`,
        response.status,
        response.statusText
      );
    }
  },

  // Delete a book
  deleteBook: async (book_id: number): Promise<DeleteBookResponse> => {
    const params = new URLSearchParams({ book_id: book_id.toString() });
    return fetchAPI<DeleteBookResponse>(`/delete-book?${params.toString()}`, {
      method: 'DELETE',
    });
  },
};

// Section Operations
export const sectionApi = {
  // Create a new section
  createSection: async (request: CreateSectionRequest): Promise<SectionMessageResponse> => {
    return fetchAPI<SectionMessageResponse>('/sections', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Get all sections for a book
  getSections: async (book_id: number, chapter_id?: number): Promise<SectionsResponse> => {
    const params = new URLSearchParams({ book_id: book_id.toString() });
    if (chapter_id !== undefined) {
      params.append('chapter_id', chapter_id.toString());
    }
    return fetchAPI<SectionsResponse>(`/sections?${params.toString()}`);
  },

  // Get a specific section by ID
  getSection: async (section_id: number): Promise<SectionResponse> => {
    return fetchAPI<SectionResponse>(`/sections/${section_id}`);
  },

  // Update a section
  updateSection: async (section_id: number, request: UpdateSectionRequest): Promise<SectionMessageResponse> => {
    return fetchAPI<SectionMessageResponse>(`/sections/${section_id}`, {
      method: 'PUT',
      body: JSON.stringify(request),
    });
  },

  // Delete a section
  deleteSection: async (section_id: number): Promise<SectionMessageResponse> => {
    return fetchAPI<SectionMessageResponse>(`/sections/${section_id}`, {
      method: 'DELETE',
    });
  },
};

// Page Operations
export const pageApi = {
  // Create a new page info entry
  createPage: async (request: CreatePageRequest): Promise<PageMessageResponse> => {
    return fetchAPI<PageMessageResponse>('/pages', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // Get all pages for a book
  getPages: async (book_id: number): Promise<PagesResponse> => {
    const params = new URLSearchParams({ book_id: book_id.toString() });
    return fetchAPI<PagesResponse>(`/pages?${params.toString()}`);
  },

  // Get a specific page by ID
  getPage: async (page_id: number): Promise<PageResponse> => {
    return fetchAPI<PageResponse>(`/pages/${page_id}`);
  },

  // Update a page
  updatePage: async (page_id: number, request: UpdatePageRequest): Promise<PageMessageResponse> => {
    return fetchAPI<PageMessageResponse>(`/pages/${page_id}`, {
      method: 'PUT',
      body: JSON.stringify(request),
    });
  },

  // Delete a page
  deletePage: async (page_id: number): Promise<PageMessageResponse> => {
    return fetchAPI<PageMessageResponse>(`/pages/${page_id}`, {
      method: 'DELETE',
    });
  },
};

export { ApiError };

