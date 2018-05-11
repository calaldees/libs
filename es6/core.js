// http://stackoverflow.com/a/10284006/3356840
//export const zip = rows=>rows[0].map((_,c)=>rows.map(row=>row[c]));

// http://tech.saigonist.com/b/code/python-list-comprehensions-javascript
//export const range = max => Array.from(new Array(max), (_, i) => i);  // TODO: make this a generator?

export function* range(target, start=0, step=1) {
    for (let i=start ; i<target ; i+=step) {yield i;}
}

export function* zip(a, b) {
    const ai = a[Symbol.iterator]();
    const bi = b[Symbol.iterator]();
    while (true) {
        const an = ai.next();
        const bn = bi.next();
        if (an.done && bn.done) {break;}
        yield [an.value, bn.value];
    }
}

export default {
    range, zip,
}