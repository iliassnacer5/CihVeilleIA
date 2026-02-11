'use client'

import React, { useState } from 'react'
import { Search, Calendar, Filter, ChevronRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'

interface SearchResult {
  id: string
  title: string
  source: string
  date: string
  theme: string
  excerpt: string
  relevance: number
}

const suggestedQueries = [
  'Capital adequacy requirements',
  'Basel IV implementation timeline',
  'Credit risk assessment methodology',
  'Regulatory compliance updates',
  'Market volatility impact on banking',
]

export default function SemanticSearchPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [filters, setFilters] = useState({
    source: '',
    dateRange: 'all',
    theme: '',
  })

  const handleSearch = async () => {
    if (searchQuery.trim()) {
      setIsLoading(true)
      setHasSearched(true)
      try {
        const data = await api.search(searchQuery)
        setResults(data)
      } catch (error) {
        console.error('Search failed:', error)
      } finally {
        setIsLoading(false)
      }
    }
  }

  const handleSuggestedQuery = (query: string) => {
    setSearchQuery(query)
    // We don't auto-search as per UI pattern of this page
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Semantic Search</h1>
        <p className="text-muted-foreground mt-1">
          Natural language search across all collected documents
        </p>
      </div>

      {/* Search Bar */}
      <Card className="border border-border">
        <CardContent className="p-6">
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask a question about regulatory updates, credit risk, market conditions..."
                  className="w-full pl-10 pr-4 py-3 border border-border rounded-lg bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
              <Button onClick={handleSearch} disabled={isLoading} className="px-6 gap-2">
                {isLoading ? <Loader2 className="animate-spin" size={18} /> : null}
                {isLoading ? 'Searching...' : 'Search'}
              </Button>
            </div>

            {/* Filters */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-2">
                  Source
                </label>
                <select
                  value={filters.source}
                  onChange={(e) =>
                    setFilters({ ...filters, source: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">All Sources</option>
                  <option value="basel">Basel Committee</option>
                  <option value="ecb">ECB</option>
                  <option value="internal">Internal</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-2">
                  Date Range
                </label>
                <select
                  value={filters.dateRange}
                  onChange={(e) =>
                    setFilters({ ...filters, dateRange: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="all">All Time</option>
                  <option value="week">Last Week</option>
                  <option value="month">Last Month</option>
                  <option value="quarter">Last Quarter</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-2">
                  Theme
                </label>
                <select
                  value={filters.theme}
                  onChange={(e) =>
                    setFilters({ ...filters, theme: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-border rounded-lg bg-background text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                >
                  <option value="">All Themes</option>
                  <option value="regulation">Regulation</option>
                  <option value="market">Market</option>
                  <option value="credit">Credit</option>
                  <option value="risk">Risk</option>
                </select>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results or Suggested Queries */}
      {hasSearched ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">
              Results {searchQuery ? `for "${searchQuery}"` : ''}
            </h2>
            <span className="text-sm text-muted-foreground">
              {results.length} results found
            </span>
          </div>

          {isLoading ? (
            <div className="py-12 flex flex-col items-center justify-center gap-4">
              <Loader2 className="animate-spin text-primary" size={40} />
              <p className="text-muted-foreground">Retrieving semantic matches...</p>
            </div>
          ) : results.length > 0 ? (
            <div className="space-y-3">
              {results.map((result) => (
                <Card key={result.id} className="border border-border hover:shadow-md transition-shadow cursor-pointer">
                  <CardContent className="p-4">
                    <div className="flex items-start gap-4">
                      <div className="flex-1">
                        <h3 className="font-semibold text-foreground mb-1">
                          {result.title}
                        </h3>
                        <p className="text-sm text-muted-foreground mb-3">
                          {result.source} • {new Date(result.date).toLocaleDateString()}
                        </p>
                        <p className="text-sm text-foreground leading-relaxed mb-3 line-clamp-2">
                          {result.excerpt}
                        </p>
                        <div className="flex flex-wrap items-center gap-3">
                          <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200">
                            {result.theme}
                          </span>
                          <div className="flex items-center gap-2 text-xs">
                            <div className="w-20 bg-secondary rounded-full h-1.5">
                              <div
                                className="bg-accent h-1.5 rounded-full"
                                style={{ width: `${result.relevance}%` }}
                              />
                            </div>
                            <span className="text-muted-foreground">
                              {result.relevance}% relevant
                            </span>
                          </div>
                        </div>
                      </div>
                      <ChevronRight className="text-muted-foreground flex-shrink-0 mt-1" size={20} />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="border border-border">
              <CardContent className="p-12 text-center">
                <p className="text-muted-foreground">No documents matched your search criteria.</p>
              </CardContent>
            </Card>
          )}
        </div>
      ) : (
        <Card className="border border-border bg-secondary/30">
          <CardContent className="p-8 text-center">
            <div className="space-y-4">
              <p className="text-muted-foreground">
                Start with a natural language query about any banking topic
              </p>
              <div>
                <p className="text-sm font-semibold text-foreground mb-3">
                  Try searching for:
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {suggestedQueries.map((query, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestedQuery(query)}
                      className="px-4 py-2 rounded-lg bg-card border border-border hover:border-accent text-foreground text-sm transition-colors"
                    >
                      {query}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
