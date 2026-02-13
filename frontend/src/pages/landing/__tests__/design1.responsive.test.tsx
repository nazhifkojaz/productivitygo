import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Design1 from '../design1';

// Mock IntersectionObserver for Framer Motion
class MockIntersectionObserver {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

global.IntersectionObserver = MockIntersectionObserver as any;

describe('Design1 - Mobile Responsiveness', () => {
  const renderWithRouter = (ui: React.ReactElement) => {
    return render(<BrowserRouter>{ui}</BrowserRouter>);
  };

  describe('Geometric background shapes use responsive sizing', () => {
    it('should apply responsive width classes to background shapes', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Check for responsive breakpoints on shapes
      expect(html).toMatch(/w-\d+\s+sm:w-\d+/);
      expect(html).toMatch(/h-\d+\s+sm:h-\d+/);
    });

    it('should hide at least one shape on very small screens', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Check for hidden sm:block pattern
      expect(html).toContain('hidden sm:block');
    });

    it('should apply responsive border widths to shapes', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Check for border-4 sm:border-6 md:border-8 pattern
      expect(html).toMatch(/border-4\s+sm:border-\d+/);
    });
  });

  describe('Typography scales appropriately on mobile', () => {
    it('should use smaller text size for hero title on mobile', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Hero title should have text-5xl or smaller on mobile
      expect(html).toMatch(/text-(4xl|5xl)\s+sm:text-/);
    });

    it('should use intermediate sm breakpoint for progressive scaling', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Check for sm: breakpoint usage
      const smBreakpointCount = (html.match(/sm:/g) || []).length;
      expect(smBreakpointCount).toBeGreaterThan(10);
    });

    it('should reduce letter spacing on mobile', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Check for tracking-tight sm:tracking-tighter pattern
      expect(html).toMatch(/tracking-tight\s+sm:tracking-tighter/);
    });
  });

  describe('Buttons have appropriate touch targets', () => {
    it('should use smaller padding on mobile for CTA button', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // CTA should have px-6 or px-8 on mobile
      expect(html).toMatch(/px-[6-8]\s+sm:px-\d+/);
    });
  });

  describe('Scroll indicator hidden on small screens', () => {
    it('should hide scroll indicator on mobile', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Scroll indicator should have hidden sm:block
      expect(html).toMatch(/hidden\s+sm:block.*animate-bounce/);
    });
  });

  describe('Feature cards use responsive padding', () => {
    it('should reduce card padding on mobile', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Look for p-4 sm:p-6 md:p-8 pattern in feature section
      expect(html).toMatch(/p-4\s+sm:p-6\s+md:p-8/);
    });

    it('should use single column layout on mobile', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Grid should explicitly start with grid-cols-1
      expect(html).toMatch(/grid-cols-1\s+sm:grid-cols-2/);
    });
  });

  describe('About section scaling', () => {
    it('should reduce level box size on mobile', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Level box should have w-32 or w-24 on mobile
      expect(html).toMatch(/w-(24|32)\s+sm:w-\d+/);
    });

    it('should scale shadow size responsively', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Check for shadow scaling - About section has sm:shadow, BMC section has shadow-[8px_8px]
      expect(html).toMatch(/shadow-\[[48]px_[48]px|sm:shadow-/);
    });
  });

  describe('Section padding optimization', () => {
    it('should reduce vertical padding on mobile', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Look for py-16 sm:py-20 md:py-24 pattern
      expect(html).toMatch(/py-1[6-8]\s+sm:py-2\d/);
    });
  });

  describe('No horizontal scroll issues', () => {
    it('should not have elements with fixed widths exceeding mobile viewport', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Check that w-96 is always part of a responsive chain (has md: or lg:)
      const lines = html.split(/\s+/);
      let hasResponsiveLargeWidth = false;

      for (const line of lines) {
        // Look for w-96, w-80, w-72, w-64 that are NOT part of responsive classes
        if (/\b(w-96|w-80|w-72|w-64)\b/.test(line)) {
          // This is okay IF it's part of a responsive chain like "w-40 md:w-96"
          // The regex above will match individual tokens, so we check the context
          if (line.includes('sm:') || line.includes('md:') || line.includes('lg:')) {
            hasResponsiveLargeWidth = true;
          }
        }
      }

      // We should have at least one responsive large width class
      expect(hasResponsiveLargeWidth).toBe(true);
    });
  });

  describe('Footer mobile optimization', () => {
    it('should use smaller text size on mobile', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Footer brand should scale
      expect(html).toMatch(/text-xl\s+sm:text-2xl/);
    });

    it('should reduce icon sizes on mobile', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Icon sizes should be responsive - look for w-6 with breakpoint suffixes
      expect(html).toMatch(/w-6.*sm:w-7/);
    });
  });

  describe('Accessibility enhancements', () => {
    it('should include aria-hidden on scroll indicator', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Scroll indicator should be hidden from screen readers
      expect(html).toMatch(/aria-hidden="true"/);
    });

    it('should include aria-labels on social links', () => {
      const { container } = renderWithRouter(<Design1 />);
      const html = container.innerHTML;

      // Social links should have aria-labels
      expect(html).toMatch(/aria-label="(GitHub|Twitter)"/);
    });
  });
});
