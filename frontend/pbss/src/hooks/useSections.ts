// Custom hook for section management

import { useState, useCallback } from 'react';
import { sectionApi, ApiError } from '../services/api';
import type { SectionItem } from '../types/api';

export function useSections() {
  const [sections, setSections] = useState<SectionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSections = useCallback(async (book_id: number, chapter_id?: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await sectionApi.getSections(book_id, chapter_id);
      setSections(response.sections);
      return response.sections;
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to load sections: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to load sections: ${err.message}`
        : 'Failed to load sections';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSection = useCallback(async (section_id: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await sectionApi.getSection(section_id);
      const section = response.section;
      
      setSections((prev) => {
        const existing = prev.findIndex((s) => s.section_id === section_id);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = section;
          return updated;
        }
        return [...prev, section];
      });

      return section;
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to load section: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to load section: ${err.message}`
        : 'Failed to load section';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const createSection = useCallback(async (request: Parameters<typeof sectionApi.createSection>[0]) => {
    setLoading(true);
    setError(null);
    try {
      const response = await sectionApi.createSection(request);
      // Reload sections for the book
      await loadSections(request.book_id);
      return response;
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to create section: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to create section: ${err.message}`
        : 'Failed to create section';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadSections]);

  const updateSection = useCallback(async (section_id: number, request: Parameters<typeof sectionApi.updateSection>[1]) => {
    setLoading(true);
    setError(null);
    try {
      const response = await sectionApi.updateSection(section_id, request);
      // Reload the section to get updated data
      await loadSection(section_id);
      return response;
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to update section: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to update section: ${err.message}`
        : 'Failed to update section';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadSection]);

  const removeSection = useCallback(async (section_id: number) => {
    setLoading(true);
    setError(null);
    try {
      await sectionApi.deleteSection(section_id);
      // Remove from local state
      setSections((prev) => prev.filter((s) => s.section_id !== section_id));
    } catch (err) {
      const message = err instanceof ApiError 
        ? `Failed to delete section: ${err.message} (${err.status})`
        : err instanceof Error 
        ? `Failed to delete section: ${err.message}`
        : 'Failed to delete section';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    sections,
    loading,
    error,
    loadSections,
    loadSection,
    createSection,
    updateSection,
    removeSection,
    setError,
  };
}

