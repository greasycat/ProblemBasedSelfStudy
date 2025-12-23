# Database Schema Documentation

This document describes the database table structure and indicates which operations (Create, Update, Read, Delete) are available for each field via the RESTful API.

## Table: `book_info`

Stores book information.

| Field | Type | Nullable | Description | Create | Update | Read | Delete |
|-------|------|----------|-------------|--------|--------|------|--------|
| `book_id` | INTEGER | NO (PK, Auto-increment) | Primary key, auto-incremented book identifier | YES | NO | YES | YES |
| `book_name` | STRING | YES | Name/title of the book | YES | YES | YES | YES |
| `book_author` | STRING | YES | Author of the book | YES | YES | YES | YES |
| `book_pages` | INTEGER | YES | Total number of pages in the book | YES | YES | YES | YES |
| `book_keywords` | STRING | YES | Keywords associated with the book | YES | YES | YES | YES |
| `book_summary` | TEXT | YES | Summary of the book | YES | YES | YES | YES |
| `book_embedding` | BLOB | YES | Vector embedding for the book | NO | NO | NO | YES |
| `book_file_name` | STRING | YES | Filename of the uploaded PDF | YES | NO | YES | YES |
| `book_toc_end_page` | INTEGER | YES | Page number where table of contents ends | YES | YES | YES | YES |
| `book_alignment_offset` | INTEGER | YES | Alignment offset for page number correction | YES | YES | YES | YES |

**API Endpoints:**

* `GET /books` - Returns all books with their information
* `POST /upload-book` - Uploads a book and creates an entry
* `POST /update-book-info` - Extracts and updates book information (book\_name, book\_author, book\_pages, book\_keywords, book\_summary)
* `POST /update-toc` - Updates table of contents (may update book\_toc\_end\_page)
* `POST /update-alignment-offset` - Updates book\_alignment\_offset
* `DELETE /delete-book` - Deletes a book

***

## Table: `chapter_info`

Stores chapter information.

| Field | Type | Nullable | Description | Create | Update | Read | Delete |
|-------|------|----------|-------------|--------|--------|------|--------|
| `chapter_id` | INTEGER | NO (PK, Auto-increment) | Primary key, auto-incremented chapter identifier | YES | NO | YES | YES |
| `title` | STRING | NO | Title of the chapter | YES | YES | YES | YES |
| `start_page_number` | INTEGER | NO | Starting page number of the chapter | YES | YES | YES | YES |
| `end_page_number` | INTEGER | YES | Ending page number of the chapter | YES | YES | YES | YES |
| `summary` | TEXT | YES | Summary of the chapter | NO | NO | NO | YES |
| `book_index_string` | STRING | YES | Index string for the chapter | YES | YES | YES | YES |
| `book_id` | INTEGER | NO (FK) | Foreign key to book\_info.book\_id | YES | NO | YES | YES |

**API Endpoints:**

* `GET /chapters?book_id={book_id}` - Returns all chapters for a book
* `POST /update-toc` - Extracts and updates table of contents (creates/updates chapters)

***

## Table: `section_info`

Stores section information.

| Field | Type | Nullable | Description | Create | Update | Read | Delete |
|-------|------|----------|-------------|--------|--------|------|--------|
| `section_id` | INTEGER | NO (PK, Auto-increment) | Primary key, auto-incremented section identifier | YES | NO | YES | YES |
| `title` | STRING | NO | Title of the section | YES | YES | YES | YES |
| `start_page_number` | INTEGER | NO | Starting page number of the section | YES | YES | YES | YES |
| `end_page_number` | INTEGER | NO | Ending page number of the section | YES | YES | YES | YES |
| `summary` | TEXT | YES | Summary of the section | YES | YES | YES | YES |
| `chapter_id` | INTEGER | YES (FK) | Foreign key to chapter\_info.chapter\_id | YES | YES | YES | YES |
| `book_index_string` | STRING | YES | Index string for the section | YES | YES | YES | YES |
| `book_id` | INTEGER | NO (FK) | Foreign key to book\_info.book\_id | YES | NO | YES | YES |

**API Endpoints:**

* `POST /sections` - Create a new section
* `GET /sections?book_id={book_id}&chapter_id={chapter_id}` - Returns all sections for a book (optionally filtered by chapter)
* `GET /sections/{section_id}` - Returns a specific section by ID
* `PUT /sections/{section_id}` - Updates a section
* `DELETE /sections/{section_id}` - Deletes a section

***

## Table: `page_info`

Stores page-level information.

| Field | Type | Nullable | Description | Create | Update | Read | Delete |
|-------|------|----------|-------------|--------|--------|------|--------|
| `page_id` | INTEGER | NO (PK, Auto-increment) | Primary key, auto-incremented page identifier | YES | NO | YES | YES |
| `page_number` | INTEGER | NO | Page number (0-indexed) | YES | YES | YES | YES |
| `summary` | TEXT | YES | Summary of the page content | YES | YES | YES | YES |
| `embedding` | BLOB | YES | Vector embedding for the page | NO | NO | NO | YES |
| `related_chapters` | BLOB | YES | Related chapters (serialized) | NO | NO | NO | YES |
| `related_section_id` | BLOB | YES | Related section ID (serialized) | NO | NO | NO | YES |
| `book_id` | INTEGER | NO (FK) | Foreign key to book\_info.book\_id | YES | NO | YES | YES |

**API Endpoints:**

* `POST /pages` - Create a new page info entry
* `GET /pages?book_id={book_id}` - Returns all pages for a book
* `GET /pages/{page_id}` - Returns a specific page by ID
* `PUT /pages/{page_id}` - Updates a page
* `DELETE /pages/{page_id}` - Deletes a page
* `POST /page-text` - Returns text content from a specific page (not stored in database)
* `POST /page-image` - Returns image representation of a specific page (not stored in database)
* `POST /page-image-binary` - Returns image as binary PNG (not stored in database)

