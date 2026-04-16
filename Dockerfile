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

# Expose port 3000 (Render's preferred port)
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node healthcheck.js

# Start the application
CMD ["serve", "-s", ".", "-l", "3000"]
