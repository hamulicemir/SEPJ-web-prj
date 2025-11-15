FROM node:20-alpine

# Arbeitsverzeichnis im Container
WORKDIR /app

# package.json + package-lock.json rein
COPY package*.json ./

# Dependencies installieren
RUN npm install

# Source Code rein
COPY . .

# Vite Dev Server Port
EXPOSE 5173

# Vite starten
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
