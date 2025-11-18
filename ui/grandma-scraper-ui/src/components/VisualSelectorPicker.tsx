/**
 * Visual selector picker - click on elements to generate CSS selectors
 * This is the "grandma-friendly" feature that makes scraping accessible
 */

import { useState, useEffect, useRef } from 'react';

interface VisualSelectorPickerProps {
  url: string;
  onSelectorSelected: (selector: string, sampleText: string) => void;
  mode: 'item' | 'field'; // 'item' for container, 'field' for data fields
  label?: string;
}

export function VisualSelectorPicker({
  url,
  onSelectorSelected,
  mode,
  label,
}: VisualSelectorPickerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSelector, setSelectedSelector] = useState<string>('');
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (!url) return;

    // Reset state when URL changes
    setIsLoading(true);
    setError(null);
    setSelectedSelector('');
  }, [url]);

  const handleIframeLoad = () => {
    setIsLoading(false);

    if (!iframeRef.current) return;

    try {
      const iframeDoc = iframeRef.current.contentDocument;
      if (!iframeDoc) {
        setError('Cannot access page content. Try using a different URL or check CORS settings.');
        return;
      }

      // Inject our click handler script
      const script = iframeDoc.createElement('script');
      script.textContent = `
        (function() {
          let hoveredElement = null;
          let originalOutline = '';

          // Generate a unique CSS selector for an element
          function generateSelector(element) {
            // Try ID first
            if (element.id) {
              return '#' + element.id;
            }

            // Try class names
            if (element.className && typeof element.className === 'string') {
              const classes = element.className.split(/\\s+/).filter(c => c).join('.');
              if (classes) {
                const selector = element.tagName.toLowerCase() + '.' + classes;
                // Check if unique
                if (document.querySelectorAll(selector).length === 1) {
                  return selector;
                }
                return selector;
              }
            }

            // Fallback to tag name with nth-child
            const parent = element.parentElement;
            if (!parent) {
              return element.tagName.toLowerCase();
            }

            const siblings = Array.from(parent.children);
            const index = siblings.indexOf(element) + 1;
            const parentSelector = generateSelector(parent);

            return parentSelector + ' > ' + element.tagName.toLowerCase() + ':nth-child(' + index + ')';
          }

          // Get sample text from element
          function getSampleText(element) {
            const text = element.textContent || element.innerText || '';
            return text.trim().substring(0, 100);
          }

          // Mouseover handler
          document.addEventListener('mouseover', function(e) {
            e.stopPropagation();

            if (hoveredElement) {
              hoveredElement.style.outline = originalOutline;
            }

            hoveredElement = e.target;
            originalOutline = hoveredElement.style.outline;
            hoveredElement.style.outline = '2px solid #9333ea';
          });

          // Click handler
          document.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            const selector = generateSelector(e.target);
            const sampleText = getSampleText(e.target);

            // Send message to parent
            window.parent.postMessage({
              type: 'selector-picked',
              selector: selector,
              sampleText: sampleText,
            }, '*');
          });
        })();
      `;
      iframeDoc.body.appendChild(script);

      // Inject CSS to prevent default link behavior
      const style = iframeDoc.createElement('style');
      style.textContent = `
        * {
          cursor: crosshair !important;
        }
        a {
          pointer-events: none;
        }
      `;
      iframeDoc.head.appendChild(style);
    } catch (err: any) {
      setError('Cannot inject selector script. The page may have security restrictions.');
      console.error('Iframe injection error:', err);
    }
  };

  // Listen for messages from iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'selector-picked') {
        setSelectedSelector(event.data.selector);
        onSelectorSelected(event.data.selector, event.data.sampleText);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onSelectorSelected]);

  return (
    <div className="space-y-4">
      {/* Instructions */}
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
        <h3 className="font-semibold text-purple-900 mb-2">
          {mode === 'item' ? 'Select an Item Container' : `Select ${label || 'a Field'}`}
        </h3>
        <p className="text-sm text-purple-800">
          {mode === 'item'
            ? 'Hover over the page and click on one of the repeating items you want to scrape (e.g., a product card, article, listing).'
            : 'Hover over the page and click on the specific data you want to extract (e.g., title, price, description).'}
        </p>
      </div>

      {/* Preview Frame */}
      <div className="relative border-2 border-gray-300 rounded-lg overflow-hidden" style={{ height: '500px' }}>
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white z-10">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mb-4"></div>
              <p className="text-gray-600">Loading page preview...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-red-50 z-10">
            <div className="text-center px-6">
              <svg
                className="mx-auto h-12 w-12 text-red-400 mb-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <p className="text-red-700 font-medium">{error}</p>
              <p className="text-red-600 text-sm mt-2">
                Note: Some websites may block iframe embedding. In that case, you'll need to manually enter CSS selectors.
              </p>
            </div>
          </div>
        )}

        {url && !error && (
          <iframe
            ref={iframeRef}
            src={url}
            className="w-full h-full border-0"
            onLoad={handleIframeLoad}
            onError={() => setError('Failed to load page. The site may block embedding.')}
            sandbox="allow-scripts allow-same-origin"
            title="Page preview for selector picking"
          />
        )}
      </div>

      {/* Selected Selector Display */}
      {selectedSelector && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-sm text-green-800 mb-2 font-medium">Selected CSS Selector:</p>
          <code className="block bg-white px-3 py-2 rounded border border-green-300 text-sm font-mono text-gray-900">
            {selectedSelector}
          </code>
        </div>
      )}
    </div>
  );
}
