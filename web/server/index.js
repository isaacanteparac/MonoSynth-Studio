const express = require('express');
const cors = require('cors');
const app = express();
const port = 3000;

app.use(cors());
app.use(express.json());

app.get('/', (req, res) => {
  res.send('Music App Server is running!');
});

app.get('/api/suggestions', (req, res) => {
  res.json([
    { id: 1, title: 'Techno Loop', bpm: 128, type: 'Techno' },
    { id: 2, title: 'Ambient Pad', bpm: 80, type: 'Ambient' },
    { id: 3, title: 'House Groove', bpm: 124, type: 'House' },
    { id: 4, title: 'Lo-Fi Chill', bpm: 90, type: 'Lo-Fi' }
  ]);
});

app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});
