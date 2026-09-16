FROM node:22-alpine AS build
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN node node_modules/@angular/cli/bin/ng.js build

FROM nginx:1.27-alpine
COPY --from=build /app/dist/bookmyshow/browser /usr/share/nginx/html
EXPOSE 80
