// http://stackoverflow.com/a/10284006/3356840
export const zip = rows=>rows[0].map((_,c)=>rows.map(row=>row[c]));

// http://tech.saigonist.com/b/code/python-list-comprehensions-javascript
export const range = max => Array.from(new Array(max), (_, i) => i);