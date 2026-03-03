import Parser from 'rss-parser';
import axios from 'axios';
import { config } from '../config.js';

export class NewsAggregator {
  constructor(config) {
    this.config = config;
    this.sources = [
      { url: 'http://feeds.bbci.co.uk/news/rss.xml', name: 'bbc', category: 'geopolitical' },
      { url: 'https://www.reuters.com/rssFeed/worldNews', name: 'reuters', category: 'geopolitical' },
      { url: 'https://techcrunch.com/feed/', name: 'techcrunch', category: 'tech' },
      { url: 'https://www.reddit.com/r/worldnews/.rss', name: 'reddit', category: 'aggregated' }
    ];
    this.newsCache = new Map();
    this.lastFetch = new Map();
  }

  async fetchNews(source) {
    try {
      const feed = await Parser.parseURL(source.url);
      const articles = feed.items.slice(0, 50).map(item => ({
        title: item.title,
        link: item.link,
        pubDate: item.pubDate,
        content: item.contentSnippet || '',
        source: source.name,
        category: source.category
      }));
      return articles;
    } catch (error) {
      console.error(`Failed to fetch from ${source.name}:`, error.message);
      return [];
    }
  }

  async getNews({ sources, categories, hours = 24 } = {}) {
    const now = Date.now();
    const cutoffTime = now - (hours * 60 * 60 * 1000);

    let filteredSources = this.sources;
    if (sources) {
      const sourceList = sources.split(',');
      filteredSources = filteredSources.filter(s => sourceList.includes(s.name));
    }
    if (categories) {
      const categoryList = categories.split(',');
      filteredSources = filteredSources.filter(s => categoryList.includes(s.category));
    }

    const allArticles = [];
    for (const source of filteredSources) {
      // Check cache (5 minutes)
      const lastFetch = this.lastFetch.get(source.name) || 0;
      if (now - lastFetch > 5 * 60 * 1000) {
        const articles = await this.fetchNews(source);
        this.newsCache.set(source.name, articles);
        this.lastFetch.set(source.name, now);
      }
      const cached = this.newsCache.get(source.name) || [];
      allArticles.push(...cached.filter(a => new Date(a.pubDate).getTime() > cutoffTime));
    }

    return {
      articles: allArticles.slice(0, 500),
      total: allArticles.length,
      fetched_at: new Date().toISOString()
    };
  }
}
