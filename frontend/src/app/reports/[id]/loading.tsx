import Skeleton from "@/components/Skeleton";

export default function ReportLoading() {
  return (
    <div className="min-h-screen bg-gray-50" data-testid="report-loading">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="space-y-4">
            <Skeleton width="60%" height={28} />
            <Skeleton width="40%" height={16} />
            <div className="pt-4 space-y-3">
              <Skeleton width="100%" height={16} />
              <Skeleton width="90%" height={16} />
              <Skeleton width="95%" height={16} />
              <Skeleton width="70%" height={16} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
