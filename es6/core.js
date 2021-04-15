// Consider reading http://es6-features.org
// https://lodash.com/ es modules

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


// https://stackoverflow.com/a/37319954/3356840
export function filterInPlace(a, condition, thisArg) {
    let j = 0;
    a.forEach((e, i) => {
        if (condition.call(thisArg, e, i, a)) {
            if (i!==j) a[j] = e;
            j++;
        }
    });
    a.length = j;
    return a;
}
assertEqualsObject([
    [ filterInPlace([1,2,3,4,5], (i)=>i%2), [1,3,5] ],
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



// https://medium.com/@TCAS3/debounce-deep-dive-javascript-es6-e6f8d983b7a1
// https://chrisboakes.com/how-a-javascript-debounce-function-works/
export function debounce(fn, time) {
    let timeout;
    return function() {
        const functionCall = () => fn.apply(this, arguments);
        clearTimeout(timeout);
        timeout = setTimeout(functionCall, time);
    }
}


export function* diffStrIndexes(aa, bb) {
    for (let [i, [a,b]] of enumerate(zip(aa,bb))) {
        if (a != b) {
            yield i;
        }
    }
}
assertEquals([
    [`${[...diffStrIndexes('abcde', 'aBcdE')]}`, '1,4'],
]);

// https://stackoverflow.com/a/1431113/3356840
export function replaceAt(string, index, replacement) {
    return string.substr(0, index) + replacement + string.substr(index + replacement.length);
}


// https://stackoverflow.com/a/53389398/3356840
export function randomString(length) {
    return ((Math.random()+3*Number.MIN_VALUE)/Math.PI).toString(36).slice(-length)
}


export function randomSegment(segments, _func_random=Math.random) {
    console.assert(Array.isArray(segments),"segments must be an array");
    const weights = segments.map((a)=>a[1]-a[0]);
    const sum = weights.reduce((sum,i)=>sum+=i, 0);
    let r = Math.floor(_func_random()*sum);
    for (let i=0 ; i<segments.length ; i++) {
        const weight = weights[i];
        if (r - weight < 0) {
            return segments[i][0] + r;
        }
        r += -weight;
    }
}
assertEquals([
    [randomSegment([[0,10],[20,30]], ()=>0.25 ),  5],
    [randomSegment([[0,10],[20,30]], ()=>0.75 ), 25],
]);


// correct modulo operator
// https://stackoverflow.com/a/17323608
export function mod(n, m) {
    return ((n % m) + m) % m;
}
assertEquals([
    [-13 % 64, -13],
    [mod(-13, 64), 51],
]);



export class Dimension {
    constructor(...dimensions) {
        this.dimensions = [...dimensions];
    }

    get width() {return this.dimensions[0];}
    get height() {return this.dimensions[1];}
    get depth() {return this.dimensions[2];}
    get size() {return this.dimensions.reduce((prev, current) => prev * current);}

    normalise_position(...position) {
        return [ // TODO: remove duplication? map?
            mod(position[0], this.dimensions[0]),
            mod(position[1], this.dimensions[1]),
            mod(position[2], this.dimensions[2]),
        ];
    }

    index_to_position(i) {
        return [
            mod(i, this.width),
            mod(Math.floor(i/this.width), this.height),
            Math.floor(i/(this.width * this.height)),
        ];
    }

    position_to_index(...position) {
        const _position = this.normalise_position(...position);
        return (this.width * this.height * _position[2]) + (this.width * _position[1]) + _position[0];
    }
}
assertEqualsObject([
    [(new Dimension(3, 3, 3)).normalise_position(0,0,0), [0,0,0]],
    [(new Dimension(3, 3, 3)).normalise_position(-1,-1,-1), [2,2,2]],

    // index_to_position
    [(new Dimension(8, 8, 3)).index_to_position(0), [0,0,0]],
    [(new Dimension(8, 8, 3)).index_to_position(7), [7,0,0]],
    [(new Dimension(8, 8, 3)).index_to_position(8), [0,1,0]],
    [(new Dimension(8, 8, 3)).index_to_position(64), [0,0,1]],
    [(new Dimension(8, 8, 3)).index_to_position(73), [1,1,1]],
    [(new Dimension(8, 8, 3)).index_to_position(146), [2,2,2]],
    [(new Dimension(4, 8, 2)).index_to_position(46), [2,3,1]],
    [(new Dimension(4, 8, 2)).index_to_position(63), [3,7,1]],
    // position_to_index (inverse of index_to_position)
    [(new Dimension(8, 8, 3)).position_to_index(0,0,0), 0],
    [(new Dimension(8, 8, 3)).position_to_index(7,0,0), 7],
    [(new Dimension(8, 8, 3)).position_to_index(0,1,0), 8],
    [(new Dimension(8, 8, 3)).position_to_index(0,0,1), 64],
    [(new Dimension(8, 8, 3)).position_to_index(1,1,1), 73],
    [(new Dimension(8, 8, 3)).position_to_index(2,2,2), 146],
    [(new Dimension(4, 8, 2)).position_to_index(2,3,1), 46],
    [(new Dimension(4, 8, 2)).position_to_index(3,7,1), 63],
    // wrap edges
    // 0 1 2   9 10 11  18 19 20
    // 3 4 5  12 13 14  21 22 23
    // 6 7 8  15 16 17  24 25 26
    [(new Dimension(3, 3, 3)).position_to_index(-1,0,0), 2],
    [(new Dimension(3, 3, 3)).position_to_index(-2,0,0), 1],
    [(new Dimension(3, 3, 3)).position_to_index(-3,0,0), 0],
    [(new Dimension(3, 3, 3)).position_to_index(-4,0,0), 2],
    [(new Dimension(3, 3, 3)).position_to_index(0,-1,0), 6],
    [(new Dimension(3, 3, 3)).position_to_index(-1,-1,0), 8],
    [(new Dimension(3, 3, 3)).position_to_index(0,0,-1), 18],
    [(new Dimension(3, 3, 3)).position_to_index(-1,-1,-1), 26],
    [(new Dimension(3, 3, 3)).position_to_index(-2,-2,-2), 13],
    [(new Dimension(3, 3, 3)).position_to_index(1,1,1), 13],
    [(new Dimension(3, 3, 3)).position_to_index(3,3,0), 0],
]);



export function swapEndianness(bits, value) {
    return [...enumerate([...range(bits)].map(x=>2**x).map(x=>value&x))].map(([bit, x])=>[(bit+1-(bits/2))*2-1, x]).map(([shift, x])=> shift<=0 ? x << Math.abs(shift) : x >> Math.abs(shift)).reduce((acc, x)=>acc+=x, 0);
}
assertEquals([
    [swapEndianness(8,   0),   0],
    [swapEndianness(8, 255), 255],
    [swapEndianness(8,   1), 128],
    [swapEndianness(8,   2),  64],
    [swapEndianness(8,   4),  32],
    [swapEndianness(8,   8),  16],
    [swapEndianness(8,  16),   8],
    [swapEndianness(8,  32),   4],
    [swapEndianness(8,  64),   2],
    [swapEndianness(8, 128),   1],
    [swapEndianness(8, 129), 129],
    [swapEndianness(8, 130),  65],
    [swapEndianness(4,   4),   2],
    [swapEndianness(4,   2),   4],
    [swapEndianness(16, 512), 64],
    [swapEndianness(16,   1), 32768],
]);



export default {
    assertEquals,
    assertEqualsObject,
    isObject,
    clearObject,
    range,
    enumerate,
    all,
    zip,
    chain,
    previousValueIterator,
    filterInPlace,
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
    debounce,
    diffStrIndexes,
    randomString,
    randomSegment,
    mod,
    Dimension,
    swapEndianness,
}