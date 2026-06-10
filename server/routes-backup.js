const express = require('express');
const axios = require('axios');
const crypto = require('crypto');

const router = express.Router();

router.post('/request-serials', async (req, res) => {

try {

    const {
        url,
        token,
        payload
    } = req.body;

    // Generate a new UUID for every request
    payload.id = crypto.randomUUID();

    console.log('Generated UUID:', payload.id);

    const response = await axios.post(
        url,
        payload,
        {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${token}`
            }
        }
    );

    res.json(response.data);

} catch (error) {

    console.error('ALTIUSHUB ERROR');

    if (error.response) {

        console.error(
            JSON.stringify(
                error.response.data,
                null,
                2
            )
        );

        return res.status(
            error.response.status
        ).json({
            error: error.message,
            details: error.response.data
        });
    }

    console.error(error.message);

    res.status(500).json({
        error: error.message
    });
}

});

module.exports = router;
