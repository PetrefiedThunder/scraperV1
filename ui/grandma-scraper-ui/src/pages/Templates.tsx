/**
 * Template marketplace/gallery page
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '@/components/Layout';

interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty: 'easy' | 'medium' | 'hard';
  config: any;
}

const SAMPLE_TEMPLATES: Template[] = [
  {
    id: '1',
    name: 'E-commerce Product Listings',
    description: 'Scrape product names, prices, and images from e-commerce sites',
    category: 'E-commerce',
    difficulty: 'easy',
    config: {
      item_selector: '.product-card',
      fields: [
        { name: 'title', selector: '.product-title', type: 'text' },
        { name: 'price', selector: '.product-price', type: 'text' },
        { name: 'image', selector: 'img', selector_attribute: 'src', type: 'text' },
      ],
    },
  },
  {
    id: '2',
    name: 'Job Listings',
    description: 'Extract job titles, companies, and descriptions from job boards',
    category: 'Jobs',
    difficulty: 'easy',
    config: {
      item_selector: '.job-listing',
      fields: [
        { name: 'title', selector: '.job-title', type: 'text' },
        { name: 'company', selector: '.company-name', type: 'text' },
        { name: 'location', selector: '.job-location', type: 'text' },
        { name: 'description', selector: '.job-description', type: 'text' },
      ],
    },
  },
  {
    id: '3',
    name: 'News Articles',
    description: 'Collect article titles, authors, and content from news websites',
    category: 'Content',
    difficulty: 'medium',
    config: {
      item_selector: 'article',
      fields: [
        { name: 'headline', selector: 'h1, h2.title', type: 'text' },
        { name: 'author', selector: '.author-name', type: 'text' },
        { name: 'date', selector: '.publish-date', type: 'text' },
        { name: 'content', selector: '.article-body', type: 'text' },
      ],
    },
  },
  {
    id: '4',
    name: 'Real Estate Listings',
    description: 'Scrape property details including price, beds, baths, and square footage',
    category: 'Real Estate',
    difficulty: 'medium',
    config: {
      item_selector: '.property-card',
      fields: [
        { name: 'address', selector: '.property-address', type: 'text' },
        { name: 'price', selector: '.property-price', type: 'text' },
        { name: 'beds', selector: '.beds', type: 'text' },
        { name: 'baths', selector: '.baths', type: 'text' },
        { name: 'sqft', selector: '.square-feet', type: 'text' },
      ],
    },
  },
];

export function Templates() {
  const navigate = useNavigate();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const categories = ['all', ...new Set(SAMPLE_TEMPLATES.map((t) => t.category))];

  const filteredTemplates =
    selectedCategory === 'all'
      ? SAMPLE_TEMPLATES
      : SAMPLE_TEMPLATES.filter((t) => t.category === selectedCategory);

  const getDifficultyColor = (difficulty: string) => {
    const colors: Record<string, string> = {
      easy: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      hard: 'bg-red-100 text-red-800',
    };
    return colors[difficulty] || 'bg-gray-100 text-gray-800';
  };

  const handleUseTemplate = (template: Template) => {
    // Store template config in sessionStorage and navigate to wizard
    sessionStorage.setItem('templateConfig', JSON.stringify(template.config));
    navigate('/jobs/new', { state: { template } });
  };

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Template Gallery</h1>
          <p className="text-gray-600 mt-1">Start with pre-configured templates for common scraping tasks</p>
        </div>

        {/* Category Filter */}
        <div className="flex space-x-2 overflow-x-auto pb-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-lg font-medium transition whitespace-nowrap ${
                selectedCategory === category
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>

        {/* Templates Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template) => (
            <div
              key={template.id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition"
            >
              {/* Category & Difficulty */}
              <div className="flex justify-between items-start mb-4">
                <span className="text-xs font-medium text-purple-600 bg-purple-50 px-3 py-1 rounded-full">
                  {template.category}
                </span>
                <span className={`text-xs font-medium px-3 py-1 rounded-full ${getDifficultyColor(template.difficulty)}`}>
                  {template.difficulty}
                </span>
              </div>

              {/* Template Info */}
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{template.name}</h3>
              <p className="text-sm text-gray-600 mb-4">{template.description}</p>

              {/* Fields Preview */}
              <div className="mb-4">
                <p className="text-xs text-gray-500 mb-2">Extracts:</p>
                <div className="flex flex-wrap gap-1">
                  {template.config.fields.slice(0, 3).map((field: any, idx: number) => (
                    <span key={idx} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                      {field.name}
                    </span>
                  ))}
                  {template.config.fields.length > 3 && (
                    <span className="text-xs text-gray-500 px-2 py-1">
                      +{template.config.fields.length - 3} more
                    </span>
                  )}
                </div>
              </div>

              {/* Use Template Button */}
              <button
                onClick={() => handleUseTemplate(template)}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition"
              >
                Use Template
              </button>
            </div>
          ))}
        </div>

        {filteredTemplates.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg border-2 border-dashed border-gray-300">
            <p className="text-gray-600">No templates found in this category</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
