import { useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

type MaxWidth = 'max-w-sm' | 'max-w-md' | 'max-w-lg' | 'max-w-xl' | 'max-w-2xl' | 'max-w-4xl';
type MaxHeight = 'max-h-[80vh]' | 'max-h-[90vh]' | 'max-h-[95vh]';
type Padding = 'p-0' | 'p-4' | 'p-6' | 'p-8';

interface NeoModalProps {
    isOpen: boolean;
    onClose: () => void;
    maxWidth?: MaxWidth;
    maxHeight?: MaxHeight;
    padding?: Padding;
    showCloseButton?: boolean;
    closeOnBackdropClick?: boolean;
    closeOnEscape?: boolean;
    title?: string;
    titleId?: string;
    children: React.ReactNode;
    className?: string;
}

export default function NeoModal({
    isOpen,
    onClose,
    maxWidth = 'max-w-md',
    maxHeight = 'max-h-[90vh]',
    padding = 'p-6',
    showCloseButton = true,
    closeOnBackdropClick = true,
    closeOnEscape = true,
    title,
    titleId = 'neo-modal-title',
    children,
    className = '',
}: NeoModalProps) {
    const modalRef = useRef<HTMLDivElement>(null);
    const previousActiveElementRef = useRef<HTMLElement | null>(null);

    // Handle Escape key
    useEffect(() => {
        if (!isOpen || !closeOnEscape) return;

        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose();
            }
        };

        document.addEventListener('keydown', handleEscape);
        return () => document.removeEventListener('keydown', handleEscape);
    }, [isOpen, closeOnEscape, onClose]);

    // Focus trap and focus management
    useEffect(() => {
        if (!isOpen) return;

        // Store the currently focused element using ref to avoid re-renders
        previousActiveElementRef.current = document.activeElement as HTMLElement;

        const modal = modalRef.current;
        if (!modal) return;

        // Focus first focusable element
        const focusableElements = modal.querySelectorAll<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        if (firstElement) {
            firstElement.focus();
        }

        // Trap focus within modal
        const handleTab = (e: KeyboardEvent) => {
            if (e.key !== 'Tab') return;

            const lastElement = focusableElements[focusableElements.length - 1];

            if (e.shiftKey && document.activeElement === firstElement) {
                e.preventDefault();
                lastElement?.focus();
            } else if (!e.shiftKey && document.activeElement === lastElement) {
                e.preventDefault();
                firstElement?.focus();
            }
        };

        document.addEventListener('keydown', handleTab);

        // Restore focus when modal closes
        return () => {
            document.removeEventListener('keydown', handleTab);
            if (previousActiveElementRef.current) {
                previousActiveElementRef.current.focus();
            }
        };
    }, [isOpen]); // Only depends on isOpen - NO infinite loop

    // Prevent body scroll when modal is open
    useEffect(() => {
        if (!isOpen) return;

        document.body.style.overflow = 'hidden';
        return () => {
            document.body.style.overflow = '';
        };
    }, [isOpen]);

    const handleBackdropClick = useCallback((e: React.MouseEvent) => {
        if (closeOnBackdropClick && e.target === e.currentTarget) {
            onClose();
        }
    }, [closeOnBackdropClick, onClose]);

    const handleContentClick = useCallback((e: React.MouseEvent) => {
        e.stopPropagation();
    }, []);

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
                    onClick={handleBackdropClick}
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby={title ? titleId : undefined}
                >
                    <motion.div
                        ref={modalRef}
                        initial={{ scale: 0.9, y: 20 }}
                        animate={{ scale: 1, y: 0 }}
                        exit={{ scale: 0.9, y: 20 }}
                        transition={{ duration: 0.2 }}
                        className={`bg-white border-4 border-black shadow-[6px_6px_0_0_#000] ${maxWidth} w-full ${maxHeight} overflow-y-auto ${padding} relative ${className}`}
                        onClick={handleContentClick}
                    >
                        {showCloseButton && (
                            <button
                                onClick={onClose}
                                className="absolute top-4 right-4 p-2 hover:bg-gray-200 border-2 border-black transition-colors z-10"
                                aria-label="Close modal"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        )}

                        {title && (
                            <h2 id={titleId} className="text-xl font-black uppercase mb-6 pr-12">
                                {title}
                            </h2>
                        )}

                        {children}
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
