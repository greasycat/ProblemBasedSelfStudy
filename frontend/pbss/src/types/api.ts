// API Types - mirroring FastAPI backend models

export interface PDFPathRequest {
  pdf_path: string;
}

export interface PageNumberRequest extends PDFPathRequest {
  page_number: number;
}

export interface PageImageRequest extends PageNumberRequest {
  dpi?: number;
}

export interface UpdateBookInfoRequest extends PDFPathRequest {
  overwrite?: boolean;
}

export interface UpdateTocRequest extends PDFPathRequest {
  caching?: boolean;
  overwrite?: boolean;
}

export interface UpdateAlignmentOffsetRequest extends PDFPathRequest {
  page_number: number;
}

export interface TotalPagesResponse {
  pdf_path: string;
  total_pages: number;
}

export interface PageTextResponse {
  pdf_path: string;
  page_number: number;
  text: string;
}

export interface PageImageResponse {
  pdf_path: string;
  page_number: number;
  image_base64: string;
  format: string;
}

export interface AlignmentCheckResponse {
  pdf_path: string;
  results: string[];
}

export interface BookInfoResponse {
  pdf_path: string;
  message: string;
}

export interface TocResponse {
  pdf_path: string;
  message: string;
}

export interface AlignmentOffsetResponse {
  pdf_path: string;
  message: string;
  offset?: number;
}

export interface TocExistsResponse {
  pdf_path: string;
  toc_exists: boolean;
}

export interface HealthResponse {
  status: string;
  llm_initialized: boolean;
  context_initialized: boolean;
}

export interface Book {
  book_id?: number; // optional because it may not exist for locally created books
  pdf_path: string; // from book_file_name
  book_name?: string;
  book_author?: string;
  total_pages?: number; // from book_pages
  book_keywords?: string;
  book_summary?: string;
  book_file_name?: string;
  book_toc_end_page?: number;
  alignment_offset?: number; // from book_alignment_offset
  toc_exists?: boolean; // computed field
}

export interface BooksListResponse {
  books: Book[];
}

