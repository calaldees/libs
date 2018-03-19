import time
import datetime


def wait_for(
        func_attempt,
        func_is_ok=lambda response: response,
        func_generate_exception=lambda response: Exception('wait_for failed'),
        seconds_to_wait=5,
        sleep_duration=1,
        ignore_exceptions=False,
):
    """
    Examples:
        # Simple
        wait_for(lambda: myobject.property_im_waiting_for)

        # Complex
        def get_data():
            class Response:
                status_code = 'failed'
                message = 'broken'
            return Response()
        wait_for(
            func_attempt=get_data,
            func_is_ok=lambda response: response.status_code == 'ok',
            func_generate_exception=lambda response: Exception(f'wait_for failed {response.message}'),
            seconds_to_wait=10,
        )

        Will repeat get_data() once perseconds for 10 seconds.
        Each time checking the return object from get_data() with func_is_ok.
        If it's not ok -> Retry again.
        If no success after seconds_to_wait, func_generate_exception is called with the last response object.
    """
    def attempt():
        response = func_attempt()
        return (func_is_ok(response), response)

    response = None
    is_ok = None
    expire_datetime = datetime.datetime.now() + datetime.timedelta(seconds=seconds_to_wait)
    while datetime.datetime.now() <= expire_datetime:
        if ignore_exceptions:
            try:
                is_ok, response = attempt()
            except Exception:
                pass
        else:
            is_ok, response = attempt()
        if is_ok:
            return response
        time.sleep(float(sleep_duration))
    raise func_generate_exception(response)
