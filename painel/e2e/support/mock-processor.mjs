// Clip-processor falso para o E2E: responde o contrato de /internal/* e grava as chamadas.
//   GET  /__calls   -> [{method, path, body, token}]
//   POST /__reset   -> limpa o registro e o modo de falha
//   POST /__fail    -> {"status": 500, "path": "/internal/reject-clip"} faz esse path falhar
import http from 'node:http';

const port = Number(process.env.MOCK_PROCESSOR_PORT ?? 8098);
let calls = [];
let failures = {};

const replies = [
    [
        /resolve-channel$/,
        () => ({
            channel_id: 'UCe2eResolved000000000000',
            channel_name: 'Canal Resolvido E2E',
            channel_handle: '@resolvido-e2e',
        }),
    ],
    [/reject-clip$/, () => ({ exit_code: 0 })],
    [/process-url$/, () => ({ exit_code: 0 })],
    [/delete-source-video$/, () => ({ deleted: true, transcript_archived: true, freed_bytes: 1024 })],
    [
        /purge-old-videos$/,
        () => ({
            deleted_rows: 0,
            retained_rows: 1,
            cleaned_videos: 1,
            transcripts_archived: 1,
            skipped_rows: 0,
            freed_bytes: 2048,
        }),
    ],
];

const send = (res, status, body) => {
    res.writeHead(status, { 'content-type': 'application/json' });
    res.end(JSON.stringify(body));
};

http.createServer((req, res) => {
    let raw = '';
    req.on('data', (c) => (raw += c));
    req.on('end', () => {
        const path = req.url.split('?')[0];
        let body = null;
        try {
            body = raw ? JSON.parse(raw) : null;
        } catch {
            body = raw;
        }

        if (path === '/__calls') return send(res, 200, calls);
        if (path === '/__reset') {
            calls = [];
            failures = {};
            return send(res, 200, { ok: true });
        }
        if (path === '/__fail') {
            failures[body.path] = body.status ?? 500;
            return send(res, 200, { ok: true });
        }
        if (path === '/health') return send(res, 200, { ok: true });

        calls.push({ method: req.method, path, body, token: req.headers['x-internal-token'] ?? null });
        if (failures[path]) return send(res, failures[path], { error: 'falha simulada' });
        const hit = replies.find(([re]) => re.test(path));
        return send(res, 200, hit ? hit[1]() : { ok: true });
    });
}).listen(port, '0.0.0.0', () => console.log(`mock clip-processor em :${port}`));
