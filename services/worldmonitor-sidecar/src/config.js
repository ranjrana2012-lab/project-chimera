export const config = {
  port: parseInt(process.env.PORT || '3001'),
  host: process.env.HOST || '0.0.0.0',

  // WebSocket broadcast to sentiment agent
  wsBroadcastUrl: process.env.WS_BROADCAST_URL || 'ws://sentiment-agent:8004/api/v1/context/stream',

  // Redis configuration
  redis: {
    host: process.env.REDIS_HOST || 'redis.shared.svc.cluster.local',
    port: parseInt(process.env.REDIS_PORT || '6379'),
    contextKey: process.env.REDIS_CONTEXT_KEY || 'worldmonitor:context',
    newsKey: process.env.REDIS_NEWS_KEY || 'worldmonitor:news',
    cacheTTL: parseInt(process.env.CONTEXT_CACHE_TTL || '300') // 5 minutes
  },

  // News sources
  newsSources: (() => {
    try {
      return JSON.parse(process.env.NEWS_SOURCES || '[]');
    } catch (error) {
      console.error('Failed to parse NEWS_SOURCES environment variable:', error.message);
      return [];
    }
  })(),

  // News aggregator settings
  news: {
    cacheTTL: parseInt(process.env.NEWS_CACHE_TTL || '300'), // 5 minutes
    maxArticlesPerSource: parseInt(process.env.MAX_ARTICLES_PER_SOURCE || '50'),
    maxTotalArticles: parseInt(process.env.MAX_TOTAL_ARTICLES || '500')
  },

  // Context update interval (seconds)
  contextUpdateInterval: parseInt(process.env.CONTEXT_UPDATE_INTERVAL || '60'),

  // Country Instability Index settings
  cii: {
    baselineWeight: 0.4,
    unrestWeight: 0.2,
    securityWeight: 0.2,
    velocityWeight: 0.2
  }
};
