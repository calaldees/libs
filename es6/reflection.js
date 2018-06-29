export function get_attr(cmd, obj, fallback_return) {
    if (typeof(cmd) == 'string') {cmd = cmd.split('.');}
    if (cmd.length == 1) {return obj[cmd.shift()];}
    if (cmd.length > 1) {
        var next_cmd = cmd.shift();
        var next_obj = obj[next_cmd];
        if (typeof(next_obj) == 'undefined') {
            //console.error(""+obj+" has no attribute "+next_cmd);
            return fallback_return;
        }
        return get_attr(cmd, next_obj, fallback_return);
    }
    //console.error('Failed to aquire ');
    return fallback_return;
}
export function get_func(cmd, obj) {return get_attr(cmd, obj, function(){})}
export function get_obj(cmd, obj) {return get_attr(cmd, obj, {})}

export default {
    get_func,
    get_obj,
}