// Strip ghost IDs from COUNTRY_BUCKETS in routes.js
const fs = require('fs');
const path = require('path');

const scraperPath = path.join('G:', 'streaming app', 'backend', 'src', 'scrapers', 'MovieBoxScraper.js');
const routesPath = path.join('G:', 'streaming app', 'backend', 'src', 'api', 'routes.js');

const scraperSrc = fs.readFileSync(scraperPath, 'utf8');
const catalogIds = new Set();
const idRegex = /^\s*[mv]\(\s*'([^']+)'/gm;
let match;
while ((match = idRegex.exec(scraperSrc)) !== null) {
    catalogIds.add(match[1]);
}

let routesSrc = fs.readFileSync(routesPath, 'utf8');

// For each bucket, replace ids: [...] array with filtered version
const bucketRegex = /('([a-z-]+)':\s*\{[^}]*?ids:\s*\[)([^\]]+)(\])/g;
let m2;
let edited = routesSrc;
while ((m2 = bucketRegex.exec(routesSrc)) !== null) {
    const prefix = m2[1];
    const bucketKey = m2[2];
    const idsBlock = m2[3];
    const suffix = m2[4];
    // Extract all single-quoted strings
    const ids = [];
    const idQuoteRegex = /'([^']+)'/g;
    let im;
    while ((im = idQuoteRegex.exec(idsBlock)) !== null) {
        ids.push(im[1]);
    }
    const realIds = ids.filter(id => catalogIds.has(id));
    if (realIds.length === ids.length) {
        continue; // no change needed
    }
    // Replace
    const oldBlock = prefix + idsBlock + suffix;
    const newIdsBlock = realIds.map(id => `'${id}'`).join(',');
    const newBlock = prefix + newIdsBlock + suffix;
    edited = edited.replace(oldBlock, newBlock);
    console.log(`${bucketKey}: ${ids.length} -> ${realIds.length} IDs`);
}

fs.writeFileSync(routesPath, edited);
console.log('routes.js updated.');
