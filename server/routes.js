const express = require('express');
const axios = require('axios');
const crypto = require('crypto');
const multer = require('multer');
const FormData = require('form-data');
const SftpClient = require('ssh2-sftp-client');

const router = express.Router();
const upload = multer({
    storage: multer.memoryStorage()
});

/* ─────────────────────────────────────────
   REQUEST SERIALS
───────────────────────────────────────── */

router.post('/request-serials', async (req, res) => {

    try {

        const {
            url,
            token,
            payload
        } = req.body;

        if (!url) {
            return res.status(400).json({
                error: 'Request URL is required'
            });
        }

        if (!token) {
            return res.status(400).json({
                error: 'API token is required'
            });
        }

        if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
            return res.status(400).json({
                error: 'Payload object is required'
            });
        }

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

/* ─────────────────────────────────────────
   EPCIS UPLOAD — HTTPS
───────────────────────────────────────── */

router.post(
    '/upload-epcis',
    upload.single('file'),
    async (req, res) => {

        try {

            const {
                url,
                token
            } = req.body;

            if (!url) {
                return res.status(400).json({
                    error: 'URL is required'
                });
            }

            if (!token) {
                return res.status(400).json({
                    error: 'API Token is required'
                });
            }

            if (!req.file) {
                return res.status(400).json({
                    error: 'XML file is required'
                });
            }

            const formData = new FormData();

            formData.append(
                'file',
                req.file.buffer,
                req.file.originalname
            );

            console.log(
                'Uploading EPCIS via HTTPS:',
                req.file.originalname
            );

            const response = await axios.post(
                url,
                formData,
                {
                    headers: {
                        ...formData.getHeaders(),
                        Authorization: `Token ${token}`
                    },
                    maxBodyLength: Infinity
                }
            );

            res.json({
                success: true,
                data: response.data
            });

        } catch (error) {

            console.error('EPCIS HTTPS UPLOAD ERROR');

            if (error.response) {

                console.error(
                    JSON.stringify(
                        error.response.data,
                        null,
                        2
                    )
                );

                return res
                    .status(error.response.status)
                    .json({
                        error: error.message,
                        details: error.response.data
                    });
            }

            res.status(500).json({
                error: error.message
            });
        }
    }
);

/* ─────────────────────────────────────────
   EPCIS UPLOAD — SFTP
───────────────────────────────────────── */

router.post(
    '/upload-epcis-sftp',
    upload.single('file'),
    async (req, res) => {

        const sftp = new SftpClient();

        try {

            const {
                host,
                port,
                username,
                password,
                privateKey,
                remotePath
            } = req.body;

            /* Validate required fields */

            if (!host) {
                return res.status(400).json({
                    error: 'SFTP host is required'
                });
            }

            if (!username) {
                return res.status(400).json({
                    error: 'SFTP username is required'
                });
            }

            if (
                !password &&
                !privateKey
            ) {
                return res.status(400).json({
                    error: 'SFTP password or private key is required'
                });
            }

            const resolvedPort = parseInt(port, 10) || 22;

            if (
                resolvedPort < 1 ||
                resolvedPort > 65535
            ) {
                return res.status(400).json({
                    error: 'SFTP port must be between 1 and 65535'
                });
            }

            if (!req.file) {
                return res.status(400).json({
                    error: 'XML file is required'
                });
            }

            /* Build the full remote file path */

            const cleanRemotePath =
                (remotePath || '').replace(/\/$/, '');

            const remoteFilePath =
                cleanRemotePath
                ? `${cleanRemotePath}/${req.file.originalname}`
                : req.file.originalname;

            console.log(
                'Connecting to SFTP:',
                `${username}@${host}:${resolvedPort}`
            );

            console.log(
                'Remote path:',
                remoteFilePath
            );

            /* Connect */

            const connectionOptions = {
                host,
                port: resolvedPort,
                username,
                readyTimeout: 20000,
                retries: 2,
                retry_factor: 2,
                retry_minTimeout: 2000
            };

            if (privateKey) {
                connectionOptions.privateKey = privateKey;
            } else {
                connectionOptions.password = password;
            }

            await sftp.connect(connectionOptions);

            /* Ensure remote directory exists */

            if (cleanRemotePath) {

                const dirExists =
                    await sftp.exists(cleanRemotePath);

                if (!dirExists) {
                    await sftp.mkdir(cleanRemotePath, true);
                    console.log(
                        'Created remote directory:',
                        cleanRemotePath
                    );
                }
            }

            /* Upload the file buffer */

            await sftp.put(
                req.file.buffer,
                remoteFilePath
            );

            console.log(
                'SFTP upload successful:',
                req.file.originalname
            );

            await sftp.end();

            res.json({
                success: true,
                data: {
                    message: `File uploaded successfully via SFTP`,
                    file: req.file.originalname,
                    remotePath: remoteFilePath
                }
            });

        } catch (error) {

            console.error('EPCIS SFTP UPLOAD ERROR:', error.message);

            /* Always close the connection on error */

            await sftp.end().catch(() => {});

            res.status(500).json({
                error: error.message
            });
        }
    }
);

module.exports = router;
