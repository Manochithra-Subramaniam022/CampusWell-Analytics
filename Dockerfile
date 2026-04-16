# Use Node.js runtime for better static file serving
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install serve package for static hosting
RUN npm install -g serve

# Copy all application files
COPY . .

# Create a simple server to handle routing properly
RUN echo 'const express = require("express"); const path = require("path"); const app = express(); const port = process.env.PORT || 3000; app.use(express.static(path.join(__dirname, "."))); app.get("*", (req, res) => { res.sendFile(path.join(__dirname, "index.html")); }); app.listen(port, () => { console.log(\`Server running on port \${port}\`); });' > server.js

# Install express for proper routing
RUN npm install express

# Expose port 3000 (Render's preferred port)
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js

# Start the application with proper routing
CMD ["node", "server.js"]
