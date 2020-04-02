// Consider reading http://es6-features.org

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

export function isObject(obj) {
    return obj != null && obj.constructor.name === "Object";
}

// https://stackoverflow.com/a/40953718/3356840
export function clearObject(obj) {
    for (let key in obj) {
        delete obj[key];
    }
}

export function* range(target, start=0, step=1) {
    for (let i=start ; i<target ; i+=step) {yield i;}
}
assertEqualsObject([
    [ [...range(3)], [0,1,2] ],
]);

export function* enumerate(iterable) {
    let count = 0;
    for (let item of iterable) {
        //yield (item[Symbol.iterator]) ? [count++, ...item] : [count++, item];
        yield [count++, item];
    }
}
assertEqualsObject([
    [ [...enumerate(['a','b','c'])], [[0,'a'],[1, 'b'],[2,'c']] ],
    [ [...enumerate([['a','a'],['b','b'],['c','c']])], [[0,['a','a']],[1,['b','b']],[2,['c','c']]] ],
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
    [ [...zip(['a','b'],['c'])], [['a','c'],['b',null]] ],
]);

export function* chain(...iterables) {
    for (let iterable of iterables) {
        if (iterable[Symbol.iterator]) {
            yield* iterable;
        }
        else {
            yield iterable;
        }
    }
}
assertEqualsObject([
    [ [...chain(['a','b'],['c','d'])], ['a','b','c','d'] ],
    [ [...chain(['a','b'],'c','d')], ['a','b','c','d'] ],
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
assertEquals([
    [ `${buildMapFromObject({'a': 1, 'b': 2}).get('b')}`, `2` ],
]);
export function buildObjectFromMap(map) {
    // https://gist.github.com/lukehorvat/133e2293ba6ae96a35ba
    return [...map.entries()].reduce((obj, [key, value]) => (obj[key] = value, obj), {});
    //const obj = {};
    //for (let [key, value] of map) {
    //    obj[key] = value;
    //}
    //return obj
}
assertEqualsObject([
    [ buildObjectFromMap(new Map().set('a', 1).set('b', 2)), {'a': 1, 'b': 2} ],
]);


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


// https://gist.github.com/clohr/44d4aa6fb749b3abd4e7fcde82e03d29
// https://stackoverflow.com/a/44827922/3356840
export const setIntersect = (set1, set2) => [...set1].filter(num => set2.has(num))
export const setDifference = (set1, set2) => [...set1].filter(num => !set2.has(num))
export const setUnion = (set1, set2) => [...set1, ...set2]
export const isSetEqual = (a, b) => a.size === b.size && [...a].every(value => b.has(value));

// https://stackoverflow.com/a/44586654/3356840
export const hasIterationProtocol = variable => variable !== null && Symbol.iterator in Object(variable);



export const capitalize = (s) => {
    if (typeof s !== 'string') {return '';}
    return s.charAt(0).toUpperCase() + s.slice(1);
}


export function objGet(cmd, obj, fallback_return) {
    obj = obj || window;
    if (!cmd) {return obj;}
    if (typeof(cmd) == "string") {cmd = cmd.split(".");}
    if (cmd.length == 1) {return obj[cmd.shift()] || fallback_return;}
    if (cmd.length > 1) {
        var next_cmd = cmd.shift();
        var next_obj = obj[next_cmd];
        if (typeof(next_obj) == "undefined") {
            return fallback_return;
        }
        return objGet(cmd, next_obj, fallback_return);
    }
    return fallback_return;
}
export function objGetFunc(cmd, obj) {return objGet(cmd, obj, function(){})}
export function objGetObj(cmd, obj) {return objGet(cmd, obj, {})}
assertEqualsObject([
    [objGet('', {a: 1}), {a: 1}],
    [objGet('a.b.c', {a: {b: {c: 5}}}), 5],
    [objGet('a.b.d', {a: {b: {c: 5}}}), undefined],
    [objGetObj('a.b.d', {a: {b: {c: 5}}}), {}],
]);



export default {
    assertEquals,
    assertEqualsObject,
    isObject,
    range,
    enumerate,
    all,
    zip,
    chain,
    previousValueIterator,
    buildMapFromObject,
    buildObjectFromMap,
    invertMap,
    MapDefaultGet,
    setIntersect,
    setDifference,
    setUnion,
    isSetEqual,
    hasIterationProtocol,
    capitalize,
    objGet,
    objGetFunc,
    objGetObj,
}