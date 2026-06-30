# Rare Dashboard

React + TypeScript + Vite frontend for the RARE (Resume Analysis & Ranking Engine) platform.

## Features

- Modern UI built with React 19, Tailwind CSS, and TypeScript
- Dashboard for viewing ranked candidates and analytics
- Resume library management
- Job description analysis interface

## Setup

### Install Dependencies

```bash
npm install
```

### Development

```bash
npm run dev
```

### Build

```bash
npm run build
```

### Preview

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── pages/          # Main application pages
│   ├── components/     # Reusable UI components
│   ├── services/       # API service layers
│   ├── layouts/        # Layout components
│   ├── app/            # Router configuration
│   └── assets/         # Static assets
├── public/             # Static files
├── package.json
├── tsconfig*.json
└── vite.config.ts
```

## API Integration

The frontend communicates with the Python backend services via REST API. Configure the API base URL in `src/services/api.ts`.