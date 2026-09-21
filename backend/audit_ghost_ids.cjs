// Audit: find ghost IDs in COUNTRY_BUCKETS that don't exist in MovieBoxScraper catalog
const fs = require('fs');
const path = require('path');

const scraperPath = path.join('G:', 'streaming app', 'backend', 'src', 'scrapers', 'MovieBoxScraper.js');
const routesPath = path.join('G:', 'streaming app', 'backend', 'src', 'api', 'routes.js');

const scraperSrc = fs.readFileSync(scraperPath, 'utf8');

// Extract all m() and v() first-arg IDs from catalog (multiline aware)
const catalogIds = new Set();
const idRegex = /^\s*[mv]\(\s*'([^']+)'/gm;
let match;
while ((match = idRegex.exec(scraperSrc)) !== null) {
    catalogIds.add(match[1]);
}

// Extract COUNTRY_BUCKETS ids arrays
const routesSrc = fs.readFileSync(routesPath, 'utf8');
// Find each bucket's ids: [...]
const bucketRegex = /'([a-z-]+)':\s*\{[^}]*?ids:\s*\[([^\]]+)\]/g;
const ghostReport = {};
let m2;
while ((m2 = bucketRegex.exec(routesSrc)) !== null) {
    const bucketKey = m2[1];
    const idsBlock = m2[2];
    const ids = [];
    const idQuoteRegex = /'([^']+)'/g;
    let im;
    while ((im = idQuoteRegex.exec(idsBlock)) !== null) {
        ids.push(im[1]);
    }
    const ghosts = ids.filter(id => !catalogIds.has(id));
    const real = ids.filter(id => catalogIds.has(id));
    ghostReport[bucketKey] = { total: ids.length, real: real.length, ghosts };
}

console.log('Total catalog IDs:', catalogIds.size);
console.log('--- Ghost report ---');
for (const [k, v] of Object.entries(ghostReport)) {
    if (v.ghosts.length > 0) {
        console.log(`${k}: ${v.real}/${v.total} real, ${v.ghosts.length} ghost: ${v.ghosts.join(', ')}`);
    } else {
        console.log(`${k}: ${v.real}/${v.total} real, 0 ghost`);
    }
}
console.log('--- Total ghosts ---');
const totalGhosts = Object.values(ghostReport).reduce((s, v) => s + v.ghosts.length, 0);
console.log(totalGhosts);

// Write the report
fs.writeFileSync(path.join('G:', 'streaming app', 'backend', 'ghost_report.json'), JSON.stringify(ghostReport, null, 2));
