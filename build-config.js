const fs = require('fs');
const path = require('path');

const anonKey = process.env.SUPABASE_ANON_KEY || '';

const filesToProcess = [
    { path: 'site/index.html', placeholder: '%%SUPABASE_ANON_KEY%%' },
    { path: 'site/app.js', placeholder: '%%SUPABASE_ANON_KEY%%' }
];

let processed = 0;
for (const file of filesToProcess) {
    if (fs.existsSync(file.path)) {
        let content = fs.readFileSync(file.path, 'utf8');
        if (content.includes(file.placeholder)) {
            content = content.replace(file.placeholder, anonKey || '');
            fs.writeFileSync(file.path, content, 'utf8');
            processed++;
        }
    }
}

if (anonKey) {
    console.log(`Build complete. Anonymized key injected into ${processed} file(s).`);
} else {
    console.log(`Build complete. No SUPABASE_ANON_KEY env var found. Placeholder remains.`);
}
