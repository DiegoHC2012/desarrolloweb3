# frontend/Dockerfile
FROM node:20-alpine

# Crea directorio de trabajo
WORKDIR /app

# Copiamos solo package.json primero para cache de dependencias
COPY package*.json ./

# Instalamos dependencias
RUN npm install

# Copiamos el resto del proyecto
COPY . .

# Puerto por defecto de Vite
EXPOSE 3000

# Levanta en modo desarrollo con hot reload accesible en la red
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
