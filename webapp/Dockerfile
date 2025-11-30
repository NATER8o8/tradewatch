FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --silent

# Copy source
COPY . /app

ENV PORT=3000
EXPOSE 3000

CMD ["npm", "run", "dev"]
