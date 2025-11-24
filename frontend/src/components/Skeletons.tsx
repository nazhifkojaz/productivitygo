// Loading Skeleton Components
// Provides content-aware loading states for better UX

export function ProfileSkeleton() {
    return (
        <div className="animate-pulse">
            <div className="flex flex-col md:flex-row items-center gap-8">
                {/* Avatar skeleton */}
                <div className="w-32 h-32 bg-gray-200 border-3 border-black rounded-full" />

                <div className="text-center md:text-left flex-1">
                    {/* Username skeleton */}
                    <div className="h-8 bg-gray-200 rounded w-48 mb-2" />
                    {/* Email skeleton */}
                    <div className="h-4 bg-gray-200 rounded w-32 mb-4" />
                    {/* Level badges */}
                    <div className="flex gap-2 justify-center md:justify-start">
                        <div className="h-6 bg-gray-200 rounded w-20" />
                        <div className="h-6 bg-gray-200 rounded w-24" />
                    </div>
                </div>
            </div>

            {/* Stats grid skeleton */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-8">
                {[1, 2, 3, 4, 5].map(i => (
                    <div key={i} className="bg-gray-100 border-3 border-black p-4">
                        <div className="h-8 bg-gray-200 rounded w-16 mx-auto mb-2" />
                        <div className="h-3 bg-gray-200 rounded w-24 mx-auto" />
                    </div>
                ))}
            </div>
        </div>
    );
}

export function UserListSkeleton({ count = 3 }: { count?: number }) {
    return (
        <div className="space-y-4">
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="bg-white border-3 border-black p-4 flex items-center justify-between animate-pulse">
                    <div className="flex items-center gap-4">
                        {/* Avatar skeleton */}
                        <div className="w-12 h-12 bg-gray-200 rounded-full border-2 border-black" />
                        <div>
                            {/* Username skeleton */}
                            <div className="h-5 bg-gray-200 rounded w-32 mb-1" />
                            {/* Level skeleton */}
                            <div className="h-3 bg-gray-200 rounded w-16" />
                        </div>
                    </div>
                    {/* Button skeleton */}
                    <div className="h-10 w-24 bg-gray-200 border-2 border-black" />
                </div>
            ))}
        </div>
    );
}

export function BattleCardSkeleton({ count = 2 }: { count?: number }) {
    return (
        <div className="space-y-4">
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className="bg-neo-white border-3 border-black p-6 animate-pulse">
                    {/* Header */}
                    <div className="flex justify-between items-center mb-4">
                        <div className="h-6 bg-gray-200 rounded w-32" />
                        <div className="h-5 bg-gray-200 rounded w-20" />
                    </div>

                    {/* Rival info */}
                    <div className="flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 bg-gray-200 rounded-full border-2 border-black" />
                        <div>
                            <div className="h-5 bg-gray-200 rounded w-24 mb-1" />
                            <div className="h-3 bg-gray-200 rounded w-32" />

                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                        <div className="h-10 bg-gray-200 border-2 border-black rounded flex-1" />
                        <div className="h-10 bg-gray-200 border-2 border-black rounded flex-1" />
                    </div>
                </div>
            ))}
        </div>
    );
}

export function DashboardSkeleton() {
    return (
        <div className="min-h-screen bg-neo-bg p-4 md:p-8 pb-24 animate-pulse">
            <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8">
                {/* Left column skeleton */}
                <div className="md:col-span-4 space-y-8">
                    <div className="bg-neo-white border-4 border-black shadow-neo p-6">
                        <div className="h-32 bg-gray-200 rounded mb-4" />
                        <div className="grid grid-cols-2 gap-4">
                            {[1, 2, 3, 4].map(i => (
                                <div key={i} className="h-20 bg-gray-200 border-3 border-black" />
                            ))}
                        </div>
                    </div>
                </div>

                {/* Right column skeleton */}
                <div className="md:col-span-8 space-y-6">
                    <div className="bg-neo-white border-4 border-black shadow-neo p-6">
                        <div className="h-64 bg-gray-200 rounded" />
                    </div>
                </div>
            </div>
        </div>
    );
}

export function PublicProfileSkeleton() {
    return (
        <div className="min-h-screen bg-neo-bg p-4 md:p-8 pb-24 animate-pulse">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="h-8 bg-gray-200 rounded w-32 mb-4" />
                </div>

                {/* Profile card */}
                <div className="bg-neo-white border-4 border-black shadow-neo p-6 md:p-8">
                    <div className="flex flex-col md:flex-row items-center gap-6 mb-6">
                        <div className="w-24 h-24 bg-gray-200 rounded-full border-4 border-black" />
                        <div className="text-center md:text-left flex-1">
                            <div className="h-8 bg-gray-200 rounded w-48 mb-2 mx-auto md:mx-0" />
                            <div className="h-5 bg-gray-200 rounded w-32 mb-4 mx-auto md:mx-0" />
                            <div className="flex gap-2 justify-center md:justify-start">
                                <div className="h-6 bg-gray-200 w-20" />
                                <div className="h-6 bg-gray-200 w-20" />
                            </div>
                        </div>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        {[1, 2, 3, 4].map(i => (
                            <div key={i} className="bg-gray-100 border-3 border-black p-4">
                                <div className="h-6 bg-gray-200 rounded w-12 mx-auto mb-1" />
                                <div className="h-3 bg-gray-200 rounded w-16 mx-auto" />
                            </div>
                        ))}
                    </div>

                    {/* Match history */}
                    <div className="space-y-2">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-12 bg-gray-200 border-2 border-black" />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
