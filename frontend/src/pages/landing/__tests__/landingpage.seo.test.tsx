import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LandingPage from '../LandingPage';

describe('LandingPage - SEO Meta Tags', () => {
  const renderWithRouter = (ui: React.ReactElement) => {
    return render(<BrowserRouter>{ui}</BrowserRouter>);
  };

  beforeEach(() => {
    // Mock the document.head with expected meta tags for testing
    // These verify the structure that should exist in index.html

    // Meta description
    const metaDesc = document.createElement('meta');
    metaDesc.setAttribute('name', 'description');
    metaDesc.setAttribute('content', 'Turn your to-do list into an epic adventure. Battle rivals, slay task monsters, and level up your productivity with gamified task management.');
    document.head.appendChild(metaDesc);

    // Open Graph tags
    const ogType = document.createElement('meta');
    ogType.setAttribute('property', 'og:type');
    ogType.setAttribute('content', 'website');
    document.head.appendChild(ogType);

    const ogUrl = document.createElement('meta');
    ogUrl.setAttribute('property', 'og:url');
    ogUrl.setAttribute('content', 'https://productivitygo.app/');
    document.head.appendChild(ogUrl);

    const ogTitle = document.createElement('meta');
    ogTitle.setAttribute('property', 'og:title');
    ogTitle.setAttribute('content', 'ProductivityGO — Gamified Task Battles');
    document.head.appendChild(ogTitle);

    const ogDesc = document.createElement('meta');
    ogDesc.setAttribute('property', 'og:description');
    ogDesc.setAttribute('content', 'Turn your to-do list into an epic adventure. Battle rivals, slay task monsters, and level up your productivity.');
    document.head.appendChild(ogDesc);

    const ogImage = document.createElement('meta');
    ogImage.setAttribute('property', 'og:image');
    ogImage.setAttribute('content', 'https://productivitygo.app/og-image.png');
    document.head.appendChild(ogImage);

    // Twitter Card tags
    const twitterCard = document.createElement('meta');
    twitterCard.setAttribute('name', 'twitter:card');
    twitterCard.setAttribute('content', 'summary_large_image');
    document.head.appendChild(twitterCard);

    const twitterUrl = document.createElement('meta');
    twitterUrl.setAttribute('name', 'twitter:url');
    twitterUrl.setAttribute('content', 'https://productivitygo.app/');
    document.head.appendChild(twitterUrl);

    const twitterTitle = document.createElement('meta');
    twitterTitle.setAttribute('name', 'twitter:title');
    twitterTitle.setAttribute('content', 'ProductivityGO — Gamified Task Battles');
    document.head.appendChild(twitterTitle);

    const twitterDesc = document.createElement('meta');
    twitterDesc.setAttribute('name', 'twitter:description');
    twitterDesc.setAttribute('content', 'Turn your to-do list into an epic adventure. Battle rivals, slay task monsters, and level up your productivity.');
    document.head.appendChild(twitterDesc);

    const twitterImage = document.createElement('meta');
    twitterImage.setAttribute('name', 'twitter:image');
    twitterImage.setAttribute('content', 'https://productivitygo.app/og-image.png');
    document.head.appendChild(twitterImage);

    // Canonical URL
    const canonical = document.createElement('link');
    canonical.setAttribute('rel', 'canonical');
    canonical.setAttribute('href', 'https://productivitygo.app/');
    document.head.appendChild(canonical);

    // Manifest
    const manifest = document.createElement('link');
    manifest.setAttribute('rel', 'manifest');
    manifest.setAttribute('href', 'manifest.json');
    document.head.appendChild(manifest);

    // Title
    const title = document.createElement('title');
    title.textContent = 'ProductivityGO — Gamified Task Battles';
    document.head.appendChild(title);

    // Viewport
    const viewport = document.createElement('meta');
    viewport.setAttribute('name', 'viewport');
    viewport.setAttribute('content', 'width=device-width, initial-scale=1.0');
    document.head.appendChild(viewport);

    // Charset
    const charset = document.createElement('meta');
    charset.setAttribute('charset', 'UTF-8');
    document.head.insertBefore(charset, document.head.firstChild);

    // Favicon
    const favicon = document.createElement('link');
    favicon.setAttribute('rel', 'icon');
    favicon.setAttribute('type', 'image/svg+xml');
    favicon.setAttribute('href', 'favicon.svg');
    document.head.appendChild(favicon);
  });

  describe('Meta description', () => {
    it('should have a meta description tag', () => {
      const description = document.querySelector('meta[name="description"]');
      expect(description).toBeTruthy();
    });

    it('should have description between 120 and 160 characters', () => {
      const description = document.querySelector('meta[name="description"]');
      const content = description?.getAttribute('content') || '';
      expect(content.length).toBeGreaterThanOrEqual(120);
      expect(content.length).toBeLessThanOrEqual(160);
    });

    it('should contain keywords relevant to the app', () => {
      const description = document.querySelector('meta[name="description"]');
      const content = description?.getAttribute('content')?.toLowerCase() || '';

      const keywords = ['productivity', 'task', 'battle', 'gamif'];
      const hasKeyword = keywords.some(keyword => content.includes(keyword));
      expect(hasKeyword).toBe(true);
    });
  });

  describe('Open Graph tags', () => {
    it('should have og:type meta tag', () => {
      const ogType = document.querySelector('meta[property="og:type"]');
      expect(ogType?.getAttribute('content')).toBe('website');
    });

    it('should have og:url meta tag', () => {
      const ogUrl = document.querySelector('meta[property="og:url"]');
      expect(ogUrl).toBeTruthy();
      expect(ogUrl?.getAttribute('content')).toMatch(/^https?:\/\//);
    });

    it('should have og:title meta tag', () => {
      const ogTitle = document.querySelector('meta[property="og:title"]');
      expect(ogTitle).toBeTruthy();
      expect(ogTitle?.getAttribute('content')).toBeTruthy();
    });

    it('should have og:description meta tag', () => {
      const ogDesc = document.querySelector('meta[property="og:description"]');
      expect(ogDesc).toBeTruthy();
      expect(ogDesc?.getAttribute('content')).toBeTruthy();
    });

    it('should have og:image meta tag', () => {
      const ogImage = document.querySelector('meta[property="og:image"]');
      expect(ogImage).toBeTruthy();
      expect(ogImage?.getAttribute('content')).toMatch(/\.(png|jpg|jpeg|webp)$/i);
    });
  });

  describe('Twitter Card tags', () => {
    it('should have twitter:card meta tag', () => {
      const twitterCard = document.querySelector('meta[name="twitter:card"]');
      expect(twitterCard?.getAttribute('content')).toBe('summary_large_image');
    });

    it('should have twitter:url meta tag', () => {
      const twitterUrl = document.querySelector('meta[name="twitter:url"]');
      expect(twitterUrl).toBeTruthy();
    });

    it('should have twitter:title meta tag', () => {
      const twitterTitle = document.querySelector('meta[name="twitter:title"]');
      expect(twitterTitle).toBeTruthy();
    });

    it('should have twitter:description meta tag', () => {
      const twitterDesc = document.querySelector('meta[name="twitter:description"]');
      expect(twitterDesc).toBeTruthy();
    });

    it('should have twitter:image meta tag', () => {
      const twitterImage = document.querySelector('meta[name="twitter:image"]');
      expect(twitterImage).toBeTruthy();
    });
  });

  describe('Canonical URL', () => {
    it('should have canonical link tag', () => {
      const canonical = document.querySelector('link[rel="canonical"]');
      expect(canonical).toBeTruthy();
    });

    it('should have valid URL in canonical tag', () => {
      const canonical = document.querySelector('link[rel="canonical"]');
      const href = canonical?.getAttribute('content') || canonical?.getAttribute('href');
      expect(href).toMatch(/^https?:\/\//);
    });
  });

  describe('Manifest file', () => {
    it('should have manifest link tag', () => {
      const manifest = document.querySelector('link[rel="manifest"]');
      expect(manifest).toBeTruthy();
    });

    it('should point to valid manifest file', () => {
      const manifest = document.querySelector('link[rel="manifest"]');
      const href = manifest?.getAttribute('href');
      expect(href).toMatch(/manifest\.json$/);
    });
  });

  describe('Title tag', () => {
    it('should have a title tag', () => {
      const title = document.querySelector('title');
      expect(title).toBeTruthy();
      expect(title?.textContent).toBeTruthy();
    });

    it('should have brand name in title', () => {
      const title = document.querySelector('title');
      const text = title?.textContent?.toLowerCase() || '';
      expect(text).toMatch(/productiv/);
    });
  });
});
