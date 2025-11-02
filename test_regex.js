const testMessage = '🌟 **Standard Plan: $3000.50 SGD** some text\n⭐ **Elite Plan (Recommended for adventure sports): $10540.80 SGD** more text';

console.log('=== Testing Standard Plan ===');
console.log('Test 1:', testMessage.match(/🌟\s*\*\*/));
console.log('Test 2:', testMessage.match(/🌟\s*\*\*(.+?):/));
console.log('Test 3:', testMessage.match(/🌟\s*\*\*(.+?):\s*\$/));
console.log('Test 4:', testMessage.match(/🌟\s*\*\*(.+?):\s*\$([\d,]+)/));
console.log('Test 5:', testMessage.match(/🌟\s*\*\*(.+?):\s*\$([\d,]+(?:\.\d{2})?)/));
console.log('Test 6:', testMessage.match(/🌟\s*\*\*(.+?):\s*\$([\d,]+(?:\.\d{2})?)\s*SGD/));
console.log('Test 7:', testMessage.match(/🌟\s*\*\*(.+?):\s*\$([\d,]+(?:\.\d{2})?)\s*SGD\*\*/));

console.log('\n=== Testing Elite Plan ===');
console.log('Test 1:', testMessage.match(/⭐\s*\*\*/));
console.log('Test 2:', testMessage.match(/⭐\s*\*\*(.+?):/));
console.log('Test 3:', testMessage.match(/⭐\s*\*\*(.+?):\s*\$/));
console.log('Test 4:', testMessage.match(/⭐\s*\*\*(.+?):\s*\$([\d,]+)/));
console.log('Test 5:', testMessage.match(/⭐\s*\*\*(.+?):\s*\$([\d,]+(?:\.\d{2})?)/));
console.log('Test 6:', testMessage.match(/⭐\s*\*\*(.+?):\s*\$([\d,]+(?:\.\d{2})?)\s*SGD/));
console.log('Test 7:', testMessage.match(/⭐\s*\*\*(.+?):\s*\$([\d,]+(?:\.\d{2})?)\s*SGD\*\*/));

// Final test with full pattern
console.log('\n=== Full Pattern Tests ===');
const standardFull = testMessage.match(/🌟\s*\*\*(.+?):\s*\$?([\d,]+(?:\.\d{2})?)\s*SGD\*\*([\s\S]*?)(?=(?:⭐|👑|All prices|$))/i);
console.log('Standard Full:', standardFull ? `FOUND - ${standardFull[1]} - $${standardFull[2]}` : 'NOT FOUND');

const eliteFull = testMessage.match(/⭐\s*\*\*(.+?):\s*\$?([\d,]+(?:\.\d{2})?)\s*SGD\*\*([\s\S]*?)(?=(?:👑|All prices|$))/i);
console.log('Elite Full:', eliteFull ? `FOUND - ${eliteFull[1]} - $${eliteFull[2]}` : 'NOT FOUND');

