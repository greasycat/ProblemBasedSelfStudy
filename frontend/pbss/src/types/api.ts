// API Types - mirroring FastAPI backend models

export interface BookIdRequest {
  book_id: number;
}

export interface PageNumberRequest {
  book_id: number;
  page_number: number;
}

export interface PageImageRequest extends PageNumberRequest {
  dpi?: number;
}

export interface UpdateBookInfoRequest {
  book_id: number;
  overwrite?: boolean;
}

export interface UpdateTocRequest {
  book_id: number;
  caching?: boolean;
  overwrite?: boolean;
}

export interface UpdateAlignmentOffsetRequest {
  book_id: number;
  page_number: number;
}

export interface TotalPagesResponse {
  book_id: number;
  total_pages: number;
}

export interface PageTextResponse {
  book_id: number;
  page_number: number;
  text: string;
}

export interface PageImageResponse {
  book_id: number;
  page_number: number;
  image_base64: string;
  format: string;
}

export interface AlignmentCheckResponse {
  book_id: number;
  results: string[];
}

export interface BookInfoResponse {
  book_id: number;
  message: string;
}

export interface TocResponse {
  book_id: number;
  message: string;
}

export interface AlignmentOffsetResponse {
  book_id: number;
  message: string;
  offset?: number;
}

export interface TocExistsResponse {
  book_id: number;
  toc_exists: boolean;
}

export interface HealthResponse {
  status: string;
  llm_initialized: boolean;
  context_initialized: boolean;
}

export interface Book {
  book_id: number; // required - all books must have an ID
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

export type TocItem = ChapterItem | SectionItem 
export type TocType = 'chapter' | 'section';

export interface ChapterItem {
  type: TocType
  chapter_id: number;
  title: string;
  start_page_number: number;
  end_page_number?: number;
  book_index_string?: string;
  summary?: string;
}

export interface ChaptersResponse {
  book_id: number;
  chapters: ChapterItem[];
}

export interface UploadBookResponse {
  book_id: number;
  message: string;
}

export interface DeleteBookResponse {
  book_id: number;
  message: string;
  deleted: boolean;
}

// Section types
export interface CreateSectionRequest {
  book_id: number;
  title: string;
  start_page_number: number;
  end_page_number: number;
  summary?: string;
  chapter_id?: number;
  book_index_string?: string;
}

export interface UpdateSectionRequest {
  title?: string;
  start_page_number?: number;
  end_page_number?: number;
  summary?: string;
  chapter_id?: number;
  book_index_string?: string;
}

export interface SectionItem {
  type: TocType;
  section_id: number;
  title: string;
  start_page_number: number;
  end_page_number: number;
  summary?: string;
  chapter_id?: number;
  book_index_string?: string;
  book_id: number;
}

export interface SectionsResponse {
  book_id: number;
  sections: SectionItem[];
}

export interface SectionResponse {
  section: SectionItem;
}

export interface SectionMessageResponse {
  section_id: number;
  message: string;
}

// Page types
export interface CreatePageRequest {
  book_id: number;
  page_number: number;
  summary?: string;
}

export interface UpdatePageRequest {
  page_number?: number;
  summary?: string;
}

export interface PageItem {
  type: TocType;
  page_id: number;
  page_number: number;
  summary?: string;
  book_id: number;
}

export interface PagesResponse {
  book_id: number;
  pages: PageItem[];
}

export interface PageResponse {
  page: PageItem;
}

export interface PageMessageResponse {
  page_id: number;
  message: string;
}

