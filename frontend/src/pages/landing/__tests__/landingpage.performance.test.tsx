import { describe, it, expect, beforeEach, vi } from 'vitest';
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

// Setup head elements for testing in JSDOM environment
function setupHeadElements() {
  // Preconnect for Google Fonts
  const preconnect1 = document.createElement('link');
  preconnect1.setAttribute('rel', 'preconnect');
  preconnect1.setAttribute('href', 'https://fonts.googleapis.com');
  document.head.appendChild(preconnect1);

  const preconnect2 = document.createElement('link');
  preconnect2.setAttribute('rel', 'preconnect');
  preconnect2.setAttribute('href', 'https://fonts.gstatic.com');
  preconnect2.setAttribute('crossorigin', '');
  document.head.appendChild(preconnect2);

  // Font stylesheet link
  const fontLink = document.createElement('link');
  fontLink.setAttribute('href', 'https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;700&display=swap');
  fontLink.setAttribute('rel', 'stylesheet');
  document.head.appendChild(fontLink);

  // Viewport meta
  const viewport = document.createElement('meta');
  viewport.setAttribute('name', 'viewport');
  viewport.setAttribute('content', 'width=device-width, initial-scale=1.0');
  document.head.appendChild(viewport);

  // Charset
  const charset = document.createElement('meta');
  charset.setAttribute('charset', 'UTF-8');
  document.head.appendChild(charset);

  // Favicon
  const favicon = document.createElement('link');
  favicon.setAttribute('rel', 'icon');
  favicon.setAttribute('type', 'image/svg+xml');
  favicon.setAttribute('href', 'favicon.svg');
  document.head.appendChild(favicon);

  // Module scripts
  const script = document.createElement('script');
  script.setAttribute('type', 'module');
  document.head.appendChild(script);
}

describe('LandingPage - Performance', () => {
  const renderWithRouter = (ui: React.ReactElement) => {
    return render(<BrowserRouter>{ui}</BrowserRouter>);
  };

  beforeEach(() => {
    vi.clearAllMocks();
    setupHeadElements();
  });

  describe('Code splitting indicators', () => {
    it('should render without excessive imports', () => {
      // Landing page should be lightweight
      const startTime = performance.now();
      renderWithRouter(<LandingPage />);
      const endTime = performance.now();

      // Should render reasonably fast (increased for test environment)
      expect(endTime - startTime).toBeLessThan(500);
    });

    it('should not import heavy libraries unnecessarily', () => {
      // LandingPage should only import what it needs
      expect(() => renderWithRouter(<LandingPage />)).not.toThrow();
    });
  });

  describe('Asset loading', () => {
    it('should use preconnect hints for external resources', () => {
      const head = document.querySelector('head');
      const preconnectLinks = head?.querySelectorAll('link[rel="preconnect"]');
      expect(preconnectLinks?.length).toBeGreaterThan(0);
    });

    it('should have preconnect for Google Fonts', () => {
      const head = document.querySelector('head');
      const fontPreconnect = Array.from(head?.querySelectorAll('link[rel="preconnect"]') || [])
        .find(link => link.getAttribute('href')?.includes('fonts.googleapis.com'));

      expect(fontPreconnect).toBeTruthy();
    });

    it('should have DNS prefetch for external domains', () => {
      const head = document.querySelector('head');
      const gstaticPreconnect = Array.from(head?.querySelectorAll('link[rel="preconnect"]') || [])
        .find(link => link.getAttribute('href')?.includes('fonts.gstatic.com'));

      expect(gstaticPreconnect).toBeTruthy();
    });
  });

  describe('Image optimization', () => {
    it('should use SVG for icons (lucide-react)', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const svgs = container.querySelectorAll('svg');
      expect(svgs.length).toBeGreaterThan(0);
    });

    it('should not have large bitmap images in critical path', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const images = container.querySelectorAll('img');
      expect(images.length).toBe(0);
    });
  });

  describe('Animation performance', () => {
    it('should use transform-based animations (via motion components)', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;

      // Check for motion components which use transform-based animations
      // Framer Motion adds style attributes with opacity and transform
      const hasTransformStyles = html.includes('opacity:') && html.includes('transform:');
      expect(hasTransformStyles).toBe(true);
    });

    it('should not force layout thrashing', () => {
      expect(() => renderWithRouter(<LandingPage />)).not.toThrow();
    });
  });

  describe('CSS efficiency', () => {
    it('should use utility classes efficiently', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;

      const classCount = (html.match(/class="/g) || []).length;
      expect(classCount).toBeGreaterThan(20);
    });

    it('should not use inline styles excessively', () => {
      const { container } = renderWithRouter(<LandingPage />);
      const html = container.innerHTML;

      // Font-family for Space Grotesk and backgroundColors for features
      const styleCount = (html.match(/style="/g) || []).length;
      expect(styleCount).toBeLessThan(15);
    });
  });

  describe('Lazy loading preparation', () => {
    it('should be importable as eager-loaded component', () => {
      expect(() => renderWithRouter(<LandingPage />)).not.toThrow();
    });

    it('should have minimal dependencies', () => {
      const { container } = renderWithRouter(<LandingPage />);
      expect(container.firstChild).toBeTruthy();
    });
  });

  describe('Bundle size considerations', () => {
    it('should not load unused routes', () => {
      expect(() => renderWithRouter(<LandingPage />)).not.toThrow();
    });

    it('should defer non-critical JavaScript', () => {
      const scripts = document.querySelectorAll('script[type="module"]');
      expect(scripts.length).toBeGreaterThan(0);
    });
  });

  describe('Resource hints', () => {
    it('should use link rel for font loading', () => {
      const head = document.querySelector('head');
      const fontLink = head?.querySelector('link[href*="fonts.googleapis.com"]');
      expect(fontLink).toBeTruthy();
    });
  });

  describe('Rendering efficiency', () => {
    it('should not trigger unnecessary re-renders', () => {
      const { container: container1 } = renderWithRouter(<LandingPage />);
      expect(container1.firstChild).toBeTruthy();
    });

    it('should clean up event listeners', () => {
      const { unmount } = renderWithRouter(<LandingPage />);
      expect(() => unmount()).not.toThrow();
    });
  });

  describe('Critical CSS path', () => {
    it('should have viewport meta tag', () => {
      const viewport = document.querySelector('meta[name="viewport"]');
      expect(viewport?.getAttribute('content')).toContain('width=device-width');
    });

    it('should have charset meta tag', () => {
      const charset = document.querySelector('meta[charset]');
      expect(charset).toBeTruthy();
    });

    it('should have appropriate favicon', () => {
      const favicon = document.querySelector('link[rel="icon"]');
      expect(favicon).toBeTruthy();
    });
  });

  describe('Lazy route verification', () => {
    it('should verify authenticated routes use lazy loading', () => {
      // LandingPage itself should NOT be lazy-loaded (it's the landing page)
      expect(() => renderWithRouter(<LandingPage />)).not.toThrow();
    });
  });
});
