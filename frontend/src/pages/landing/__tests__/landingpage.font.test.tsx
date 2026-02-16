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

describe('LandingPage - Font Loading', () => {
  it('applies Space Grotesk font to the root container', () => {
    const { container } = render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );

    // Find the root div with min-h-screen
    const rootDiv = container.querySelector('.min-h-screen');
    expect(rootDiv).toBeTruthy();

    // Check for inline font-family style
    const style = (rootDiv as HTMLElement).style.fontFamily;
    expect(style).toContain('Space Grotesk');
  });

  it('does not use inline style tag for font loading', () => {
    const { container } = render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );

    // Ensure no style tags with @import exist
    const styleTags = container.querySelectorAll('style');
    styleTags.forEach((tag) => {
      expect(tag.innerHTML).not.toContain('@import');
      expect(tag.innerHTML).not.toContain('font-family');
    });
  });

  it('does not set global body font-family', () => {
    const { container } = render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );

    // The component should not contain body { font-family: ... }
    const styleTags = container.querySelectorAll('style');
    styleTags.forEach((tag) => {
      expect(tag.innerHTML).not.toContain('body {');
    });
  });

  it('has root container with background color and font style', () => {
    const { container } = render(
      <BrowserRouter>
        <LandingPage />
      </BrowserRouter>
    );

    // Find the root div with min-h-screen - it uses bg-landing-coral token now
    const rootDiv = container.querySelector('div.min-h-screen.bg-landing-coral');
    expect(rootDiv).toBeTruthy();

    // Verify it has the Space Grotesk font style
    const style = (rootDiv as HTMLElement).style.fontFamily;
    expect(style).toContain('Space Grotesk');
  });
});
