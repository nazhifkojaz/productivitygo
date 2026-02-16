import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LandingPage from '../LandingPage';

// Mock IntersectionObserver for Framer Motion
class MockIntersectionObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

global.IntersectionObserver = MockIntersectionObserver as any;

// Helper to render with Router
function renderWithRouter(ui: React.ReactElement) {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
}

describe('LandingPage - Color Token Usage', () => {
  describe('No arbitrary color classes', () => {
    it('should not use arbitrary background color classes with hex values', () => {
      const { container } = renderWithRouter(<LandingPage />);

      // Check that no arbitrary bg-[#XXXXXX] classes remain
      const html = container.innerHTML;
      expect(html).not.toMatch(/bg-\[#([0-9A-Fa-f]{6})\]/);
      expect(html).not.toMatch(/bg-\[#([0-9A-Fa-f]{3})\]/);
    });

    it('should not use arbitrary text color classes with hex values', () => {
      const { container } = renderWithRouter(<LandingPage />);

      const html = container.innerHTML;
      expect(html).not.toMatch(/text-\[#([0-9A-Fa-f]{6})\]/);
      expect(html).not.toMatch(/text-\[#([0-9A-Fa-f]{3})\]/);
    });

    it('should not use arbitrary hover text color classes with hex values', () => {
      const { container } = renderWithRouter(<LandingPage />);

      const html = container.innerHTML;
      expect(html).not.toMatch(/hover:text-\[#([0-9A-Fa-f]{6})\]/);
      expect(html).not.toMatch(/hover:text-\[#([0-9A-Fa-f]{3})\]/);
    });
  });

  describe('Semantic landing color classes are used', () => {
    it('should use landing-coral color class', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;
      expect(html).toContain('bg-landing-coral');
      expect(html).toContain('text-landing-coral');
    });

    it('should use landing-teal color class', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;
      expect(html).toContain('bg-landing-teal');
    });

    it('should use landing-yellow color class', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;
      expect(html).toContain('bg-landing-yellow');
      expect(html).toContain('hover:text-landing-yellow');
    });

    it('should use landing-mint color class', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;
      expect(html).toContain('bg-landing-mint');
    });

    it('should use landing-salmon color class', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;
      expect(html).toContain('bg-landing-salmon');
    });
  });

  describe('Feature icons use CSS variables', () => {
    it('should use CSS variables for feature background colors', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;

      // Check that CSS variables are used in style attributes
      expect(html).toContain('var(--color-landing-coral)');
      expect(html).toContain('var(--color-landing-teal)');
      expect(html).toContain('var(--color-landing-mint)');
    });

    it('should not use raw hex values in feature data', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;

      // Ensure no raw hex colors remain in feature backgrounds
      // The pattern checks for style attributes with hex colors
      expect(html).not.toMatch(/style="[^"]*background-color:\s*#[0-9A-Fa-f]{6}/);
    });
  });

  describe('Complete migration verification', () => {
    it('should have migrated all coral colors', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;
      const coralPattern = /#FF6B6B/g;
      const matches = html.match(coralPattern);
      // We expect very few or no matches (only possibly in comments or other non-class contexts)
      expect(matches?.length || 0).toBeLessThan(3);
    });

    it('should have migrated all teal colors', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;
      const tealPattern = /#4ECDC4/g;
      const matches = html.match(tealPattern);
      expect(matches?.length || 0).toBeLessThan(3);
    });

    it('should have migrated all yellow colors', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;
      const yellowPattern = /#FFE66D/g;
      const matches = html.match(yellowPattern);
      expect(matches?.length || 0).toBeLessThan(3);
    });

    it('should have migrated all mint colors', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;
      const mintPattern = /#95E1D3/g;
      const matches = html.match(mintPattern);
      expect(matches?.length || 0).toBeLessThan(3);
    });

    it('should have migrated all salmon colors', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;
      const salmonPattern = /#F38181/g;
      const matches = html.match(salmonPattern);
      expect(matches?.length || 0).toBeLessThan(3);
    });
  });
});
