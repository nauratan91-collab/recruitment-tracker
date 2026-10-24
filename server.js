const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || process.env.SERVER_PORT || 3000;

app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Serve static assets from static directory
const staticDir = path.join(__dirname, 'static');
if (fs.existsSync(staticDir)) {
  app.use('/static', express.static(staticDir));
}

// Serve public directory if exists
const publicDir = path.join(__dirname, 'public');
if (fs.existsSync(publicDir)) {
  app.use(express.static(publicDir));
}

// Serve uploads directory
const uploadsDir = path.join(__dirname, 'uploads');
if (fs.existsSync(uploadsDir)) {
  app.use('/uploads', express.static(uploadsDir));
  app.use('/api/uploads', express.static(uploadsDir));
}

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    service: 'Key Dynamics Solutions - Job Tracker Portal',
    timestamp: new Date().toISOString()
  });
});

// Settings endpoint
app.get('/api/settings', (req, res) => {
  res.json({
    usd_inr_exchange_rate: process.env.USD_INR_RATE || '84.00'
  });
});

// Serve root index.html for all page requests
app.get('*', (req, res) => {
  const indexPath = path.join(__dirname, 'index.html');
  if (fs.existsSync(indexPath)) {
    return res.sendFile(indexPath);
  }
  const publicIndexPath = path.join(__dirname, 'public', 'index.html');
  if (fs.existsSync(publicIndexPath)) {
    return res.sendFile(publicIndexPath);
  }
  const templatePath = path.join(__dirname, 'templates', 'index.html');
  if (fs.existsSync(templatePath)) {
    return res.sendFile(templatePath);
  }
  res.status(404).send('Portal index.html not found');
});

const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`Key Dynamics Solutions Portal running on port ${PORT}`);
});

module.exports = app;
