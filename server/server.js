const express = require('express');
const cors = require('cors');
const path = require('path');
const routes = require('./routes');

const app = express();

const corsOptions = {
  origin: 'https://epcis-simulation.netlify.app',
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
};

app.options('*', cors(corsOptions));
app.use(cors(corsOptions));

app.use(express.json());

// Serve static files from project root
app.use(express.static(path.join(__dirname, '..')));

app.get('/api/health', (req, res) => {
  res.send('Serialization Gateway Running');
});

app.use('/api', routes);

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});