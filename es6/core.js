// http://stackoverflow.com/a/10284006/3356840
//export const zip = rows=>rows[0].map((_,c)=>rows.map(row=>row[c]));

// http://tech.saigonist.com/b/code/python-list-comprehensions-javascript
//export const range = max => Array.from(new Array(max), (_, i) => i);  // TODO: make this a generator?

export function assertEquals(comparison_tuples) {
    for (let [a, b] of comparison_tuples) {
        //console.debug(a, b);
        console.assert(a == b, `${a} should-equal ${b}`);
    }
}
export function assertEqualsObject(comparison_tuples) {
    return assertEquals(comparison_tuples.map(v => v.map(JSON.stringify)))
};


export function* range(target, start=0, step=1) {
    for (let i=start ; i<target ; i+=step) {yield i;}
}
assertEqualsObject([
    [ [...range(3)], [0,1,2] ],
]);

export function* enumerate(iterable) {
    let count = 0;
    for (let item of iterable) {
        yield (item[Symbol.iterator]) ? [count++, ...item] : [count++, item];
    }
}
assertEqualsObject([
    [ [...enumerate(['a','b','c'])], [[0,'a'],[1, 'b'],[2,'c']] ],
    [ [...enumerate([['a','a'],['b','b'],['c','c']])], [[0,'a','a'],[1,'b','b'],[2,'c','c']] ],
]);

export function all(iterable) {
    for (let i of iterable) {
        if (!i) {return false;}
    }
    return true;
}
assertEquals([
    [ all([true, true]) , true],
    [ all([true, false]) , false],
    [ all([true, 'bob', 1]) , true],
]);

export function* zip(...iterables) {
    const iterators = [...iterables].map(iterable => iterable[Symbol.iterator]());
    while (true) {
        const iterable_items = iterators.map(iterator => iterator.next());
        if (all(iterable_items.map(i => i.done))) {break;}
        yield iterable_items.map(i => i.value);
    }
}
assertEqualsObject([
    [ [...zip(['a','b'],['c','d'])], [['a','c'],['b','d']] ],
    [ [...zip(['a','b'],['c','d'],['e','f'])], [['a','c','e'],['b','d','f']] ],
]);


export function* previousValueIterator(iterable) {
    let previous_value = null;
    for (let i of iterable) {
        yield [previous_value, i];
        previous_value = i;
    }
}
assertEquals([
    [ `${[...previousValueIterator([1,2,3])]}`, `${[ [null,1], [1,2], [2,3]] }`],
]);

export function buildMapFromObject(obj) {
    // https://stackoverflow.com/questions/36644438/how-to-convert-a-plain-object-into-an-es6-map
    // return Object.keys(obj).reduce((map, key) => map.set(key, obj[key]), new Map());
    return new Map(Object.entries(obj));
}


export function invertMap(map) {
    return new Map([...map.entries()].map((kv) => kv.reverse()));
}
assertEquals([
    [`${[...invertMap(buildMapFromObject({a:1, b:2}))]}`, '1,a,2,b'],
]);


export function MapDefaultGet(map, function_to_create_new_value) {
    // TODO: assert map is a Map
    if (typeof(function_to_create_new_value) != "function") {throw `${function_to_create_new_value} is not a function`;}
    return function(key){
        if (!map.has(key)) {
            map.set(key, function_to_create_new_value());
        }
        return map.get(key);
    };
}
(function(){
    const m = new Map();
    const mg = MapDefaultGet(m, Array);
    console.assert(typeof(mg) == "function");
    m.set('a', [1,2]);
    mg('a').push(3);
    console.assert(m.get('a').toString() == [1,2,3]);
    mg('b').push(4);
    console.assert(m.get('b').toString() == [4]);
}());


export default {
    range, enumerate, zip, previousValueIterator, buildMapFromObject, invertMap, MapDefaultGet, assertEquals, assertEqualsObject
}