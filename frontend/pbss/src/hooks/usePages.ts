// Custom hook for page management

import { useState, useCallback } from 'react';
import { pageApi, ApiError } from '../services/api';
import type { PageItem } from '../types/api';

export function usePages() {
  const [pages, setPages] = useState<PageItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPages = useCallback(async (book_id: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await pageApi.getPages(book_id);
      setPages(response.pages);
      return response.pages;
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to load pages: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to load pages: ${err.message}`
        : 'Failed to load pages';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadPage = useCallback(async (page_id: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await pageApi.getPage(page_id);
      const page = response.page;
      
      setPages((prev) => {
        const existing = prev.findIndex((p) => p.page_id === page_id);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = page;
          return updated;
        }
        return [...prev, page];
      });

      return page;
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to load page: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to load page: ${err.message}`
        : 'Failed to load page';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const createPage = useCallback(async (request: Parameters<typeof pageApi.createPage>[0]) => {
    setLoading(true);
    setError(null);
    try {
      const response = await pageApi.createPage(request);
      // Reload pages for the book
      await loadPages(request.book_id);
      return response;
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to create page: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to create page: ${err.message}`
        : 'Failed to create page';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadPages]);

  const updatePage = useCallback(async (page_id: number, request: Parameters<typeof pageApi.updatePage>[1]) => {
    setLoading(true);
    setError(null);
    try {
      const response = await pageApi.updatePage(page_id, request);
      // Reload the page to get updated data
      await loadPage(page_id);
      return response;
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to update page: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to update page: ${err.message}`
        : 'Failed to update page';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadPage]);

  const removePage = useCallback(async (page_id: number) => {
    setLoading(true);
    setError(null);
    try {
      await pageApi.deletePage(page_id);
      // Remove from local state
      setPages((prev) => prev.filter((p) => p.page_id !== page_id));
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to delete page: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to delete page: ${err.message}`
        : 'Failed to delete page';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    pages,
    loading,
    error,
    loadPages,
    loadPage,
    createPage,
    updatePage,
    removePage,
    setError,
  };
}

