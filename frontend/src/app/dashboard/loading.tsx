import Skeleton from "@/components/Skeleton";

export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-gray-50" data-testid="dashboard-loading">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <Skeleton width="200px" height={32} />
          <div className="mt-2">
            <Skeleton width="300px" height={16} />
          </div>
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-white rounded-lg border border-gray-200 p-6"
              data-testid="stockcard-skeleton"
            >
              <div className="flex items-center justify-between">
                <div className="space-y-2">
                  <Skeleton width="160px" height={20} />
                  <Skeleton width="100px" height={14} />
                </div>
                <div className="text-right space-y-2">
                  <Skeleton width="120px" height={20} />
                  <Skeleton width="80px" height={14} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
