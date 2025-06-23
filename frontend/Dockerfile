# Stage 1: Build the React application
FROM node:18-alpine as builder

WORKDIR /app

# Copy package.json and install dependencies
COPY package*.json ./
# REMOVED --omit=dev: Ensure devDependencies (like react-scripts) are installed
RUN npm install --production

# Copy rest of the application code
COPY . .

# Build the React app
ARG REACT_APP_API_BASE_URL
ENV REACT_APP_API_BASE_URL=$REACT_APP_API_BASE_URL

# Use npx to explicitly run react-scripts
RUN npx react-scripts build

# Stage 2: Serve the built application with Nginx
FROM nginx:alpine

# Copy the build output from the builder stage to Nginx's default public directory
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
