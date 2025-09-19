# Usar una imagen oficial de Node.js como base
FROM node:20-alpine

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar package.json y package-lock.json para instalar dependencias
# Esto aprovecha el caché de Docker y solo reinstala si estos archivos cambian
COPY package*.json ./

# Instalar las dependencias del proyecto
RUN npm install

# Copiar el resto de los archivos de la aplicación
COPY . .

# Exponer el puerto en el que corre la aplicación de React
EXPOSE 3000

# El comando para iniciar la aplicación
CMD ["npm", "start"]