**Note:** The API can extract page text and images via `/page-text`, `/page-image`, and `/page-image-binary`, but these are not stored in the `page_info` table. The `embedding`, `related_chapters`, and `related_section_id` fields are BLOB fields and are not exposed via the API.

***

## Table: `exercise_info`

Stores exercise information.

| Field | Type | Nullable | Description | Create | Update | Read | Delete |
|-------|------|----------|-------------|--------|--------|------|--------|
| `exercise_id` | INTEGER | NO (PK, Auto-increment) | Primary key, auto-incremented exercise identifier | NO | NO | NO | YES |
| `exercise_description` | TEXT | NO | Description of the exercise | NO | NO | NO | YES |
| `page_number` | INTEGER | NO | Page number where the exercise appears | NO | NO | NO | YES |
| `page_id` | INTEGER | YES (FK) | Foreign key to page\_info.page\_id | NO | NO | NO | YES |
| `related_chapters` | BLOB | YES | Related chapters (serialized) | NO | NO | NO | YES |
| `related_section_id` | BLOB | YES | Related section ID (serialized) | NO | NO | NO | YES |
| `embedding` | BLOB | YES | Vector embedding for the exercise | NO | NO | NO | YES |
| `book_id` | INTEGER | NO (FK) | Foreign key to book\_info.book\_id | NO | NO | NO | YES |

**API Endpoints:**

* None currently available

***

## Table: `exercise_details`

Stores detailed information about exercises.

| Field | Type | Nullable | Description | Create | Update | Read | Delete |
|-------|------|----------|-------------|--------|--------|------|--------|
| `exercise_id` | INTEGER | NO (PK, FK) | Primary key and foreign key to exercise\_info.exercise\_id | NO | NO | NO | YES |
| `study_guide` | TEXT | YES | Study guide for the exercise | NO | NO | NO | YES |
| `estimated_time_to_complete` | INTEGER | YES | Estimated time to complete (in minutes) | NO | NO | NO | YES |
| `difficulty_level` | INTEGER | YES | Difficulty level of the exercise | NO | NO | NO | YES |
| `chapter_id` | STRING | YES (FK) | Foreign key to chapter\_info.chapter\_id | NO | NO | NO | YES |
| `section_id` | STRING | YES (FK) | Foreign key to section\_info.section\_id | NO | NO | NO | YES |
| `book_id` | INTEGER | YES (FK) | Foreign key to book\_info.book\_id | NO | NO | NO | YES |

**API Endpoints:**

* None currently available

***

## Summary

### Fully Supported Tables (Create, Update, Read, Delete)

* **book\_info** - Most fields support Create, Update, Read, and Delete operations via `/upload-book`, `/update-book-info`, `/update-toc`, `/update-alignment-offset`, `/books`, and `/delete-book`
* **chapter\_info** - All fields support Create, Update, Read, and Delete operations via `/update-toc` and `/chapters`

### Fully Supported Tables (Create, Update, Read, Delete)

* **book\_info** - Most fields support Create, Update, Read, and Delete operations via `/upload-book`, `/update-book-info`, `/update-toc`, `/update-alignment-offset`, `/books`, and `/delete-book`
* **chapter\_info** - All fields support Create, Update, Read, and Delete operations via `/update-toc` and `/chapters`
* **section\_info** - All fields support Create, Update, Read, and Delete operations via `/sections` endpoints
* **page\_info** - `page_number`, `summary`, and `book_id` support Create, Update, Read, and Delete operations via `/pages` endpoints

### Partially Supported Tables

* **page\_info** - The `embedding`, `related_chapters`, and `related_section_id` fields are BLOB fields and are not exposed via the API. The `/page-text`, `/page-image`, and `/page-image-binary` endpoints extract page content but do not store it in the database.

### Not Supported via API (Delete only via cascade)
* **exercise\_info** - No API endpoints available for Create, Update, or Read operations
* **exercise\_details** - No API endpoints available for Create, Update, or Read operations

**Note:** Records in unsupported tables can be deleted when parent records (books) are deleted due to CASCADE foreign key constraints.

### Additional API Features

* `GET /total-pages` - Returns total pages from PDF (not stored in database)
* `GET /check-toc-exists` - Checks if table of contents exists (computed field)
* `GET /check-alignment-offset` - Checks alignment offset by returning sample pages
* `GET /health` - Health check endpoint

***

## Notes

1. **Embeddings**: Fields containing embeddings (`book_embedding`, `embedding` in page\_info and exercise\_info) are not accessible via the API as they are generated internally.

2. **BLOB Fields**: Fields stored as BLOB (like `related_chapters`, `related_section_id`) are typically serialized data structures and are not directly accessible via the API.

3. **Computed Fields**: Some fields like `toc_exists` in the `/books` endpoint are computed on-the-fly and not stored in the database.

4. **Page Content**: While the API can extract page text and images via `/page-text` and `/page-image`, this content is not stored in the `page_info` table. The table is designed for storing summaries and embeddings, which are not currently exposed via the API.

5. **Delete Operations**: Delete operations marked as YES typically occur via cascade when parent records (books) are deleted. Direct deletion endpoints are only available for books via `/delete-book`.

6. **Create Operations**: Create operations for `book_info` fields occur via `/upload-book` (which creates the book entry) and `/update-book-info` (which populates book metadata). Chapter creation occurs via `/update-toc`.

7. **Update Operations**: Update operations may overwrite existing data depending on the `overwrite` parameter in endpoints like `/update-book-info` and `/update-toc`.
