const express = require('express');
const cors = require('cors');

const routes = require('./routes');

const app = express();

const path = require('path');

app.use(express.json());
app.use(cors());

// Serve static files from project root
app.use(express.static(path.join(__dirname, '..')));

app.get('/api/health', (req, res) => {
res.send('Serialization Gateway Running');
});

app.use('/api', routes);

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
console.log(
`Server running on port ${PORT}`
);
});
