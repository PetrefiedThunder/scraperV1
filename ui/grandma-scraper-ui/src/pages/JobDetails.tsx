/**
 * Job details page with results and controls
 */

import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '@/services/api';
import { Layout } from '@/components/Layout';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { ScrapeResult } from '@/types';

export function JobDetails() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedResult, setSelectedResult] = useState<string | null>(null);

  // Fetch job details
  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.getJob(jobId!),
    enabled: !!jobId,
  });

  // Fetch job results
  const { data: results, isLoading: resultsLoading } = useQuery({
    queryKey: ['results', jobId],
    queryFn: () => api.getJobResults(jobId!),
    enabled: !!jobId,
  });

  // Real-time updates via WebSocket
  const handleProgress = useCallback(() => {
    // Invalidate and refetch results when progress is received
    queryClient.invalidateQueries({ queryKey: ['results', jobId] });
  }, [queryClient, jobId]);

  const handleCompletion = useCallback(() => {
    // Invalidate and refetch results when job completes
    queryClient.invalidateQueries({ queryKey: ['results', jobId] });
  }, [queryClient, jobId]);

  useWebSocket({
    onProgress: handleProgress,
    onCompletion: handleCompletion,
    enabled: true,
  });

  // Fetch selected result details
  const { data: resultDetails } = useQuery({
    queryKey: ['result', selectedResult],
    queryFn: () => api.getResult(selectedResult!),
    enabled: !!selectedResult,
  });

  // Run job mutation
  const runJobMutation = useMutation({
    mutationFn: () => api.runJob(jobId!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['results', jobId] });
    },
  });

  // Delete job mutation
  const deleteJobMutation = useMutation({
    mutationFn: () => api.deleteJob(jobId!),
    onSuccess: () => {
      navigate('/dashboard');
    },
  });

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      running: 'bg-blue-100 text-blue-800',
      failed: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const handleRunJob = async () => {
    if (window.confirm('Run this scraping job now?')) {
      runJobMutation.mutate();
    }
  };

  const handleDeleteJob = async () => {
    if (window.confirm('Are you sure you want to delete this job? This cannot be undone.')) {
      deleteJobMutation.mutate();
    }
  };

  const handleDownloadResult = async (resultId: string, format: 'json' | 'csv') => {
    try {
      const blob = await api.downloadResult(resultId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `result-${resultId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  if (jobLoading) {
    return (
      <Layout>
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        </div>
      </Layout>
    );
  }

  if (!job) {
    return (
      <Layout>
        <div className="text-center py-12">
          <p className="text-red-600">Job not found</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{job.name}</h1>
            <p className="text-gray-600 mt-1">{job.config.start_url}</p>
          </div>
          <div className="flex space-x-3">
            <button
              onClick={handleRunJob}
              disabled={runJobMutation.isPending}
              className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-2 rounded-lg transition disabled:opacity-50"
            >
              {runJobMutation.isPending ? 'Starting...' : 'Run Now'}
            </button>
            <button
              onClick={handleDeleteJob}
              disabled={deleteJobMutation.isPending}
              className="bg-red-600 hover:bg-red-700 text-white font-semibold px-6 py-2 rounded-lg transition disabled:opacity-50"
            >
              Delete
            </button>
          </div>
        </div>

        {/* Job Configuration */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Configuration</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Item Selector:</span>
              <p className="font-mono text-gray-900 mt-1">{job.config.item_selector}</p>
            </div>
            <div>
              <span className="text-gray-600">Fields:</span>
              <p className="text-gray-900 mt-1">{job.config.fields?.length || 0} configured</p>
            </div>
            {job.config.max_pages && (
              <div>
                <span className="text-gray-600">Max Pages:</span>
                <p className="text-gray-900 mt-1">{job.config.max_pages}</p>
              </div>
            )}
            <div>
              <span className="text-gray-600">Status:</span>
              <p className="text-gray-900 mt-1">{job.enabled ? 'Enabled' : 'Disabled'}</p>
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold mb-4">Results History</h2>

          {resultsLoading && (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          )}

          {!resultsLoading && results && results.length === 0 && (
            <p className="text-gray-600 text-center py-8">No results yet. Run the job to see results.</p>
          )}

          {!resultsLoading && results && results.length > 0 && (
            <div className="space-y-3">
              {results.map((result: ScrapeResult) => (
                <div
                  key={result.id}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition cursor-pointer"
                  onClick={() => setSelectedResult(result.id)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(result.status)}`}>
                          {result.status}
                        </span>
                        {result.total_items !== null && (
                          <span className="text-sm text-gray-600">
                            {result.total_items} items scraped
                          </span>
                        )}
                        {result.pages_scraped !== null && (
                          <span className="text-sm text-gray-600">
                            {result.pages_scraped} pages
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">
                        Started: {result.started_at ? new Date(result.started_at).toLocaleString() : 'N/A'}
                      </p>
                      {result.completed_at && (
                        <p className="text-sm text-gray-600">
                          Completed: {new Date(result.completed_at).toLocaleString()}
                          {result.duration_seconds && ` (${result.duration_seconds}s)`}
                        </p>
                      )}
                      {result.error_message && (
                        <p className="text-sm text-red-600 mt-2">Error: {result.error_message}</p>
                      )}
                    </div>
                    {result.status === 'completed' && (
                      <div className="flex space-x-2 ml-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDownloadResult(result.id, 'json');
                          }}
                          className="text-sm text-purple-600 hover:text-purple-700 font-medium"
                        >
                          JSON
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDownloadResult(result.id, 'csv');
                          }}
                          className="text-sm text-purple-600 hover:text-purple-700 font-medium"
                        >
                          CSV
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Result Details Modal */}
        {selectedResult && resultDetails && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            onClick={() => setSelectedResult(null)}
          >
            <div
              className="bg-white rounded-lg max-w-4xl w-full max-h-[80vh] overflow-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                <h3 className="text-xl font-semibold">Scraped Data</h3>
                <button
                  onClick={() => setSelectedResult(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6">
                {resultDetails.items && resultDetails.items.length > 0 ? (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          {Object.keys(resultDetails.items[0]).map((key) => (
                            <th
                              key={key}
                              className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                            >
                              {key}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {resultDetails.items.map((item: any, idx: number) => (
                          <tr key={idx}>
                            {Object.values(item).map((value: any, vidx: number) => (
                              <td key={vidx} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {String(value)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-gray-600 text-center py-8">No data available</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
