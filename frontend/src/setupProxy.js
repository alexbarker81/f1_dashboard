const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api', // Requests to /api will be proxied
    createProxyMiddleware({
      target: 'http://localhost:3000', // Your Mojolicious app's address (on host)
      changeOrigin: true,
      pathRewrite: {
        '^/api': '/api', // Rewrite path if necessary, but here it's 1:1
      },
    })
  );
};
