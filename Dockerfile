# Node.js Express Backend & Frontend Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package definition files
COPY package*.json ./

# Install application dependencies
RUN npm install --production

# Copy application files
COPY backend ./backend
COPY frontend ./frontend
COPY database ./database

# Expose Express server port
EXPOSE 5000

# Set environment variables default
ENV PORT=5000
ENV NODE_ENV=production

# Start Node.js Express application
CMD ["npm", "start"]
