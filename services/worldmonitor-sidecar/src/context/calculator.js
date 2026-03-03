import Redis from 'ioredis';
import { config } from '../config.js';
import { NewsAggregator } from '../news/aggregator.js';

export class ContextCalculator {
  constructor(config) {
    this.config = config;
    this.redis = new Redis({
      host: config.redis.host,
      port: config.redis.port
    });
    this.newsAggregator = new NewsAggregator(config);
    this.contextCache = null;
    this.lastUpdate = 0;
  }

  async getGlobalContext() {
    const now = Date.now();

    // Return cached context if fresh
    if (this.contextCache && (now - this.lastUpdate < this.config.redis.cacheTTL * 1000)) {
      return this.contextCache;
    }

    // Fetch news
    const news = await this.newsAggregator.getNews({ hours: 24 });

    // Calculate Country Instability Index (CII)
    const ciiScores = await this.calculateCII(news);

    // Classify threats
    const threats = this.classifyThreats(news);

    // Identify major events
    const majorEvents = this.identifyMajorEvents(news);

    const context = {
      global_cii: this.calculateGlobalCII(ciiScores),
      country_summary: ciiScores,
      active_threats: threats,
      major_events: majorEvents,
      last_updated: new Date().toISOString()
    };

    // Cache in Redis
    await this.redis.setex(
      this.config.redis.contextKey,
      this.config.redis.cacheTTL,
      JSON.stringify(context)
    );

    this.contextCache = context;
    this.lastUpdate = now;

    return context;
  }

  async getCountryContext(countryCode) {
    const globalContext = await this.getGlobalContext();
    const countryData = globalContext.country_summary[countryCode];

    if (!countryData) {
      throw new Error(`Country ${countryCode} not found`);
    }

    return {
      country_code: countryCode,
      country_cii: countryData.score,
      trend: countryData.trend,
      recent_events: countryData.events || [],
      news_summary: countryData.newsSummary || '',
      instability_factors: countryData.factors || {}
    };
  }

  calculateCII(news) {
    // NOTE: This returns hardcoded mock data as an intentional placeholder.
    // In production, this would integrate with a proper CII calculation service
    // that analyzes news sentiment, historical data, and other geopolitical factors.
    const countryScores = {
      'GB': { score: 25, trend: 'stable', events: [], newsSummary: 'Low instability' },
      'US': { score: 35, trend: 'stable', events: [], newsSummary: 'Moderate instability' },
      'UA': { score: 85, trend: 'rising', events: ['conflict'], newsSummary: 'High instability due to conflict' }
    };
    return countryScores;
  }

  calculateGlobalCII(countryScores) {
    if (Object.keys(countryScores).length === 0) return 0;
    const sum = Object.values(countryScores).reduce((acc, c) => acc + c.score, 0);
    return Math.round(sum / Object.keys(countryScores).length);
  }

  classifyThreats(news) {
    // Keyword-based threat classification
    const threatKeywords = {
      'critical': ['war', 'attack', 'terrorist', 'bomb', 'explosion'],
      'high': ['protest', 'violence', 'clash', 'military'],
      'medium': ['unrest', 'demonstration', 'riot'],
      'low': ['incident', 'alert']
    };

    const threats = [];
    for (const article of news.articles.slice(0, 20)) {
      const titleLower = article.title.toLowerCase();
      for (const [level, keywords] of Object.entries(threatKeywords)) {
        if (keywords.some(kw => titleLower.includes(kw))) {
          threats.push({
            level,
            type: this.classifyThreatType(titleLower),
            title: article.title,
            source: article.source,
            location: this.extractLocation(article)
          });
          break;
        }
      }
    }

    return threats.slice(0, 10);
  }

  classifyThreatType(text) {
    if (text.includes('war') || text.includes('military')) return 'conflict';
    if (text.includes('protest') || text.includes('riot')) return 'civil_unrest';
    if (text.includes('attack') || text.includes('bomb')) return 'security';
    if (text.includes('flood') || text.includes('earthquake')) return 'natural_disaster';
    return 'other';
  }

  extractLocation(article) {
    // Simple extraction - in production, use NER
    const locations = ['London', 'New York', 'Kyiv', 'Washington DC', 'Moscow'];
    const text = (article.title + ' ' + (article.content || '')).toLowerCase();
    return locations.find(loc => text.toLowerCase().includes(loc.toLowerCase())) || 'Unknown';
  }

  identifyMajorEvents(news) {
    const events = [];
    for (const article of news.articles.slice(0, 5)) {
      events.push({
        type: 'news',
        summary: article.title,
        source: article.source,
        published: article.pubDate
      });
    }
    return events;
  }

  /**
   * Cleanup method to properly close Redis connection
   * Should be called during graceful shutdown
   */
  async cleanup() {
    try {
      await this.redis.quit();
      console.log('Redis connection closed successfully');
    } catch (error) {
      console.error('Error closing Redis connection:', error.message);
      // Force close if graceful quit fails
      try {
        await this.redis.disconnect();
      } catch (disconnectError) {
        console.error('Error force disconnecting Redis:', disconnectError.message);
      }
    }
  }
}
