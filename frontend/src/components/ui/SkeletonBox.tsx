interface SkeletonBoxProps {
  className?: string;
}

/**
 * Primitive skeleton component for loading states.
 * Uses design tokens for consistent styling.
 *
 * @example
 * <SkeletonBox className="h-8 w-32" />
 * <SkeletonBox className="h-32 w-32 rounded-full" />
 */
export function SkeletonBox({ className = '' }: SkeletonBoxProps) {
  return (
    <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
  );
}
