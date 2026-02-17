import Skeleton from "@/components/Skeleton";

export default function StockDetailLoading() {
  return (
    <div className="min-h-screen bg-gray-50" data-testid="stock-detail-skeleton">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {/* Header skeleton */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <Skeleton width="200px" height={28} />
              <Skeleton width="120px" height={16} />
            </div>
            <div className="space-y-2">
              <Skeleton width="140px" height={24} />
              <Skeleton width="80px" height={14} />
            </div>
          </div>
        </div>
        {/* Timeline skeleton */}
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center gap-4">
                <Skeleton width="80px" height={16} />
                <div className="flex-1 space-y-2">
                  <Skeleton width="60%" height={16} />
                  <Skeleton width="40%" height={14} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
