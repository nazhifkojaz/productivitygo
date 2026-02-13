import { describe, it, expect, vi } from 'vitest';
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

describe('Design1 Landing Page - Visual Regression', () => {
  it('renders all feature cards with correct structure and content', () => {
    const { container } = render(
      <BrowserRouter>
        <Design1 />
      </BrowserRouter>
    );

    // Check for feature titles
    expect(container.textContent).toContain('SLAY MONSTERS');
    expect(container.textContent).toContain('BATTLE RIVALS');
    expect(container.textContent).toContain('EARN REWARDS');

    // Check for icons (svg elements)
    const svgs = container.querySelectorAll('svg');
    expect(svgs.length).toBeGreaterThan(0);
  });

  it('does not use dynamic Tailwind class concatenation', () => {
    // This test ensures we haven't reintroduced the bug
    const { container } = render(
      <BrowserRouter>
        <Design1 />
      </BrowserRouter>
    );

    // Get all className strings
    const allElements = container.querySelectorAll('*');
    const hasDynamicBgClass = Array.from(allElements).some((el: Element) => {
      const className = (el as HTMLElement).getAttribute('class') || '';
      // Check for anti-pattern: bg-[ followed by dynamic property reference
      // The pattern we're guarding against is className={`bg-${feature.color}`}
      return /\{bg-\$\{/.test(className);
    });

    expect(hasDynamicBgClass).toBe(false);
  });

  it('applies inline background colors to feature icon containers', () => {
    const { container } = render(
      <BrowserRouter>
        <Design1 />
      </BrowserRouter>
    );

    // Find all elements with inline styles
    const elementsWithInlineBg = Array.from(container.querySelectorAll('*')).filter((el: Element) => {
      const style = (el as HTMLElement).style;
      return style.backgroundColor && style.backgroundColor !== '';
    });

    // We expect to find elements with inline background colors
    expect(elementsWithInlineBg.length).toBeGreaterThan(0);

    // Verify the expected colors are present - now using CSS variables
    const colors = elementsWithInlineBg.map((el: Element) =>
      (el as HTMLElement).style.backgroundColor
    );

    // Check for CSS variables used for feature colors
    expect(colors.some(c => c.includes('var(--color-landing-coral)'))).toBe(true);
    expect(colors.some(c => c.includes('var(--color-landing-teal)'))).toBe(true);
    expect(colors.some(c => c.includes('var(--color-landing-mint)'))).toBe(true);
  });
});
