FROM node:18-alpine

WORKDIR /app

# Install dependencies (prefer npm ci if lockfile is present)
COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci --silent; else npm install --silent; fi

# Copy source
COPY . /app

ENV PORT=3000
EXPOSE 3000

CMD ["npm", "run", "dev"]
