/**
 * Job creation wizard with visual selector picking
 * Multi-step form that makes scraping accessible to everyone
 */

import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { api } from '@/services/api';
import { Layout } from '@/components/Layout';
import { VisualSelectorPicker } from '@/components/VisualSelectorPicker';
import type { ScrapeJobCreate, FieldConfig } from '@/types';

type WizardStep = 'basic' | 'item-selector' | 'fields' | 'pagination' | 'review';

export function JobWizard() {
  const navigate = useNavigate();
  const location = useLocation();
  const templateConfig = location.state?.template?.config;

  const [currentStep, setCurrentStep] = useState<WizardStep>('basic');
  const [jobData, setJobData] = useState<Partial<ScrapeJobCreate>>({
    name: '',
    config: {
      start_url: '',
      item_selector: templateConfig?.item_selector || '',
      fields: templateConfig?.fields || [],
      max_pages: 10,
      respect_robots_txt: true,
      rate_limit: 1,
    },
    enabled: true,
  });

  const [currentField, setCurrentField] = useState<FieldConfig>({
    name: '',
    selector: '',
    type: 'text',
    required: false,
  });

  const createJobMutation = useMutation({
    mutationFn: (data: ScrapeJobCreate) => api.createJob(data),
    onSuccess: (job) => {
      navigate(`/jobs/${job.id}`);
    },
  });

  const handleBasicInfoSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentStep('item-selector');
  };

  const handleItemSelectorSelected = (selector: string, _sampleText: string) => {
    setJobData((prev) => ({
      ...prev,
      config: {
        ...prev.config!,
        item_selector: selector,
      },
    }));
  };

  const handleFieldSelectorSelected = (selector: string, _sampleText: string) => {
    setCurrentField((prev) => ({
      ...prev,
      selector,
    }));
  };

  const handleAddField = () => {
    if (!currentField.name || !currentField.selector) {
      alert('Please provide both field name and selector');
      return;
    }

    setJobData((prev) => ({
      ...prev,
      config: {
        ...prev.config!,
        fields: [...(prev.config!.fields || []), currentField],
      },
    }));

    // Reset current field
    setCurrentField({
      name: '',
      selector: '',
      type: 'text',
      required: false,
    });
  };

  const handleRemoveField = (index: number) => {
    setJobData((prev) => ({
      ...prev,
      config: {
        ...prev.config!,
        fields: prev.config!.fields?.filter((_field, i) => i !== index) || [],
      },
    }));
  };

  const handleSubmit = async () => {
    if (!jobData.name || !jobData.config?.start_url || !jobData.config?.item_selector) {
      alert('Please complete all required fields');
      return;
    }

    if (!jobData.config.fields || jobData.config.fields.length === 0) {
      alert('Please add at least one field to extract');
      return;
    }

    createJobMutation.mutate(jobData as ScrapeJobCreate);
  };

  const steps: { id: WizardStep; label: string }[] = [
    { id: 'basic', label: 'Basic Info' },
    { id: 'item-selector', label: 'Item Container' },
    { id: 'fields', label: 'Data Fields' },
    { id: 'pagination', label: 'Pagination' },
    { id: 'review', label: 'Review' },
  ];

  const currentStepIndex = steps.findIndex((s) => s.id === currentStep);

  return (
    <Layout>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Create Scraping Job</h1>
          <p className="text-gray-600 mt-1">Follow the steps to set up your web scraper</p>
        </div>

        {/* Progress Bar */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex items-center flex-col">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                      index <= currentStepIndex
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {index + 1}
                  </div>
                  <span
                    className={`text-sm mt-2 ${
                      index <= currentStepIndex ? 'text-purple-600 font-medium' : 'text-gray-600'
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`flex-1 h-1 mx-4 ${
                      index < currentStepIndex ? 'bg-purple-600' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          {/* Step 1: Basic Info */}
          {currentStep === 'basic' && (
            <form onSubmit={handleBasicInfoSubmit} className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-4">Basic Information</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Job Name *
                    </label>
                    <input
                      type="text"
                      value={jobData.name}
                      onChange={(e) => setJobData({ ...jobData, name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                      placeholder="e.g., Amazon Product Scraper"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Start URL *
                    </label>
                    <input
                      type="url"
                      value={jobData.config?.start_url}
                      onChange={(e) =>
                        setJobData({
                          ...jobData,
                          config: { ...jobData.config!, start_url: e.target.value },
                        })
                      }
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                      placeholder="https://example.com/products"
                      required
                    />
                    <p className="text-sm text-gray-600 mt-1">
                      The URL of the page you want to scrape
                    </p>
                  </div>
                </div>
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-2 rounded-lg transition"
                >
                  Next: Select Items
                </button>
              </div>
            </form>
          )}

          {/* Step 2: Item Selector */}
          {currentStep === 'item-selector' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-2">Select Item Container</h2>
                <p className="text-gray-600">
                  Click on one of the repeating items on the page (e.g., a product card, article, listing)
                </p>
              </div>

              {jobData.config?.start_url ? (
                <VisualSelectorPicker
                  url={jobData.config.start_url}
                  onSelectorSelected={handleItemSelectorSelected}
                  mode="item"
                />
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <p className="text-yellow-800">Please enter a start URL first</p>
                </div>
              )}

              {/* Manual input option */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Or enter CSS selector manually:
                </label>
                <input
                  type="text"
                  value={jobData.config?.item_selector}
                  onChange={(e) =>
                    setJobData({
                      ...jobData,
                      config: { ...jobData.config!, item_selector: e.target.value },
                    })
                  }
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none font-mono text-sm"
                  placeholder=".product-card, article, .listing"
                />
              </div>

              <div className="flex justify-between">
                <button
                  onClick={() => setCurrentStep('basic')}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-6 py-2 rounded-lg transition"
                >
                  Back
                </button>
                <button
                  onClick={() => setCurrentStep('fields')}
                  disabled={!jobData.config?.item_selector}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-2 rounded-lg transition disabled:opacity-50"
                >
                  Next: Add Fields
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Fields */}
          {currentStep === 'fields' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-2">Configure Data Fields</h2>
                <p className="text-gray-600">
                  Add the fields you want to extract from each item
                </p>
              </div>

              {/* Existing fields */}
              {jobData.config?.fields && jobData.config.fields.length > 0 && (
                <div className="space-y-2">
                  <h3 className="font-medium text-gray-900">Configured Fields:</h3>
                  {jobData.config.fields.map((field, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between bg-gray-50 p-4 rounded-lg border border-gray-200"
                    >
                      <div>
                        <p className="font-medium text-gray-900">{field.name}</p>
                        <p className="text-sm text-gray-600 font-mono">{field.selector}</p>
                        <div className="flex items-center space-x-3 mt-1">
                          <span className="text-xs text-gray-500">Type: {field.type}</span>
                          {field.required && (
                            <span className="text-xs bg-red-100 text-red-800 px-2 py-0.5 rounded">
                              Required
                            </span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveField(index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Add new field */}
              <div className="border-t border-gray-200 pt-6">
                <h3 className="font-medium text-gray-900 mb-4">Add New Field:</h3>

                <div className="space-y-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Field Name *
                    </label>
                    <input
                      type="text"
                      value={currentField.name}
                      onChange={(e) => setCurrentField({ ...currentField, name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                      placeholder="e.g., title, price, description"
                    />
                  </div>

                  {jobData.config?.start_url && (
                    <VisualSelectorPicker
                      url={jobData.config.start_url}
                      onSelectorSelected={handleFieldSelectorSelected}
                      mode="field"
                      label={currentField.name || 'this field'}
                    />
                  )}

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      CSS Selector *
                    </label>
                    <input
                      type="text"
                      value={currentField.selector}
                      onChange={(e) => setCurrentField({ ...currentField, selector: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none font-mono text-sm"
                      placeholder=".title, h2, .price"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Field Type
                      </label>
                      <select
                        value={currentField.type || 'text'}
                        onChange={(e) => setCurrentField({ ...currentField, type: e.target.value as 'text' | 'number' | 'url' })}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                      >
                        <option value="text">Text</option>
                        <option value="number">Number</option>
                        <option value="url">URL</option>
                      </select>
                    </div>
                    <div className="flex items-center">
                      <label className="flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={currentField.required}
                          onChange={(e) => setCurrentField({ ...currentField, required: e.target.checked })}
                          className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                        />
                        <span className="ml-2 text-sm text-gray-700">Required field</span>
                      </label>
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleAddField}
                  className="w-full bg-purple-100 hover:bg-purple-200 text-purple-700 font-medium px-4 py-2 rounded-lg transition"
                >
                  + Add Field
                </button>
              </div>

              <div className="flex justify-between">
                <button
                  onClick={() => setCurrentStep('item-selector')}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-6 py-2 rounded-lg transition"
                >
                  Back
                </button>
                <button
                  onClick={() => setCurrentStep('pagination')}
                  disabled={!jobData.config?.fields || jobData.config.fields.length === 0}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-2 rounded-lg transition disabled:opacity-50"
                >
                  Next: Pagination
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Pagination */}
          {currentStep === 'pagination' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-2">Pagination Settings</h2>
                <p className="text-gray-600">Configure how to navigate through multiple pages</p>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Maximum Pages to Scrape
                  </label>
                  <input
                    type="number"
                    value={jobData.config?.max_pages}
                    onChange={(e) =>
                      setJobData({
                        ...jobData,
                        config: { ...jobData.config!, max_pages: parseInt(e.target.value) || 1 },
                      })
                    }
                    min="1"
                    max="100"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                  />
                  <p className="text-sm text-gray-600 mt-1">Limit: 1-100 pages</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rate Limit (seconds between requests)
                  </label>
                  <input
                    type="number"
                    value={jobData.config?.rate_limit}
                    onChange={(e) =>
                      setJobData({
                        ...jobData,
                        config: { ...jobData.config!, rate_limit: parseFloat(e.target.value) || 1 },
                      })
                    }
                    min="0.5"
                    step="0.5"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
                  />
                  <p className="text-sm text-gray-600 mt-1">
                    Delay between page requests to be respectful to servers
                  </p>
                </div>

                <div className="flex items-center">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={jobData.config?.respect_robots_txt}
                      onChange={(e) =>
                        setJobData({
                          ...jobData,
                          config: { ...jobData.config!, respect_robots_txt: e.target.checked },
                        })
                      }
                      className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      Respect robots.txt (recommended)
                    </span>
                  </label>
                </div>
              </div>

              <div className="flex justify-between">
                <button
                  onClick={() => setCurrentStep('fields')}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-6 py-2 rounded-lg transition"
                >
                  Back
                </button>
                <button
                  onClick={() => setCurrentStep('review')}
                  className="bg-purple-600 hover:bg-purple-700 text-white font-semibold px-6 py-2 rounded-lg transition"
                >
                  Next: Review
                </button>
              </div>
            </div>
          )}

          {/* Step 5: Review */}
          {currentStep === 'review' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold mb-2">Review Configuration</h2>
                <p className="text-gray-600">Check your scraping job configuration before creating</p>
              </div>

              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">Job Name</h3>
                  <p className="text-gray-700">{jobData.name}</p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">Start URL</h3>
                  <p className="text-gray-700 break-all">{jobData.config?.start_url}</p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">Item Selector</h3>
                  <code className="text-sm bg-white px-3 py-2 rounded border border-gray-200 block font-mono">
                    {jobData.config?.item_selector}
                  </code>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-3">
                    Fields ({jobData.config?.fields?.length || 0})
                  </h3>
                  <div className="space-y-2">
                    {jobData.config?.fields?.map((field, index) => (
                      <div key={index} className="bg-white p-3 rounded border border-gray-200">
                        <p className="font-medium text-gray-900">{field.name}</p>
                        <code className="text-xs text-gray-600 font-mono">{field.selector}</code>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">Settings</h3>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>Max Pages: {jobData.config?.max_pages}</li>
                    <li>Rate Limit: {jobData.config?.rate_limit}s</li>
                    <li>Respect robots.txt: {jobData.config?.respect_robots_txt ? 'Yes' : 'No'}</li>
                  </ul>
                </div>
              </div>

              <div className="flex justify-between">
                <button
                  onClick={() => setCurrentStep('pagination')}
                  className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold px-6 py-2 rounded-lg transition"
                >
                  Back
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={createJobMutation.isPending}
                  className="bg-green-600 hover:bg-green-700 text-white font-semibold px-8 py-2 rounded-lg transition disabled:opacity-50"
                >
                  {createJobMutation.isPending ? 'Creating...' : 'Create Job'}
                </button>
              </div>

              {createJobMutation.isError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                  Failed to create job. Please try again.
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
