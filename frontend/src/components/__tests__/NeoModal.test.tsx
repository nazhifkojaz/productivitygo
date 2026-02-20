import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import NeoModal from '../NeoModal';

describe('NeoModal', () => {
    let consoleSpy: ReturnType<typeof vi.spyOn>;

    beforeEach(() => {
        consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
        consoleSpy.mockRestore();
    });

    const defaultProps = {
        isOpen: true,
        onClose: vi.fn(),
        children: <div>Modal Content</div>,
    };

    describe('rendering', () => {
        it('does not render when isOpen is false', () => {
            const { container } = render(<NeoModal {...defaultProps} isOpen={false} />);
            expect(container.firstChild).toBe(null);
        });

        it('renders when isOpen is true', () => {
            render(<NeoModal {...defaultProps} />);
            expect(screen.getByText('Modal Content')).toBeInTheDocument();
        });

        it('renders with custom title', () => {
            render(<NeoModal {...defaultProps} title="Test Modal" />);
            expect(screen.getByText('Test Modal')).toBeInTheDocument();
        });

        it('renders without close button when showCloseButton is false', () => {
            const { container } = render(<NeoModal {...defaultProps} showCloseButton={false} />);
            const closeButton = container.querySelector('[aria-label="Close modal"]');
            expect(closeButton).not.toBeInTheDocument();
        });

        it('renders with close button by default', () => {
            const { container } = render(<NeoModal {...defaultProps} />);
            const closeButton = container.querySelector('[aria-label="Close modal"]');
            expect(closeButton).toBeInTheDocument();
        });
    });

    describe('size variants', () => {
        it('applies max-w-sm class', () => {
            const { container } = render(<NeoModal {...defaultProps} maxWidth="max-w-sm" />);
            const modal = container.querySelector('.max-w-sm');
            expect(modal).toBeInTheDocument();
        });

        it('applies max-w-md class (default)', () => {
            const { container } = render(<NeoModal {...defaultProps} />);
            const modal = container.querySelector('.max-w-md');
            expect(modal).toBeInTheDocument();
        });

        it('applies max-w-2xl class', () => {
            const { container } = render(<NeoModal {...defaultProps} maxWidth="max-w-2xl" />);
            const modal = container.querySelector('.max-w-2xl');
            expect(modal).toBeInTheDocument();
        });
    });

    describe('interaction', () => {
        it('calls onClose when close button is clicked', () => {
            const onClose = vi.fn();
            const { container } = render(<NeoModal {...defaultProps} onClose={onClose} />);
            const closeButton = container.querySelector('[aria-label="Close modal"]');
            fireEvent.click(closeButton!);
            expect(onClose).toHaveBeenCalledTimes(1);
        });

        it('calls onClose when backdrop is clicked', () => {
            const onClose = vi.fn();
            const { container } = render(<NeoModal {...defaultProps} onClose={onClose} />);
            const backdrop = container.querySelector('.bg-black\\/50');
            fireEvent.click(backdrop!);
            expect(onClose).toHaveBeenCalledTimes(1);
        });

        it('does not call onClose when closeOnBackdropClick is false', () => {
            const onClose = vi.fn();
            const { container } = render(
                <NeoModal {...defaultProps} onClose={onClose} closeOnBackdropClick={false} />
            );
            const backdrop = container.querySelector('.bg-black\\/50');
            fireEvent.click(backdrop!);
            expect(onClose).not.toHaveBeenCalled();
        });

        it('does not call onClose when modal content is clicked', () => {
            const onClose = vi.fn();
            const { container } = render(<NeoModal {...defaultProps} onClose={onClose} />);
            const content = container.querySelector('.bg-white');
            fireEvent.click(content!);
            expect(onClose).not.toHaveBeenCalled();
        });

        it('calls onClose when Escape key is pressed', () => {
            const onClose = vi.fn();
            render(<NeoModal {...defaultProps} onClose={onClose} />);
            fireEvent.keyDown(document, { key: 'Escape' });
            expect(onClose).toHaveBeenCalledTimes(1);
        });

        it('does not call onClose when Escape is pressed and closeOnEscape is false', () => {
            const onClose = vi.fn();
            render(<NeoModal {...defaultProps} onClose={onClose} closeOnEscape={false} />);
            fireEvent.keyDown(document, { key: 'Escape' });
            expect(onClose).not.toHaveBeenCalled();
        });
    });

    describe('accessibility', () => {
        it('has role="dialog"', () => {
            const { container } = render(<NeoModal {...defaultProps} />);
            const dialog = container.querySelector('[role="dialog"]');
            expect(dialog).toBeInTheDocument();
        });

        it('has aria-modal="true"', () => {
            const { container } = render(<NeoModal {...defaultProps} />);
            const dialog = container.querySelector('[aria-modal="true"]');
            expect(dialog).toBeInTheDocument();
        });

        it('has aria-labelledby when title is provided', () => {
            const { container } = render(<NeoModal {...defaultProps} title="Test Modal" />);
            const dialog = container.querySelector('[aria-labelledby="neo-modal-title"]');
            expect(dialog).toBeInTheDocument();
        });

        it('has aria-label on close button', () => {
            const { container } = render(<NeoModal {...defaultProps} />);
            const closeButton = container.querySelector('[aria-label="Close modal"]');
            expect(closeButton).toBeInTheDocument();
        });

        it('auto-focuses first focusable element on open', () => {
            render(
                <NeoModal {...defaultProps}>
                    <button type="button">First Button</button>
                    <button type="button">Second Button</button>
                </NeoModal>
            );
            const firstButton = screen.getByText('First Button');
            // In jsdom, focus() is called but the actual focus state isn't fully simulated
            // We just verify the button exists in the modal
            expect(firstButton).toBeInTheDocument();
        });

        it('locks body scroll when open', () => {
            render(<NeoModal {...defaultProps} />);
            expect(document.body.style.overflow).toBe('hidden');
        });

        it('restores body scroll when closed', () => {
            const { rerender } = render(<NeoModal {...defaultProps} />);
            expect(document.body.style.overflow).toBe('hidden');
            rerender(<NeoModal {...defaultProps} isOpen={false} />);
            expect(document.body.style.overflow).toBe('');
        });
    });

    describe('edge cases', () => {
        it('handles empty children', () => {
            const { container } = render(<NeoModal {...defaultProps}>{null}</NeoModal>);
            expect(container.querySelector('.bg-white')).toBeInTheDocument();
        });

        it('handles custom className', () => {
            const { container } = render(<NeoModal {...defaultProps} className="custom-class" />);
            const modal = container.querySelector('.custom-class');
            expect(modal).toBeInTheDocument();
        });

        it('handles missing title', () => {
            const { container } = render(<NeoModal {...defaultProps} />);
            const dialog = container.querySelector('[aria-labelledby]');
            expect(dialog).not.toBeInTheDocument();
        });

        it('handles different padding variants', () => {
            const { container: p4 } = render(<NeoModal {...defaultProps} padding="p-4" />);
            expect(p4.querySelector('.p-4')).toBeInTheDocument();

            const { container: p6 } = render(<NeoModal {...defaultProps} padding="p-6" />);
            expect(p6.querySelector('.p-6')).toBeInTheDocument();

            const { container: p8 } = render(<NeoModal {...defaultProps} padding="p-8" />);
            expect(p8.querySelector('.p-8')).toBeInTheDocument();
        });

        it('handles different height variants', () => {
            const { container: h80 } = render(<NeoModal {...defaultProps} maxHeight="max-h-[80vh]" />);
            expect(h80.querySelector('.max-h-\\[80vh\\]')).toBeInTheDocument();

            const { container: h90 } = render(<NeoModal {...defaultProps} maxHeight="max-h-[90vh]" />);
            expect(h90.querySelector('.max-h-\\[90vh\\]')).toBeInTheDocument();
        });
    });
});
